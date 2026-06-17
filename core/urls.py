from django.urls import path
from .views import deposit_confirm_view, index, investments_view, investment_subscribe, login, profile_view, register, dashboard, kyc_view, stock_confirm, wallet_view, deposit_view, withdraw_view, withdraw_confirm_view, stocks_list, stock_detail, stock_buy, portfolio_view, inventory_view, vehicle_detail_view, vehicle_order_view, vehicle_order_confirm_view, vehicle_order_success_view, logout
from core import views

urlpatterns = [
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
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
    path('inventory/', inventory_view, name='inventory'),
    path('inventory/<int:pk>/', vehicle_detail_view, name='vehicle_detail'),
    path('inventory/<int:pk>/order/', vehicle_order_view, name='vehicle_order'),
    path('inventory/<int:pk>/order/confirm/', vehicle_order_confirm_view, name='vehicle_order_confirm'),
    path('inventory/<int:pk>/order/success/', vehicle_order_success_view, name='vehicle_order_success'),
]