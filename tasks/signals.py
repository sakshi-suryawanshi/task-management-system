"""
Signals for Task notifications.

This module contains Django signals for automatically creating notifications
when tasks are created, updated, assigned, or when comments/attachments are added.
Notifications are created asynchronously using Celery tasks.
"""

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification
from notifications.tasks import create_notification, send_bulk_notifications

logger = logging.getLogger(__name__)

# Store original instance before save for detecting changes
_original_instances = {}


def get_user_from_instance(instance):
    """
    Attempt to get the user who performed the action from the instance.
    
    Args:
        instance: Model instance
        
    Returns:
        User instance or None
    """
    user_fields = ['created_by', 'user', 'author', 'uploaded_by', 'assignee']
    
    for field_name in user_fields:
        if hasattr(instance, field_name):
            user = getattr(instance, field_name, None)
            if user:
                return user
    
    return None


def detect_field_changes(old_instance, new_instance):
    """
    Detect which fields changed between old and new instance.
    
    Args:
        old_instance: Instance before save
        new_instance: Instance after save
        
    Returns:
        dict: Dictionary of changed fields with old and new values
    """
    if not old_instance:
        return {}
    
    changes = {}
    fields = [f.name for f in new_instance._meta.get_fields() if hasattr(f, 'attname')]
    
    for field in fields:
        if field in ['updated_at', 'id', 'pk']:
            continue
        
        try:
            old_value = getattr(old_instance, field, None)
            new_value = getattr(new_instance, field, None)
            
            # Handle ForeignKey fields
            if hasattr(new_instance._meta.get_field(field), 'remote_field'):
                old_value = old_value.pk if old_value else None
                new_value = new_value.pk if new_value else None
            
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value) if old_value is not None else None,
                    'new': str(new_value) if new_value is not None else None,
                }
        except (AttributeError, ValueError):
            continue
    
    return changes


# ==================== Task Signals ====================

@receiver(pre_save, sender='tasks.Task')
def task_pre_save(sender, instance, **kwargs):
    """Store original Task instance before save to detect changes."""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            _original_instances[id(instance)] = original
        except sender.DoesNotExist:
            _original_instances[id(instance)] = None
    else:
        _original_instances[id(instance)] = None


