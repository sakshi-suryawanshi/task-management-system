"""
Core models for Task Management System.

This module defines core models that are used across the application,
such as ActivityLog for tracking user activities.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class ActivityLog(models.Model):
    """
    ActivityLog model for tracking user activities across the system.
    
    This model provides an audit trail of all significant actions performed
    by users on various objects (Tasks, Projects, Teams, etc.). It uses
    Django's ContentType framework to create a generic foreign key relationship,
    allowing it to track activities on any model type.
    
    Fields:
        user: User who performed the action (ForeignKey to User)
        action: Type of action performed (created, updated, deleted, etc.)
        content_type: ContentType of the related object (ForeignKey)
        object_id: Primary key of the related object (PositiveIntegerField)
        content_object: GenericForeignKey to the related object
        metadata: Additional action details in JSON format (JSONField)
        ip_address: IP address of the user (optional, for security tracking)
        user_agent: User agent string (optional, for security tracking)
        timestamp: When the action was performed (DateTimeField)
    """
    
    # Action type constants
    ACTION_CREATED = 'created'
    ACTION_UPDATED = 'updated'
    ACTION_DELETED = 'deleted'
    ACTION_VIEWED = 'viewed'
    ACTION_ASSIGNED = 'assigned'
    ACTION_UNASSIGNED = 'unassigned'
    ACTION_STATUS_CHANGED = 'status_changed'
    ACTION_PRIORITY_CHANGED = 'priority_changed'
    ACTION_MEMBER_ADDED = 'member_added'
    ACTION_MEMBER_REMOVED = 'member_removed'
    ACTION_COMMENT_ADDED = 'comment_added'
    ACTION_ATTACHMENT_ADDED = 'attachment_added'
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    
    ACTION_CHOICES = [
        (ACTION_CREATED, _('Created')),
        (ACTION_UPDATED, _('Updated')),
        (ACTION_DELETED, _('Deleted')),
        (ACTION_VIEWED, _('Viewed')),
        (ACTION_ASSIGNED, _('Assigned')),
        (ACTION_UNASSIGNED, _('Unassigned')),
        (ACTION_STATUS_CHANGED, _('Status Changed')),
        (ACTION_PRIORITY_CHANGED, _('Priority Changed')),
        (ACTION_MEMBER_ADDED, _('Member Added')),
        (ACTION_MEMBER_REMOVED, _('Member Removed')),
        (ACTION_COMMENT_ADDED, _('Comment Added')),
        (ACTION_ATTACHMENT_ADDED, _('Attachment Added')),
        (ACTION_LOGIN, _('Login')),
        (ACTION_LOGOUT, _('Logout')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('User'),
        help_text=_('User who performed the action')
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text=_('Type of action performed')
    )
    
    # Generic foreign key to link to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        null=True,
        blank=True,
        verbose_name=_('Content Type'),
        help_text=_('Type of the related object (optional)')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Primary key of the related object (optional)')
    )
    
    content_object = GenericForeignKey('content_type', 'object_id')
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional action details in JSON format')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        help_text=_('IP address of the user (optional)')
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('User Agent'),
        help_text=_('User agent string (optional)')
    )
    
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text=_('When the action was performed')
    )
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']
        verbose_name = _('Activity Log')
        verbose_name_plural = _('Activity Logs')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id', 'timestamp']),
        ]
    
    def __str__(self):
        """Return string representation of activity log."""
        user_str = self.user.username if self.user else 'Unknown'
        obj_str = self.get_object_display()
        return f"{user_str} {self.get_action_display()} {obj_str}"
    
    @classmethod
    def log_activity(cls, user, action, obj=None, metadata=None, ip_address=None, user_agent=None):
        """
        Class method to create an activity log entry.
        
        Args:
            user: User instance who performed the action (can be None)
            action: Action type (must be one of ACTION_* constants)
            obj: Object instance that the action was performed on (optional)
            metadata: Dictionary of additional metadata (optional)
            ip_address: IP address string (optional)
            user_agent: User agent string (optional)
            
        Returns:
            ActivityLog: Created ActivityLog instance
            
        Example:
            ActivityLog.log_activity(
                user=request.user,
                action=ActivityLog.ACTION_CREATED,
                obj=task,
                metadata={'title': task.title, 'project': task.project.name}
            )
        """
        # Convert None to empty string for CharField (user_agent)
        user_agent = user_agent or ''
        
        if obj is None:
            # If no object provided, create log without content_type/object_id
            log = cls.objects.create(
                user=user,
                action=action,
                content_type=None,
                object_id=None,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            content_type = ContentType.objects.get_for_model(obj.__class__)
            log = cls.objects.create(
                user=user,
                action=action,
                content_type=content_type,
                object_id=obj.pk,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent,
            )
        
        return log
    
    def get_object_display(self):
        """
        Get a string representation of the related object.
        
        Returns:
            str: String representation of the object, or 'Unknown Object' if not available
        """
        if self.content_object:
            return str(self.content_object)
        elif self.content_type:
            return f'{self.content_type.name} #{self.object_id}'
        return _('Unknown Object')
    
    def get_user_display(self):
        """
        Get a string representation of the user.
        
        Returns:
            str: Username or 'System' if user is None
        """
        if self.user:
            return self.user.username
        return _('System')
    
    def get_action_display_class(self):
        """
        Get CSS class name for action display (for admin/frontend).
        
        Returns:
            str: CSS class name for action
        """
        action_classes = {
            self.ACTION_CREATED: 'created',
            self.ACTION_UPDATED: 'updated',
            self.ACTION_DELETED: 'deleted',
            self.ACTION_VIEWED: 'viewed',
            self.ACTION_ASSIGNED: 'assigned',
            self.ACTION_UNASSIGNED: 'unassigned',
            self.ACTION_STATUS_CHANGED: 'status-changed',
            self.ACTION_PRIORITY_CHANGED: 'priority-changed',
            self.ACTION_MEMBER_ADDED: 'member-added',
            self.ACTION_MEMBER_REMOVED: 'member-removed',
            self.ACTION_COMMENT_ADDED: 'comment-added',
            self.ACTION_ATTACHMENT_ADDED: 'attachment-added',
            self.ACTION_LOGIN: 'login',
            self.ACTION_LOGOUT: 'logout',
        }
        return action_classes.get(self.action, '')
    
    def get_icon(self):
        """
        Get icon name for action type (for frontend display).
        
        Returns:
            str: Icon name for the action
        """
        icon_map = {
            self.ACTION_CREATED: 'plus-circle',
            self.ACTION_UPDATED: 'edit',
            self.ACTION_DELETED: 'trash',
            self.ACTION_VIEWED: 'eye',
            self.ACTION_ASSIGNED: 'user-plus',
            self.ACTION_UNASSIGNED: 'user-minus',
            self.ACTION_STATUS_CHANGED: 'arrow-right',
            self.ACTION_PRIORITY_CHANGED: 'flag',
            self.ACTION_MEMBER_ADDED: 'user-plus',
            self.ACTION_MEMBER_REMOVED: 'user-minus',
            self.ACTION_COMMENT_ADDED: 'message-square',
            self.ACTION_ATTACHMENT_ADDED: 'paperclip',
            self.ACTION_LOGIN: 'log-in',
            self.ACTION_LOGOUT: 'log-out',
        }
        return icon_map.get(self.action, 'activity')
    
    def get_age_in_days(self):
        """
        Get the age of this activity log in days.
        
        Returns:
            int: Number of days since the activity was logged
        """
        time_diff = timezone.now() - self.timestamp
        return time_diff.days
    
    def get_age_in_hours(self):
        """
        Get the age of this activity log in hours.
        
        Returns:
            float: Number of hours since the activity was logged
        """
        time_diff = timezone.now() - self.timestamp
        return time_diff.total_seconds() / 3600
    
    def is_recent(self, hours=24):
        """
        Check if the activity log is recent (within specified hours).
        
        Args:
            hours: Number of hours to check against (default: 24)
            
        Returns:
            bool: True if activity is within the specified hours
        """
        return self.get_age_in_hours() <= hours
    
    @classmethod
    def get_recent_activities(cls, user=None, hours=24, limit=50):
        """
        Get recent activity logs.
        
        Args:
            user: User instance to filter by (optional)
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of logs to return (default: 50)
            
        Returns:
            QuerySet: Recent ActivityLog instances
        """
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        queryset = cls.objects.filter(timestamp__gte=cutoff_time)
        
        if user:
            queryset = queryset.filter(user=user)
        
        return queryset[:limit]
    
    @classmethod
    def get_activities_for_object(cls, obj):
        """
        Get all activity logs for a specific object.
        
        Args:
            obj: Object instance to get logs for
            
        Returns:
            QuerySet: ActivityLog instances for the object
        """
        content_type = ContentType.objects.get_for_model(obj.__class__)
        return cls.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        )
