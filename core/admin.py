# admin.py
from django.utils import timezone
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .notifications import create_notification
from .models import (
    Profile, KYCVerification, WalletTransaction, Stock, 
    StockHolding, InvestmentPlan, TeslaVehicle, 
    Order, ReferralBonus, InvestmentPlan, UserInvestment, PaymentMethod
)
from .email_utils import send_deposit_received_email, send_withdrawal_completed_email


# ====================== Inline Models ======================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class KYCVerificationInline(admin.StackedInline):
    model = KYCVerification
    can_delete = False
    verbose_name_plural = 'KYC Verification'


class StockHoldingInline(admin.TabularInline):
    model = StockHolding
    extra = 0


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('balance_before', 'balance_after', 'created_at', 'confirmed_at')


# ====================== Custom User Admin ======================

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline, KYCVerificationInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_kyc_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__kyc_status',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__referral_code')

    def get_kyc_status(self, obj):
        return obj.profile.kyc_status if hasattr(obj, 'profile') else '-'
    get_kyc_status.short_description = 'KYC Status'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ====================== Actions ======================

@admin.action(description='✅ Approve Deposits')
def approve_deposits(modeladmin, request, queryset):
    approved = 0
    for tx in queryset.filter(transaction_type='deposit', status='pending'):
        profile = tx.profile
        balance_before = profile.available_balance
        profile.available_balance += tx.amount
        profile.total_balance     += tx.amount
        profile.save(update_fields=['available_balance', 'total_balance'])
 
        tx.status       = 'completed'
        tx.balance_before = balance_before
        tx.balance_after  = profile.available_balance
        tx.confirmed_at   = timezone.now()
        tx.save()

        send_deposit_received_email(
            to_email=profile.user.email,
            first_name=profile.user.get_full_name() or profile.user.username,
            amount=float(tx.amount),
            reference_number=tx.pk
        )
 
        create_notification(
            profile,
            title      = '✅ Deposit Approved',
            message    = f'Your deposit of ${tx.amount:,.2f} via {tx.get_payment_method_display()} has been approved and credited to your account.',
            notif_type = 'deposit',
        )
        approved += 1
    modeladmin.message_user(request, f'✅ {approved} deposit(s) approved.', messages.SUCCESS)
 
 
@admin.action(description='❌ Reject Deposits')
def reject_deposits(modeladmin, request, queryset):
    rejected = 0
    for tx in queryset.filter(transaction_type='deposit', status='pending'):
        tx.status = 'failed'
        tx.save()
 
        create_notification(
            tx.profile,
            title      = '❌ Deposit Rejected',
            message    = f'Your deposit of ${tx.amount:,.2f} via {tx.get_payment_method_display()} could not be verified and has been rejected. Please contact support if you believe this is an error.',
            notif_type = 'deposit',
        )
        rejected += 1
    modeladmin.message_user(request, f'❌ {rejected} deposit(s) rejected.', messages.SUCCESS)
 
 
@admin.action(description='✅ Approve Withdrawals')
def approve_withdrawals(modeladmin, request, queryset):
    approved = 0
    for tx in queryset.filter(transaction_type='withdrawal', status='pending'):
        tx.status       = 'completed'
        tx.confirmed_at = timezone.now()
        tx.save()

        send_withdrawal_completed_email(
            to_email=tx.profile.user.email,
            first_name=tx.profile.user.get_full_name() or tx.profile.user.username,
            amount=float(tx.amount),
            reference_number=tx.pk
        )
 
        create_notification(
            tx.profile,
            title      = '✅ Withdrawal Approved',
            message    = f'Your withdrawal of ${abs(tx.amount):,.2f} to {tx.destination[:40]} has been approved and is being processed.',
            notif_type = 'withdrawal',
        )
        approved += 1
    modeladmin.message_user(request, f'✅ {approved} withdrawal(s) approved.', messages.SUCCESS)
 
 
@admin.action(description='❌ Reject Withdrawals (Restore Balance)')
def reject_withdrawals(modeladmin, request, queryset):
    rejected = 0
    for tx in queryset.filter(transaction_type='withdrawal', status='pending'):
        profile = tx.profile
        profile.available_balance += abs(tx.amount)
        profile.save()
 
        tx.status       = 'failed'
        tx.balance_after  = profile.available_balance
        tx.confirmed_at   = timezone.now()
        tx.save()
 
        create_notification(
            profile,
            title      = '❌ Withdrawal Rejected',
            message    = f'Your withdrawal of ${abs(tx.amount):,.2f} was rejected and ${abs(tx.amount):,.2f} has been returned to your balance.',
            notif_type = 'withdrawal',
        )
        rejected += 1
    modeladmin.message_user(request, f'❌ {rejected} withdrawal(s) rejected and balance restored.', messages.SUCCESS)
 
 
