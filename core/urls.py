from django.urls import path
from .views import deposit_confirm_view, index, login, profile_view, register, dashboard, kyc_view, wallet_view, deposit_view, withdraw_view

urlpatterns = [
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('kyc/', kyc_view, name='kyc'),
    path('wallet/', wallet_view, name='wallet'),
    path('deposit/', deposit_view, name='deposit'),
    path('deposit/<int:pk>/confirm/', deposit_confirm_view, name='deposit_confirm'),
    path('withdraw/', withdraw_view, name='withdraw'),
]