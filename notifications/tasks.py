"""
Celery tasks for notifications in Task Management System.

This module contains all Celery tasks for:
- Sending email notifications to users for various events
- Creating in-app notifications (database records)
- Bulk notification operations

All tasks are designed to be:
- Async and non-blocking
- Retryable on failure
- Respectful of user preferences
- Well-logged for debugging
- Production-ready with proper error handling

Email notification tasks:
- send_task_assignment_email
- send_task_due_reminder
- send_project_update_email
- send_welcome_email

Notification creation tasks:
- create_notification
- send_bulk_notifications
"""

import logging
from typing import Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from celery import shared_task

from users.models import User, UserProfile
from tasks.models import Task
from projects.models import Project

logger = logging.getLogger(__name__)


def should_send_email(user: User) -> bool:
    """
    Check if email should be sent to user based on their preferences.
    
    Args:
        user: User instance to check
        
    Returns:
        bool: True if email should be sent, False otherwise
    """
    try:
        # Check if user has email notifications enabled in their profile
        profile = user.profile
        return profile.email_notifications if profile else True
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, default to sending emails
        return True
    except Exception as e:
        logger.warning(f"Error checking email preferences for user {user.id}: {e}")
        # On error, default to sending emails to avoid missing important notifications
        return True


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,  # Add randomness to retry timing
    ignore_result=False,
)
def send_task_assignment_email(
    self,
    user_id: int,
    task_id: int,
    assigner_id: Optional[int] = None
) -> dict:
    """
    Send email notification when a task is assigned to a user.
    
    This task sends a professional email notification to the user
    when they are assigned a new task, including task details,
    project information, and due date if available.
    
    Args:
        self: Celery task instance (for retries)
        user_id: ID of the user who is assigned the task
        task_id: ID of the task being assigned
        assigner_id: Optional ID of the user who assigned the task
        
    Returns:
        dict: Result dictionary with status and details
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
    """
    try:
        # Get user and task from database
        user = User.objects.get(pk=user_id)
        task = Task.objects.select_related('project', 'assignee', 'created_by').get(pk=task_id)
        
        # Check if email should be sent
        if not should_send_email(user):
            logger.info(f"Email notifications disabled for user {user.username}, skipping task assignment email")
            return {
                'status': 'skipped',
                'reason': 'email_notifications_disabled',
                'user_id': user_id,
                'task_id': task_id
            }
        
        # Get assigner information if provided
        assigner = None
        if assigner_id:
            try:
                assigner = User.objects.get(pk=assigner_id)
            except User.DoesNotExist:
                logger.warning(f"Assigner with ID {assigner_id} not found")
                assigner = task.created_by
        
        # Prepare email context
        context = {
            'user': user,
            'task': task,
            'project': task.project,
            'assigner': assigner or task.created_by,
            'due_date': task.due_date,
            'task_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/tasks/{task.id}",
            'project_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/projects/{task.project.id}",
            'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
        }
        
        # Render email templates
        subject = f"New Task Assigned: {task.title}"
        text_message = render_to_string('notifications/emails/task_assignment.txt', context)
        html_message = render_to_string('notifications/emails/task_assignment.html', context)
        
        # Send email
        from_email = settings.DEFAULT_FROM_EMAIL
        send_email_with_html(user.email, subject, text_message, html_message, from_email)
        
        logger.info(f"Task assignment email sent successfully to {user.email} for task {task.id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'task_id': task_id,
            'email': user.email
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'status': 'error',
            'error': 'user_not_found',
            'user_id': user_id
        }
    except Task.DoesNotExist:
        logger.error(f"Task with ID {task_id} not found")
        return {
            'status': 'error',
            'error': 'task_not_found',
            'task_id': task_id
        }
    except Exception as exc:
        logger.error(f"Error sending task assignment email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_task_due_reminder(
    self,
    user_id: int,
    task_id: int,
    days_until_due: Optional[int] = None
) -> dict:
    """
    Send email reminder when a task is due soon or overdue.
    
    This task sends a reminder email to the user about upcoming
    or overdue tasks, helping them stay on top of their deadlines.
    
    Args:
        self: Celery task instance (for retries)
        user_id: ID of the user who is assigned the task
        task_id: ID of the task that is due
        days_until_due: Optional number of days until due (negative if overdue)
        
    Returns:
        dict: Result dictionary with status and details
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
    """
    try:
        # Get user and task from database
        user = User.objects.get(pk=user_id)
        task = Task.objects.select_related('project', 'assignee').get(pk=task_id)
        
        # Skip if task is already completed
        if task.status == Task.STATUS_DONE:
            logger.info(f"Task {task.id} is already completed, skipping due reminder email")
            return {
                'status': 'skipped',
                'reason': 'task_completed',
                'task_id': task_id
            }
        
        # Check if email should be sent
        if not should_send_email(user):
            logger.info(f"Email notifications disabled for user {user.username}, skipping due reminder email")
            return {
                'status': 'skipped',
                'reason': 'email_notifications_disabled',
                'user_id': user_id,
                'task_id': task_id
            }
        
        # Calculate days until due if not provided
        if days_until_due is None and task.due_date:
            time_diff = task.due_date - timezone.now()
            days_until_due = time_diff.days
        
        # Determine if task is overdue
        is_overdue = days_until_due is not None and days_until_due < 0
        
        # Calculate absolute days for display (overdue tasks show positive days overdue)
        days_display = abs(days_until_due) if days_until_due is not None else None
        
        # Prepare email context
        context = {
            'user': user,
            'task': task,
            'project': task.project,
            'due_date': task.due_date,
            'days_until_due': days_until_due,
            'days_display': days_display,
            'is_overdue': is_overdue,
            'task_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/tasks/{task.id}",
            'project_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/projects/{task.project.id}",
            'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
        }
        
        # Render email templates
        if is_overdue:
            subject = f"⚠️ Overdue Task: {task.title}"
        else:
            subject = f"Reminder: Task Due Soon - {task.title}"
        
        text_message = render_to_string('notifications/emails/task_due_reminder.txt', context)
        html_message = render_to_string('notifications/emails/task_due_reminder.html', context)
        
        # Send email
        from_email = settings.DEFAULT_FROM_EMAIL
        send_email_with_html(user.email, subject, text_message, html_message, from_email)
        
        logger.info(f"Task due reminder email sent successfully to {user.email} for task {task.id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'task_id': task_id,
            'email': user.email,
            'is_overdue': is_overdue,
            'days_until_due': days_until_due
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'status': 'error',
            'error': 'user_not_found',
            'user_id': user_id
        }
    except Task.DoesNotExist:
        logger.error(f"Task with ID {task_id} not found")
        return {
            'status': 'error',
            'error': 'task_not_found',
            'task_id': task_id
        }
    except Exception as exc:
        logger.error(f"Error sending task due reminder email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_project_update_email(
    self,
    user_id: int,
    project_id: int,
    update_type: str = 'general',
    update_description: Optional[str] = None
) -> dict:
    """
    Send email notification when a project is updated.
    
    This task sends an email to all project members (or specific user)
    when important project updates occur, such as status changes,
    new members, or other significant changes.
    
    Args:
        self: Celery task instance (for retries)
        user_id: ID of the user to notify
        project_id: ID of the project that was updated
        update_type: Type of update (status_change, member_added, general, etc.)
        update_description: Optional description of the update
        
    Returns:
        dict: Result dictionary with status and details
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
    """
    try:
        # Get user and project from database
        user = User.objects.get(pk=user_id)
        project = Project.objects.select_related('team').get(pk=project_id)
        
        # Check if email should be sent
        if not should_send_email(user):
            logger.info(f"Email notifications disabled for user {user.username}, skipping project update email")
            return {
                'status': 'skipped',
                'reason': 'email_notifications_disabled',
                'user_id': user_id,
                'project_id': project_id
            }
        
        # Prepare email context
        context = {
            'user': user,
            'project': project,
            'team': project.team,
            'update_type': update_type,
            'update_description': update_description or 'Project has been updated',
            'project_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/projects/{project.id}",
            'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
        }
        
        # Render email templates
        subject = f"Project Update: {project.name}"
        text_message = render_to_string('notifications/emails/project_update.txt', context)
        html_message = render_to_string('notifications/emails/project_update.html', context)
        
        # Send email
        from_email = settings.DEFAULT_FROM_EMAIL
        send_email_with_html(user.email, subject, text_message, html_message, from_email)
        
        logger.info(f"Project update email sent successfully to {user.email} for project {project.id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'project_id': project_id,
            'email': user.email,
            'update_type': update_type
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'status': 'error',
            'error': 'user_not_found',
            'user_id': user_id
        }
    except Project.DoesNotExist:
        logger.error(f"Project with ID {project_id} not found")
        return {
            'status': 'error',
            'error': 'project_not_found',
            'project_id': project_id
        }
    except Exception as exc:
        logger.error(f"Error sending project update email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_welcome_email(self, user_id: int) -> dict:
    """
    Send welcome email to a new user.
    
    This task sends a welcome email to newly registered users,
    introducing them to the Task Management System and providing
    helpful information to get started.
    
    Args:
        self: Celery task instance (for retries)
        user_id: ID of the newly registered user
        
    Returns:
        dict: Result dictionary with status and details
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
    """
    try:
        # Get user from database
        user = User.objects.get(pk=user_id)
        
        # Check if email should be sent
        # Note: Welcome emails are typically sent regardless of preferences,
        # but we'll check anyway for consistency
        if not should_send_email(user):
            logger.info(f"Email notifications disabled for user {user.username}, skipping welcome email")
            return {
                'status': 'skipped',
                'reason': 'email_notifications_disabled',
                'user_id': user_id
            }
        
        # Prepare email context
        context = {
            'user': user,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'login_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login",
            'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
            'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
        }
        
        # Render email templates
        subject = f"Welcome to {context['site_name']}!"
        text_message = render_to_string('notifications/emails/welcome.txt', context)
        html_message = render_to_string('notifications/emails/welcome.html', context)
        
        # Send email
        from_email = settings.DEFAULT_FROM_EMAIL
        send_email_with_html(user.email, subject, text_message, html_message, from_email)
        
        logger.info(f"Welcome email sent successfully to {user.email} for user {user.id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'email': user.email
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'status': 'error',
            'error': 'user_not_found',
            'user_id': user_id
        }
    except Exception as exc:
        logger.error(f"Error sending welcome email: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


def send_email_with_html(
    to_email: str,
    subject: str,
    text_message: str,
    html_message: str,
    from_email: Optional[str] = None
) -> None:
    """
    Helper function to send email with both text and HTML versions.
    
    This function creates an EmailMultiAlternatives email message
    with both plain text and HTML versions for better email client compatibility.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        text_message: Plain text email content
        html_message: HTML email content
        from_email: Sender email address (defaults to DEFAULT_FROM_EMAIL)
        
    Raises:
        Exception: If email sending fails
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # Create email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=from_email,
        to=[to_email]
    )
    
    # Attach HTML version
    email.attach_alternative(html_message, "text/html")
    
    # Send email
    email.send(fail_silently=False)
    
    logger.debug(f"Email sent successfully to {to_email} with subject: {subject}")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def create_notification(
    self,
    user_id: int,
    message: str,
    notification_type: str,
    related_object_type: Optional[str] = None,
    related_object_id: Optional[int] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Create a notification for a user.
    
    This task creates an in-app notification (database record) for a user.
    Notifications are displayed in the user's notification center and can
    be used to track various events like task assignments, project updates, etc.
    
    Args:
        self: Celery task instance (for retries)
        user_id: ID of the user who will receive the notification
        message: Notification message text
        notification_type: Type of notification (use Notification.TYPE_* constants)
        related_object_type: Optional app_label.ModelName of related object (e.g., 'tasks.Task')
        related_object_id: Optional ID of related object
        metadata: Optional dictionary with additional metadata
        
    Returns:
        dict: Result dictionary with status and notification details
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        from notifications.tasks import create_notification
        from notifications.models import Notification
        
        # Queue notification task
        result = create_notification.delay(
            user_id=1,
            message="You have been assigned a new task",
            notification_type=Notification.TYPE_TASK_ASSIGNED,
            related_object_type='tasks.Task',
            related_object_id=5
        )
    """
    try:
        from notifications.models import Notification
        from users.models import User
        from django.contrib.contenttypes.models import ContentType
        
        # Get user from database
        user = User.objects.get(pk=user_id)
        
        # Get related object if provided
        related_object = None
        if related_object_type and related_object_id:
            try:
                app_label, model_name = related_object_type.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
                model_class = content_type.model_class()
                related_object = model_class.objects.get(pk=related_object_id)
            except (ValueError, ContentType.DoesNotExist, Exception) as e:
                logger.warning(f"Could not find related object {related_object_type}#{related_object_id}: {e}")
                # Continue without related object - notification can still be created
        
        # Create notification using the model's class method
        notification = Notification.create_notification(
            user=user,
            message=message,
            notification_type=notification_type,
            related_object=related_object,
            metadata=metadata
        )
        
        logger.info(f"Notification created successfully for user {user.username} (ID: {user_id}): {notification_type}")
        
        return {
            'status': 'success',
            'notification_id': notification.id,
            'user_id': user_id,
            'notification_type': notification_type,
            'message': message
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {
            'status': 'error',
            'error': 'user_not_found',
            'user_id': user_id
        }
    except Exception as exc:
        logger.error(f"Error creating notification: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_bulk_notifications(
    self,
    user_ids: list,
    message: str,
    notification_type: str,
    related_object_type: Optional[str] = None,
    related_object_id: Optional[int] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Create notifications for multiple users (bulk operation).
    
    This task creates notifications for multiple users at once, which is
    useful when notifying all project members or team members about
    an event. Each user receives their own notification instance.
    
    Args:
        self: Celery task instance (for retries)
        user_ids: List of user IDs who will receive notifications
        message: Notification message text (same for all users)
        notification_type: Type of notification (use Notification.TYPE_* constants)
        related_object_type: Optional app_label.ModelName of related object
        related_object_id: Optional ID of related object
        metadata: Optional dictionary with additional metadata
        
    Returns:
        dict: Result dictionary with status and summary statistics
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        from notifications.tasks import send_bulk_notifications
        from notifications.models import Notification
        
        # Queue bulk notification task
        result = send_bulk_notifications.delay(
            user_ids=[1, 2, 3, 4],
            message="A new project has been created",
            notification_type=Notification.TYPE_PROJECT_UPDATED,
            related_object_type='projects.Project',
            related_object_id=10
        )
    """
    try:
        from notifications.models import Notification
        from users.models import User
        from django.contrib.contenttypes.models import ContentType
        
        if not user_ids:
            logger.warning("No user IDs provided for bulk notifications")
            return {
                'status': 'skipped',
                'reason': 'no_users',
                'created_count': 0,
                'failed_count': 0
            }
        
        # Get related object if provided (only once for efficiency)
        related_object = None
        if related_object_type and related_object_id:
            try:
                app_label, model_name = related_object_type.split('.')
                content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
                model_class = content_type.model_class()
                related_object = model_class.objects.get(pk=related_object_id)
            except (ValueError, ContentType.DoesNotExist, Exception) as e:
                logger.warning(f"Could not find related object {related_object_type}#{related_object_id}: {e}")
                # Continue without related object
        
        # Get all users at once for efficiency
        users = User.objects.filter(id__in=user_ids)
        existing_user_ids = set(users.values_list('id', flat=True))
        missing_user_ids = set(user_ids) - existing_user_ids
        
        if missing_user_ids:
            logger.warning(f"Some user IDs not found: {missing_user_ids}")
        
        created_count = 0
        failed_count = 0
        
        # Create notifications for each user
        for user in users:
            try:
                notification = Notification.create_notification(
                    user=user,
                    message=message,
                    notification_type=notification_type,
                    related_object=related_object,
                    metadata=metadata
                )
                created_count += 1
                logger.debug(f"Notification created for user {user.username} (ID: {user.id})")
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to create notification for user {user.id}: {e}", exc_info=True)
                # Continue with other users even if one fails
        
        # Count missing users as failed
        failed_count += len(missing_user_ids)
        
        logger.info(
            f"Bulk notifications completed: {created_count} created, "
            f"{failed_count} failed for notification type: {notification_type}"
        )
        
        return {
            'status': 'success',
            'created_count': created_count,
            'failed_count': failed_count,
            'total_requested': len(user_ids),
            'notification_type': notification_type
        }
        
    except Exception as exc:
        logger.error(f"Error in bulk notification creation: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_daily_reminders(self) -> dict:
    """
    Send daily task reminders to users for tasks due today or overdue.
    
    This scheduled task runs daily (typically in the morning) and sends
    email reminders to users about:
    - Tasks due today
    - Overdue tasks
    - Tasks due in the next 1-2 days (upcoming deadlines)
    
    The task respects user email preferences and only sends to users
    who have email notifications enabled.
    
    Returns:
        dict: Result dictionary with summary statistics:
            {
                'status': 'success',
                'total_users_notified': int,
                'tasks_due_today': int,
                'overdue_tasks': int,
                'upcoming_tasks': int,
                'errors': int
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        This task is typically scheduled via Celery Beat to run daily:
        - Schedule: Daily at 9:00 AM
        - Task: notifications.tasks.send_daily_reminders
    """
    try:
        from datetime import timedelta
        from django.db.models import Q
        
        logger.info("Starting daily reminders task")
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        tomorrow_end = today_end + timedelta(days=1)
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        total_users_notified = 0
        tasks_due_today = 0
        overdue_tasks = 0
        upcoming_tasks = 0
        errors = 0
        
        for user in users:
            try:
                # Skip if email notifications disabled
                if not should_send_email(user):
                    continue
                
                # Get user's tasks
                user_tasks = Task.objects.filter(
                    assignee=user,
                    status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_BLOCKED]
                ).select_related('project')
                
                # Tasks due today
                tasks_today = user_tasks.filter(
                    due_date__gte=today_start,
                    due_date__lt=today_end
                )
                
                # Overdue tasks
                overdue = user_tasks.filter(
                    due_date__lt=today_start
                )
                
                # Upcoming tasks (due tomorrow or day after)
                upcoming = user_tasks.filter(
                    due_date__gte=today_end,
                    due_date__lt=tomorrow_end
                )
                
                # Only send email if user has relevant tasks
                if not (tasks_today.exists() or overdue.exists() or upcoming.exists()):
                    continue
                
                # Prepare email context
                context = {
                    'user': user,
                    'tasks_due_today': list(tasks_today),
                    'overdue_tasks': list(overdue),
                    'upcoming_tasks': list(upcoming),
                    'total_tasks_due_today': tasks_today.count(),
                    'total_overdue': overdue.count(),
                    'total_upcoming': upcoming.count(),
                    'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
                    'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
                }
                
                # Render email templates (we'll create these)
                subject = f"Daily Task Reminder - {context['total_tasks_due_today'] + context['total_overdue']} tasks need attention"
                text_message = render_to_string('notifications/emails/daily_reminder.txt', context)
                html_message = render_to_string('notifications/emails/daily_reminder.html', context)
                
                # Send email
                from_email = settings.DEFAULT_FROM_EMAIL
                send_email_with_html(user.email, subject, text_message, html_message, from_email)
                
                total_users_notified += 1
                tasks_due_today += tasks_today.count()
                overdue_tasks += overdue.count()
                upcoming_tasks += upcoming.count()
                
                logger.debug(f"Daily reminder sent to {user.email}: {tasks_today.count()} due today, {overdue.count()} overdue")
                
            except Exception as e:
                errors += 1
                logger.error(f"Error sending daily reminder to user {user.id}: {e}", exc_info=True)
                # Continue with other users even if one fails
                continue
        
        result = {
            'status': 'success',
            'total_users_notified': total_users_notified,
            'tasks_due_today': tasks_due_today,
            'overdue_tasks': overdue_tasks,
            'upcoming_tasks': upcoming_tasks,
            'errors': errors,
            'executed_at': now.isoformat()
        }
        
        logger.info(
            f"Daily reminders task completed: {total_users_notified} users notified, "
            f"{tasks_due_today} tasks due today, {overdue_tasks} overdue tasks"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in daily reminders task: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def send_weekly_digest(self) -> dict:
    """
    Send weekly digest email to users with summary of their activity.
    
    This scheduled task runs weekly (typically on Monday morning) and sends
    a comprehensive weekly summary email to users including:
    - Tasks completed this week
    - Tasks created this week
    - Upcoming deadlines
    - Project updates
    - Team activity summary
    
    The task respects user email preferences and only sends to active users
    who have email notifications enabled.
    
    Returns:
        dict: Result dictionary with summary statistics:
            {
                'status': 'success',
                'total_users_notified': int,
                'total_tasks_completed': int,
                'total_tasks_created': int,
                'total_projects_active': int,
                'errors': int
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        This task is typically scheduled via Celery Beat to run weekly:
        - Schedule: Every Monday at 9:00 AM
        - Task: notifications.tasks.send_weekly_digest
    """
    try:
        from datetime import timedelta
        from django.db.models import Count, Q
        
        logger.info("Starting weekly digest task")
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        
        # Get all active users
        users = User.objects.filter(is_active=True)
        total_users_notified = 0
        total_tasks_completed = 0
        total_tasks_created = 0
        total_projects_active = 0
        errors = 0
        
        for user in users:
            try:
                # Skip if email notifications disabled
                if not should_send_email(user):
                    continue
                
                # Get user's tasks
                user_tasks = Task.objects.filter(
                    Q(assignee=user) | Q(created_by=user)
                ).select_related('project', 'assignee', 'created_by')
                
                # Tasks completed this week
                tasks_completed = user_tasks.filter(
                    status=Task.STATUS_DONE,
                    updated_at__gte=week_ago
                )
                
                # Tasks created this week
                tasks_created = user_tasks.filter(
                    created_at__gte=week_ago
                )
                
                # Tasks assigned to user (active)
                tasks_assigned = user_tasks.filter(
                    assignee=user,
                    status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS]
                )
                
                # Upcoming deadlines (next 7 days)
                next_week = now + timedelta(days=7)
                upcoming_deadlines = user_tasks.filter(
                    assignee=user,
                    due_date__gte=now,
                    due_date__lte=next_week,
                    status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS]
                )
                
                # Projects user is involved in
                from projects.models import ProjectMember
                user_projects = Project.objects.filter(
                    members__user=user
                ).distinct()
                
                active_projects = user_projects.filter(
                    status=Project.STATUS_ACTIVE
                )
                
                # Only send email if user has activity
                if not (tasks_completed.exists() or tasks_created.exists() or 
                        tasks_assigned.exists() or active_projects.exists()):
                    continue
                
                # Prepare email context
                context = {
                    'user': user,
                    'week_start': week_ago.date(),
                    'week_end': now.date(),
                    'tasks_completed': list(tasks_completed[:10]),  # Limit to 10 for email
                    'tasks_completed_count': tasks_completed.count(),
                    'tasks_created': list(tasks_created[:10]),
                    'tasks_created_count': tasks_created.count(),
                    'tasks_assigned': list(tasks_assigned[:10]),
                    'tasks_assigned_count': tasks_assigned.count(),
                    'upcoming_deadlines': list(upcoming_deadlines[:10]),
                    'upcoming_deadlines_count': upcoming_deadlines.count(),
                    'active_projects': list(active_projects[:5]),
                    'active_projects_count': active_projects.count(),
                    'site_name': getattr(settings, 'SITE_NAME', 'Task Management System'),
                    'support_email': getattr(settings, 'SUPPORT_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/dashboard",
                }
                
                # Render email templates
                subject = f"Weekly Digest - {context['tasks_completed_count']} tasks completed"
                text_message = render_to_string('notifications/emails/weekly_digest.txt', context)
                html_message = render_to_string('notifications/emails/weekly_digest.html', context)
                
                # Send email
                from_email = settings.DEFAULT_FROM_EMAIL
                send_email_with_html(user.email, subject, text_message, html_message, from_email)
                
                total_users_notified += 1
                total_tasks_completed += tasks_completed.count()
                total_tasks_created += tasks_created.count()
                total_projects_active += active_projects.count()
                
                logger.debug(
                    f"Weekly digest sent to {user.email}: "
                    f"{tasks_completed.count()} completed, {tasks_created.count()} created"
                )
                
            except Exception as e:
                errors += 1
                logger.error(f"Error sending weekly digest to user {user.id}: {e}", exc_info=True)
                # Continue with other users even if one fails
                continue
        
        result = {
            'status': 'success',
            'total_users_notified': total_users_notified,
            'total_tasks_completed': total_tasks_completed,
            'total_tasks_created': total_tasks_created,
            'total_projects_active': total_projects_active,
            'errors': errors,
            'executed_at': now.isoformat()
        }
        
        logger.info(
            f"Weekly digest task completed: {total_users_notified} users notified, "
            f"{total_tasks_completed} tasks completed, {total_tasks_created} tasks created"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in weekly digest task: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    ignore_result=False,
)
def cleanup_old_notifications(self, days_old: int = 30) -> dict:
    """
    Clean up old read notifications from the database.
    
    This scheduled task runs periodically to remove old read notifications,
    helping to keep the database size manageable and improve query performance.
    
    Only deletes notifications that:
    - Have been read (read=True)
    - Are older than the specified number of days (default: 30 days)
    - Are not system-critical notifications (optional filter)
    
    Unread notifications are never deleted to ensure users don't miss important
    information.
    
    Args:
        self: Celery task instance (for retries)
        days_old: Number of days old notifications should be before deletion (default: 30)
        
    Returns:
        dict: Result dictionary with cleanup statistics:
            {
                'status': 'success',
                'notifications_deleted': int,
                'days_old': int,
                'cutoff_date': str (ISO format)
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        This task is typically scheduled via Celery Beat to run weekly:
        - Schedule: Every Sunday at 2:00 AM
        - Task: notifications.tasks.cleanup_old_notifications
        - Arguments: {'days_old': 30}
    """
    try:
        from datetime import timedelta
        from notifications.models import Notification
        
        logger.info(f"Starting cleanup of old notifications (older than {days_old} days)")
        now = timezone.now()
        cutoff_date = now - timedelta(days=days_old)
        
        # Get old read notifications
        old_notifications = Notification.objects.filter(
            read=True,
            created_at__lt=cutoff_date
        )
        
        # Count before deletion for reporting
        count_before = old_notifications.count()
        
        # Delete old notifications
        deleted_count, _ = old_notifications.delete()
        
        result = {
            'status': 'success',
            'notifications_deleted': deleted_count,
            'days_old': days_old,
            'cutoff_date': cutoff_date.isoformat(),
            'executed_at': now.isoformat()
        }
        
        logger.info(
            f"Cleanup completed: {deleted_count} old read notifications deleted "
            f"(older than {days_old} days, cutoff: {cutoff_date.date()})"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in cleanup old notifications task: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)

