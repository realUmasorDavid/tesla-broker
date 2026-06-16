from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile, KYCVerification, WalletTransaction, Stock, StockHolding, InvestmentPlan, UserInvestment
from .forms import KYCForm, ProfileUpdateForm
from decimal import Decimal
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
import requests

User = get_user_model()

def index(request):
    return render(request, 'index.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            auth_login(request, user)
            return redirect('dashboard')

        messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')

def register(request):
    first_name = ''
    last_name = ''
    email = ''
    referral_code = ''

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        referral_code = request.POST.get('referral_code', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not first_name or not last_name or not email or not password or not password2:
            messages.error(request, 'Please complete all fields.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with that email already exists.')
        else:
            referrer_profile = None
            if referral_code:
                try:
                    referrer_profile = Profile.objects.get(referral_code__iexact=referral_code)
                except Profile.DoesNotExist:
                    messages.error(request, 'Referral code not found. Please check and try again.')
                    referrer_profile = None

            if not messages.get_messages(request):
                try:
                    validate_password(password)
                except ValidationError as error:
                    for message in error.messages:
                        messages.error(request, message)
                else:
                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    profile, _ = Profile.objects.get_or_create(user=user)
                    if referrer_profile:
                        profile.referred_by = referrer_profile
                        profile.save()

                    auth_login(request, user, backend='core.backends.EmailOrUsernameBackend')
                    messages.success(request, 'Welcome, your account has been created successfully.')
                    return redirect('dashboard')

    return render(request, 'register.html', {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'referral_code': referral_code,
    })

@login_required
def dashboard(request):
    profile = request.user.profile
    
    # Get recent transactions
    transactions = WalletTransaction.objects.filter(profile=profile).order_by('-created_at')[:10]

    # Calculate total stock holdings value
    total_stock_holding = StockHolding.objects.filter(profile=profile).select_related('stock').count()
    stock_holdings = StockHolding.objects.filter(profile=profile).select_related('stock')
    
    total_stock_value = 0
    for holding in stock_holdings:
        stock_price = round(float(holding.stock.current_price), 2)
        total_stock_value += float(holding.shares) * stock_price

    context = {
        'profile': profile,
        'transactions': transactions,
        'total_stock_holding': total_stock_holding,
        'total_stock_value': total_stock_value,
        'portfolio_value': total_stock_value,  # You can expand this later
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
    
    # If already verified
    if profile.kyc_status == 'verified':
        messages.info(request, "Your KYC is already verified.")
        return redirect('dashboard')
    
    try:
        kyc = profile.kyc_verification
    except KYCVerification.DoesNotExist:
        kyc = None

    if request.method == 'POST':
        form = KYCForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc_obj = form.save(commit=False)
            kyc_obj.profile = profile
            kyc_obj.save()
            
            profile.kyc_status = 'pending'
            profile.save()
            
            messages.success(request, "KYC documents submitted successfully! We will review them shortly.")
            return redirect('dashboard')
    else:
        form = KYCForm(instance=kyc)

    return render(request, 'kyc.html', {
        'form': form,
        'profile': profile,
        'kyc': kyc
    })
    
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
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'deposit_total': deposit_total,
        'withdrawal_total': withdrawal_total,
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
        profile = request.user.profile
        shares = Decimal(order_data['shares'])
        total_cost = Decimal(order_data['total_cost'])

        # Execute the purchase
        holding, created = StockHolding.objects.get_or_create(
            profile=profile,
            stock=stock,
            defaults={'shares': 0, 'average_buy_price': stock.current_price}
        )

        if not created:
            total_shares = holding.shares + shares
            total_cost_basis = (holding.shares * holding.average_buy_price) + total_cost
            holding.average_buy_price = total_cost_basis / total_shares

        holding.shares += shares
        holding.save()

        # Deduct balance
        profile.available_balance -= total_cost
        profile.save()

        # Record transaction
        WalletTransaction.objects.create(
            profile=profile,
            transaction_type='stock_buy',
            amount=-total_cost,
            balance_before=profile.available_balance + total_cost,
            balance_after=profile.available_balance,
            description=f"Bought {shares} shares of {stock.symbol} @ ${stock.current_price:.2f}"
        )

        # Clear session
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