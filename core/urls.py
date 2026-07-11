from django.urls import path
from . import views

urlpatterns = [
    # Autentikasi
    path('login/', views.login_view, name='login_view'),
    path('register/', views.register_view, name='register_view'),
    path('logout/', views.logout_view, name='logout_view'),

    # Halaman Utama (Pages)
    path('', views.game_view, name='game_view'),
    path('deposit/', views.deposit_view, name='deposit_view'),
    path('withdraw/', views.withdraw_view, name='withdraw_view'),
    path('profile/', views.profile_view, name='profile_view'),
    
    # Internal APIs
    path('api/history/', views.api_game_history, name='api_history'),
    path('api/wallet/deposit/', views.api_simulate_deposit, name='api_simulate_deposit'),
    path('api/wallet/withdraw/', views.api_simulate_withdraw, name='api_simulate_withdraw'),
]