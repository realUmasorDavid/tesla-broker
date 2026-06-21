from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile, KYCVerification, WalletTransaction, Stock, StockHolding, InvestmentPlan, UserInvestment, Order, TeslaVehicle, Notification, EmailVerificationCode
from .forms import KYCForm, ProfileUpdateForm
from decimal import Decimal
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
import requests
from .notifications import create_notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random
import string
from .email_utils import send_verification_email

User = get_user_model()

def index(request):
    vehicles = TeslaVehicle.objects.filter(is_available=True)[:4]
    
    context = {
        'vehicles': vehicles,
    }
    return render(request, 'index.html', context)

def blog(request):
    return render(request, 'blog.html')

def about(request):
    return render(request, 'about.html')

def careers(request):
    return render(request, 'careers.html')

def help(request):
    return render(request, 'help.html')

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')

def _generate_code():
    return ''.join(random.choices(string.digits, k=6))

def _issue_code(user, purpose):
    """Invalidate old codes and issue a fresh one."""
    from django.utils import timezone
    EmailVerificationCode.objects.filter(
        user=user, purpose=purpose, is_used=False
    ).update(is_used=True)
 
    code = _generate_code()
    EmailVerificationCode.objects.create(
        user       = user,
        code       = code,
        purpose    = purpose,
        expires_at = timezone.now() + timedelta(minutes=10),
    )
    return code

def login(request):
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
 
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            # Don't log in yet — send OTP first
            code = _issue_code(user, 'login')
            try:
                send_verification_email(user.email, code, 'login', user.first_name)
            except Exception:
                pass  # log silently; don't block the user
 
            # Store pending user pk in session
            request.session['pending_login_user_id'] = user.pk
            return redirect('verify_email')
 
        messages.error(request, 'Invalid email or password.')
 
    return render(request, 'login.html')
 
 
def register(request):
    first_name    = ''
    last_name     = ''
    email         = ''
    referral_code = ''
 
    if request.method == 'POST':
        first_name    = request.POST.get('first_name', '').strip()
        last_name     = request.POST.get('last_name', '').strip()
        email         = request.POST.get('email', '').strip()
        referral_code = request.POST.get('referral_code', '').strip()
        password      = request.POST.get('password', '')
        password2     = request.POST.get('password2', '')
 
        if not first_name or not last_name or not email or not password or not password2:
            messages.error(request, 'Please complete all fields.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username__iexact=email).exists() or \
             User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with that email already exists.')
        else:
            referrer_profile = None
            if referral_code:
                try:
                    referrer_profile = Profile.objects.get(referral_code__iexact=referral_code)
                except Profile.DoesNotExist:
                    messages.error(request, 'Referral code not found. Please check and try again.')
 
            if not list(messages.get_messages(request)):
                try:
                    validate_password(password)
                except ValidationError as error:
                    for msg in error.messages:
                        messages.error(request, msg)
                else:
                    # Create user but don't log in yet
                    user = User.objects.create_user(
                        username   = email,
                        email      = email,
                        password   = password,
                        first_name = first_name,
                        last_name  = last_name,
                        is_active  = True,
                    )
                    profile, _ = Profile.objects.get_or_create(user=user)
                    if referrer_profile:
                        profile.referred_by = referrer_profile
                        profile.save()
 
                    # Send OTP
                    code = _issue_code(user, 'register')
                    try:
                        send_verification_email(user.email, code, 'register', user.first_name)
                    except Exception:
                        pass
 
                    request.session['pending_login_user_id'] = user.pk
                    request.session['pending_register']       = True
                    return redirect('verify_email')
 
    return render(request, 'register.html', {
        'first_name':    first_name,
        'last_name':     last_name,
        'email':         email,
        'referral_code': referral_code,
    })
 
 
def verify_email(request):
    from django.utils import timezone
 
    user_id = request.session.get('pending_login_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('login')
 
    user        = get_object_or_404(User, pk=user_id)
    is_register = request.session.get('pending_register', False)
    purpose     = 'register' if is_register else 'login'
    error       = None
 
    if request.method == 'POST':
        action = request.POST.get('action')
 
        # ── Resend ────────────────────────────────────────────────────────
        if action == 'resend':
            code = _issue_code(user, purpose)
            try:
                send_verification_email(user.email, code, purpose, user.first_name)
                messages.success(request, 'A new code has been sent to your email.')
            except Exception:
                messages.error(request, 'Failed to resend. Please try again.')
            return redirect('verify_email')
 
        # ── Verify ────────────────────────────────────────────────────────
        entered = request.POST.get('code', '').strip()
        otp = EmailVerificationCode.objects.filter(
            user    = user,
            purpose = purpose,
            is_used = False,
        ).order_by('-created_at').first()
 
        if not otp:
            error = 'No active code found. Please request a new one.'
        elif otp.is_expired:
            error = 'This code has expired. Please request a new one.'
        elif otp.code != entered:
            error = 'Incorrect code. Please try again.'
        else:
            # ✅ Mark used and log the user in
            otp.is_used = True
            otp.save(update_fields=['is_used'])
 
            auth_login(request, user, backend='core.backends.EmailOrUsernameBackend')
 
            # Clean session
            del request.session['pending_login_user_id']
            request.session.pop('pending_register', None)
 
            if is_register:
                messages.success(request, 'Welcome! Your account has been verified.')
            else:
                messages.success(request, f'Welcome back, {user.first_name}!')
 
            return redirect('dashboard')
 
    context = {
        'email':       user.email,
        'is_register': is_register,
        'error':       error,
    }
    return render(request, 'verify_email.html', context)
    
def logout(request):
    auth_logout(request)
    return redirect('index')

@login_required
def dashboard(request):
    profile = request.user.profile

    # ── Transactions ──────────────────────────────────────────────────────────
    transactions = WalletTransaction.objects.filter(profile=profile).order_by('-created_at')[:10]

    # ── Stock holdings ────────────────────────────────────────────────────────
    stock_holdings = StockHolding.objects.filter(profile=profile).select_related('stock')
    total_stock_holding = stock_holdings.count()

    total_stock_value = Decimal('0')
    for holding in stock_holdings:
        total_stock_value += holding.shares * holding.stock.current_price

    # ── Active investments ────────────────────────────────────────────────────
    active_investments = UserInvestment.objects.filter(
        profile=profile, status='active'
    ).select_related('plan')
    active_count     = active_investments.count()
    total_active_val = sum(i.amount for i in active_investments)

    # ── Portfolio value = cash + stocks + investments ─────────────────────────
    portfolio_value = profile.available_balance + total_stock_value + total_active_val

    # ── Recent vehicle orders ─────────────────────────────────────────────────
    recent_orders = Order.objects.filter(
        profile=profile, order_type='vehicle'
    ).select_related('vehicle').order_by('-created_at')[:5]

    # ── Tesla vehicles owned (completed vehicle orders) ───────────────────────
    tesla_vehicles = Order.objects.filter(
        profile=profile, order_type='vehicle', status='completed'
    ).count()

    context = {
        'profile':             profile,
        'transactions':        transactions,
        'total_stock_holding': total_stock_holding,
        'total_stock_value':   total_stock_value,
        'active_count':        active_count,
        'total_active_val':    total_active_val,
        'portfolio_value':     portfolio_value,
        'recent_orders':       recent_orders,
        'tesla_vehicles':      tesla_vehicles,
    }
    return render(request, 'dashboard.html', context)
    
@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'profile.html', {'form': form, 'profile': profile})


@login_required
def kyc_view(request):
    profile = request.user.profile
    
    try:
        kyc = profile.kyc_verification
    except KYCVerification.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        form = KYCForm(request.POST, request.FILES, instance=kyc, tier=profile.kyc_tier)
        if form.is_valid():
            kyc_obj = form.save(commit=False)
            kyc_obj.profile = profile
            kyc_obj.save()

            # Only set to pending — do NOT advance tier here
            profile.kyc_status = 'pending'
            profile.save()

            messages.success(request, f"Your documents for {profile.kyc_tier.title()} tier have been submitted and are under review.")
            return redirect('dashboard')
    else:
        form = KYCForm(instance=kyc, tier=profile.kyc_tier)

    context = {
        'form': form,
        'profile': profile,
        'kyc': kyc,
        'current_tier': profile.kyc_tier,
    }
    return render(request, 'kyc.html', context)
    
