"""
Admin configuration for core models.
"""

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for ActivityLog model.
    
    Provides comprehensive management interface with filtering, search,
    and detailed activity information display.
    """
    
    list_display = [
        'id',
        'timestamp',
        'user_display',
        'action_display',
        'object_display',
        'object_link',
        'ip_address',
        'age_display',
    ]
    
    list_filter = [
        'action',
        'timestamp',
        'content_type',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'metadata',
        'ip_address',
        'user_agent',
    ]
    
    readonly_fields = [
        'user',
        'action',
        'content_type',
        'object_id',
        'content_object',
        'metadata_display',
        'ip_address',
        'user_agent',
        'timestamp',
        'object_link',
    ]
    
    fieldsets = (
        (_('Activity Information'), {
            'fields': ('user', 'action', 'timestamp', 'age_display')
        }),
        (_('Related Object'), {
            'fields': ('content_type', 'object_id', 'object_link', 'content_object')
        }),
        (_('Additional Information'), {
            'fields': ('metadata_display', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'timestamp'
    
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'content_type')
    
    def user_display(self, obj):
        """Display user with styling."""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            color = '#2271b1' if obj.user.is_active else '#d63638'
            return format_html(
                '<a href="{}" style="color: {};">{}</a>',
                url,
                color,
                obj.user.username
            )
        return format_html('<span style="color: #50575e;">{}</span>', _('System'))
    user_display.short_description = _('User')
    user_display.admin_order_field = 'user__username'
    
    def action_display(self, obj):
        """Display action with color coding."""
        action_colors = {
            ActivityLog.ACTION_CREATED: '#00a32a',  # Green
            ActivityLog.ACTION_UPDATED: '#2271b1',  # Blue
            ActivityLog.ACTION_DELETED: '#d63638',  # Red
            ActivityLog.ACTION_VIEWED: '#50575e',   # Gray
            ActivityLog.ACTION_ASSIGNED: '#2271b1', # Blue
            ActivityLog.ACTION_UNASSIGNED: '#d63638', # Red
            ActivityLog.ACTION_STATUS_CHANGED: '#2271b1', # Blue
            ActivityLog.ACTION_PRIORITY_CHANGED: '#dba617', # Yellow
            ActivityLog.ACTION_MEMBER_ADDED: '#00a32a', # Green
            ActivityLog.ACTION_MEMBER_REMOVED: '#d63638', # Red
            ActivityLog.ACTION_COMMENT_ADDED: '#2271b1', # Blue
            ActivityLog.ACTION_ATTACHMENT_ADDED: '#2271b1', # Blue
            ActivityLog.ACTION_LOGIN: '#00a32a', # Green
            ActivityLog.ACTION_LOGOUT: '#50575e', # Gray
        }
        
        color = action_colors.get(obj.action, '#50575e')
        icon_map = {
            ActivityLog.ACTION_CREATED: '✓',
            ActivityLog.ACTION_UPDATED: '✎',
            ActivityLog.ACTION_DELETED: '✕',
            ActivityLog.ACTION_VIEWED: '👁',
            ActivityLog.ACTION_ASSIGNED: '➕',
            ActivityLog.ACTION_UNASSIGNED: '➖',
            ActivityLog.ACTION_STATUS_CHANGED: '→',
            ActivityLog.ACTION_PRIORITY_CHANGED: '⚑',
            ActivityLog.ACTION_MEMBER_ADDED: '👤+',
            ActivityLog.ACTION_MEMBER_REMOVED: '👤-',
            ActivityLog.ACTION_COMMENT_ADDED: '💬',
            ActivityLog.ACTION_ATTACHMENT_ADDED: '📎',
            ActivityLog.ACTION_LOGIN: '🔓',
            ActivityLog.ACTION_LOGOUT: '🔒',
        }
        icon = icon_map.get(obj.action, '●')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_action_display()
        )
    action_display.short_description = _('Action')
    action_display.admin_order_field = 'action'
    
    def object_display(self, obj):
        """Display related object name."""
        return obj.get_object_display()
    object_display.short_description = _('Object')
    
    def object_link(self, obj):
        """Display link to related object in admin if available."""
        if not obj.content_type or not obj.object_id:
            return format_html('<span style="color: #50575e;">{}</span>', _('N/A'))
        
        try:
            model_class = obj.content_type.model_class()
            if model_class:
                # Try to get admin URL for the object
                admin_url = reverse(
                    f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                    args=[obj.object_id]
                )
                return format_html(
                    '<a href="{}" target="_blank">{}</a>',
                    admin_url,
                    obj.get_object_display()
                )
        except Exception:
            pass
        
        return obj.get_object_display()
    object_link.short_description = _('Link')
    
    def metadata_display(self, obj):
        """Display metadata in a readable format."""
        if not obj.metadata:
            return format_html('<span style="color: #50575e;">{}</span>', _('No metadata'))
        
        # Format JSON metadata nicely
        import json
        formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        return format_html('<pre style="background: #f0f0f0; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
    metadata_display.short_description = _('Metadata')
    
    def age_display(self, obj):
        """Display age of activity in human-readable format."""
        hours = obj.get_age_in_hours()
        
        if hours < 1:
            minutes = int(hours * 60)
            return format_html('<span style="color: #00a32a;">{} {}</span>', minutes, _('min ago'))
        elif hours < 24:
            hours_int = int(hours)
            color = '#00a32a' if hours_int < 6 else '#dba617'
            return format_html('<span style="color: {};">{} {}</span>', color, hours_int, _('hours ago'))
        else:
            days = obj.get_age_in_days()
            color = '#dba617' if days < 7 else '#50575e'
            return format_html('<span style="color: {};">{} {}</span>', color, days, _('days ago'))
    age_display.short_description = _('Age')
    age_display.admin_order_field = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable manual addition of activity logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make activity logs read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of activity logs (with caution)."""
        return request.user.is_superuser
