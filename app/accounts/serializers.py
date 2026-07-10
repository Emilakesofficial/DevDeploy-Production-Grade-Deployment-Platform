from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import User
from accounts.services.security_service import SecurityService

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
        
    def validate_email(self, value):
        """validate email is unique"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, data):
        """validate password and confirm password match and meet strength requirements"""
        password = data.get('password')
        password_confirm = data.get('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        is_valid, error = SecurityService.validate_password_strength(password)
        if not is_valid:
            raise serializers.ValidationError({
                'password': error
            })
            
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return data
    
class EmailVerificationSerializer(serializers.Serializer):
    """serializer for email verification"""
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """validate token not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Token is required.")
        return value.strip()
    
class ResendVerificationSerializer(serializers.Serializer):
    """serializer for resending verification email"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """validate email exists and is not already verified"""
        return value.lower()
    
class UserSerializer(serializers.ModelSerializer):
    """serializer for user details"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'is_active', 'is_verified', 'created_at', 'last_login')
        read_only_fields = fields
        
    def get_full_name(self, obj):
        """return full name of user"""
        return obj.get_full_name()
    
class PasswordResetRequestSerializer(serializers.Serializer):
    """serializer for password reset request"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower()
    
class PasswordResetConfirmSerializer(serializers.Serializer):
    """serializer for password reset confirmation"""
    
    token = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """validate password and confirm password match and meet strength requirements"""
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm', None)
        
        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate password strength
        is_valid, error = SecurityService.validate_password_strength(password)
        if not is_valid:
            raise serializers.ValidationError({
                'password': error
            })
            
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'password': list(e.messages)
            })
        
        return attrs
    
class LoginSerializer(serializers.Serializer):
    """serializer for user login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_email(self, value):
        """normalize email"""
        return value.lower()
    
class LogoutSerializer(serializers.Serializer):
    """serializer for user logout"""
    refresh = serializers.CharField(required=True)
    
class TokenRefreshSerializer(serializers.Serializer):
    """serializer for refreshing JWT tokens"""
    refresh = serializers.CharField(required=True)
    
class ChangePasswordSerializer(serializers.Serializer):
    """serializer for changing password"""
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """validate new password and confirm password match and meet strength requirements"""
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm', None)
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError("New passwords do not match.")
        
        # Validate password strength
        is_valid, error = SecurityService.validate_password_strength(new_password)
        if not is_valid:
            raise serializers.ValidationError({
                'new_password': error
            })
            
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs
    
class ValidateResetTokenSerializer(serializers.Serializer):
    """Serializer for validating reset token"""
    token = serializers.CharField(required=True)


class RevokeSessionSerializer(serializers.Serializer):
    """Serializer for revoking a session"""
    session_id = serializers.UUIDField(required=True)


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']