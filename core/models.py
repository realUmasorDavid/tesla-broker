# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import secrets


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
 
    # ── Referral ───────────────────────────────────────────────────────────
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by   = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='referrals'
    )
 
    # ── Personal Info ──────────────────────────────────────────────────────
    phone_number  = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address       = models.TextField(blank=True)
    city          = models.CharField(max_length=100, blank=True)
    country       = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
 
    # ── Financial ──────────────────────────────────────────────────────────
    total_balance     = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
 
    # ── KYC ───────────────────────────────────────────────────────────────
    # No tiers — single one-time verification
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('not_submitted', 'Not Submitted'),
            ('pending',       'Under Review'),
            ('verified',      'Verified'),
            ('rejected',      'Rejected'),
        ],
        default='not_submitted'
    )
 
    # ── Timestamps ─────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = secrets.token_urlsafe(8).upper()[:12]
        super().save(*args, **kwargs)
 
    @property
    def is_kyc_verified(self):
        return self.kyc_status == 'verified'
 
    def __str__(self):
        return f"{self.user.username}'s Profile"


class KYCVerification(models.Model):
    """
    Single one-time KYC verification.
    User picks ONE document type and uploads front + back + selfie.
    """
 
    ID_TYPE_CHOICES = [
        ('national_id',       'National ID Card'),
        ('drivers_license',   "Driver's License"),
    ]
 
    ADDRESS_TYPE_CHOICES = [
        ('utility_bill',      'Utility Bill'),
        ('bank_statement',    'Bank Statement'),
        ('rental_agreement',  'Rental Agreement'),
        ('government_letter', 'Government Letter'),
    ]
 
    profile = models.OneToOneField(
        'Profile', on_delete=models.CASCADE, related_name='kyc_verification'
    )
 
    # ── ID document (user picks one type) ─────────────────────────────────
    id_type        = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=True)
    id_number      = models.CharField(max_length=100, blank=True)
    id_front       = models.ImageField(upload_to='kyc/ids/', blank=True)
    id_back        = models.ImageField(upload_to='kyc/ids/', blank=True)  # not required for passport
 
    # ── Selfie ─────────────────────────────────────────────────────────────
    selfie         = models.ImageField(upload_to='kyc/selfies/', blank=True)
 
    # ── Proof of address (optional but useful for higher limits) ───────────
    address_type   = models.CharField(max_length=30, choices=ADDRESS_TYPE_CHOICES, blank=True)
    proof_of_address = models.ImageField(upload_to='kyc/address/', blank=True)
 
    # ── Admin fields ───────────────────────────────────────────────────────
    verification_date = models.DateTimeField(null=True, blank=True)
    reviewed_by    = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='kyc_reviews'
    )
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return f"KYC — {self.profile.user.username} ({self.profile.kyc_status})"

class WalletTransaction(models.Model):
 
    TRANSACTION_TYPES = [
        ('deposit',    'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer',   'Transfer'),
        ('investment', 'Investment'),
        ('return',     'Investment Return'),
        ('purchase',   'Vehicle Purchase'),
        ('stock_buy',  'Stock Purchase'),   # ← ADD THIS
        ('stock_sell', 'Stock Sale'),       # ← ADD THIS (for future use)
    ]
 
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
    ]
 
    PAYMENT_METHODS = [
        ('btc', 'Bitcoin'),
        ('eth', 'Ethereum'),
        ('ltc', 'Litecoin'),
        ('bank', 'Bank Transfer'),
        ('card', 'Card'),
        ('internal', 'Internal'),
    ]
 
    profile          = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    payment_method   = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='internal')
    amount           = models.DecimalField(max_digits=14, decimal_places=2)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    balance_before   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_after    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    destination = models.TextField(blank=True, default='')
    description      = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    confirmed_at     = models.DateTimeField(null=True, blank=True)  # set when admin approves
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f'{self.profile.user.username} | {self.transaction_type} | ${self.amount} | {self.status}'


