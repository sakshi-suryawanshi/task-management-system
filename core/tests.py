"""
Comprehensive tests for Core app components.

This module contains tests for:
- Health check view
- ActivityLog model
- Permission classes (if needed)
"""

import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from django.db import connection
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

from core.views import health_check
from core.models import ActivityLog
from factories import UserFactory, TaskFactory, ProjectFactory, TeamFactory


# ============================================================================
# Health Check View Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.view
class TestHealthCheckView:
    """Test suite for health check endpoint."""
    
    def test_health_check_all_healthy(self):
        """Test health check when all services are healthy."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        response = health_check(request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'database' in data['services']
        assert data['services']['database'] == 'healthy'
    
    def test_health_check_database_unhealthy(self):
        """Test health check when database is unhealthy."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch.object(connection, 'cursor') as mock_cursor:
            mock_cursor.side_effect = Exception("Database connection failed")
            
            response = health_check(request)
            
            assert response.status_code == 503
            data = response.json()
            assert data['status'] == 'unhealthy'
            assert 'database' in data['services']
            assert 'unhealthy' in data['services']['database']
    
    def test_health_check_redis_healthy(self):
        """Test health check when Redis is healthy."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('core.views.redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.from_url.return_value = mock_client
            
            # Set CELERY_BROKER_URL in settings
            original_broker = getattr(settings, 'CELERY_BROKER_URL', None)
            with patch.object(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'):
                response = health_check(request)
                
                assert response.status_code == 200
                data = response.json()
                assert 'redis' in data['services']
                assert data['services']['redis'] == 'healthy'
    
    def test_health_check_redis_unhealthy(self):
        """Test health check when Redis is unhealthy."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('core.views.redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Redis connection failed")
            mock_redis.from_url.return_value = mock_client
            
            # Set CELERY_BROKER_URL in settings
            original_broker = getattr(settings, 'CELERY_BROKER_URL', None)
            with patch.object(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'):
                with patch.object(settings, 'DEBUG', False):  # In production, Redis failure makes it unhealthy
                    response = health_check(request)
                    
                    assert response.status_code == 503
                    data = response.json()
                    assert data['status'] == 'unhealthy'
                    assert 'redis' in data['services']
                    assert 'unhealthy' in data['services']['redis']
    
    def test_health_check_redis_not_configured(self):
        """Test health check when Redis is not configured."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch.object(settings, 'CELERY_BROKER_URL', None):
            response = health_check(request)
            
            assert response.status_code == 200
            data = response.json()
            assert 'redis' in data['services']
            assert data['services']['redis'] == 'not configured'
    
    def test_health_check_redis_unhealthy_in_debug_mode(self):
        """Test health check when Redis is unhealthy but DEBUG=True (should not fail)."""
        factory = RequestFactory()
        request = factory.get('/health/')
        
        with patch('core.views.redis') as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Redis connection failed")
            mock_redis.from_url.return_value = mock_client
            
            with patch.object(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'):
                with patch.object(settings, 'DEBUG', True):  # In debug mode, Redis failure doesn't fail health check
                    response = health_check(request)
                    
                    # Should still return 200 in debug mode even if Redis fails
                    assert response.status_code == 200
                    data = response.json()
                    assert 'redis' in data['services']
                    assert 'unhealthy' in data['services']['redis']


# ============================================================================
# ActivityLog Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestActivityLogModel:
    """Test suite for ActivityLog model."""
    
    def test_activity_log_creation(self):
        """Test basic activity log creation."""
        user = UserFactory()
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            metadata={'test': 'data'}
        )
        
        assert log.user == user
        assert log.action == ActivityLog.ACTION_CREATED
        assert log.metadata == {'test': 'data'}
        assert log.pk is not None
    
    def test_activity_log_str_representation(self):
        """Test string representation of ActivityLog."""
        user = UserFactory(username='testuser')
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED
        )
        
        str_repr = str(log)
        assert 'testuser' in str_repr
        assert 'Created' in str_repr
    
    def test_activity_log_without_user(self):
        """Test activity log creation without user."""
        log = ActivityLog.objects.create(
            action=ActivityLog.ACTION_CREATED,
            metadata={'system': 'action'}
        )
        
        assert log.user is None
        assert log.action == ActivityLog.ACTION_CREATED
    
    def test_activity_log_with_related_object(self):
        """Test activity log with related object using GenericForeignKey."""
        user = UserFactory()
        task = TaskFactory()
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            obj=task
        )
        
        assert log.user == user
        assert log.content_object == task
        assert log.content_type == ContentType.objects.get_for_model(task.__class__)
        assert log.object_id == task.pk
    
    def test_activity_log_without_related_object(self):
        """Test activity log creation without related object."""
        user = UserFactory()
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_LOGIN
        )
        
        assert log.user == user
        assert log.content_object is None
        assert log.content_type is None
        assert log.object_id is None
    
    def test_activity_log_with_metadata(self):
        """Test activity log with metadata."""
        user = UserFactory()
        metadata = {'key': 'value', 'number': 123}
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_UPDATED,
            metadata=metadata
        )
        
        assert log.metadata == metadata
    
    def test_activity_log_with_ip_and_user_agent(self):
        """Test activity log with IP address and user agent."""
        user = UserFactory()
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_LOGIN,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        assert log.ip_address == '192.168.1.1'
        assert log.user_agent == 'Mozilla/5.0'
    
    def test_get_object_display_with_object(self):
        """Test get_object_display when object exists."""
        user = UserFactory()
        task = TaskFactory()
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            obj=task
        )
        
        display = log.get_object_display()
        assert str(task) in display or task.title in display
    
    def test_get_object_display_without_object(self):
        """Test get_object_display when object doesn't exist."""
        user = UserFactory()
        
        log = ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_LOGIN
        )
        
        display = log.get_object_display()
        assert display == 'Unknown Object'
    
    def test_get_user_display_with_user(self):
        """Test get_user_display when user exists."""
        user = UserFactory(username='testuser')
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED
        )
        
        assert log.get_user_display() == 'testuser'
    
    def test_get_user_display_without_user(self):
        """Test get_user_display when user is None."""
        log = ActivityLog.objects.create(
            action=ActivityLog.ACTION_CREATED
        )
        
        assert log.get_user_display() == 'System'
    
    def test_get_action_display_class(self):
        """Test get_action_display_class returns correct CSS class."""
        user = UserFactory()
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED
        )
        
        assert log.get_action_display_class() == 'created'
        
        log.action = ActivityLog.ACTION_UPDATED
        assert log.get_action_display_class() == 'updated'
        
        log.action = ActivityLog.ACTION_DELETED
        assert log.get_action_display_class() == 'deleted'
    
    def test_get_icon(self):
        """Test get_icon returns correct icon name."""
        user = UserFactory()
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED
        )
        
        assert log.get_icon() == 'plus-circle'
        
        log.action = ActivityLog.ACTION_UPDATED
        assert log.get_icon() == 'edit'
        
        log.action = ActivityLog.ACTION_LOGIN
        assert log.get_icon() == 'log-in'
    
    def test_get_age_in_days(self):
        """Test get_age_in_days calculates correctly."""
        user = UserFactory()
        past_time = timezone.now() - timedelta(days=5)
        
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=past_time
        )
        
        # Should be approximately 5 days (allowing for small time differences)
        age = log.get_age_in_days()
        assert 4 <= age <= 6
    
    def test_get_age_in_hours(self):
        """Test get_age_in_hours calculates correctly."""
        user = UserFactory()
        past_time = timezone.now() - timedelta(hours=12)
        
        log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=past_time
        )
        
        # Should be approximately 12 hours (allowing for small time differences)
        age = log.get_age_in_hours()
        assert 11 <= age <= 13
    
    def test_is_recent(self):
        """Test is_recent method."""
        user = UserFactory()
        
        # Recent log (1 hour ago)
        recent_log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=timezone.now() - timedelta(hours=1)
        )
        
        # Old log (25 hours ago)
        old_log = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=timezone.now() - timedelta(hours=25)
        )
        
        assert recent_log.is_recent(hours=24) is True
        assert old_log.is_recent(hours=24) is False
    
    def test_get_recent_activities(self):
        """Test get_recent_activities class method."""
        user = UserFactory()
        
        # Create recent activities
        ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=timezone.now() - timedelta(hours=1)
        )
        ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_UPDATED,
            timestamp=timezone.now() - timedelta(hours=2)
        )
        
        # Create old activity (should not be included)
        ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_DELETED,
            timestamp=timezone.now() - timedelta(hours=25)
        )
        
        recent = ActivityLog.get_recent_activities(user=user, hours=24)
        assert recent.count() == 2
    
    def test_get_recent_activities_with_limit(self):
        """Test get_recent_activities respects limit parameter."""
        user = UserFactory()
        
        # Create more than limit
        for i in range(10):
            ActivityLog.objects.create(
                user=user,
                action=ActivityLog.ACTION_CREATED,
                timestamp=timezone.now() - timedelta(hours=i)
            )
        
        recent = ActivityLog.get_recent_activities(user=user, hours=24, limit=5)
        assert recent.count() == 5
    
    def test_get_activities_for_object(self):
        """Test get_activities_for_object class method."""
        user = UserFactory()
        task = TaskFactory()
        
        # Create activities for the task
        ActivityLog.log_activity(user=user, action=ActivityLog.ACTION_CREATED, obj=task)
        ActivityLog.log_activity(user=user, action=ActivityLog.ACTION_UPDATED, obj=task)
        
        # Create activity for different object
        other_task = TaskFactory()
        ActivityLog.log_activity(user=user, action=ActivityLog.ACTION_CREATED, obj=other_task)
        
        activities = ActivityLog.get_activities_for_object(task)
        assert activities.count() == 2
        assert all(act.content_object == task for act in activities)
    
    def test_activity_log_ordering(self):
        """Test that activity logs are ordered by timestamp descending."""
        user = UserFactory()
        
        log1 = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            timestamp=timezone.now() - timedelta(hours=2)
        )
        log2 = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_UPDATED,
            timestamp=timezone.now() - timedelta(hours=1)
        )
        log3 = ActivityLog.objects.create(
            user=user,
            action=ActivityLog.ACTION_DELETED,
            timestamp=timezone.now()
        )
        
        logs = list(ActivityLog.objects.all())
        assert logs[0] == log3  # Most recent first
        assert logs[1] == log2
        assert logs[2] == log1
    
    def test_activity_log_all_action_choices(self):
        """Test that all action choices are valid."""
        user = UserFactory()
        
        # Test all action constants
        actions = [
            ActivityLog.ACTION_CREATED,
            ActivityLog.ACTION_UPDATED,
            ActivityLog.ACTION_DELETED,
            ActivityLog.ACTION_VIEWED,
            ActivityLog.ACTION_ASSIGNED,
            ActivityLog.ACTION_UNASSIGNED,
            ActivityLog.ACTION_STATUS_CHANGED,
            ActivityLog.ACTION_PRIORITY_CHANGED,
            ActivityLog.ACTION_MEMBER_ADDED,
            ActivityLog.ACTION_MEMBER_REMOVED,
            ActivityLog.ACTION_COMMENT_ADDED,
            ActivityLog.ACTION_ATTACHMENT_ADDED,
            ActivityLog.ACTION_LOGIN,
            ActivityLog.ACTION_LOGOUT,
        ]
        
        for action in actions:
            log = ActivityLog.objects.create(
                user=user,
                action=action
            )
            assert log.action == action
            assert log.get_action_display()  # Should not raise error