@login_required
def wallet_view(request):
    profile = request.user.profile
    all_transactions = WalletTransaction.objects.filter(profile=profile)
    transactions = WalletTransaction.objects.filter(profile=profile).order_by('-created_at')[:10]
    
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    current_month_transactions = all_transactions.filter(
        created_at__year=current_year,
        created_at__month=current_month
    )
    
    deposits = current_month_transactions.filter(transaction_type='deposit')
    withdrawals = current_month_transactions.filter(transaction_type='withdrawal')
    
    withdrawal_total = abs(withdrawals.aggregate(Sum('amount')).get('amount__sum') or 0.00)
    deposit_total = deposits.aggregate(Sum('amount')).get('amount__sum') or 0.00
    
    active_investments = UserInvestment.objects.filter(
        profile=profile, status='active'
    ).select_related('plan')
    total_invested = sum(i.amount for i in active_investments)
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'deposit_total': deposit_total,
        'withdrawal_total': withdrawal_total,
        'total_invested': total_invested,
    }
    return render(request, 'wallet.html', context)

CRYPTO_ADDRESSES = {
    'btc': 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
    'eth': '0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
    'ltc': 'ltc1qhf7s7ajrj8ncrx8ewrzmk8aqv8rmujq2ell9x0',
}
 
 
@login_required
def deposit_view(request):
    profile = request.user.profile
 
    if request.method == 'POST':
        raw_amount = request.POST.get('amount', '0')
        method     = request.POST.get('method', '').strip().lower()
 
        try:
            amount = Decimal(raw_amount)
        except Exception:
            amount = Decimal('0')
 
        if amount <= 0:
            messages.error(request, 'Please enter a valid amount greater than $0.')
            return redirect('deposit')
 
        if method not in CRYPTO_ADDRESSES:
            messages.error(request, 'Please select a valid payment method.')
            return redirect('deposit')
 
        # Create a PENDING transaction — balance is NOT touched yet
        transaction = WalletTransaction.objects.create(
            profile=profile,
            transaction_type='deposit',
            payment_method=method,
            amount=amount,
            status='pending',
            balance_before=profile.available_balance,
            balance_after=profile.available_balance,   # unchanged until approved
            description=f'{method.upper()} deposit of ${amount}',
        )
 
        return redirect('deposit_confirm', pk=transaction.pk)
 
    # GET — pass crypto addresses so the template can inject them into JS
    context = {
        'profile':     profile,
        'btc_address': CRYPTO_ADDRESSES['btc'],
        'eth_address': CRYPTO_ADDRESSES['eth'],
        'ltc_address': CRYPTO_ADDRESSES['ltc'],
    }
    return render(request, 'deposit.html', context)
 
 
@login_required
def deposit_confirm_view(request, pk):
    transaction = get_object_or_404(
        WalletTransaction,
        pk=pk,
        profile=request.user.profile,
        transaction_type='deposit',
    )
    return render(request, 'deposit_confirm.html', {'transaction': transaction})

@login_required
def withdraw_view(request):
    profile = request.user.profile
 
    if request.method == 'POST':
        raw_amount  = request.POST.get('amount', '0')
        method      = request.POST.get('method', '').strip().lower()
        destination = request.POST.get('destination', '').strip()
 
        try:
            amount = Decimal(raw_amount)
        except Exception:
            amount = Decimal('0')
 
        # ── Validations ───────────────────────────────────────────────────
        if amount <= 0:
            messages.error(request, 'Please enter a valid amount greater than $0.')
            return redirect('withdraw')
 
        if method not in ('btc', 'eth', 'ltc', 'bank'):
            messages.error(request, 'Please select a valid withdrawal method.')
            return redirect('withdraw')
 
        if not destination:
            messages.error(request, 'Please provide a destination wallet address or bank details.')
            return redirect('withdraw')
 
        if amount > profile.available_balance:
            messages.error(request, f'Insufficient balance. Your available balance is ${profile.available_balance}.')
            return redirect('withdraw')
 
        # ── Deduct balance immediately (held pending admin approval) ──────
        balance_before = profile.available_balance
        profile.available_balance -= amount
        profile.save(update_fields=['available_balance'])
 
        # ── Create PENDING withdrawal transaction ─────────────────────────
        transaction = WalletTransaction.objects.create(
            profile=profile,
            transaction_type='withdrawal',
            payment_method=method,
            amount=amount,
            destination=destination,
            status='pending',
            balance_before=balance_before,
            balance_after=profile.available_balance,
            description=f'{method.upper()} withdrawal of ${amount} to {destination[:40]}',
        )
 
        return redirect('withdraw_confirm', pk=transaction.pk)
 
    return render(request, 'withdraw.html', {'profile': profile})
 
 