@admin.action(description='✅ Approve & Pay Out Investments')
def approve_investment_payouts(modeladmin, request, queryset):
    from .notifications import create_notification as _notif
    paid = 0
    for inv in queryset.filter(status='active'):
        profile = inv.profile
        payout  = inv.amount + inv.expected_return
 
        balance_before             = profile.available_balance
        profile.available_balance += payout
        profile.total_balance     += inv.expected_return
        profile.save(update_fields=['available_balance', 'total_balance'])
 
        inv.status      = 'completed'
        inv.paid_out_at = timezone.now()
        inv.save()
 
        WalletTransaction.objects.create(
            profile          = profile,
            transaction_type = 'return',
            payment_method   = 'internal',
            amount           = payout,
            status           = 'completed',
            balance_before   = balance_before,
            balance_after    = profile.available_balance,
            description      = f'Investment payout: {inv.plan.name} — principal ${inv.amount} + return ${inv.expected_return}',
        )
 
        _notif(
            profile,
            title      = '💰 Investment Payout Received',
            message    = f'Your {inv.plan.name} investment has matured! ${inv.amount:,.2f} principal + ${inv.expected_return:,.2f} return (${payout:,.2f} total) has been credited to your account.',
            notif_type = 'investment',
        )
        paid += 1
    modeladmin.message_user(request, f'✅ {paid} investment(s) paid out.', messages.SUCCESS)
 
 
@admin.action(description='❌ Cancel Investments (Restore Principal)')
def cancel_investments(modeladmin, request, queryset):
    from .notifications import create_notification as _notif
    cancelled = 0
    for inv in queryset.filter(status='active'):
        profile = inv.profile
        balance_before             = profile.available_balance
        profile.available_balance += inv.amount
        profile.save(update_fields=['available_balance'])
 
        inv.status = 'cancelled'
        inv.save()
 
        WalletTransaction.objects.create(
            profile          = profile,
            transaction_type = 'return',
            payment_method   = 'internal',
            amount           = inv.amount,
            status           = 'completed',
            balance_before   = balance_before,
            balance_after    = profile.available_balance,
            description      = f'Investment cancelled — principal refunded for {inv.plan.name}',
        )
 
        _notif(
            profile,
            title      = '❌ Investment Cancelled',
            message    = f'Your {inv.plan.name} investment has been cancelled. Your principal of ${inv.amount:,.2f} has been refunded to your account.',
            notif_type = 'investment',
        )
        cancelled += 1
    modeladmin.message_user(request, f'❌ {cancelled} investment(s) cancelled and principal restored.', messages.SUCCESS)
 
 
@admin.action(description='✅ Approve KYC — mark as verified')
def approve_kyc(modeladmin, request, queryset):
    approved = 0
    for kyc in queryset.select_related('profile'):
        if kyc.profile.kyc_status != 'pending':
            continue
        kyc.profile.kyc_status  = 'verified'
        kyc.profile.save(update_fields=['kyc_status'])
        kyc.verification_date   = timezone.now()
        kyc.reviewed_by         = request.user
        kyc.save(update_fields=['verification_date', 'reviewed_by'])

        send_kyc_approved_email(
            to_email=profile.user.email,
            first_name=profile.user.get_full_name() or profile.user.username
        )
        
        approved += 1
    if approved:
        modeladmin.message_user(request, f'✅ {approved} KYC submission(s) approved.', messages.SUCCESS)
 
 
@admin.action(description='❌ Reject KYC — request resubmission')
def reject_kyc(modeladmin, request, queryset):
    rejected = 0
    for kyc in queryset.select_related('profile'):
        if kyc.profile.kyc_status not in ('pending', 'verified'):
            continue
        kyc.profile.kyc_status = 'rejected'
        kyc.profile.save(update_fields=['kyc_status'])
        kyc.reviewed_by = request.user
        kyc.save(update_fields=['reviewed_by'])
        rejected += 1
    if rejected:
        modeladmin.message_user(request, f'❌ {rejected} KYC submission(s) rejected.', messages.SUCCESS)

