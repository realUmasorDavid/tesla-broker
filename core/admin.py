# admin.py
from django.utils import timezone
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Profile, KYCVerification, WalletTransaction, Stock, 
    StockHolding, InvestmentPlan, TeslaVehicle, 
    Order, ReferralBonus
)


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
    readonly_fields = ('balance_before', 'balance_after', 'created_at')


# ====================== Custom User Admin ======================

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline, KYCVerificationInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_kyc_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__kyc_status', 'profile__kyc_tier')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'profile__referral_code')

    def get_kyc_status(self, obj):
        return obj.profile.kyc_status if hasattr(obj, 'profile') else '-'
    get_kyc_status.short_description = 'KYC Status'
    get_kyc_status.admin_order_field = 'profile__kyc_status'


# Unregister default User and register custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ====================== Main Models ======================    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'kyc_status', 'kyc_tier', 'available_balance', 'total_balance', 'created_at')
    list_filter = ('kyc_status', 'kyc_tier', 'created_at')
    search_fields = ('user__username', 'user__email', 'referral_code', 'phone_number')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'phone_number', 'date_of_birth', 'address', 'city', 'country')}),
        ('Referral', {'fields': ('referral_code', 'referred_by')}),
        ('Financial', {'fields': ('total_balance', 'available_balance')}),
        ('KYC', {'fields': ('kyc_status', 'kyc_tier')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'id_type', 'kyc_status_display', 'verification_date', 'created_at')
    list_filter = ('profile__kyc_status', 'id_type', 'created_at')
    search_fields = ('profile__user__username', 'id_number')
    readonly_fields = ('verification_date', 'reviewed_by')

    def kyc_status_display(self, obj):
        return obj.profile.kyc_status
    kyc_status_display.short_description = 'KYC Status'


@admin.action(description='✅ Approve selected deposits (credit balance)')
def approve_deposits(modeladmin, request, queryset):
    """
    Credits the user's wallet for each selected pending deposit.
    Only acts on transactions that are still 'pending'.
    """
    approved = 0
    skipped  = 0
 
    for tx in queryset:
        if tx.transaction_type != 'deposit' or tx.status != 'pending':
            skipped += 1
            continue
 
        profile = tx.profile
        balance_before = profile.available_balance
 
        # Credit the balance
        profile.available_balance += tx.amount
        profile.total_balance     += tx.amount
        profile.save()
 
        # Update the transaction record
        tx.status          = 'completed'
        tx.balance_before  = balance_before
        tx.balance_after   = profile.available_balance
        tx.confirmed_at    = timezone.now()
        tx.save()
 
        approved += 1
 
    if approved:
        modeladmin.message_user(request, f'{approved} deposit(s) approved and credited.', messages.SUCCESS)
    if skipped:
        modeladmin.message_user(request, f'{skipped} transaction(s) skipped (not pending deposits).', messages.WARNING)
 
 
@admin.action(description='❌ Reject selected deposits')
def reject_deposits(modeladmin, request, queryset):
    rejected = 0
    skipped  = 0
 
    for tx in queryset:
        if tx.transaction_type != 'deposit' or tx.status != 'pending':
            skipped += 1
            continue
 
        tx.status = 'failed'
        tx.save()
        rejected += 1
 
    if rejected:
        modeladmin.message_user(request, f'{rejected} deposit(s) rejected.', messages.SUCCESS)
    if skipped:
        modeladmin.message_user(request, f'{skipped} transaction(s) skipped.', messages.WARNING)
 
@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display  = (
        'id', 'profile', 'transaction_type', 'payment_method',
        'amount', 'status', 'created_at', 'confirmed_at',
    )
    list_filter   = ('status', 'transaction_type', 'payment_method')
    search_fields = ('profile__user__username', 'profile__user__email', 'description')
    readonly_fields = (
        'balance_before', 'balance_after', 'created_at', 'confirmed_at',
    )
    ordering      = ('-created_at',)
    actions       = [approve_deposits, reject_deposits]
 
    # Highlight pending rows in the list
    def get_list_display_links(self, request, list_display):
        return ['id']
 
    def status_badge(self, obj):
        colours = {'pending': 'orange', 'completed': 'green', 'failed': 'red'}
        colour  = colours.get(obj.status, 'grey')
        return f'<span style="color:{colour};font-weight:600">{obj.status.upper()}</span>'
    status_badge.allow_tags  = True
    status_badge.short_description = 'Status'
    
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'current_price', 'previous_close', 'market_cap', 'is_active', 'updated_at')
    list_filter = ('is_active', 'industry')
    search_fields = ('symbol', 'name', 'industry')
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
    list_display = ('profile', 'name', 'amount_per_cycle', 'cycle', 'is_active', 'next_execution')
    list_filter = ('cycle', 'is_active')
    search_fields = ('profile__user__username', 'name')


@admin.register(TeslaVehicle)
class TeslaVehicleAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'variant', 'price', 'range_miles', 'zero_to_sixty', 'top_speed', 'is_available', 'stock_quantity')
    list_filter = ('is_available', 'model_name')
    search_fields = ('model_name', 'variant')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'order_type', 'status', 'total_amount', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('profile__user__username',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'amount', 'is_claimed', 'created_at')
    list_filter = ('is_claimed', 'created_at')
    search_fields = ('referrer__user__username', 'referred_user__user__username')
    readonly_fields = ('created_at',)