@receiver(post_save, sender='tasks.Task')
def create_task_notification(sender, instance, created, **kwargs):
    """
    Create notifications when tasks are created or updated.
    
    Notifications are created for:
    - Task assignment (when assignee is set)
    - Task status changes
    - Task priority changes
    - Task updates (general)
    """
    original_instance = _original_instances.pop(id(instance), None)
    created_by = get_user_from_instance(instance)
    
    if created:
        # Task created - notify assignee if assigned
        if instance.assignee:
            message = f"New task assigned to you: {instance.title}"
            if instance.project:
                message += f" in project {instance.project.name}"
            
            create_notification.delay(
                user_id=instance.assignee.id,
                message=message,
                notification_type=Notification.TYPE_TASK_ASSIGNED,
                related_object_type='tasks.Task',
                related_object_id=instance.id,
                metadata={
                    'task_title': instance.title,
                    'project_id': instance.project_id if instance.project else None,
                    'project_name': str(instance.project) if instance.project else None,
                    'created_by_id': created_by.id if created_by else None,
                }
            )
            logger.info(f"Task assignment notification queued for user {instance.assignee.id}")
    else:
        # Task updated - detect specific changes
        changes = detect_field_changes(original_instance, instance)
        
        # Task assigned
        if 'assignee' in changes and changes['assignee']['new']:
            assignee_id = int(changes['assignee']['new'])
            message = f"Task assigned to you: {instance.title}"
            if instance.project:
                message += f" in project {instance.project.name}"
            
            create_notification.delay(
                user_id=assignee_id,
                message=message,
                notification_type=Notification.TYPE_TASK_ASSIGNED,
                related_object_type='tasks.Task',
                related_object_id=instance.id,
                metadata={
                    'task_title': instance.title,
                    'project_id': instance.project_id if instance.project else None,
                    'project_name': str(instance.project) if instance.project else None,
                    'assigned_by_id': created_by.id if created_by else None,
                }
            )
            logger.info(f"Task assignment notification queued for user {assignee_id}")
        
        # Task status changed
        if 'status' in changes:
            new_status = changes['status']['new']
            old_status = changes['status']['old']
            
            # Notify assignee (if task has assignee)
            if instance.assignee:
                message = f"Task status changed: {instance.title} ({old_status} → {new_status})"
                
                notification_type = Notification.TYPE_TASK_STATUS_CHANGED
                if new_status == 'done':
                    notification_type = Notification.TYPE_TASK_COMPLETED
                
                create_notification.delay(
                    user_id=instance.assignee.id,
                    message=message,
                    notification_type=notification_type,
                    related_object_type='tasks.Task',
                    related_object_id=instance.id,
                    metadata={
                        'task_title': instance.title,
                        'old_status': old_status,
                        'new_status': new_status,
                        'project_id': instance.project_id if instance.project else None,
                    }
                )
                logger.info(f"Task status change notification queued for user {instance.assignee.id}")
            
            # If task is completed, notify project members
            if new_status == 'done' and instance.project:
                project_members = instance.project.members.exclude(user=instance.assignee)
                if project_members.exists():
                    user_ids = list(project_members.values_list('user_id', flat=True))
                    message = f"Task completed: {instance.title} in project {instance.project.name}"
                    
                    send_bulk_notifications.delay(
                        user_ids=user_ids,
                        message=message,
                        notification_type=Notification.TYPE_TASK_COMPLETED,
                        related_object_type='tasks.Task',
                        related_object_id=instance.id,
                        metadata={
                            'task_title': instance.title,
                            'project_id': instance.project_id,
                            'project_name': str(instance.project),
                            'completed_by_id': instance.assignee.id if instance.assignee else None,
                        }
                    )
                    logger.info(f"Task completion bulk notifications queued for {len(user_ids)} project members")
        
        # Task priority changed
        if 'priority' in changes and instance.assignee:
            new_priority = changes['priority']['new']
            old_priority = changes['priority']['old']
            message = f"Task priority changed: {instance.title} ({old_priority} → {new_priority})"
            
            create_notification.delay(
                user_id=instance.assignee.id,
                message=message,
                notification_type=Notification.TYPE_TASK_PRIORITY_CHANGED,
                related_object_type='tasks.Task',
                related_object_id=instance.id,
                metadata={
                    'task_title': instance.title,
                    'old_priority': old_priority,
                    'new_priority': new_priority,
                    'project_id': instance.project_id if instance.project else None,
                }
            )
            logger.info(f"Task priority change notification queued for user {instance.assignee.id}")
        
        # General task update (notify assignee if task is assigned)
        if instance.assignee and not any(key in changes for key in ['assignee', 'status', 'priority']):
            # Only notify if there were meaningful changes
            if changes:
                message = f"Task updated: {instance.title}"
                if instance.project:
                    message += f" in project {instance.project.name}"
                
                create_notification.delay(
                    user_id=instance.assignee.id,
                    message=message,
                    notification_type=Notification.TYPE_TASK_UPDATED,
                    related_object_type='tasks.Task',
                    related_object_id=instance.id,
                    metadata={
                        'task_title': instance.title,
                        'project_id': instance.project_id if instance.project else None,
                        'changes': list(changes.keys()),
                    }
                )
                logger.info(f"Task update notification queued for user {instance.assignee.id}")


# ==================== TaskComment Signals ====================

