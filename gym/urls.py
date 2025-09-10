from django.urls import path
from . import views

app_name = 'gym'

urlpatterns = [
    path('', views.home, name='home'),
    path('scan/', views.scan, name='scan'),
    path('scan-result/', views.scan_result, name='scan_result'),
    path('member/<int:member_id>/qr/', views.generate_qr, name='generate_qr'),
    path('download-qr/<int:member_id>/', views.download_qr_code, name='download_qr'),
    path('send-qr-email/<int:member_id>/', views.send_qr_email, name='send_qr_email'),
    path('take-photo/<int:member_id>/', views.take_photo, name='take_photo'),
    path('save-photo/<int:member_id>/', views.save_photo, name='save_photo'),
    path('wallet-pass/<str:member_uuid>/', views.generate_wallet_pass, name='generate_wallet_pass'),
    path('wallet/', views.wallet, name='wallet'),
    
    # URL per membri di sala
    path('sala-member/<int:member_id>/qr/', views.generate_sala_qr, name='generate_sala_qr'),
    path('download-sala-qr/<int:member_id>/', views.download_sala_qr_code, name='download_sala_qr'),
    path('send-sala-qr-email/<int:member_id>/', views.send_sala_qr_email, name='send_sala_qr_email'),
    path('take-sala-photo/<int:member_id>/', views.take_sala_photo, name='take_sala_photo'),
    path('save-sala-photo/<int:member_id>/', views.save_sala_photo, name='save_sala_photo'),
] 