# ====================== Main Models ======================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display    = ('user', 'referral_code', 'kyc_status', 'available_balance', 'total_balance', 'created_at')
    list_filter     = ('kyc_status',)
    search_fields   = ('user__username', 'user__email', 'referral_code')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')
    ordering        = ('-created_at',)


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display    = ('get_username', 'get_email', 'id_type', 'id_number', 'kyc_status_badge', 'created_at', 'verification_date')
    list_filter     = ('profile__kyc_status', 'id_type')
    search_fields   = ('profile__user__username', 'profile__user__email', 'id_number')
    readonly_fields = ('created_at', 'updated_at', 'verification_date',
                       'id_front', 'id_back', 'selfie', 'proof_of_address')
    ordering        = ('-created_at',)
    actions         = [approve_kyc, reject_kyc]
 
    fieldsets = (
        ('User', {
            'fields': ('profile',)
        }),
        ('ID Document', {
            'fields': ('id_type', 'id_number', 'id_front', 'id_back', 'selfie')
        }),
        ('Proof of Address', {
            'fields': ('address_type', 'proof_of_address'),
            'classes': ('collapse',),
        }),
        ('Review', {
            'fields': ('notes', 'reviewed_by', 'verification_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
 
    @admin.display(description='Username')
    def get_username(self, obj):
        return obj.profile.user.username
 
    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.profile.user.email
 
    @admin.display(description='Status')
    def kyc_status_badge(self, obj):
        colours = {
            'not_submitted': '#9ca3af',
            'pending':       '#f59e0b',
            'verified':      '#10b981',
            'rejected':      '#ef4444',
        }
        colour = colours.get(obj.profile.kyc_status, '#9ca3af')
        label  = obj.profile.get_kyc_status_display()
        return f'<span style="color:{colour};font-weight:600;text-transform:uppercase;font-size:11px">{label}</span>'
    kyc_status_badge.allow_tags = True


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'transaction_type', 'amount', 'colored_status', 'created_at')
    list_filter = ('status', 'transaction_type', 'payment_method')
    search_fields = ('profile__user__username', 'description')
    readonly_fields = ('balance_before', 'balance_after', 'created_at', 'confirmed_at')
    ordering = ('-created_at',)
    actions = [approve_deposits, reject_deposits, approve_withdrawals, reject_withdrawals]

    @admin.display(description='User')
    def get_username(self, obj):
        return obj.profile.user.username

    @admin.display(description='Status')
    def colored_status(self, obj):
        colours = {
            'pending': '#f59e0b',
            'completed': '#10b981',
            'failed': '#ef4444'
        }
        colour = colours.get(obj.status, '#6b7280')
        return f'<span style="color:{colour}; font-weight:600;">{obj.status.upper()}</span>'
    colored_status.allow_tags = True


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'previous_close', 'market_cap', 'is_active', 'updated_at')
    list_filter = ('is_active', 'industry')
    search_fields = ('symbol', 'name')
    readonly_fields = ('updated_at',)


@admin.register(StockHolding)
class StockHoldingAdmin(admin.ModelAdmin):
    list_display = ('profile', 'stock', 'shares', 'average_buy_price', 'total_value', 'updated_at')
    list_filter = ('stock__symbol',)
    search_fields = ('profile__user__username', 'stock__symbol')
    readonly_fields = ('updated_at',)

    def total_value(self, obj):
        return obj.shares * obj.stock.current_price if obj.stock else 0
    total_value.short_description = 'Current Value'


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display  = ('name', 'roi_percent', 'duration_days', 'cycle', 'min_amount', 'max_amount', 'badge_color', 'is_active')
    list_filter   = ('is_active', 'cycle')
    search_fields = ('name',)
 
 
@admin.register(UserInvestment)
class UserInvestmentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'get_username', 'plan', 'amount', 'expected_return',
                     'colored_status', 'started_at', 'matures_at', 'paid_out_at')
    list_filter   = ('status', 'plan')
    search_fields = ('profile__user__username', 'plan__name')
    readonly_fields = ('started_at', 'matures_at', 'paid_out_at', 'balance_before', 'balance_after')
    ordering      = ('-started_at',)
    actions       = [approve_investment_payouts, cancel_investments]
 
    @admin.display(description='User')
    def get_username(self, obj):
        return obj.profile.user.username
 
    @admin.display(description='Status')
    def colored_status(self, obj):
        colours = {
            'active':    '#3b82f6',
            'completed': '#10b981',
            'cancelled': '#ef4444',
        }
        colour = colours.get(obj.status, '#6b7280')
        return f'<span style="color:{colour}; font-weight:600;">{obj.status.upper()}</span>'
    colored_status.allow_tags = True


@admin.register(TeslaVehicle)
class TeslaVehicleAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'variant', 'price', 'is_available', 'stock_quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'order_type', 'status', 'total_amount', 'created_at')
    list_filter = ('order_type', 'status')


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'amount', 'is_claimed', 'created_at')
    list_filter = ('is_claimed',)
    
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display  = ('name', 'ticker', 'network_key', 'short_address', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    list_filter   = ('is_active', 'network_key')
    search_fields = ('name', 'ticker', 'address')
    ordering      = ('sort_order', 'name')
 
    fieldsets = (
        ('Display', {
            'fields': ('name', 'ticker', 'network_label', 'network_key', 'icon_symbol', 'color')
        }),
        ('Wallet', {
            'fields': ('address',)
        }),
        ('Settings', {
            'fields': ('is_active', 'sort_order')
        }),
    )
 
    @admin.display(description='Address')
    def short_address(self, obj):
        return obj.address[:20] + '…' if len(obj.address) > 20 else obj.address