@login_required
def withdraw_confirm_view(request, pk):
    transaction = get_object_or_404(
        WalletTransaction,
        pk=pk,
        profile=request.user.profile,
        transaction_type='withdrawal',
    )
    return render(request, 'withdraw_confirm.html', {'transaction': transaction})

@login_required
def stocks_list(request):
    stocks = Stock.objects.filter(is_active=True).order_by('symbol')
    context = {'stocks': stocks}
    return render(request, 'stocks.html', context)

FINNHUB_API_KEY = 'd8l9239r01qut1f9ro7gd8l9239r01qut1f9ro80'

@login_required
def stock_detail(request, symbol):
    symbol = symbol.upper()
    
    # Fetch fresh data from Finnhub
    try:
        quote = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        ).json()
        
        profile = requests.get(
            f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}"
        ).json()
    except:
        quote = {}
        profile = {}

    # Get or create stock record
    stock, created = Stock.objects.get_or_create(
        symbol=symbol,
        defaults={
            'name': profile.get('name', symbol),
            'current_price': quote.get('c', 0),
            'previous_close': quote.get('pc', 0),
            'market_cap': profile.get('marketCapitalization'),
            'industry': profile.get('finnhubIndustry', 'N/A'),
        }
    )

    # Update latest price
    if quote.get('c'):
        stock.current_price = quote.get('c')
        stock.previous_close = quote.get('pc')
        stock.save()

    # Get user's holding
    try:
        holding = StockHolding.objects.get(profile=request.user.profile, stock=stock)
    except StockHolding.DoesNotExist:
        holding = None
    
    current_stock_value = float(holding.shares) * float(stock.current_price) if holding else 0

    context = {
        'stock': stock,
        'holding': holding,
        'change': ((stock.current_price - stock.previous_close) / stock.previous_close * 100) if stock.previous_close else 0,
        'current_stock_value': current_stock_value,
    }
    
    return render(request, 'stock_detail.html', context)


@login_required
def stock_buy(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol.upper())
    
    if request.method == 'POST':
        try:
            shares = Decimal(request.POST.get('shares', 0))
        except:
            shares = Decimal('0')

        if shares <= 0:
            messages.error(request, "Please enter a valid number of shares.")
            return redirect('stock_detail', symbol=symbol)

        total_cost = shares * stock.current_price

        if total_cost > request.user.profile.available_balance:
            messages.error(request, f"Insufficient balance. You need ${total_cost:.2f}.")
            return redirect('stock_detail', symbol=symbol)

        # Store order details in session for confirmation
        request.session['pending_stock_order'] = {
            'symbol': stock.symbol,
            'shares': float(shares),
            'price_per_share': float(stock.current_price),
            'total_cost': float(total_cost),
        }

        return redirect('stock_confirm', symbol=stock.symbol)

    return redirect('stock_detail', symbol=symbol)


