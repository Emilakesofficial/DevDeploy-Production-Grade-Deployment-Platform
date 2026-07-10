"""
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RefreshToken, EmailToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model"""
    
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_active', 'is_verified'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Admin configuration for RefreshToken model"""
    
    list_display = ['user', 'ip_address', 'device_info', 'expires_at', 'revoked', 'created_at']
    list_filter = ['revoked', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address', 'device_info']
    readonly_fields = ['token_hash', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(EmailToken)
class EmailTokenAdmin(admin.ModelAdmin):
    """Admin configuration for EmailToken model"""
    
    list_display = ['user', 'token_type', 'used', 'expires_at', 'created_at']
    list_filter = ['token_type', 'used', 'created_at', 'expires_at']
    search_fields = ['user__email']
    readonly_fields = ['token_hash', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False