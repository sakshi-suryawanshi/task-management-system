"""
Signals for ActivityLog.

This module contains Django signals for automatically logging user activities
when models are created, updated, or deleted.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import ActivityLog


# Store original instance before save for detecting changes
# Use instance id (memory address) as key since pk may not exist yet
_original_instances = {}


def get_user_from_instance(instance):
    """
    Attempt to get the user who performed the action from the instance.
    
    Checks common field names: created_by, user, author, uploaded_by, assignee, etc.
    
    Args:
        instance: Model instance
        
    Returns:
        User instance or None
    """
    user_fields = ['created_by', 'user', 'author', 'uploaded_by', 'assignee', 'owner']
    
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
    
    # Get all fields from the model
    fields = [f.name for f in new_instance._meta.get_fields() if hasattr(f, 'attname')]
    
    for field in fields:
        # Skip certain fields that change automatically
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
                # Convert values to strings for JSON serialization
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
def log_task_activity(sender, instance, created, **kwargs):
    """Log Task creation or update activity."""
    user = get_user_from_instance(instance)
    original_instance = _original_instances.pop(id(instance), None)
    
    if created:
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            obj=instance,
            metadata={
                'title': instance.title,
                'status': instance.status,
                'priority': instance.priority,
                'project_id': instance.project_id,
                'project_name': str(instance.project) if instance.project else None,
                'assignee_id': instance.assignee_id,
            }
        )
    else:
        # Detect changes
        changes = detect_field_changes(original_instance, instance)
        
        # Determine specific action based on changes
        action = ActivityLog.ACTION_UPDATED
        if 'status' in changes:
            action = ActivityLog.ACTION_STATUS_CHANGED
        elif 'priority' in changes:
            action = ActivityLog.ACTION_PRIORITY_CHANGED
        elif 'assignee' in changes:
            if changes['assignee']['new']:
                action = ActivityLog.ACTION_ASSIGNED
            else:
                action = ActivityLog.ACTION_UNASSIGNED
        
        ActivityLog.log_activity(
            user=user,
            action=action,
            obj=instance,
            metadata={
                'title': instance.title,
                'changes': changes,
            }
        )


@receiver(post_delete, sender='tasks.Task')
def log_task_deletion(sender, instance, **kwargs):
    """Log Task deletion activity."""
    user = get_user_from_instance(instance)
    
    ActivityLog.log_activity(
        user=user,
        action=ActivityLog.ACTION_DELETED,
        obj=instance,
        metadata={
            'title': instance.title,
            'status': instance.status,
            'project_id': instance.project_id,
        }
    )


# ==================== Project Signals ====================

@receiver(pre_save, sender='projects.Project')
def project_pre_save(sender, instance, **kwargs):
    """Store original Project instance before save to detect changes."""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            _original_instances[id(instance)] = original
        except sender.DoesNotExist:
            _original_instances[id(instance)] = None
    else:
        _original_instances[id(instance)] = None


@receiver(post_save, sender='projects.Project')
def log_project_activity(sender, instance, created, **kwargs):
    """Log Project creation or update activity."""
    user = get_user_from_instance(instance)
    original_instance = _original_instances.pop(id(instance), None)
    
    if created:
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            obj=instance,
            metadata={
                'name': instance.name,
                'status': instance.status,
                'priority': instance.priority,
                'team_id': instance.team_id,
                'team_name': str(instance.team) if instance.team else None,
            }
        )
    else:
        changes = detect_field_changes(original_instance, instance)
        
        action = ActivityLog.ACTION_UPDATED
        if 'status' in changes:
            action = ActivityLog.ACTION_STATUS_CHANGED
        elif 'priority' in changes:
            action = ActivityLog.ACTION_PRIORITY_CHANGED
        
        ActivityLog.log_activity(
            user=user,
            action=action,
            obj=instance,
            metadata={
                'name': instance.name,
                'changes': changes,
            }
        )


@receiver(post_delete, sender='projects.Project')
def log_project_deletion(sender, instance, **kwargs):
    """Log Project deletion activity."""
    user = get_user_from_instance(instance)
    
    ActivityLog.log_activity(
        user=user,
        action=ActivityLog.ACTION_DELETED,
        obj=instance,
        metadata={
            'name': instance.name,
            'status': instance.status,
            'team_id': instance.team_id,
        }
    )


# ==================== Team Signals ====================

@receiver(pre_save, sender='teams.Team')
def team_pre_save(sender, instance, **kwargs):
    """Store original Team instance before save to detect changes."""
    if instance.pk:
        try:
            original = sender.objects.get(pk=instance.pk)
            _original_instances[id(instance)] = original
        except sender.DoesNotExist:
            _original_instances[id(instance)] = None
    else:
        _original_instances[id(instance)] = None


@receiver(post_save, sender='teams.Team')
def log_team_activity(sender, instance, created, **kwargs):
    """Log Team creation or update activity."""
    user = get_user_from_instance(instance)
    original_instance = _original_instances.pop(id(instance), None)
    
    if created:
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_CREATED,
            obj=instance,
            metadata={
                'name': instance.name,
            }
        )
    else:
        changes = detect_field_changes(original_instance, instance)
        
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_UPDATED,
            obj=instance,
            metadata={
                'name': instance.name,
                'changes': changes,
            }
        )


@receiver(post_delete, sender='teams.Team')
def log_team_deletion(sender, instance, **kwargs):
    """Log Team deletion activity."""
    user = get_user_from_instance(instance)
    
    ActivityLog.log_activity(
        user=user,
        action=ActivityLog.ACTION_DELETED,
        obj=instance,
        metadata={
            'name': instance.name,
        }
    )


# ==================== TaskComment Signals ====================

@receiver(post_save, sender='tasks.TaskComment')
def log_task_comment_activity(sender, instance, created, **kwargs):
    """Log TaskComment creation or update activity."""
    if created:
        user = instance.author if hasattr(instance, 'author') else None
        
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_COMMENT_ADDED,
            obj=instance.task,
            metadata={
                'comment_id': instance.id,
                'task_title': instance.task.title if instance.task else None,
                'comment_preview': instance.content[:100] if instance.content else None,
            }
        )


@receiver(post_delete, sender='tasks.TaskComment')
def log_task_comment_deletion(sender, instance, **kwargs):
    """Log TaskComment deletion activity."""
    user = getattr(instance, 'author', None)
    # Store task info before accessing in case of cascade issues
    task = getattr(instance, 'task', None)
    task_id = task.id if task else None
    task_title = task.title if task else None
    
    ActivityLog.log_activity(
        user=user,
        action=ActivityLog.ACTION_DELETED,
        obj=task,
        metadata={
            'comment_id': instance.id,
            'task_id': task_id,
            'task_title': task_title,
        }
    )


# ==================== TaskAttachment Signals ====================

@receiver(post_save, sender='tasks.TaskAttachment')
def log_task_attachment_activity(sender, instance, created, **kwargs):
    """Log TaskAttachment creation activity."""
    if created:
        user = instance.uploaded_by if hasattr(instance, 'uploaded_by') else None
        
        ActivityLog.log_activity(
            user=user,
            action=ActivityLog.ACTION_ATTACHMENT_ADDED,
            obj=instance.task,
            metadata={
                'attachment_id': instance.id,
                'filename': instance.filename,
                'file_size': instance.file_size,
                'file_type': instance.file_type,
                'task_title': instance.task.title if instance.task else None,
            }
        )


@receiver(post_delete, sender='tasks.TaskAttachment')
def log_task_attachment_deletion(sender, instance, **kwargs):
    """Log TaskAttachment deletion activity."""
    user = getattr(instance, 'uploaded_by', None)
    # Store task info before accessing in case of cascade issues
    task = getattr(instance, 'task', None)
    task_id = task.id if task else None
    task_title = task.title if task else None
    
    ActivityLog.log_activity(
        user=user,
        action=ActivityLog.ACTION_DELETED,
        obj=task,
        metadata={
            'attachment_id': instance.id,
            'filename': getattr(instance, 'filename', None),
            'task_id': task_id,
            'task_title': task_title,
        }
    )


# ==================== TeamMember Signals ====================

@receiver(post_save, sender='teams.TeamMember')
def log_team_member_activity(sender, instance, created, **kwargs):
    """Log TeamMember addition activity."""
    if created:
        ActivityLog.log_activity(
            user=instance.user,
            action=ActivityLog.ACTION_MEMBER_ADDED,
            obj=instance.team,
            metadata={
                'member_id': instance.user_id,
                'member_username': instance.user.username if instance.user else None,
                'role': instance.role,
                'team_name': instance.team.name if instance.team else None,
            }
        )


@receiver(post_delete, sender='teams.TeamMember')
def log_team_member_removal(sender, instance, **kwargs):
    """Log TeamMember removal activity."""
    ActivityLog.log_activity(
        user=instance.user,
        action=ActivityLog.ACTION_MEMBER_REMOVED,
        obj=instance.team,
        metadata={
            'member_id': instance.user_id,
            'member_username': instance.user.username if instance.user else None,
            'role': instance.role,
            'team_name': instance.team.name if instance.team else None,
        }
    )


# ==================== ProjectMember Signals ====================

@receiver(post_save, sender='projects.ProjectMember')
def log_project_member_activity(sender, instance, created, **kwargs):
    """Log ProjectMember addition activity."""
    if created:
        ActivityLog.log_activity(
            user=instance.user,
            action=ActivityLog.ACTION_MEMBER_ADDED,
            obj=instance.project,
            metadata={
                'member_id': instance.user_id,
                'member_username': instance.user.username if instance.user else None,
                'role': instance.role,
                'project_name': instance.project.name if instance.project else None,
            }
        )


@receiver(post_delete, sender='projects.ProjectMember')
def log_project_member_removal(sender, instance, **kwargs):
    """Log ProjectMember removal activity."""
    ActivityLog.log_activity(
        user=instance.user,
        action=ActivityLog.ACTION_MEMBER_REMOVED,
        obj=instance.project,
        metadata={
            'member_id': instance.user_id,
            'member_username': instance.user.username if instance.user else None,
            'role': instance.role,
            'project_name': instance.project.name if instance.project else None,
        }
    )