@receiver(post_save, sender='tasks.TaskComment')
def create_task_comment_notification(sender, instance, created, **kwargs):
    """
    Create notification when a comment is added to a task.
    
    Notifies the task assignee and other project members (excluding the comment author).
    """
    if not created:
        return
    
    task = instance.task
    comment_author = instance.author
    
    # Notify task assignee (if different from comment author)
    if task.assignee and task.assignee != comment_author:
        message = f"New comment on task: {task.title}"
        if instance.content:
            preview = instance.content[:100] + ('...' if len(instance.content) > 100 else '')
            message += f"\n{preview}"
        
        create_notification.delay(
            user_id=task.assignee.id,
            message=message,
            notification_type=Notification.TYPE_COMMENT_ADDED,
            related_object_type='tasks.Task',
            related_object_id=task.id,
            metadata={
                'task_title': task.title,
                'comment_id': instance.id,
                'comment_author_id': comment_author.id if comment_author else None,
                'comment_author_username': comment_author.username if comment_author else None,
                'project_id': task.project_id if task.project else None,
            }
        )
        logger.info(f"Task comment notification queued for task assignee {task.assignee.id}")
    
    # Notify other project members (if task has project)
    if task.project:
        project_members = task.project.members.exclude(user=comment_author)
        if task.assignee and task.assignee != comment_author:
            project_members = project_members.exclude(user=task.assignee)
        
        if project_members.exists():
            user_ids = list(project_members.values_list('user_id', flat=True))
            message = f"New comment on task: {task.title} in project {task.project.name}"
            if instance.content:
                preview = instance.content[:100] + ('...' if len(instance.content) > 100 else '')
                message += f"\n{preview}"
            
            send_bulk_notifications.delay(
                user_ids=user_ids,
                message=message,
                notification_type=Notification.TYPE_COMMENT_ADDED,
                related_object_type='tasks.Task',
                related_object_id=task.id,
                metadata={
                    'task_title': task.title,
                    'comment_id': instance.id,
                    'comment_author_id': comment_author.id if comment_author else None,
                    'project_id': task.project_id,
                    'project_name': str(task.project),
                }
            )
            logger.info(f"Task comment bulk notifications queued for {len(user_ids)} project members")


# ==================== TaskAttachment Signals ====================

@receiver(post_save, sender='tasks.TaskAttachment')
def create_task_attachment_notification(sender, instance, created, **kwargs):
    """
    Create notification when an attachment is added to a task.
    
    Notifies the task assignee and other project members (excluding the uploader).
    """
    if not created:
        return
    
    task = instance.task
    uploader = instance.uploaded_by
    
    # Notify task assignee (if different from uploader)
    if task.assignee and task.assignee != uploader:
        message = f"New attachment added to task: {task.title}"
        if instance.filename:
            message += f"\nFile: {instance.filename}"
        
        create_notification.delay(
            user_id=task.assignee.id,
            message=message,
            notification_type=Notification.TYPE_ATTACHMENT_ADDED,
            related_object_type='tasks.Task',
            related_object_id=task.id,
            metadata={
                'task_title': task.title,
                'attachment_id': instance.id,
                'filename': instance.filename,
                'file_type': instance.file_type,
                'uploader_id': uploader.id if uploader else None,
                'uploader_username': uploader.username if uploader else None,
                'project_id': task.project_id if task.project else None,
            }
        )
        logger.info(f"Task attachment notification queued for task assignee {task.assignee.id}")
    
    # Notify other project members (if task has project)
    if task.project:
        project_members = task.project.members.exclude(user=uploader)
        if task.assignee and task.assignee != uploader:
            project_members = project_members.exclude(user=task.assignee)
        
        if project_members.exists():
            user_ids = list(project_members.values_list('user_id', flat=True))
            message = f"New attachment added to task: {task.title} in project {task.project.name}"
            if instance.filename:
                message += f"\nFile: {instance.filename}"
            
            send_bulk_notifications.delay(
                user_ids=user_ids,
                message=message,
                notification_type=Notification.TYPE_ATTACHMENT_ADDED,
                related_object_type='tasks.Task',
                related_object_id=task.id,
                metadata={
                    'task_title': task.title,
                    'attachment_id': instance.id,
                    'filename': instance.filename,
                    'file_type': instance.file_type,
                    'uploader_id': uploader.id if uploader else None,
                    'project_id': task.project_id,
                    'project_name': str(task.project),
                }
            )
            logger.info(f"Task attachment bulk notifications queued for {len(user_ids)} project members")

