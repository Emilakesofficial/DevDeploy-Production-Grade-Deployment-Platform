"""
Views for accounts app
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)
from rest_framework import serializers as drf_serializers

from accounts.models import User, RefreshToken
from accounts.serializers import (
    UserRegistrationSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    LoginSerializer,
    LogoutSerializer,
    TokenRefreshSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    ValidateResetTokenSerializer,
    RevokeSessionSerializer,
    UpdateProfileSerializer,
)
from accounts.services.auth_service import AuthService
from accounts.services.token_service import TokenService
from accounts.services.security_service import SecurityService
from accounts.tasks import (
    send_welcome_email_task,
    send_verification_email_task,
    send_password_reset_email_task,
    send_password_changed_email_task,
)
from audit.models import AuditLog

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# SYSTEM
# ─────────────────────────────────────────────

@extend_schema(
    tags=['System'],
    summary="Health Check",
    description="Check if all services (database, cache) are running properly",
    responses={
        200: inline_serializer(
            name='HealthCheckResponse',
            fields={
                'status': drf_serializers.CharField(),
                'services': drf_serializers.DictField(
                    child=drf_serializers.CharField()
                ),
            }
        ),
        503: OpenApiResponse(description="One or more services are unhealthy"),
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    health_status = {
        'status': 'healthy',
        'services': {}
    }

    try:
        connection.ensure_connection()
        health_status['services']['database'] = 'connected'
    except Exception as e:
        health_status['services']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'

    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['redis'] = 'connected'
        else:
            raise Exception('Cache not working')
    except Exception as e:
        health_status['services']['redis'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'

    status_code = (
        status.HTTP_200_OK
        if health_status['status'] == 'healthy'
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return Response(health_status, status=status_code)


# ─────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────

@extend_schema(
    tags=['Registration'],
    summary="Register New User",
    description="""
    Register a new user account.

    - Creates user with `is_active=False` and `is_verified=False`
    - Sends a verification email via Celery
    - **No JWT tokens issued at this stage**

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """,
    request=UserRegistrationSerializer,
    responses={
        201: inline_serializer(
            name='RegisterResponse',
            fields={
                'message': drf_serializers.CharField(),
                'email': drf_serializers.EmailField(),
            }
        ),
        400: OpenApiResponse(description="Validation error"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user"""
    serializer = UserRegistrationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    user, error = AuthService.register_user(
        email=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
        first_name=serializer.validated_data['first_name'],
        last_name=serializer.validated_data['last_name']
    )

    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    verification_token, token_obj = TokenService.create_email_token(
        user=user,
        token_type='verify'
    )

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=user,
        action='register',
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={'email': user.email}
    )

    send_welcome_email_task.delay(str(user.id))
    send_verification_email_task.delay(str(user.id), verification_token)

    return Response(
        {
            'message': 'Registration successful. Please check your email to verify your account.',
            'email': user.email,
        },
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    tags=['Registration'],
    summary="Verify Email Address",
    description="""
    Verify user's email address using the token sent via email.

    - Sets `is_verified=True` and `is_active=True`
    - Marks token as used (single-use)
    - **No JWT tokens issued here**

    Token expires after 24 hours.
    """,
    request=EmailVerificationSerializer,
    responses={
        200: inline_serializer(
            name='VerifyEmailResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        400: OpenApiResponse(description="Invalid or expired token"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify user email address"""
    serializer = EmailVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    token = serializer.validated_data['token']
    email_token = TokenService.validate_email_token(token, 'verify')

    if not email_token:
        return Response(
            {'error': 'Invalid or expired verification token.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = email_token.user

    if user.is_verified:
        return Response(
            {'message': 'Email already verified. You can login now.'},
            status=status.HTTP_200_OK
        )

    user.is_verified = True
    user.is_active = True
    user.save(update_fields=['is_verified', 'is_active'])

    TokenService.mark_token_used(email_token)

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=user,
        action='email_verified',
        ip_address=ip_address,
        user_agent=user_agent
    )

    return Response(
        {'message': 'Email verified successfully. You can now login.'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Registration'],
    summary="Resend Verification Email",
    description="Resend verification email. Rate limited to 3 requests per hour.",
    request=ResendVerificationSerializer,
    responses={
        200: inline_serializer(
            name='ResendVerificationResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        429: OpenApiResponse(description="Too many requests"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """Resend email verification"""
    serializer = ResendVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data['email']
    cache_key = f'resend_verification:{email}'
    attempts = cache.get(cache_key, 0)

    if attempts >= 3:
        return Response(
            {'error': 'Too many verification emails sent. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'message': 'If the email exists and is not verified, a verification email has been sent.'},
            status=status.HTTP_200_OK
        )

    if user.is_verified:
        return Response(
            {'message': 'Email already verified. You can login now.'},
            status=status.HTTP_200_OK
        )

    verification_token, token_obj = TokenService.create_email_token(
        user=user,
        token_type='verify'
    )

    send_verification_email_task.delay(str(user.id), verification_token)
    cache.set(cache_key, attempts + 1, timeout=3600)

    return Response(
        {'message': 'Verification email sent. Please check your inbox.'},
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────

@extend_schema(
    tags=['Authentication'],
    summary="User Login",
    description="""
    Authenticate user and receive JWT tokens.

    **Security:**
    - 5 failed attempts lock account for 15 minutes
    - All attempts logged in audit logs
    - Suspicious activity detection (new IP/device)

    **Returns:**
    - `access`: JWT access token (15 minutes)
    - `refresh`: Refresh token (7 days)
    - `user`: User profile
    """,
    request=LoginSerializer,
    responses={
        200: inline_serializer(
            name='LoginResponse',
            fields={
                'access': drf_serializers.CharField(),
                'refresh': drf_serializers.CharField(),
                'user': UserSerializer(),
                'message': drf_serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description="Invalid credentials or account not active"),
        429: OpenApiResponse(description="Account locked — too many failed attempts"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user and return JWT tokens"""
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    tokens, user, error = AuthService.login_user(email, password, request)

    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    user_serializer = UserSerializer(user)

    return Response(
        {
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user_serializer.data,
            'message': 'Login successful'
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Authentication'],
    summary="User Logout",
    description="""
    Logout user by revoking the refresh token.

    - Refresh token is marked as revoked in database
    - Access token remains valid until expiration
    - Client should delete both tokens from storage
    """,
    request=LogoutSerializer,
    responses={
        200: inline_serializer(
            name='LogoutResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        400: OpenApiResponse(description="Invalid refresh token"),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user"""
    serializer = LogoutSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    refresh_token = serializer.validated_data['refresh_token']
    success, error = AuthService.logout_user(refresh_token, request)

    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def debug_login(request):
    """
    TEMPORARY DEBUG VIEW — REMOVE IN PRODUCTION
    """
    import traceback
    from django.contrib.auth import authenticate
    from accounts.services.security_service import SecurityService

    email = request.data.get('email', '').lower()
    password = request.data.get('password', '')

    debug_info = {}

    # Check 1: User exists
    try:
        from accounts.models import User
        user = User.objects.get(email__iexact=email)
        debug_info['user_found'] = True
        debug_info['is_active'] = user.is_active
        debug_info['is_verified'] = user.is_verified
        debug_info['password_correct'] = user.check_password(password)
        debug_info['stored_email'] = user.email
        debug_info['input_email'] = email
        debug_info['emails_match'] = user.email == email
    except User.DoesNotExist:
        debug_info['user_found'] = False
        return Response({'debug': debug_info}, status=200)

    # Check 2: Cache/lockout
    is_locked, attempts, ttl = SecurityService.check_login_attempts(email)
    debug_info['is_locked'] = is_locked
    debug_info['attempts'] = attempts
    debug_info['ttl'] = ttl

    # Check 3: Authenticate
    try:
        auth_result = authenticate(request, username=email, password=password)
        debug_info['authenticate_result'] = str(auth_result)
    except Exception as e:
        debug_info['authenticate_error'] = str(e)
        debug_info['authenticate_traceback'] = traceback.format_exc()

    # Check 4: Backends
    from django.conf import settings
    debug_info['backends'] = getattr(settings, 'AUTHENTICATION_BACKENDS', [])

    return Response({'debug': debug_info}, status=200)

@extend_schema(
    tags=['Authentication'],
    summary="Refresh Access Token",
    description="""
    Get a new access token using a refresh token.

    **Token Rotation:**
    - Old refresh token is revoked immediately
    - New refresh token is issued
    - New access token is issued
    - Prevents token replay attacks
    """,
    request=TokenRefreshSerializer,
    responses={
        200: inline_serializer(
            name='TokenRefreshResponse',
            fields={
                'access': drf_serializers.CharField(),
                'refresh': drf_serializers.CharField(),
                'message': drf_serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description="Invalid or expired refresh token"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token"""
    serializer = TokenRefreshSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    refresh_token_value = serializer.validated_data['refresh_token']
    new_tokens, error = AuthService.refresh_tokens(refresh_token_value, request)

    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            'access': new_tokens['access'],
            'refresh': new_tokens['refresh'],
            'message': 'Tokens refreshed successfully'
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# PASSWORD MANAGEMENT
# ─────────────────────────────────────────────

@extend_schema(
    tags=['Password'],
    summary="Request Password Reset",
    description="""
    Request a password reset link via email.

    - Does not reveal whether email exists
    - Rate limited: 3 requests per hour
    - Reset token expires in 1 hour
    """,
    request=PasswordResetRequestSerializer,
    responses={
        200: inline_serializer(
            name='ForgotPasswordResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        429: OpenApiResponse(description="Too many reset requests"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Request password reset"""
    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    email = serializer.validated_data['email']
    cache_key = f'password_reset:{email}'
    attempts = cache.get(cache_key, 0)

    if attempts >= 3:
        return Response(
            {'error': 'Too many password reset requests. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        user = User.objects.get(email=email)
        reset_token, token_obj = TokenService.create_email_token(
            user=user,
            token_type='reset'
        )
        send_password_reset_email_task.delay(str(user.id), reset_token)

        ip_address = SecurityService.get_client_ip(request)
        user_agent = SecurityService.get_user_agent(request)

        AuditLog.objects.create(
            user=user,
            action='password_reset_request',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'token_id': str(token_obj.id)}
        )
    except User.DoesNotExist:
        pass  # Don't reveal user existence

    cache.set(cache_key, attempts + 1, timeout=3600)

    return Response(
        {'message': 'If the email exists, a password reset link has been sent.'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Password'],
    summary="Validate Reset Token",
    description="Check if a password reset token is valid before showing reset form.",
    request=ValidateResetTokenSerializer,
    responses={
        200: inline_serializer(
            name='ValidateResetTokenResponse',
            fields={
                'valid': drf_serializers.BooleanField(),
                'email': drf_serializers.EmailField(),
            }
        ),
        400: OpenApiResponse(description="Invalid or expired token"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_reset_token(request):
    """Validate password reset token"""
    serializer = ValidateResetTokenSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    token = serializer.validated_data['token']
    email_token = TokenService.validate_email_token(token, 'reset')

    if not email_token:
        return Response(
            {'valid': False, 'error': 'Invalid or expired reset token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {'valid': True, 'email': email_token.user.email},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Password'],
    summary="Reset Password",
    description="""
    Reset password using the token received via email.

    - Token is single-use only
    - Token expires after 1 hour
    - All existing sessions are terminated after reset
    - Confirmation email is sent
    """,
    request=PasswordResetConfirmSerializer,
    responses={
        200: inline_serializer(
            name='ResetPasswordResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        400: OpenApiResponse(description="Invalid token or validation error"),
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password with token"""
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    token = serializer.validated_data['token']
    new_password = serializer.validated_data['password']

    email_token = TokenService.validate_email_token(token, 'reset')

    if not email_token:
        return Response(
            {'error': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = email_token.user
    user.set_password(new_password)
    user.save(update_fields=['password'])

    TokenService.mark_token_used(email_token)
    TokenService.revoke_all_user_tokens(user)

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=user,
        action='password_reset_success',
        ip_address=ip_address,
        user_agent=user_agent
    )

    send_password_changed_email_task.delay(str(user.id))

    return Response(
        {'message': 'Password reset successful. You can now login with your new password.'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Password'],
    summary="Change Password",
    description="""
    Change password for authenticated user.

    - Old password must be correct
    - All other sessions are revoked
    - New access token is returned for current session
    """,
    request=ChangePasswordSerializer,
    responses={
        200: inline_serializer(
            name='ChangePasswordResponse',
            fields={
                'message': drf_serializers.CharField(),
                'access': drf_serializers.CharField(),
            }
        ),
        400: OpenApiResponse(description="Invalid old password or validation error"),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """Change password for authenticated user"""
    serializer = ChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']

    success, error = AuthService.change_password(
        user=request.user,
        old_password=old_password,
        new_password=new_password
    )

    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=request.user,
        action='password_changed',
        ip_address=ip_address,
        user_agent=user_agent
    )

    send_password_changed_email_task.delay(str(request.user.id))

    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(request.user)
    new_access_token = str(refresh.access_token)

    return Response(
        {
            'message': 'Password changed successfully. You have been logged out from all other devices.',
            'access': new_access_token,
        },
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

@extend_schema(
    tags=['Profile'],
    summary="Get Current User Profile",
    description="Get the authenticated user's profile information.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get current user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Profile'],
    summary="Update User Profile",
    description="Update authenticated user's first name and last name.",
    request=UpdateProfileSerializer,
    responses={
        200: UserSerializer,
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UpdateProfileSerializer(
        request.user,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer.save()

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=request.user,
        action='profile_updated',
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={'fields_updated': list(request.data.keys())}
    )

    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Profile'],
    summary="Delete Account",
    description="""
    Soft delete user account.

    - User is marked as inactive
    - All sessions are revoked
    - Requires password confirmation
    """,
    request=inline_serializer(
        name='DeleteAccountRequest',
        fields={
            'password': drf_serializers.CharField(),
            'confirm': drf_serializers.BooleanField(),
        }
    ),
    responses={
        200: inline_serializer(
            name='DeleteAccountResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        400: OpenApiResponse(description="Invalid password or confirmation missing"),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """Soft delete user account"""
    user = request.user
    password = request.data.get('password')
    confirm = request.data.get('confirm')

    if not password or not confirm:
        return Response(
            {'error': 'Password and confirmation required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not user.check_password(password):
        return Response(
            {'error': 'Invalid password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.is_active = False
    user.save()

    TokenService.revoke_all_user_tokens(user)

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=user,
        action='account_deleted',
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={'type': 'soft_delete'}
    )

    return Response(
        {'message': 'Account deleted successfully'},
        status=status.HTTP_200_OK
    )


# ─────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────

@extend_schema(
    tags=['Sessions'],
    summary="Get Active Sessions",
    description="Get all active refresh tokens (sessions) for the current user.",
    responses={
        200: inline_serializer(
            name='ActiveSessionsResponse',
            fields={
                'sessions': drf_serializers.ListField(
                    child=inline_serializer(
                        name='SessionItem',
                        fields={
                            'id': drf_serializers.UUIDField(),
                            'device_info': drf_serializers.CharField(),
                            'ip_address': drf_serializers.IPAddressField(),
                            'created_at': drf_serializers.DateTimeField(),
                            'expires_at': drf_serializers.DateTimeField(),
                            'is_current': drf_serializers.BooleanField(),
                        }
                    )
                ),
                'total': drf_serializers.IntegerField(),
            }
        ),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_sessions(request):
    """Get all active sessions for current user"""
    active_tokens = RefreshToken.objects.filter(
        user=request.user,
        revoked=False
    ).order_by('-created_at')

    current_ip = SecurityService.get_client_ip(request)

    sessions = [
        {
            'id': str(token.id),
            'device_info': token.device_info,
            'ip_address': token.ip_address,
            'created_at': token.created_at,
            'expires_at': token.expires_at,
            'is_current': token.ip_address == current_ip
        }
        for token in active_tokens
    ]

    return Response(
        {'sessions': sessions, 'total': len(sessions)},
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Sessions'],
    summary="Revoke Session",
    description="Revoke a specific session (refresh token) by session ID.",
    request=RevokeSessionSerializer,
    responses={
        200: inline_serializer(
            name='RevokeSessionResponse',
            fields={'message': drf_serializers.CharField()}
        ),
        400: OpenApiResponse(description="Invalid session ID"),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_session(request):
    """Revoke a specific session"""
    serializer = RevokeSessionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    session_id = serializer.validated_data['session_id']

    try:
        token = RefreshToken.objects.get(
            id=session_id,
            user=request.user,
            revoked=False
        )
        TokenService.revoke_refresh_token(token)

        ip_address = SecurityService.get_client_ip(request)
        user_agent = SecurityService.get_user_agent(request)

        AuditLog.objects.create(
            user=request.user,
            action='token_revoked',
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={'session_id': str(session_id)}
        )

        return Response(
            {'message': 'Session revoked successfully'},
            status=status.HTTP_200_OK
        )

    except RefreshToken.DoesNotExist:
        return Response(
            {'error': 'Session not found or already revoked'},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    tags=['Sessions'],
    summary="Revoke All Other Sessions",
    description="Revoke all sessions except the current one.",
    request=None,
    responses={
        200: inline_serializer(
            name='RevokeAllSessionsResponse',
            fields={
                'message': drf_serializers.CharField(),
                'revoked_count': drf_serializers.IntegerField(),
            }
        ),
        401: OpenApiResponse(description="Not authenticated"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_all_sessions(request):
    """Revoke all sessions except current"""
    current_ip = SecurityService.get_client_ip(request)

    revoked_count = RefreshToken.objects.filter(
        user=request.user,
        revoked=False
    ).exclude(
        ip_address=current_ip
    ).update(revoked=True)

    ip_address = SecurityService.get_client_ip(request)
    user_agent = SecurityService.get_user_agent(request)

    AuditLog.objects.create(
        user=request.user,
        action='token_revoked',
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={'action': 'revoke_all_sessions', 'count': revoked_count}
    )

    return Response(
        {
            'message': f'Successfully revoked {revoked_count} sessions',
            'revoked_count': revoked_count
        },
        status=status.HTTP_200_OK
    )