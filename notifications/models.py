"""
Notification models for Task Management System.

This module defines the Notification model for managing user notifications
across the task management application.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Notification(models.Model):
    """
    Notification model for user notifications.
    
    Notifications inform users about various events in the system such as
    task assignments, project updates, comments, etc.
    
    Fields:
        user: ForeignKey to User (notification recipient)
        message: Notification message text
        type: Type of notification (task_assigned, task_completed, etc.)
        read: Boolean indicating if notification has been read
        created_at: Notification creation timestamp
        related_content_type: ContentType for generic foreign key (optional)
        related_object_id: ID of related object (optional)
        related_object: GenericForeignKey to related object (optional)
    """
    
    # Notification type constants
    TYPE_TASK_ASSIGNED = 'task_assigned'
    TYPE_TASK_COMPLETED = 'task_completed'
    TYPE_TASK_UPDATED = 'task_updated'
    TYPE_TASK_DUE_SOON = 'task_due_soon'
    TYPE_TASK_OVERDUE = 'task_overdue'
    TYPE_TASK_STATUS_CHANGED = 'task_status_changed'
    TYPE_TASK_PRIORITY_CHANGED = 'task_priority_changed'
    TYPE_PROJECT_UPDATED = 'project_updated'
    TYPE_PROJECT_MEMBER_ADDED = 'project_member_added'
    TYPE_PROJECT_MEMBER_REMOVED = 'project_member_removed'
    TYPE_PROJECT_STATUS_CHANGED = 'project_status_changed'
    TYPE_TEAM_MEMBER_ADDED = 'team_member_added'
    TYPE_TEAM_MEMBER_REMOVED = 'team_member_removed'
    TYPE_COMMENT_ADDED = 'comment_added'
    TYPE_ATTACHMENT_ADDED = 'attachment_added'
    TYPE_TASK_DEPENDENCY_ADDED = 'task_dependency_added'
    TYPE_TASK_DEPENDENCY_COMPLETED = 'task_dependency_completed'
    TYPE_WELCOME = 'welcome'
    TYPE_SYSTEM = 'system'
    
    TYPE_CHOICES = [
        # Task-related notifications
        (TYPE_TASK_ASSIGNED, _('Task Assigned')),
        (TYPE_TASK_COMPLETED, _('Task Completed')),
        (TYPE_TASK_UPDATED, _('Task Updated')),
        (TYPE_TASK_DUE_SOON, _('Task Due Soon')),
        (TYPE_TASK_OVERDUE, _('Task Overdue')),
        (TYPE_TASK_STATUS_CHANGED, _('Task Status Changed')),
        (TYPE_TASK_PRIORITY_CHANGED, _('Task Priority Changed')),
        (TYPE_TASK_DEPENDENCY_ADDED, _('Task Dependency Added')),
        (TYPE_TASK_DEPENDENCY_COMPLETED, _('Task Dependency Completed')),
        
        # Project-related notifications
        (TYPE_PROJECT_UPDATED, _('Project Updated')),
        (TYPE_PROJECT_MEMBER_ADDED, _('Project Member Added')),
        (TYPE_PROJECT_MEMBER_REMOVED, _('Project Member Removed')),
        (TYPE_PROJECT_STATUS_CHANGED, _('Project Status Changed')),
        
        # Team-related notifications
        (TYPE_TEAM_MEMBER_ADDED, _('Team Member Added')),
        (TYPE_TEAM_MEMBER_REMOVED, _('Team Member Removed')),
        
        # Comment and attachment notifications
        (TYPE_COMMENT_ADDED, _('Comment Added')),
        (TYPE_ATTACHMENT_ADDED, _('Attachment Added')),
        
        # System notifications
        (TYPE_WELCOME, _('Welcome')),
        (TYPE_SYSTEM, _('System Notification')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('User'),
        help_text=_('User who will receive this notification')
    )
    
    message = models.TextField(
        max_length=500,
        help_text=_('Notification message')
    )
    
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        db_index=True,
        help_text=_('Type of notification')
    )
    
    read = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_('Whether the notification has been read')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when notification was read')
    )
    
    # Generic foreign key for linking to related objects (Task, Project, etc.)
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        help_text=_('Content type of related object')
    )
    
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of related object')
    )
    
    related_object = GenericForeignKey(
        'related_content_type',
        'related_object_id'
    )
    
    # Additional metadata (JSON field would be better, but keeping it simple)
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Additional notification metadata')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Notification creation timestamp')
    )
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['type', 'created_at']),
            models.Index(fields=['read', 'created_at']),
        ]
    
    def __str__(self):
        """Return string representation of notification."""
        read_status = _('Read') if self.read else _('Unread')
        return f"{self.get_type_display()} - {self.user.username} ({read_status})"
    
    def mark_as_read(self):
        """
        Mark the notification as read.
        
        Sets the read flag to True and records the read timestamp.
        """
        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=['read', 'read_at'])
    
    def mark_as_unread(self):
        """
        Mark the notification as unread.
        
        Sets the read flag to False and clears the read timestamp.
        """
        if self.read:
            self.read = False
            self.read_at = None
            self.save(update_fields=['read', 'read_at'])
    
    def is_unread(self):
        """
        Check if the notification is unread.
        
        Returns:
            bool: True if notification is unread, False otherwise
        """
        return not self.read
    
    def is_read(self):
        """
        Check if the notification has been read.
        
        Returns:
            bool: True if notification is read, False otherwise
        """
        return self.read
    
    def get_age_in_days(self):
        """
        Get the age of the notification in days.
        
        Returns:
            int: Number of days since notification was created
        """
        time_diff = timezone.now() - self.created_at
        return time_diff.days
    
    def get_age_in_hours(self):
        """
        Get the age of the notification in hours.
        
        Returns:
            int: Number of hours since notification was created
        """
        time_diff = timezone.now() - self.created_at
        return int(time_diff.total_seconds() / 3600)
    
    def is_recent(self, hours=24):
        """
        Check if the notification is recent (within specified hours).
        
        Args:
            hours: Number of hours to consider as recent (default: 24)
            
        Returns:
            bool: True if notification was created within the specified hours
        """
        return self.get_age_in_hours() < hours
    
    def get_type_display_class(self):
        """
        Get CSS class name for notification type display (for admin/frontend).
        
        Returns:
            str: CSS class name for notification type
        """
        type_classes = {
            self.TYPE_TASK_ASSIGNED: 'task-assigned',
            self.TYPE_TASK_COMPLETED: 'task-completed',
            self.TYPE_TASK_UPDATED: 'task-updated',
            self.TYPE_TASK_DUE_SOON: 'task-due-soon',
            self.TYPE_TASK_OVERDUE: 'task-overdue',
            self.TYPE_TASK_STATUS_CHANGED: 'task-status-changed',
            self.TYPE_TASK_PRIORITY_CHANGED: 'task-priority-changed',
            self.TYPE_PROJECT_UPDATED: 'project-updated',
            self.TYPE_PROJECT_MEMBER_ADDED: 'project-member-added',
            self.TYPE_PROJECT_MEMBER_REMOVED: 'project-member-removed',
            self.TYPE_PROJECT_STATUS_CHANGED: 'project-status-changed',
            self.TYPE_TEAM_MEMBER_ADDED: 'team-member-added',
            self.TYPE_TEAM_MEMBER_REMOVED: 'team-member-removed',
            self.TYPE_COMMENT_ADDED: 'comment-added',
            self.TYPE_ATTACHMENT_ADDED: 'attachment-added',
            self.TYPE_TASK_DEPENDENCY_ADDED: 'task-dependency-added',
            self.TYPE_TASK_DEPENDENCY_COMPLETED: 'task-dependency-completed',
            self.TYPE_WELCOME: 'welcome',
            self.TYPE_SYSTEM: 'system',
        }
        return type_classes.get(self.type, '')
    
    def get_icon(self):
        """
        Get icon name for notification type (for frontend display).
        
        Returns:
            str: Icon name based on notification type
        """
        icon_map = {
            self.TYPE_TASK_ASSIGNED: 'assignment',
            self.TYPE_TASK_COMPLETED: 'check_circle',
            self.TYPE_TASK_UPDATED: 'update',
            self.TYPE_TASK_DUE_SOON: 'schedule',
            self.TYPE_TASK_OVERDUE: 'warning',
            self.TYPE_TASK_STATUS_CHANGED: 'swap_horiz',
            self.TYPE_TASK_PRIORITY_CHANGED: 'priority_high',
            self.TYPE_PROJECT_UPDATED: 'folder',
            self.TYPE_PROJECT_MEMBER_ADDED: 'person_add',
            self.TYPE_PROJECT_MEMBER_REMOVED: 'person_remove',
            self.TYPE_PROJECT_STATUS_CHANGED: 'change_circle',
            self.TYPE_TEAM_MEMBER_ADDED: 'group_add',
            self.TYPE_TEAM_MEMBER_REMOVED: 'group_remove',
            self.TYPE_COMMENT_ADDED: 'comment',
            self.TYPE_ATTACHMENT_ADDED: 'attach_file',
            self.TYPE_TASK_DEPENDENCY_ADDED: 'link',
            self.TYPE_TASK_DEPENDENCY_COMPLETED: 'link_off',
            self.TYPE_WELCOME: 'waving_hand',
            self.TYPE_SYSTEM: 'notifications',
        }
        return icon_map.get(self.type, 'notifications')
    
    @classmethod
    def get_unread_count(cls, user):
        """
        Get the count of unread notifications for a user.
        
        Args:
            user: User instance
            
        Returns:
            int: Number of unread notifications
        """
        return cls.objects.filter(user=user, read=False).count()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        Mark all notifications as read for a user.
        
        Args:
            user: User instance
        """
        now = timezone.now()
        cls.objects.filter(user=user, read=False).update(
            read=True,
            read_at=now
        )
    
    @classmethod
    def create_notification(cls, user, message, notification_type, related_object=None, metadata=None):
        """
        Create a notification with optional related object.
        
        Args:
            user: User instance (notification recipient)
            message: Notification message text
            notification_type: Type of notification (use TYPE_* constants)
            related_object: Optional related object (Task, Project, etc.)
            metadata: Optional dictionary with additional metadata
            
        Returns:
            Notification: Created notification instance
        """
        notification = cls(
            user=user,
            message=message,
            type=notification_type,
            metadata=metadata
        )
        
        if related_object:
            notification.related_content_type = ContentType.objects.get_for_model(related_object)
            notification.related_object_id = related_object.pk
        
        notification.save()
        return notification