@login_required
def stock_confirm(request, symbol):
    stock = get_object_or_404(Stock, symbol=symbol.upper())
    order_data = request.session.get('pending_stock_order')
 
    if not order_data or order_data['symbol'] != symbol:
        messages.error(request, "No pending order found.")
        return redirect('stocks')
 
    if request.method == 'POST':
        profile    = request.user.profile
        shares     = Decimal(str(order_data['shares']))
        total_cost = Decimal(str(order_data['total_cost']))
 
        # ── Re-validate balance ───────────────────────────────────────────
        if total_cost > profile.available_balance:
            messages.error(request, "Insufficient balance.")
            del request.session['pending_stock_order']
            return redirect('stocks')
 
        balance_before = profile.available_balance
 
        # ── Update or create holding ──────────────────────────────────────
        holding, created = StockHolding.objects.get_or_create(
            profile=profile,
            stock=stock,
            defaults={
                'shares':           Decimal('0'),
                'average_buy_price': stock.current_price,
            }
        )
 
        if not created:
            total_shares     = holding.shares + shares
            total_cost_basis = (holding.shares * holding.average_buy_price) + total_cost
            holding.average_buy_price = total_cost_basis / total_shares
 
        holding.shares += shares
        holding.save()
 
        # ── Deduct balance ────────────────────────────────────────────────
        profile.available_balance -= total_cost
        profile.save(update_fields=['available_balance'])
 
        # ── Wallet transaction (now using valid type 'stock_buy') ─────────
        WalletTransaction.objects.create(
            profile          = profile,
            transaction_type = 'stock_buy',           # valid choice now
            payment_method   = 'internal',
            amount           = -total_cost,
            status           = 'completed',
            balance_before   = balance_before,
            balance_after    = profile.available_balance,
            description      = f"Bought {shares} shares of {stock.symbol} @ ${stock.current_price:.2f}",
        )
 
        # ── Order record ──────────────────────────────────────────────────
        Order.objects.create(
            profile      = profile,
            order_type   = 'stock',
            stock        = stock,
            shares       = shares,
            total_amount = total_cost,
            status       = 'completed',   # stock orders complete immediately
        )
        
        create_notification(
            profile,
            title      = f'📈 Stock Purchase Confirmed',
            message    = f'You successfully purchased {shares} shares of {stock.symbol} ({stock.name}) at ${stock.current_price:.2f} per share. Total: ${total_cost:,.2f}.',
            notif_type = 'stock',
        )
 
        # ── Clear session ─────────────────────────────────────────────────
        del request.session['pending_stock_order']
 
        messages.success(request, f"Successfully purchased {shares} shares of {stock.symbol}!")
        return redirect('dashboard')
 
    context = {
        'stock': stock,
        'order': order_data,
    }
    return render(request, 'stock_confirm.html', context)

@login_required
def investments_view(request):
    profile = request.user.profile
 
    plans = InvestmentPlan.objects.filter(is_active=True)

    active_investments = UserInvestment.objects.filter(
        profile=profile, status='active'
    ).select_related('plan')
 
    history = UserInvestment.objects.filter(
        profile=profile, status__in=['completed', 'cancelled']
    ).select_related('plan')
    
    total_invested   = sum(i.amount          for i in UserInvestment.objects.filter(profile=profile))
    total_earned     = sum(i.expected_return for i in UserInvestment.objects.filter(profile=profile, status='completed'))
    active_count     = active_investments.count()
    total_active_val = sum(i.amount for i in active_investments)
 
    context = {
        'profile':          profile,
        'plans':            plans,
        'active_investments': active_investments,
        'history':          history,
        'total_invested':   total_invested,
        'total_earned':     total_earned,
        'active_count':     active_count,
        'total_active_val': total_active_val,
    }
    return render(request, 'investments.html', context)
 
 
