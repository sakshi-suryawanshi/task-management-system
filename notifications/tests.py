"""
API tests for Notification endpoints.

This module contains comprehensive tests for the Notification API endpoints,
including listing, marking as read, and getting notification counts.
"""

import pytest
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification
from factories import NotificationFactory, UserFactory


# ============================================================================
# API Tests - Notification Endpoints
# ============================================================================

@pytest.mark.django_db
@pytest.mark.api
class TestNotificationListAPI:
    """Test suite for notification list API endpoint."""
    
    def test_list_notifications_authenticated(self, authenticated_api_client, user):
        """Test listing notifications when authenticated."""
        notification1 = NotificationFactory(user=user, read=False)
        notification2 = NotificationFactory(user=user, read=True)
        
        url = '/api/notifications/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 2
    
    def test_list_notifications_unauthenticated(self, api_client):
        """Test listing notifications fails when unauthenticated."""
        url = '/api/notifications/'
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_list_notifications_only_own(self, authenticated_api_client, user):
        """Test that users only see their own notifications."""
        other_user = UserFactory()
        own_notification = NotificationFactory(user=user)
        other_notification = NotificationFactory(user=other_user)
        
        url = '/api/notifications/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        notification_ids = [n['id'] for n in response.data]
        assert own_notification.id in notification_ids
        assert other_notification.id not in notification_ids
    
    def test_list_notifications_filter_by_read(self, authenticated_api_client, user):
        """Test filtering notifications by read status."""
        read_notification = NotificationFactory(user=user, read=True)
        unread_notification = NotificationFactory(user=user, read=False)
        
        url = '/api/notifications/?read=true'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        notification_ids = [n['id'] for n in response.data]
        assert read_notification.id in notification_ids
        assert unread_notification.id not in notification_ids
        
        url = '/api/notifications/?read=false'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        notification_ids = [n['id'] for n in response.data]
        assert unread_notification.id in notification_ids
        assert read_notification.id not in notification_ids
    
    def test_list_notifications_filter_by_type(self, authenticated_api_client, user):
        """Test filtering notifications by type."""
        task_notification = NotificationFactory(
            user=user,
            type='task_assigned'
        )
        project_notification = NotificationFactory(
            user=user,
            type='project_updated'
        )
        
        url = '/api/notifications/?type=task_assigned'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        notification_ids = [n['id'] for n in response.data]
        assert task_notification.id in notification_ids
        assert project_notification.id not in notification_ids
    
    def test_list_notifications_ordering(self, authenticated_api_client, user):
        """Test that notifications are ordered by created_at descending."""
        notification1 = NotificationFactory(user=user)
        notification2 = NotificationFactory(user=user)
        notification3 = NotificationFactory(user=user)
        
        url = '/api/notifications/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        # Should be ordered newest first
        assert len(response.data) >= 3
        # Check ordering (newest first)
        created_dates = [n['created_at'] for n in response.data[:3]]
        assert created_dates[0] >= created_dates[1]
        assert created_dates[1] >= created_dates[2]
    
    def test_list_notifications_search(self, authenticated_api_client, user):
        """Test searching notifications by message content."""
        notification1 = NotificationFactory(
            user=user,
            message='Task assigned to you'
        )
        notification2 = NotificationFactory(
            user=user,
            message='Project updated'
        )
        
        url = '/api/notifications/?search=Task'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        notification_ids = [n['id'] for n in response.data]
        assert notification1.id in notification_ids


