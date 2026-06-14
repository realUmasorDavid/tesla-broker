from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile, KYCVerification, WalletTransaction
from .forms import KYCForm, ProfileUpdateForm
from decimal import Decimal

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
                    if referrer_profile:
                        user.profile.referred_by = referrer_profile
                        user.profile.save()

                    auth_login(request, user)
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
    return render(request, 'dashboard.html', {
        'balance': '40,210.30',
        'portfolio_value': '72,033',
        'investments_value': '5,669',
        'stock_holdings': '26,153',
        'tesla_vehicles': 1,
        # 'recent_orders': Order.objects.filter(user=request.user).order_by('-date')[:3],
    })
    
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
    transactions = WalletTransaction.objects.filter(profile=profile).order_by('-created_at')[:10]
    
    context = {
        'profile': profile,
        'transactions': transactions,
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
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        profile = request.user.profile
        
        if amount <= 0:
            messages.error(request, "Please enter a valid amount.")
        elif amount > profile.available_balance:
            messages.error(request, "Insufficient balance.")
        else:
            profile.available_balance -= amount
            profile.save()

            WalletTransaction.objects.create(
                profile=profile,
                transaction_type='withdrawal',
                amount=-amount,
                balance_before=profile.available_balance + amount,
                balance_after=profile.available_balance,
                description=f"Withdrawal of ${amount}"
            )
            messages.success(request, f"${amount} withdrawn successfully!")
            return redirect('wallet')
    
    return render(request, 'withdraw.html')