@login_required
def investment_subscribe(request, plan_id):
    """POST only — deducts balance and creates UserInvestment."""
    plan = get_object_or_404(InvestmentPlan, pk=plan_id, is_active=True)
    profile = request.user.profile
 
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except Exception:
            amount = Decimal('0')
 
        # Validations
        if amount < plan.min_amount:
            messages.error(request, f'Minimum investment for {plan.name} is ${plan.min_amount:,.2f}.')
            return redirect('investments')
 
        if plan.max_amount and amount > plan.max_amount:
            messages.error(request, f'Maximum investment for {plan.name} is ${plan.max_amount:,.2f}.')
            return redirect('investments')
 
        if amount > profile.available_balance:
            messages.error(request, f'Insufficient balance. Your available balance is ${profile.available_balance:,.2f}.')
            return redirect('investments')
 
        # Calculate return
        expected_return = (amount * plan.roi_percent / Decimal('100')).quantize(Decimal('0.01'))
        matures_at      = timezone.now() + timedelta(days=plan.duration_days)
 
        # Deduct balance
        balance_before             = profile.available_balance
        profile.available_balance -= amount
        profile.save(update_fields=['available_balance'])
 
        # Create investment record
        UserInvestment.objects.create(
            profile         = profile,
            plan            = plan,
            amount          = amount,
            expected_return = expected_return,
            matures_at      = matures_at,
            balance_before  = balance_before,
            balance_after   = profile.available_balance,
        )
        
        create_notification(
            profile,
            title      = f'📊 Investment Started',
            message    = f'You have successfully invested ${amount:,.2f} in the {plan.name}. Expected return: ${expected_return:,.2f}. Matures on {matures_at.strftime("%b %d, %Y")}.',
            notif_type = 'investment',
        )
 
        # Log as wallet transaction
        WalletTransaction.objects.create(
            profile          = profile,
            transaction_type = 'investment',
            payment_method   = 'internal',
            amount           = -amount,
            status           = 'completed',
            balance_before   = balance_before,
            balance_after    = profile.available_balance,
            description      = f'Invested ${amount:,.2f} in {plan.name} ({plan.roi_percent}% ROI)',
        )
 
        messages.success(request, f'🎉 Successfully invested ${amount:,.2f} in {plan.name}! It matures on {matures_at.strftime("%b %d, %Y")}.')
        return redirect('investments')
 
    return redirect('investments')

@login_required
def portfolio_view(request):
    profile = request.user.profile
 
    # ── Stock holdings ────────────────────────────────────────────────────────
    stock_holdings = StockHolding.objects.filter(
        profile=profile
    ).select_related('stock')
 
    holdings_data = []
    total_stock_value = Decimal('0')
    for h in stock_holdings:
        current_value = h.shares * h.stock.current_price
        total_stock_value += current_value
        holdings_data.append({
            'symbol':        h.stock.symbol,
            'name':          h.stock.name,
            'shares':        h.shares,
            'current_price': h.stock.current_price,
            'current_value': current_value,
        })
 
    # ── Active investments ────────────────────────────────────────────────────
    active_investments = UserInvestment.objects.filter(
        profile=profile, status='active'
    ).select_related('plan')
    total_investment_value = sum(i.amount for i in active_investments)
 
    # ── Recent transactions (last 6) ──────────────────────────────────────────
    recent_transactions = WalletTransaction.objects.filter(
        profile=profile
    ).order_by('-created_at')[:6]
 
    # ── Portfolio totals ──────────────────────────────────────────────────────
    cash_balance       = profile.available_balance
    total_portfolio    = cash_balance + total_stock_value + total_investment_value
 
    # Allocation percentages for chart (guard div-by-zero)
    if total_portfolio > 0:
        cash_pct   = round(float(cash_balance)         / float(total_portfolio) * 100, 1)
        stocks_pct = round(float(total_stock_value)    / float(total_portfolio) * 100, 1)
        invest_pct = round(float(total_investment_value) / float(total_portfolio) * 100, 1)
    else:
        cash_pct = stocks_pct = invest_pct = 0
 
    # Total earned from completed investments
    total_earned = sum(
        i.expected_return
        for i in UserInvestment.objects.filter(profile=profile, status='completed')
    )
 
    context = {
        'profile':               profile,
        'holdings_data':         holdings_data,
        'active_investments':    active_investments,
        'recent_transactions':   recent_transactions,
        'total_stock_value':     total_stock_value,
        'total_investment_value': total_investment_value,
        'cash_balance':          cash_balance,
        'total_portfolio':       total_portfolio,
        'total_earned':          total_earned,
        'cash_pct':              cash_pct,
        'stocks_pct':            stocks_pct,
        'invest_pct':            invest_pct,
        'active_inv_count':      active_investments.count(),
    }
    return render(request, 'portfolio.html', context)

