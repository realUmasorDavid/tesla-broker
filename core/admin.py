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
    readonly_fields = ('balance_before', 'balance_after', 'created_at', 'confirmed_at')


# ====================== Custom User Admin ======================

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline, KYCVerificationInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_kyc_status')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__kyc_status', 'profile__kyc_tier')
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
        profile.total_balance += tx.amount
        profile.save(update_fields=['available_balance', 'total_balance'])
        
        tx.status = 'completed'
        tx.balance_before = balance_before
        tx.balance_after = profile.available_balance
        tx.confirmed_at = timezone.now()
        tx.save()
        approved += 1
    modeladmin.message_user(request, f'✅ {approved} deposit(s) approved.', messages.SUCCESS)


@admin.action(description='❌ Reject Deposits')
def reject_deposits(modeladmin, request, queryset):
    rejected = 0
    for tx in queryset.filter(transaction_type='deposit', status='pending'):
        tx.status = 'failed'
        tx.save()
        rejected += 1
    modeladmin.message_user(request, f'❌ {rejected} deposit(s) rejected.', messages.SUCCESS)


@admin.action(description='✅ Approve Withdrawals')
def approve_withdrawals(modeladmin, request, queryset):
    approved = 0
    for tx in queryset.filter(transaction_type='withdrawal', status='pending'):
        tx.status = 'completed'
        tx.confirmed_at = timezone.now()
        tx.save()
        approved += 1
    modeladmin.message_user(request, f'✅ {approved} withdrawal(s) approved.', messages.SUCCESS)


@admin.action(description='❌ Reject Withdrawals (Restore Balance)')
def reject_withdrawals(modeladmin, request, queryset):
    rejected = 0
    for tx in queryset.filter(transaction_type='withdrawal', status='pending'):
        profile = tx.profile
        profile.available_balance += abs(tx.amount)  # restore
        profile.save()
        
        tx.status = 'failed'
        tx.balance_after = profile.available_balance
        tx.confirmed_at = timezone.now()
        tx.save()
        rejected += 1
    modeladmin.message_user(request, f'❌ {rejected} withdrawal(s) rejected and balance restored.', messages.SUCCESS)


# ====================== Main Models ======================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'kyc_status', 'kyc_tier', 'available_balance', 'total_balance')
    list_filter = ('kyc_status', 'kyc_tier')
    search_fields = ('user__username', 'user__email', 'referral_code')
    readonly_fields = ('referral_code', 'created_at', 'updated_at')


@admin.register(KYCVerification)
class KYCVerificationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'id_type', 'kyc_status_display', 'verification_date')
    list_filter = ('profile__kyc_status', 'id_type')
    readonly_fields = ('verification_date', 'reviewed_by')

    def kyc_status_display(self, obj):
        return obj.profile.kyc_status
    kyc_status_display.short_description = 'KYC Status'


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
    list_display = ('profile', 'name', 'amount_per_cycle', 'cycle', 'is_active', 'next_execution')
    list_filter = ('cycle', 'is_active')


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