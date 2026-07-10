from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    
    path('register/', views.register, name='register'),
    path('verify-email/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.resend_verification, name='resend-verification'),
    
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', views.refresh_token, name='refresh-token'),
    
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('validate-reset-token/', views.validate_reset_token, name='validate-reset-token'),
    path('change-password/', views.change_password, name='change-password'),
    
    path('sessions/', views.get_active_sessions, name='active-sessions'),
    path('revoke-session/', views.revoke_session, name='revoke-session'),
    path('revoke-all-sessions/', views.revoke_all_sessions, name='revoke-all-session'),
    
    path('me/', views.get_user_profile, name='user-profile'),
    path('profile/', views.update_profile, name='update-profile'),
    path('account/', views.delete_account, name='delete-account'),
    
    path('debug-login/', views.debug_login, name='debug-login'),
]