class Stock(models.Model):
    """Available stocks for trading"""
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    company_logo = models.URLField(blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    previous_close = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    market_cap = models.BigIntegerField(null=True, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class StockHolding(models.Model):
    """User's owned stocks"""
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='stock_holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    
    shares = models.DecimalField(max_digits=12, decimal_places=4)
    average_buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('profile', 'stock')

    def __str__(self):
        return f"{self.profile.user.username} - {self.stock.symbol} ({self.shares} shares)"

class InvestmentPlan(models.Model):
    """Admin-defined fixed investment plans (e.g. Basic 5%, Gold 15%)"""
    CYCLE_CHOICES = [
        ('daily',   'Daily'),
        ('weekly',  'Weekly'),
        ('monthly', 'Monthly'),
        ('bi-annually', 'Bi-Anually'),
        ('annually', 'Anually'),
    ]

    name          = models.CharField(max_length=100)
    description   = models.TextField(blank=True)
    roi_percent   = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)   # e.g. 15.00
    duration_days = models.PositiveIntegerField(default=180)                          # e.g. 30
    cycle         = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='monthly')
    min_amount    = models.DecimalField(max_digits=14, decimal_places=2, default=100)
    max_amount    = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    is_active     = models.BooleanField(default=True)
    # Controls the accent colour on the plan card — use Tailwind keyword: gray / blue / yellow / green / purple
    badge_color   = models.CharField(max_length=30, default='gray')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['roi_percent']

    def __str__(self):
        return f"{self.name} ({self.roi_percent}% / {self.duration_days}d)"


class UserInvestment(models.Model):
    """A user's active or historical investment in a plan."""
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    profile         = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='user_investments')
    plan            = models.ForeignKey(InvestmentPlan, on_delete=models.PROTECT, related_name='subscriptions')
    amount          = models.DecimalField(max_digits=14, decimal_places=2)
    # Locked in at subscription time so price changes don't shift it
    expected_return = models.DecimalField(max_digits=14, decimal_places=2)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    started_at      = models.DateTimeField(auto_now_add=True)
    matures_at      = models.DateTimeField()       # started_at + duration_days
    paid_out_at     = models.DateTimeField(null=True, blank=True)

    balance_before  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_after   = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.profile.user.username} — {self.plan.name} ${self.amount} [{self.status}]"

    @property
    def progress_percent(self):
        from django.utils import timezone
        now     = timezone.now()
        total   = (self.matures_at - self.started_at).total_seconds()
        elapsed = (now - self.started_at).total_seconds()
        if total <= 0:
            return 100
        return min(100, max(0, int(elapsed / total * 100)))

    @property
    def is_matured(self):
        from django.utils import timezone
        return timezone.now() >= self.matures_at

    @property
    def total_payout(self):
        return self.amount + self.expected_return


class TeslaVehicle(models.Model):
    """Tesla Inventory"""
    model_name = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    range_miles = models.IntegerField()
    zero_to_sixty = models.DecimalField(max_digits=4, decimal_places=1)
    top_speed = models.IntegerField()
    
    image = models.ImageField(upload_to='vehicles/', blank=True)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=5)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} {self.variant}"


class Order(models.Model):
    """Orders for vehicles or stocks"""
    ORDER_TYPES = [('vehicle', 'Vehicle'), ('stock', 'Stock')]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    
    # Vehicle order
    vehicle = models.ForeignKey(TeslaVehicle, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Stock order
    stock = models.ForeignKey(Stock, on_delete=models.SET_NULL, null=True, blank=True)
    shares = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.order_type == 'vehicle':
            return f"Vehicle Order #{self.id} - {self.profile.user.username}"
        return f"Stock Order #{self.id} - {self.profile.user.username}"


class ReferralBonus(models.Model):
    """Track referral rewards"""
    referrer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referral_bonuses')
    referred_user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referred_by_bonus')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Referral bonus from {self.referrer.user.username} → {self.referred_user.user.username}"
    
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('deposit',    'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('stock',      'Stock'),
        ('investment', 'Investment'),
        ('vehicle',    'Vehicle Order'),
        ('kyc',        'KYC'),
        ('general',    'General'),
    ]
 
    profile    = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.profile.user.username} — {self.title} ({'read' if self.is_read else 'unread'})"
    
class EmailVerificationCode(models.Model):
    """Short-lived 6-digit OTP for login and registration verification."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code       = models.CharField(max_length=6)
    purpose    = models.CharField(max_length=20, choices=[('login', 'Login'), ('register', 'Register')])
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
 
    class Meta:
        ordering = ['-created_at']
 
    def __str__(self):
        return f"{self.user.email} — {self.code} ({self.purpose})"
 
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at