from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
from accounts.models import User
from .token_service import TokenService
from .security_service import SecurityService
from audit.models import AuditLog
from accounts.tasks import send_suspicious_activity_alert_task

class AuthService:
    @staticmethod
    def register_user(email, password, first_name, last_name):
        # validate password strength
        is_valid, error = SecurityService.validate_password_strength(password)
        if not is_valid:
            return None, error
        
        # check if user already exists
        if User.objects.filter(email__iexact=email).exists():
            return None, 'User with this email already exists'
        
        # Create user (inactive and unverified by default)
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
            is_verified=False
        )
        
        return user, None
    
    @staticmethod
    def generate_jwt_tokens(user):
        """Generate JWT access and refresh tokens for a user"""
        refresh = JWTRefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
        
    @classmethod
    def login_user(cls, email, password, request):
        """
        Authenticate user and generate tokens
        """
        ip_address = SecurityService.get_client_ip(request)
        user_agent = SecurityService.get_user_agent(request)
        email = email.lower()

        # Step 1: Check lockout FIRST
        is_locked, attempts, time_remaining = SecurityService.check_login_attempts(email)
        if is_locked:
            minutes = max(1, time_remaining // 60)
            AuditLog.objects.create(
                user=None,
                action='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'email': email,
                    'reason': 'Account locked',
                }
            )
            return None, None, (
                f'Account temporarily locked due to too many failed attempts. '
                f'Please try again in {minutes} minute(s) or reset your password.'
            )

        # Step 2: Check user exists
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            SecurityService.record_failed_login(email, ip_address)
            AuditLog.objects.create(
                user=None,
                action='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'email': email, 'reason': 'User not found'}
            )
            return None, None, 'Invalid credentials. Please check your email and password.'

        # Step 3: Check active status
        if not user_obj.is_active:
            AuditLog.objects.create(
                user=user_obj,
                action='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'reason': 'Account not active'}
            )
            return None, None, 'Account is not active. Please verify your email first.'

        # Step 4: Check verified status
        if not user_obj.is_verified:
            AuditLog.objects.create(
                user=user_obj,
                action='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={'reason': 'Email not verified'}
            )
            return None, None, 'Please verify your email address before logging in.'

        # Step 5: Authenticate credentials
        user = authenticate(request, username=email, password=password)

        # WRONG PASSWORD
        if user is None:
            is_locked, remaining = SecurityService.record_failed_login(email, ip_address)

            AuditLog.objects.create(
                user=user_obj,
                action='login_failed',
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    'reason': 'Invalid password',
                    'is_locked': is_locked,
                }
            )

            if is_locked:
                AuditLog.objects.create(
                    user=user_obj,
                    action='account_locked',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={'reason': 'Max failed attempts reached'}
                )
                return None, None, (
                    f'Account locked due to too many failed attempts. '
                    f'Please try again in {SecurityService.LOGIN_LOCKOUT_DURATION} '
                    f'minutes or reset your password.'
                )

            # Generic error — no attempt count exposed
            return None, None, 'Invalid credentials. Please check your email and password.'

        # Step 6: Successful login
        SecurityService.reset_login_attempts(email)

        # Generate JWT tokens
        jwt_tokens = cls.generate_jwt_tokens(user)

        # Store refresh token in DB
        device_info = SecurityService.get_device_info(request)
        raw_refresh_token, refresh_token_obj = TokenService.create_refresh_token(
            user=user,
            ip_address=ip_address,
            device_info=device_info
        )

        # Update last login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        # Check for suspicious activity
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user, ip_address, user_agent
        )

        # Log successful login
        AuditLog.objects.create(
            user=user,
            action='login_success',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                'device_info': device_info,
                'suspicious': is_suspicious,
                'suspicious_reason': reason,
            }
        )

        # Send suspicious activity alert
        if is_suspicious:
            activity_details = {
                'ip_address': ip_address,
                'timestamp': str(timezone.now()),
                'device_info': device_info,
                'reason': reason,
            }
            send_suspicious_activity_alert_task.delay(
                user_id=str(user.id),
                activity_details=activity_details
            )

        return {
            'access': jwt_tokens['access'],
            'refresh': raw_refresh_token,
        }, user, None

    
    @classmethod
    def logout_user(cls, refresh_token, request):
        """"Logout user by revoking refresh token"""
        
        refresh_token_obj = TokenService.validate_refresh_token(refresh_token)
        
        if not refresh_token_obj:
            return False, 'Invalid or expired refresh token'
        
        # revoke token
        TokenService.revoke_refresh_token(refresh_token_obj)
        
        #log logout action
        ip_address = SecurityService.get_client_ip(request)
        user_agent = SecurityService.get_user_agent(request)
        
        AuditLog.objects.create(
            user=refresh_token_obj.user,
            action='logout',
            ip_address=ip_address,
            user_agent=user_agent
        )
        return True, None
    
    @classmethod
    def refresh_tokens(cls, refresh_token, request):
        """Refresh JWT tokens using a valid refresh token"""
        refresh_token_obj = TokenService.validate_refresh_token(refresh_token)
        
        if not refresh_token_obj:
            return None, 'Invalid or expired refresh token'
        
        user = refresh_token_obj.user
        
        # revoke old refresh token
        TokenService.revoke_refresh_token(refresh_token_obj)
        
        # generate new JWT tokens
        jwt_tokens = cls.generate_jwt_tokens(user)
        
        # create new refresh token in db
        ip_address = SecurityService.get_client_ip(request)
        device_info = SecurityService.get_device_info(request)
        
        raw_new_refresh, rwn_refresh_obj = TokenService.create_refresh_token(
            user=user,
            ip_address=ip_address,
            device_info=device_info
        )
        
        # Log token refresh
        user_agent = SecurityService.get_user_agent(request)
        AuditLog.objects.create(
            user=user,
            action='token_refresh',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        new_tokens = {
            'access': jwt_tokens['access'],
            'refresh': raw_new_refresh
        }
        
        return new_tokens, None
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """Change user password after validating old password and new password strength"""
        
        if not user.check_password(old_password):
            return False, 'Old password is incorrect'
        
        # validate new password strength
        is_valid, error = SecurityService.validate_password_strength(new_password)
        if not is_valid:
            return False, error
        
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        # Log password change
        AuditLog.objects.create(
            user=user,
            action='password_change',
        )
        TokenService.revoke_all_user_tokens(user)
        
        return True, None