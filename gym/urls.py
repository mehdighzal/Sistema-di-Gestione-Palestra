from django.urls import path
from . import views

app_name = 'gym'

urlpatterns = [
    path('', views.home, name='home'),
    path('scan/', views.scan, name='scan'),
    path('scan-result/', views.scan_result, name='scan_result'),
    # URL for generating a wallet pass (Apple or Google) for a member (e.g. /wallet-pass/<str:member_uuid>/?type=apple or /wallet-pass/<str:member_uuid>/?type=google)
    path('wallet-pass/<str:member_uuid>/', views.generate_wallet_pass, name='generate_wallet_pass'),
    # (Insert a dummy "wallet" view URL for testing, so that you can see a "wallet" function (for example, a link to /wallet-pass/<str:member_uuid>/?type=apple) in action.)
    path('wallet/', views.wallet, name='wallet'),
] 