@login_required
def inventory_view(request):
    """Vehicle listing with optional model filter."""
    model_filter = request.GET.get('model', '').strip()
 
    vehicles = TeslaVehicle.objects.filter(is_available=True)
    if model_filter:
        vehicles = vehicles.filter(model_name__icontains=model_filter)
    vehicles = vehicles.order_by('model_name', 'price')
 
    # Distinct model names for filter tabs
    all_models = TeslaVehicle.objects.filter(
        is_available=True
    ).values_list('model_name', flat=True).distinct().order_by('model_name')
 
    context = {
        'profile':      request.user.profile,
        'vehicles':     vehicles,
        'all_models':   all_models,
        'model_filter': model_filter,
    }
    return render(request, 'inventory.html', context)
 
 
@login_required
def vehicle_detail_view(request, pk):
    """Single vehicle detail page."""
    vehicle = get_object_or_404(TeslaVehicle, pk=pk, is_available=True)
    profile = request.user.profile
 
    can_afford = profile.available_balance >= vehicle.price
 
    context = {
        'profile':    profile,
        'vehicle':    vehicle,
        'can_afford': can_afford,
    }
    return render(request, 'vehicle_detail.html', context)
 
 
@login_required
def vehicle_order_view(request, pk):
    """POST — store order in session, redirect to confirm."""
    vehicle = get_object_or_404(TeslaVehicle, pk=pk, is_available=True)
    profile = request.user.profile
 
    if request.method == 'POST':
        if vehicle.price > profile.available_balance:
            messages.error(request, f'Insufficient balance. You need ${vehicle.price:,.2f} but have ${profile.available_balance:,.2f}.')
            return redirect('vehicle_detail', pk=pk)
 
        if vehicle.stock_quantity < 1:
            messages.error(request, 'This vehicle is currently out of stock.')
            return redirect('vehicle_detail', pk=pk)
 
        # Store in session for confirmation step
        request.session['pending_vehicle_order'] = {
            'vehicle_id': vehicle.pk,
            'price':      float(vehicle.price),
        }
        return redirect('vehicle_order_confirm', pk=vehicle.pk)
 
    return redirect('vehicle_detail', pk=pk)
 
 
@login_required
def vehicle_order_confirm_view(request, pk):
    """GET — show confirm page. POST — execute purchase."""
    vehicle = get_object_or_404(TeslaVehicle, pk=pk, is_available=True)
    profile = request.user.profile
    order_data = request.session.get('pending_vehicle_order')
 
    if not order_data or order_data.get('vehicle_id') != pk:
        messages.error(request, 'No pending order found.')
        return redirect('inventory')
 
    if request.method == 'POST':
        # Re-validate
        if vehicle.price > profile.available_balance:
            messages.error(request, 'Insufficient balance.')
            return redirect('vehicle_detail', pk=pk)
 
        if vehicle.stock_quantity < 1:
            messages.error(request, 'This vehicle is no longer available.')
            return redirect('inventory')
 
        balance_before             = profile.available_balance
        profile.available_balance -= vehicle.price
        profile.save(update_fields=['available_balance'])
 
        # Reduce stock
        vehicle.stock_quantity -= 1
        if vehicle.stock_quantity == 0:
            vehicle.is_available = False
        vehicle.save(update_fields=['stock_quantity', 'is_available'])
 
        # Create order
        order = Order.objects.create(
            profile      = profile,
            order_type   = 'vehicle',
            vehicle      = vehicle,
            total_amount = vehicle.price,
            status       = 'pending',
        )
        
        create_notification(
            profile,
            title      = f'🚗 Vehicle Order Placed',
            message    = f'Your order for a {vehicle.model_name} {vehicle.variant} has been placed successfully. Our team will contact you with delivery details shortly.',
            notif_type = 'vehicle',
        )
 
        # Wallet transaction
        WalletTransaction.objects.create(
            profile          = profile,
            transaction_type = 'purchase',
            payment_method   = 'internal',
            amount           = -vehicle.price,
            status           = 'completed',
            balance_before   = balance_before,
            balance_after    = profile.available_balance,
            description      = f'Vehicle purchase: {vehicle.model_name} {vehicle.variant} (Order #{order.pk})',
        )
 
        # Clear session
        del request.session['pending_vehicle_order']
 
        messages.success(request, f'🎉 Order placed for {vehicle.model_name} {vehicle.variant}! Our team will be in touch shortly.')
        return redirect('vehicle_order_success', pk=order.pk)
 
    context = {
        'profile': profile,
        'vehicle': vehicle,
        'order_data': order_data,
    }
    return render(request, 'vehicle_order_confirm.html', context)
 
 
