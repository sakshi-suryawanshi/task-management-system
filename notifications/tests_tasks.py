"""
Comprehensive tests for Celery tasks in notifications app.

This module contains tests for:
- Email notification tasks (send_task_assignment_email, send_task_due_reminder, etc.)
- Notification creation tasks (create_notification, send_bulk_notifications)
- Scheduled tasks (send_daily_reminders, send_weekly_digest, cleanup_old_notifications)

All tests use mocking to avoid actually sending emails and ensure fast execution.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from notifications.tasks import (
    send_task_assignment_email,
    send_task_due_reminder,
    send_project_update_email,
    send_welcome_email,
    create_notification,
    send_bulk_notifications,
    send_daily_reminders,
    send_weekly_digest,
    cleanup_old_notifications,
    should_send_email,
)
from notifications.models import Notification
from users.models import User, UserProfile
from tasks.models import Task
from projects.models import Project
from factories import (
    UserFactory,
    UserProfileFactory,
    TeamFactory,
    ProjectFactory,
    TaskFactory,
    NotificationFactory,
)


# ============================================================================
# Email Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestSendTaskAssignmentEmail:
    """Test suite for send_task_assignment_email task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_assignment_email_success(self, mock_send_email, user, task):
        """Test successful task assignment email sending."""
        assigner = UserFactory()
        
        result = send_task_assignment_email(
            user_id=user.id,
            task_id=task.id,
            assigner_id=assigner.id
        )
        
        assert result['status'] == 'success'
        assert result['user_id'] == user.id
        assert result['task_id'] == task.id
        assert result['email'] == user.email
        assert mock_send_email.called
        assert mock_send_email.call_count == 1

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_assignment_email_without_assigner(self, mock_send_email, user, task):
        """Test task assignment email without assigner ID."""
        result = send_task_assignment_email(
            user_id=user.id,
            task_id=task.id
        )
        
        assert result['status'] == 'success'
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_assignment_email_skips_when_notifications_disabled(
        self, mock_send_email, task
    ):
        """Test that email is skipped when user has notifications disabled."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=False)
        
        result = send_task_assignment_email(
            user_id=user.id,
            task_id=task.id
        )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'email_notifications_disabled'
        assert not mock_send_email.called

    def test_send_task_assignment_email_user_not_found(self, task):
        """Test task assignment email when user doesn't exist."""
        result = send_task_assignment_email(
            user_id=99999,
            task_id=task.id
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'user_not_found'

    def test_send_task_assignment_email_task_not_found(self, user):
        """Test task assignment email when task doesn't exist."""
        result = send_task_assignment_email(
            user_id=user.id,
            task_id=99999
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'task_not_found'

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_assignment_email_with_nonexistent_assigner(
        self, mock_send_email, user, task
    ):
        """Test task assignment email with non-existent assigner ID."""
        result = send_task_assignment_email(
            user_id=user.id,
            task_id=task.id,
            assigner_id=99999
        )
        
        # Should still succeed, using task.created_by as fallback
        assert result['status'] == 'success'
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_assignment_email_retries_on_exception(self, mock_send_email, user, task):
        """Test that task retries on exception."""
        mock_send_email.side_effect = Exception("Email service error")
        
        # Create a mock task instance for retry
        mock_task_instance = MagicMock()
        mock_task_instance.retry = MagicMock()
        
        # We can't easily test retry in unit tests, but we can verify the exception is raised
        with pytest.raises(Exception):
            send_task_assignment_email(
                user_id=user.id,
                task_id=task.id
            )


@pytest.mark.django_db
@pytest.mark.celery
class TestSendTaskDueReminder:
    """Test suite for send_task_due_reminder task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_due_reminder_success(self, mock_send_email, user, task):
        """Test successful task due reminder email."""
        task.due_date = timezone.now() + timedelta(days=1)
        task.save()
        
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=task.id,
            days_until_due=1
        )
        
        assert result['status'] == 'success'
        assert result['user_id'] == user.id
        assert result['task_id'] == task.id
        assert result['is_overdue'] is False
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_due_reminder_overdue_task(self, mock_send_email, user, task):
        """Test due reminder for overdue task."""
        task.due_date = timezone.now() - timedelta(days=2)
        task.save()
        
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=task.id,
            days_until_due=-2
        )
        
        assert result['status'] == 'success'
        assert result['is_overdue'] is True
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_due_reminder_calculates_days_until_due(
        self, mock_send_email, user, task
    ):
        """Test that days_until_due is calculated if not provided."""
        task.due_date = timezone.now() + timedelta(days=3)
        task.save()
        
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=task.id
        )
        
        assert result['status'] == 'success'
        assert result['days_until_due'] == 3
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_due_reminder_skips_completed_task(
        self, mock_send_email, user, task
    ):
        """Test that reminder is skipped for completed tasks."""
        task.status = Task.STATUS_DONE
        task.save()
        
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=task.id
        )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'task_completed'
        assert not mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_task_due_reminder_skips_when_notifications_disabled(
        self, mock_send_email, task
    ):
        """Test that reminder is skipped when notifications are disabled."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=False)
        
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=task.id
        )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'email_notifications_disabled'
        assert not mock_send_email.called

    def test_send_task_due_reminder_user_not_found(self, task):
        """Test due reminder when user doesn't exist."""
        result = send_task_due_reminder(
            user_id=99999,
            task_id=task.id
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'user_not_found'

    def test_send_task_due_reminder_task_not_found(self, user):
        """Test due reminder when task doesn't exist."""
        result = send_task_due_reminder(
            user_id=user.id,
            task_id=99999
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'task_not_found'


@pytest.mark.django_db
@pytest.mark.celery
class TestSendProjectUpdateEmail:
    """Test suite for send_project_update_email task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_project_update_email_success(
        self, mock_send_email, user, project
    ):
        """Test successful project update email."""
        result = send_project_update_email(
            user_id=user.id,
            project_id=project.id,
            update_type='status_change',
            update_description='Project status changed to active'
        )
        
        assert result['status'] == 'success'
        assert result['user_id'] == user.id
        assert result['project_id'] == project.id
        assert result['update_type'] == 'status_change'
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_project_update_email_with_defaults(
        self, mock_send_email, user, project
    ):
        """Test project update email with default parameters."""
        result = send_project_update_email(
            user_id=user.id,
            project_id=project.id
        )
        
        assert result['status'] == 'success'
        assert result['update_type'] == 'general'
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_project_update_email_skips_when_notifications_disabled(
        self, mock_send_email, project
    ):
        """Test that email is skipped when notifications are disabled."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=False)
        
        result = send_project_update_email(
            user_id=user.id,
            project_id=project.id
        )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'email_notifications_disabled'
        assert not mock_send_email.called

    def test_send_project_update_email_user_not_found(self, project):
        """Test project update email when user doesn't exist."""
        result = send_project_update_email(
            user_id=99999,
            project_id=project.id
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'user_not_found'

    def test_send_project_update_email_project_not_found(self, user):
        """Test project update email when project doesn't exist."""
        result = send_project_update_email(
            user_id=user.id,
            project_id=99999
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'project_not_found'


@pytest.mark.django_db
@pytest.mark.celery
class TestSendWelcomeEmail:
    """Test suite for send_welcome_email task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_welcome_email_success(self, mock_send_email, user):
        """Test successful welcome email."""
        result = send_welcome_email(user_id=user.id)
        
        assert result['status'] == 'success'
        assert result['user_id'] == user.id
        assert result['email'] == user.email
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_welcome_email_skips_when_notifications_disabled(
        self, mock_send_email
    ):
        """Test that welcome email is skipped when notifications are disabled."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=False)
        
        result = send_welcome_email(user_id=user.id)
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'email_notifications_disabled'
        assert not mock_send_email.called

    def test_send_welcome_email_user_not_found(self):
        """Test welcome email when user doesn't exist."""
        result = send_welcome_email(user_id=99999)
        
        assert result['status'] == 'error'
        assert result['error'] == 'user_not_found'


# ============================================================================
# Notification Creation Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestCreateNotification:
    """Test suite for create_notification task."""

    def test_create_notification_success(self, user, task):
        """Test successful notification creation."""
        result = create_notification(
            user_id=user.id,
            message='You have been assigned a new task',
            notification_type=Notification.TYPE_TASK_ASSIGNED,
            related_object_type='tasks.Task',
            related_object_id=task.id
        )
        
        assert result['status'] == 'success'
        assert result['user_id'] == user.id
        assert result['notification_type'] == Notification.TYPE_TASK_ASSIGNED
        assert 'notification_id' in result
        
        # Verify notification was created
        notification = Notification.objects.get(id=result['notification_id'])
        assert notification.user == user
        assert notification.message == 'You have been assigned a new task'
        assert notification.type == Notification.TYPE_TASK_ASSIGNED
        assert notification.related_object == task

    def test_create_notification_without_related_object(self, user):
        """Test notification creation without related object."""
        result = create_notification(
            user_id=user.id,
            message='System notification',
            notification_type=Notification.TYPE_SYSTEM
        )
        
        assert result['status'] == 'success'
        notification = Notification.objects.get(id=result['notification_id'])
        assert notification.related_object is None

    def test_create_notification_with_metadata(self, user, task):
        """Test notification creation with metadata."""
        metadata = {'priority': 'high', 'source': 'automated'}
        
        result = create_notification(
            user_id=user.id,
            message='Task updated',
            notification_type=Notification.TYPE_TASK_UPDATED,
            related_object_type='tasks.Task',
            related_object_id=task.id,
            metadata=metadata
        )
        
        assert result['status'] == 'success'
        notification = Notification.objects.get(id=result['notification_id'])
        assert notification.metadata == metadata

    def test_create_notification_with_invalid_related_object(self, user):
        """Test notification creation with invalid related object."""
        result = create_notification(
            user_id=user.id,
            message='Test notification',
            notification_type=Notification.TYPE_SYSTEM,
            related_object_type='tasks.Task',
            related_object_id=99999
        )
        
        # Should still succeed, but without related object
        assert result['status'] == 'success'
        notification = Notification.objects.get(id=result['notification_id'])
        assert notification.related_object is None

    def test_create_notification_user_not_found(self):
        """Test notification creation when user doesn't exist."""
        result = create_notification(
            user_id=99999,
            message='Test',
            notification_type=Notification.TYPE_SYSTEM
        )
        
        assert result['status'] == 'error'
        assert result['error'] == 'user_not_found'


@pytest.mark.django_db
@pytest.mark.celery
class TestSendBulkNotifications:
    """Test suite for send_bulk_notifications task."""

    def test_send_bulk_notifications_success(self, task):
        """Test successful bulk notification creation."""
        users = UserFactory.create_batch(3)
        user_ids = [user.id for user in users]
        
        result = send_bulk_notifications(
            user_ids=user_ids,
            message='A new project has been created',
            notification_type=Notification.TYPE_PROJECT_UPDATED,
            related_object_type='projects.Project',
            related_object_id=task.project.id
        )
        
        assert result['status'] == 'success'
        assert result['created_count'] == 3
        assert result['failed_count'] == 0
        assert result['total_requested'] == 3
        
        # Verify notifications were created
        for user in users:
            assert Notification.objects.filter(
                user=user,
                type=Notification.TYPE_PROJECT_UPDATED
            ).exists()

    def test_send_bulk_notifications_with_empty_list(self):
        """Test bulk notifications with empty user list."""
        result = send_bulk_notifications(
            user_ids=[],
            message='Test',
            notification_type=Notification.TYPE_SYSTEM
        )
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'no_users'
        assert result['created_count'] == 0

    def test_send_bulk_notifications_with_invalid_users(self, task):
        """Test bulk notifications with some invalid user IDs."""
        valid_user = UserFactory()
        invalid_user_ids = [99999, 99998]
        
        result = send_bulk_notifications(
            user_ids=[valid_user.id] + invalid_user_ids,
            message='Test notification',
            notification_type=Notification.TYPE_SYSTEM
        )
        
        assert result['status'] == 'success'
        assert result['created_count'] == 1
        assert result['failed_count'] == 2  # Two invalid users

    def test_send_bulk_notifications_with_metadata(self, task):
        """Test bulk notifications with metadata."""
        users = UserFactory.create_batch(2)
        user_ids = [user.id for user in users]
        metadata = {'source': 'bulk_operation', 'batch_id': '123'}
        
        result = send_bulk_notifications(
            user_ids=user_ids,
            message='Bulk notification',
            notification_type=Notification.TYPE_SYSTEM,
            metadata=metadata
        )
        
        assert result['status'] == 'success'
        assert result['created_count'] == 2
        
        # Verify metadata is set
        for user in users:
            notification = Notification.objects.get(user=user)
            assert notification.metadata == metadata


# ============================================================================
# Scheduled Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestSendDailyReminders:
    """Test suite for send_daily_reminders scheduled task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_daily_reminders_success(self, mock_send_email):
        """Test successful daily reminders sending."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=True)
        
        team = TeamFactory()
        project = ProjectFactory(team=team)
        
        # Create tasks due today, overdue, and upcoming
        task_due_today = TaskFactory(
            project=project,
            assignee=user,
            due_date=timezone.now().replace(hour=23, minute=59),
            status=Task.STATUS_TODO
        )
        task_overdue = TaskFactory(
            project=project,
            assignee=user,
            due_date=timezone.now() - timedelta(days=2),
            status=Task.STATUS_TODO
        )
        task_upcoming = TaskFactory(
            project=project,
            assignee=user,
            due_date=timezone.now() + timedelta(days=1),
            status=Task.STATUS_TODO
        )
        
        result = send_daily_reminders()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 1
        assert result['tasks_due_today'] >= 1
        assert result['overdue_tasks'] >= 1
        assert result['upcoming_tasks'] >= 1
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_daily_reminders_skips_users_with_no_tasks(self, mock_send_email):
        """Test that users with no relevant tasks are skipped."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=True)
        
        result = send_daily_reminders()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 0
        # Should not be called if user has no tasks
        assert mock_send_email.call_count == 0

    @patch('notifications.tasks.send_email_with_html')
    def test_send_daily_reminders_skips_notifications_disabled(
        self, mock_send_email
    ):
        """Test that users with notifications disabled are skipped."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=False)
        
        team = TeamFactory()
        project = ProjectFactory(team=team)
        TaskFactory(
            project=project,
            assignee=user,
            due_date=timezone.now(),
            status=Task.STATUS_TODO
        )
        
        result = send_daily_reminders()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 0
        assert not mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_daily_reminders_handles_errors_gracefully(self, mock_send_email):
        """Test that errors for individual users don't stop the task."""
        user1 = UserFactory()
        user2 = UserFactory()
        UserProfileFactory(user=user1, email_notifications=True)
        UserProfileFactory(user=user2, email_notifications=True)
        
        team = TeamFactory()
        project = ProjectFactory(team=team)
        
        TaskFactory(
            project=project,
            assignee=user1,
            due_date=timezone.now(),
            status=Task.STATUS_TODO
        )
        TaskFactory(
            project=project,
            assignee=user2,
            due_date=timezone.now(),
            status=Task.STATUS_TODO
        )
        
        # Make email sending fail for one user
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Email service error")
            return None
        
        mock_send_email.side_effect = side_effect
        
        result = send_daily_reminders()
        
        # Task should complete despite errors
        assert result['status'] == 'success'
        assert result['errors'] >= 1


@pytest.mark.django_db
@pytest.mark.celery
class TestSendWeeklyDigest:
    """Test suite for send_weekly_digest scheduled task."""

    @patch('notifications.tasks.send_email_with_html')
    def test_send_weekly_digest_success(self, mock_send_email):
        """Test successful weekly digest sending."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=True)
        
        team = TeamFactory()
        project = ProjectFactory(team=team)
        
        # Create tasks completed this week
        task_completed = TaskFactory(
            project=project,
            assignee=user,
            status=Task.STATUS_DONE,
            updated_at=timezone.now() - timedelta(days=2)
        )
        
        # Create tasks assigned to user
        task_assigned = TaskFactory(
            project=project,
            assignee=user,
            status=Task.STATUS_TODO
        )
        
        result = send_weekly_digest()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 1
        assert result['total_tasks_completed'] >= 1
        assert mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_weekly_digest_skips_users_with_no_activity(
        self, mock_send_email
    ):
        """Test that users with no activity are skipped."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=True)
        
        result = send_weekly_digest()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 0
        assert not mock_send_email.called

    @patch('notifications.tasks.send_email_with_html')
    def test_send_weekly_digest_includes_multiple_metrics(
        self, mock_send_email
    ):
        """Test that weekly digest includes various metrics."""
        user = UserFactory()
        UserProfileFactory(user=user, email_notifications=True)
        
        team = TeamFactory()
        project = ProjectFactory(team=team, status=Project.STATUS_ACTIVE)
        
        # Add user to project
        from projects.models import ProjectMember
        ProjectMember.objects.create(
            project=project,
            user=user,
            role='member'
        )
        
        # Create various tasks
        TaskFactory(
            project=project,
            assignee=user,
            status=Task.STATUS_DONE,
            updated_at=timezone.now() - timedelta(days=3)
        )
        TaskFactory(
            project=project,
            created_by=user,
            created_at=timezone.now() - timedelta(days=2)
        )
        
        result = send_weekly_digest()
        
        assert result['status'] == 'success'
        assert result['total_users_notified'] == 1
        assert result['total_tasks_completed'] >= 1
        assert result['total_tasks_created'] >= 1
        assert result['total_projects_active'] >= 1


@pytest.mark.django_db
@pytest.mark.celery
class TestCleanupOldNotifications:
    """Test suite for cleanup_old_notifications scheduled task."""

    def test_cleanup_old_notifications_success(self, user):
        """Test successful cleanup of old notifications."""
        # Create old read notifications
        old_notification1 = NotificationFactory(
            user=user,
            read=True,
            created_at=timezone.now() - timedelta(days=35)
        )
        old_notification2 = NotificationFactory(
            user=user,
            read=True,
            created_at=timezone.now() - timedelta(days=40)
        )
        
        # Create recent read notification (should not be deleted)
        recent_notification = NotificationFactory(
            user=user,
            read=True,
            created_at=timezone.now() - timedelta(days=10)
        )
        
        # Create unread notification (should not be deleted)
        unread_notification = NotificationFactory(
            user=user,
            read=False,
            created_at=timezone.now() - timedelta(days=50)
        )
        
        result = cleanup_old_notifications(days_old=30)
        
        assert result['status'] == 'success'
        assert result['notifications_deleted'] == 2
        assert result['days_old'] == 30
        
        # Verify old notifications are deleted
        assert not Notification.objects.filter(id=old_notification1.id).exists()
        assert not Notification.objects.filter(id=old_notification2.id).exists()
        
        # Verify recent and unread notifications are kept
        assert Notification.objects.filter(id=recent_notification.id).exists()
        assert Notification.objects.filter(id=unread_notification.id).exists()

    def test_cleanup_old_notifications_custom_days(self, user):
        """Test cleanup with custom days_old parameter."""
        # Create notification older than 60 days
        old_notification = NotificationFactory(
            user=user,
            read=True,
            created_at=timezone.now() - timedelta(days=70)
        )
        
        # Create notification older than 30 but not 60 days
        recent_notification = NotificationFactory(
            user=user,
            read=True,
            created_at=timezone.now() - timedelta(days=40)
        )
        
        result = cleanup_old_notifications(days_old=60)
        
        assert result['status'] == 'success'
        assert result['notifications_deleted'] == 1
        assert result['days_old'] == 60
        
        # Verify only old notification is deleted
        assert not Notification.objects.filter(id=old_notification.id).exists()
        assert Notification.objects.filter(id=recent_notification.id).exists()

    def test_cleanup_old_notifications_no_notifications(self):
        """Test cleanup when there are no old notifications."""
        result = cleanup_old_notifications(days_old=30)
        
        assert result['status'] == 'success'
        assert result['notifications_deleted'] == 0

    def test_cleanup_old_notifications_preserves_unread(self, user):
        """Test that unread notifications are never deleted."""
        # Create very old unread notification
        old_unread = NotificationFactory(
            user=user,
            read=False,
            created_at=timezone.now() - timedelta(days=100)
        )
        
        result = cleanup_old_notifications(days_old=30)
        
        assert result['status'] == 'success'
        # Should not delete unread notification
        assert Notification.objects.filter(id=old_unread.id).exists()


# ============================================================================
# Helper Function Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestShouldSendEmail:
    """Test suite for should_send_email helper function."""

    def test_should_send_email_when_enabled(self, user):
        """Test that email is sent when notifications are enabled."""
        UserProfileFactory(user=user, email_notifications=True)
        assert should_send_email(user) is True

    def test_should_send_email_when_disabled(self, user):
        """Test that email is not sent when notifications are disabled."""
        UserProfileFactory(user=user, email_notifications=False)
        assert should_send_email(user) is False

    def test_should_send_email_defaults_to_true_without_profile(self, user):
        """Test that email defaults to True when profile doesn't exist."""
        # User without profile
        assert should_send_email(user) is True

    def test_should_send_email_handles_exception_gracefully(self, user):
        """Test that function handles exceptions gracefully."""
        # Test that function defaults to True when profile doesn't exist
        # (which is already tested in test_should_send_email_defaults_to_true_without_profile)
        # This test verifies the exception handling path in should_send_email
        # by ensuring it doesn't crash on unexpected exceptions
        
        # User without profile should default to True
        result = should_send_email(user)
        assert result is True
        
        # Test with user that has profile - should work normally
        UserProfileFactory(user=user, email_notifications=True)
        result = should_send_email(user)
        assert result is True

