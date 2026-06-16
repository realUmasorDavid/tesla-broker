from django.urls import path
from .views import deposit_confirm_view, index, investments_view, investment_subscribe, login, profile_view, register, dashboard, kyc_view, stock_confirm, wallet_view, deposit_view, withdraw_view, withdraw_confirm_view, stocks_list, stock_detail, stock_buy, portfolio_view
from core import views

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
    path('withdraw/<int:pk>/confirm/', withdraw_confirm_view, name='withdraw_confirm'),
    path('stocks/', stocks_list, name='stocks'),
    path('stocks/<str:symbol>/', stock_detail, name='stock_detail'),
    path('stocks/<str:symbol>/buy/', stock_buy, name='stock_buy'),
    path('stocks/<str:symbol>/confirm/', stock_confirm, name='stock_confirm'),
    path('investments/', investments_view, name='investments'),
    path('investments/subscribe/<int:plan_id>/', investment_subscribe, name='investment_subscribe'),
    path('portfolio/', portfolio_view, name='portfolio'),
]