@login_required
def vehicle_order_success_view(request, pk):
    """Order success/receipt page."""
    order = get_object_or_404(Order, pk=pk, profile=request.user.profile, order_type='vehicle')
    return render(request, 'vehicle_order_success.html', {'order': order, 'profile': request.user.profile})

@login_required
def orders_view(request):
    profile       = request.user.profile
    status_filter = request.GET.get('status', '').strip().lower()
 
    # ── All orders (vehicle + stock) from Order model ─────────────────────
    all_orders = Order.objects.filter(profile=profile).select_related(
        'vehicle', 'stock'
    ).order_by('-created_at')
 
    if status_filter in ('pending', 'processing', 'completed', 'cancelled'):
        all_orders = all_orders.filter(status=status_filter)
 
    orders = []
    for o in all_orders:
        if o.order_type == 'vehicle' and o.vehicle:
            name        = f"{o.vehicle.model_name} {o.vehicle.variant}"
            reorder_url = f"/inventory/{o.vehicle.pk}/"
        elif o.order_type == 'stock' and o.stock:
            name        = f"{o.stock.symbol} — {o.shares} share{'s' if o.shares != 1 else ''}"
            reorder_url = f"/stocks/{o.stock.symbol}/"
        else:
            name        = "Order"
            reorder_url = None
 
        orders.append({
            'type':        o.order_type,
            'id':          o.pk,
            'name':        name,
            'amount':      o.total_amount,
            'status':      o.status,
            'date':        o.created_at,
            'reorder_url': reorder_url,
        })
 
    # ── Summary counts (always unfiltered) ───────────────────────────────
    base         = Order.objects.filter(profile=profile)
    total_count  = base.count()
    pending_count    = base.filter(status='pending').count()
    completed_count  = base.filter(status='completed').count()
 
    context = {
        'profile':         profile,
        'orders':          orders,
        'status_filter':   status_filter,
        'total_count':     total_count,
        'pending_count':   pending_count,
        'completed_count': completed_count,
    }
    return render(request, 'orders.html', context)

@login_required
def notifications_view(request):
    NOTIFICATION_TYPE_LABELS = [
        ('deposit',    'Deposits'),
        ('withdrawal', 'Withdrawals'),
        ('stock',      'Stocks'),
        ('investment', 'Investments'),
        ('vehicle',    'Vehicles'),
        ('kyc',        'KYC'),
    ]

    profile = request.user.profile
    notif_type_filter = request.GET.get('type', '').strip()
 
    notifications = Notification.objects.filter(profile=profile)
    if notif_type_filter:
        notifications = notifications.filter(notif_type=notif_type_filter)
 
    unread_count = Notification.objects.filter(profile=profile, is_read=False).count()
 
    context = {
        'profile':            profile,
        'notifications':      notifications,
        'unread_count':       unread_count,
        'notif_type_filter':  notif_type_filter,
        'notification_types': NOTIFICATION_TYPE_LABELS,
    }
    return render(request, 'notifications.html', context)
 
 
@login_required
@require_POST
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, profile=request.user.profile)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return JsonResponse({'status': 'ok'})
 
 
@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(
        profile=request.user.profile, is_read=False
    ).update(is_read=True)
    return JsonResponse({'status': 'ok'})
 
 
@login_required
def notifications_unread_count(request):
    """Lightweight endpoint polled by the topbar bell every 30s."""
    count = Notification.objects.filter(
        profile=request.user.profile, is_read=False
    ).count()
    return JsonResponse({'count': count})