@pytest.mark.django_db
@pytest.mark.api
class TestNotificationDetailAPI:
    """Test suite for notification detail API endpoint."""
    
    def test_get_notification_detail_success(self, authenticated_api_client, user):
        """Test retrieving notification details."""
        notification = NotificationFactory(user=user)
        
        url = f'/api/notifications/{notification.id}/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['id'] == notification.id
        assert response.data['message'] == notification.message
    
    def test_get_notification_detail_not_own(self, authenticated_api_client, user):
        """Test retrieving notification details fails for other user's notification."""
        other_user = UserFactory()
        notification = NotificationFactory(user=other_user)
        
        url = f'/api/notifications/{notification.id}/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 404
    
    def test_get_notification_detail_unauthenticated(self, api_client, user):
        """Test retrieving notification details fails when unauthenticated."""
        notification = NotificationFactory(user=user)
        
        url = f'/api/notifications/{notification.id}/'
        response = api_client.get(url)
        
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.api
class TestNotificationMarkReadAPI:
    """Test suite for marking notification as read API endpoint."""
    
    def test_mark_notification_read_success(self, authenticated_api_client, user):
        """Test marking a notification as read."""
        notification = NotificationFactory(user=user, read=False)
        
        url = f'/api/notifications/{notification.id}/mark-read/'
        response = authenticated_api_client.patch(url)
        
        assert response.status_code == 200
        assert response.data['data']['read'] is True
        assert response.data['message'] == 'Notification marked as read'
        
        # Verify in database
        notification.refresh_from_db()
        assert notification.read is True
        assert notification.read_at is not None
    
    def test_mark_notification_read_already_read(self, authenticated_api_client, user):
        """Test marking an already read notification as read."""
        notification = NotificationFactory(user=user, read=True)
        original_read_at = notification.read_at
        
        url = f'/api/notifications/{notification.id}/mark-read/'
        response = authenticated_api_client.patch(url)
        
        assert response.status_code == 200
        assert response.data['data']['read'] is True
    
    def test_mark_notification_read_not_own(self, authenticated_api_client, user):
        """Test marking notification as read fails for other user's notification."""
        other_user = UserFactory()
        notification = NotificationFactory(user=other_user, read=False)
        
        url = f'/api/notifications/{notification.id}/mark-read/'
        response = authenticated_api_client.patch(url)
        
        assert response.status_code == 403
    
    def test_mark_notification_read_unauthenticated(self, api_client, user):
        """Test marking notification as read fails when unauthenticated."""
        notification = NotificationFactory(user=user, read=False)
        
        url = f'/api/notifications/{notification.id}/mark-read/'
        response = api_client.patch(url)
        
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.api
class TestNotificationMarkAllReadAPI:
    """Test suite for marking all notifications as read API endpoint."""
    
    def test_mark_all_notifications_read_success(self, authenticated_api_client, user):
        """Test marking all notifications as read."""
        unread1 = NotificationFactory(user=user, read=False)
        unread2 = NotificationFactory(user=user, read=False)
        read_notification = NotificationFactory(user=user, read=True)
        
        url = '/api/notifications/mark-all-read/'
        response = authenticated_api_client.post(url)
        
        assert response.status_code == 200
        assert response.data['message'] == 'All notifications marked as read'
        assert response.data['marked_count'] == 2
        
        # Verify in database
        unread1.refresh_from_db()
        unread2.refresh_from_db()
        assert unread1.read is True
        assert unread2.read is True
    
    def test_mark_all_notifications_read_no_unread(self, authenticated_api_client, user):
        """Test marking all notifications as read when all are already read."""
        read1 = NotificationFactory(user=user, read=True)
        read2 = NotificationFactory(user=user, read=True)
        
        url = '/api/notifications/mark-all-read/'
        response = authenticated_api_client.post(url)
        
        assert response.status_code == 200
        assert response.data['marked_count'] == 0
    
    def test_mark_all_notifications_read_unauthenticated(self, api_client, user):
        """Test marking all notifications as read fails when unauthenticated."""
        url = '/api/notifications/mark-all-read/'
        response = api_client.post(url)
        
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.api
class TestNotificationCountAPI:
    """Test suite for notification count API endpoint."""
    
    def test_get_notification_count_success(self, authenticated_api_client, user):
        """Test getting notification counts."""
        unread1 = NotificationFactory(user=user, read=False)
        unread2 = NotificationFactory(user=user, read=False)
        read_notification = NotificationFactory(user=user, read=True)
        
        url = '/api/notifications/count/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['unread_count'] == 2
        assert response.data['total_count'] == 3
    
    def test_get_notification_count_no_notifications(self, authenticated_api_client, user):
        """Test getting notification counts when user has no notifications."""
        url = '/api/notifications/count/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['unread_count'] == 0
        assert response.data['total_count'] == 0
    
    def test_get_notification_count_only_own(self, authenticated_api_client, user):
        """Test that notification counts only include own notifications."""
        own_unread = NotificationFactory(user=user, read=False)
        other_user = UserFactory()
        other_notification = NotificationFactory(user=other_user, read=False)
        
        url = '/api/notifications/count/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['unread_count'] == 1
        assert response.data['total_count'] == 1
    
    def test_get_notification_count_unauthenticated(self, api_client):
        """Test getting notification counts fails when unauthenticated."""
        url = '/api/notifications/count/'
        response = api_client.get(url)
        
        assert response.status_code == 401