# ============================================================================
# Permission Classes Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.permission
class TestIsTeamMemberPermission:
    """Test suite for IsTeamMember permission class."""
    
    def test_has_permission_authenticated_user(self, authenticated_api_client, user):
        """Test has_permission returns True for authenticated user."""
        from core.permissions import IsTeamMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/teams/')
        request.user = user
        
        permission = IsTeamMember()
        assert permission.has_permission(request, APIView()) is True
    
    def test_has_permission_unauthenticated_user(self):
        """Test has_permission returns False for unauthenticated user."""
        from core.permissions import IsTeamMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/teams/')
        request.user = None
        
        permission = IsTeamMember()
        assert permission.has_permission(request, APIView()) is False
    
    def test_has_object_permission_team_member(self, team_with_members):
        """Test has_object_permission returns True for team member."""
        from core.permissions import IsTeamMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        team, owner, admin, member = team_with_members
        factory = APIRequestFactory()
        request = factory.get(f'/api/teams/{team.id}/')
        request.user = member
        
        permission = IsTeamMember()
        assert permission.has_object_permission(request, APIView(), team) is True
    
    def test_has_object_permission_not_team_member(self, team, user):
        """Test has_object_permission returns False for non-team member."""
        from core.permissions import IsTeamMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/teams/{team.id}/')
        request.user = user
        
        permission = IsTeamMember()
        assert permission.has_object_permission(request, APIView(), team) is False
    
    def test_has_object_permission_wrong_object_type(self, user):
        """Test has_object_permission raises PermissionDenied for wrong object type."""
        from core.permissions import IsTeamMember
        from rest_framework.exceptions import PermissionDenied
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/teams/1/')
        request.user = user
        
        permission = IsTeamMember()
        with pytest.raises(PermissionDenied):
            permission.has_object_permission(request, APIView(), "not a team")


