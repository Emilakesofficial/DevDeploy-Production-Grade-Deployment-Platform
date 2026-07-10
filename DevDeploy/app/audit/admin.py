"""
Admin configuration for audit app
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AuditLog model"""
    
    list_display = ['action', 'user', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'ip_address', 'action']
    readonly_fields = ['id', 'user', 'action', 'ip_address', 'user_agent', 'metadata', 'timestamp']
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser