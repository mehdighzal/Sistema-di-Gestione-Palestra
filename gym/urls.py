from django.urls import path
from . import views

app_name = 'gym'

urlpatterns = [
    path('', views.home, name='home'),
    path('scan/', views.scan, name='scan'),
    path('scan-result/', views.scan_result, name='scan_result'),
    path('member/<int:member_id>/qr/', views.generate_qr, name='generate_qr'),
    path('download-qr/<int:member_id>/', views.download_qr_code, name='download_qr'),
    path('take-photo/<int:member_id>/', views.take_photo, name='take_photo'),
    path('save-photo/<int:member_id>/', views.save_photo, name='save_photo'),
    path('wallet-pass/<str:member_uuid>/', views.generate_wallet_pass, name='generate_wallet_pass'),
    path('wallet/', views.wallet, name='wallet'),
] 