@pytest.mark.django_db
@pytest.mark.permission
class TestIsProjectMemberPermission:
    """Test suite for IsProjectMember permission class."""
    
    def test_has_permission_authenticated_user(self, authenticated_api_client, user):
        """Test has_permission returns True for authenticated user."""
        from core.permissions import IsProjectMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/projects/')
        request.user = user
        
        permission = IsProjectMember()
        assert permission.has_permission(request, APIView()) is True
    
    def test_has_permission_unauthenticated_user(self):
        """Test has_permission returns False for unauthenticated user."""
        from core.permissions import IsProjectMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/projects/')
        request.user = None
        
        permission = IsProjectMember()
        assert permission.has_permission(request, APIView()) is False
    
    def test_has_object_permission_project_member(self, project_with_members):
        """Test has_object_permission returns True for project member."""
        from core.permissions import IsProjectMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        project, owner, admin, member = project_with_members
        factory = APIRequestFactory()
        request = factory.get(f'/api/projects/{project.id}/')
        request.user = member
        
        permission = IsProjectMember()
        assert permission.has_object_permission(request, APIView(), project) is True
    
    def test_has_object_permission_not_project_member(self, project, user):
        """Test has_object_permission returns False for non-project member."""
        from core.permissions import IsProjectMember
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/projects/{project.id}/')
        request.user = user
        
        permission = IsProjectMember()
        assert permission.has_object_permission(request, APIView(), project) is False
    
    def test_has_object_permission_wrong_object_type(self, user):
        """Test has_object_permission raises PermissionDenied for wrong object type."""
        from core.permissions import IsProjectMember
        from rest_framework.exceptions import PermissionDenied
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/projects/1/')
        request.user = user
        
        permission = IsProjectMember()
        with pytest.raises(PermissionDenied):
            permission.has_object_permission(request, APIView(), "not a project")


