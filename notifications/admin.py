"""
Admin configuration for Notification models.

This module provides Django admin interface configuration
for the Notification model.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    
    Provides comprehensive notification management interface with
    filtering, search, and bulk actions.
    """
    
    list_display = [
        'id',
        'user',
        'get_message_preview',
        'get_type_display_colored',
        'get_read_status_colored',
        'get_related_object_link',
        'get_age_display',
        'created_at',
        'read_at'
    ]
    
    list_filter = [
        'type',
        'read',
        'created_at',
        'read_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'message',
    ]
    
    readonly_fields = [
        'created_at',
        'read_at',
        'get_related_object_link',
        'get_age_display',
        'get_type_display_colored',
        'get_read_status_colored',
    ]
    
    fieldsets = (
        (_('Notification Information'), {
            'fields': (
                'user',
                'message',
                'type',
                'get_type_display_colored',
            )
        }),
        (_('Status'), {
            'fields': (
                'read',
                'get_read_status_colored',
            )
        }),
        (_('Related Object'), {
            'fields': (
                'related_content_type',
                'related_object_id',
                'get_related_object_link',
            ),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'get_age_display',
                'read_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    list_per_page = 50
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def get_message_preview(self, obj):
        """Display a preview of the notification message."""
        if len(obj.message) > 60:
            return f"{obj.message[:60]}..."
        return obj.message
    get_message_preview.short_description = _('Message')
    get_message_preview.admin_order_field = 'message'
    
    def get_type_display_colored(self, obj):
        """Display notification type with color coding."""
        type_colors = {
            Notification.TYPE_TASK_ASSIGNED: '#2271b1',  # Blue
            Notification.TYPE_TASK_COMPLETED: '#00a32a',  # Green
            Notification.TYPE_TASK_UPDATED: '#2271b1',  # Blue
            Notification.TYPE_TASK_DUE_SOON: '#dba617',  # Yellow
            Notification.TYPE_TASK_OVERDUE: '#d63638',  # Red
            Notification.TYPE_TASK_STATUS_CHANGED: '#2271b1',  # Blue
            Notification.TYPE_TASK_PRIORITY_CHANGED: '#dba617',  # Yellow
            Notification.TYPE_PROJECT_UPDATED: '#2271b1',  # Blue
            Notification.TYPE_PROJECT_MEMBER_ADDED: '#00a32a',  # Green
            Notification.TYPE_PROJECT_MEMBER_REMOVED: '#d63638',  # Red
            Notification.TYPE_PROJECT_STATUS_CHANGED: '#2271b1',  # Blue
            Notification.TYPE_TEAM_MEMBER_ADDED: '#00a32a',  # Green
            Notification.TYPE_TEAM_MEMBER_REMOVED: '#d63638',  # Red
            Notification.TYPE_COMMENT_ADDED: '#2271b1',  # Blue
            Notification.TYPE_ATTACHMENT_ADDED: '#2271b1',  # Blue
            Notification.TYPE_TASK_DEPENDENCY_ADDED: '#2271b1',  # Blue
            Notification.TYPE_TASK_DEPENDENCY_COMPLETED: '#00a32a',  # Green
            Notification.TYPE_WELCOME: '#00a32a',  # Green
            Notification.TYPE_SYSTEM: '#50575e',  # Gray
        }
        
        color = type_colors.get(obj.type, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    get_type_display_colored.short_description = _('Type')
    get_type_display_colored.admin_order_field = 'type'
    
    def get_read_status_colored(self, obj):
        """Display read status with color coding."""
        if obj.read:
            return format_html(
                '<span style="color: #00a32a; font-weight: bold;">✓ {}</span>',
                _('Read')
            )
        else:
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">● {}</span>',
                _('Unread')
            )
    get_read_status_colored.short_description = _('Status')
    get_read_status_colored.admin_order_field = 'read'
    
    def get_related_object_link(self, obj):
        """Display a link to the related object if available."""
        if obj.related_object:
            try:
                # Try to get admin URL for the related object
                content_type = obj.related_content_type
                model = content_type.model_class()
                if model:
                    admin_url = reverse(
                        f'admin:{content_type.app_label}_{content_type.model}_change',
                        args=[obj.related_object_id]
                    )
                    return format_html(
                        '<a href="{}" target="_blank">{}</a>',
                        admin_url,
                        str(obj.related_object)
                    )
            except Exception:
                pass
            return str(obj.related_object)
        return format_html('<span style="color: #999;">{}</span>', _('None'))
    get_related_object_link.short_description = _('Related Object')
    
    def get_age_display(self, obj):
        """Display the age of the notification in a human-readable format."""
        age_days = obj.get_age_in_days()
        age_hours = obj.get_age_in_hours()
        
        if age_days == 0:
            if age_hours == 0:
                return _('Just now')
            elif age_hours == 1:
                return _('1 hour ago')
            else:
                return _('{} hours ago').format(age_hours)
        elif age_days == 1:
            return _('1 day ago')
        else:
            return _('{} days ago').format(age_days)
    get_age_display.short_description = _('Age')
    
    def mark_as_read(self, request, queryset):
        """Bulk action to mark selected notifications as read."""
        from django.utils import timezone
        updated = queryset.filter(read=False).update(
            read=True,
            read_at=timezone.now()
        )
        self.message_user(
            request,
            _('{} notification(s) marked as read.').format(updated),
            level='success'
        )
    mark_as_read.short_description = _('Mark selected notifications as read')
    
    def mark_as_unread(self, request, queryset):
        """Bulk action to mark selected notifications as unread."""
        updated = queryset.filter(read=True).update(
            read=False,
            read_at=None
        )
        self.message_user(
            request,
            _('{} notification(s) marked as unread.').format(updated),
            level='success'
        )
    mark_as_unread.short_description = _('Mark selected notifications as unread')
    
    def get_list_filter(self, request):
        """Add user filter if user is not superuser."""
        filters = list(self.list_filter)
        if not request.user.is_superuser:
            # Non-superusers can only see their own notifications
            # This is handled in get_queryset, but we can add user filter
            if 'user' not in filters:
                filters.insert(0, 'user')
        return filters
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see their own notifications
            qs = qs.filter(user=request.user)
        return qs.select_related('user', 'related_content_type')
