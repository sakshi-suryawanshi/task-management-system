"""
Serializers for Notification API.

This module contains DRF serializers for notification management, including
notification serialization and read status management.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    
    Handles notification serialization with computed fields and related object information.
    
    Fields:
        id: Notification ID (read-only)
        user: User ID (read-only, automatically set to current user)
        message: Notification message text
        type: Notification type (task_assigned, task_completed, etc.)
        type_display: Human-readable notification type (read-only)
        read: Whether notification has been read
        read_at: Timestamp when notification was read (read-only)
        related_content_type: Content type of related object (optional, read-only)
        related_object_id: ID of related object (optional, read-only)
        related_object: String representation of related object (read-only)
        metadata: Additional notification metadata (optional)
        created_at: Notification creation timestamp (read-only)
        age_in_hours: Age of notification in hours (read-only)
        age_in_days: Age of notification in days (read-only)
        is_recent: Whether notification is recent (within 24 hours) (read-only)
        icon: Icon name for notification type (read-only)
        type_display_class: CSS class name for notification type (read-only)
    """
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    age_in_hours = serializers.SerializerMethodField(read_only=True)
    age_in_days = serializers.SerializerMethodField(read_only=True)
    is_recent = serializers.SerializerMethodField(read_only=True)
    icon = serializers.SerializerMethodField(read_only=True)
    type_display_class = serializers.SerializerMethodField(read_only=True)
    related_object = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'message',
            'type',
            'type_display',
            'read',
            'read_at',
            'related_content_type',
            'related_object_id',
            'related_object',
            'metadata',
            'created_at',
            'age_in_hours',
            'age_in_days',
            'is_recent',
            'icon',
            'type_display_class',
        ]
        read_only_fields = [
            'id',
            'user',
            'type_display',
            'read_at',
            'related_content_type',
            'related_object_id',
            'related_object',
            'created_at',
            'age_in_hours',
            'age_in_days',
            'is_recent',
            'icon',
            'type_display_class',
        ]
    
    def get_age_in_hours(self, obj):
        """Return the age of the notification in hours."""
        return obj.get_age_in_hours()
    
    def get_age_in_days(self, obj):
        """Return the age of the notification in days."""
        return obj.get_age_in_days()
    
    def get_is_recent(self, obj):
        """Return whether the notification is recent (within 24 hours)."""
        return obj.is_recent(hours=24)
    
    def get_icon(self, obj):
        """Return the icon name for the notification type."""
        return obj.get_icon()
    
    def get_type_display_class(self, obj):
        """Return the CSS class name for the notification type."""
        return obj.get_type_display_class()
    
    def get_related_object(self, obj):
        """Return string representation of related object if available."""
        if obj.related_object:
            return str(obj.related_object)
        return None


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    
    This serializer is used for bulk marking notifications as read.
    It doesn't require any fields - all unread notifications for the user
    will be marked as read.
    """
    pass


class NotificationCountSerializer(serializers.Serializer):
    """
    Serializer for notification count response.
    
    Returns the count of unread notifications for the current user.
    """
    unread_count = serializers.IntegerField(read_only=True)
    total_count = serializers.IntegerField(read_only=True)