@pytest.mark.django_db
@pytest.mark.permission
class TestIsTaskAssigneePermission:
    """Test suite for IsTaskAssignee permission class."""
    
    def test_has_permission_authenticated_user(self, authenticated_api_client, user):
        """Test has_permission returns True for authenticated user."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/')
        request.user = user
        
        permission = IsTaskAssignee()
        assert permission.has_permission(request, APIView()) is True
    
    def test_has_permission_unauthenticated_user(self):
        """Test has_permission returns False for unauthenticated user."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/')
        request.user = None
        
        permission = IsTaskAssignee()
        assert permission.has_permission(request, APIView()) is False
    
    def test_has_object_permission_task_assignee(self, task, user):
        """Test has_object_permission returns True for task assignee."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        task.assignee = user
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = user
        
        permission = IsTaskAssignee()
        assert permission.has_object_permission(request, APIView(), task) is True
    
    def test_has_object_permission_task_creator(self, task, user):
        """Test has_object_permission returns True for task creator."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        task.created_by = user
        task.assignee = None  # Not assigned
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = user
        
        permission = IsTaskAssignee()
        assert permission.has_object_permission(request, APIView(), task) is True
    
    def test_has_object_permission_project_member(self, project_with_members, task):
        """Test has_object_permission returns True for project member."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        project, owner, admin, member = project_with_members
        task.project = project
        task.assignee = None
        task.created_by = None
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = member
        
        permission = IsTaskAssignee()
        assert permission.has_object_permission(request, APIView(), task) is True
    
    def test_has_object_permission_no_access(self, task, user):
        """Test has_object_permission returns False when user has no access."""
        from core.permissions import IsTaskAssignee
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        # Create another user who is not assignee, creator, or project member
        other_user = UserFactory()
        task.assignee = None
        task.created_by = None
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = other_user
        
        permission = IsTaskAssignee()
        assert permission.has_object_permission(request, APIView(), task) is False
    
    def test_has_object_permission_wrong_object_type(self, user):
        """Test has_object_permission raises PermissionDenied for wrong object type."""
        from core.permissions import IsTaskAssignee
        from rest_framework.exceptions import PermissionDenied
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/1/')
        request.user = user
        
        permission = IsTaskAssignee()
        with pytest.raises(PermissionDenied):
            permission.has_object_permission(request, APIView(), "not a task")


@pytest.mark.django_db
@pytest.mark.permission
class TestIsTaskAssigneeOnlyPermission:
    """Test suite for IsTaskAssigneeOnly permission class."""
    
    def test_has_permission_authenticated_user(self, authenticated_api_client, user):
        """Test has_permission returns True for authenticated user."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/')
        request.user = user
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_permission(request, APIView()) is True
    
    def test_has_permission_unauthenticated_user(self):
        """Test has_permission returns False for unauthenticated user."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/')
        request.user = None
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_permission(request, APIView()) is False
    
    def test_has_object_permission_task_assignee(self, task, user):
        """Test has_object_permission returns True for task assignee."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        task.assignee = user
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = user
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_object_permission(request, APIView(), task) is True
    
    def test_has_object_permission_task_creator_not_assigned(self, task, user):
        """Test has_object_permission returns False for task creator who is not assigned."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        task.created_by = user
        task.assignee = None  # Not assigned
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = user
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_object_permission(request, APIView(), task) is False
    
    def test_has_object_permission_project_member_not_assigned(self, project_with_members, task):
        """Test has_object_permission returns False for project member who is not assigned."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        project, owner, admin, member = project_with_members
        task.project = project
        task.assignee = None
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = member
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_object_permission(request, APIView(), task) is False
    
    def test_has_object_permission_no_assignee(self, task, user):
        """Test has_object_permission returns False when task has no assignee."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        task.assignee = None
        task.save()
        
        factory = APIRequestFactory()
        request = factory.get(f'/api/tasks/{task.id}/')
        request.user = user
        
        permission = IsTaskAssigneeOnly()
        assert permission.has_object_permission(request, APIView(), task) is False
    
    def test_has_object_permission_wrong_object_type(self, user):
        """Test has_object_permission raises PermissionDenied for wrong object type."""
        from core.permissions import IsTaskAssigneeOnly
        from rest_framework.exceptions import PermissionDenied
        from rest_framework.test import APIRequestFactory
        from rest_framework.views import APIView
        
        factory = APIRequestFactory()
        request = factory.get('/api/tasks/1/')
        request.user = user
        
        permission = IsTaskAssigneeOnly()
        with pytest.raises(PermissionDenied):
            permission.has_object_permission(request, APIView(), "not a task")
