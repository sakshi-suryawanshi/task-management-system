"""
Signals for Project notifications.

This module contains Django signals for automatically creating notifications
when projects are created, updated, or when members are added/removed.
Notifications are created asynchronously using Celery tasks.
"""

import logging
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

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
    user_fields = ['created_by', 'user', 'author', 'owner']
    
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
def create_project_notification(sender, instance, created, **kwargs):
    """
    Create notifications when projects are created or updated.
    
    Notifications are created for:
    - Project creation (notify all team members)
    - Project status changes (notify all project members)
    - Project updates (general, notify all project members)
    """
    original_instance = _original_instances.pop(id(instance), None)
    created_by = get_user_from_instance(instance)
    
    if created:
        # Project created - notify all team members
        if instance.team:
            team_members = instance.team.members.exclude(user=created_by)
            if team_members.exists():
                user_ids = list(team_members.values_list('user_id', flat=True))
                message = f"New project created: {instance.name} in team {instance.team.name}"
                
                send_bulk_notifications.delay(
                    user_ids=user_ids,
                    message=message,
                    notification_type=Notification.TYPE_PROJECT_UPDATED,
                    related_object_type='projects.Project',
                    related_object_id=instance.id,
                    metadata={
                        'project_name': instance.name,
                        'project_status': instance.status,
                        'team_id': instance.team_id,
                        'team_name': str(instance.team),
                        'created_by_id': created_by.id if created_by else None,
                    }
                )
                logger.info(f"Project creation bulk notifications queued for {len(user_ids)} team members")
    else:
        # Project updated - detect specific changes
        changes = detect_field_changes(original_instance, instance)
        
        # Get project members for notifications
        project_members = instance.members.all()
        if not project_members.exists():
            return
        
        user_ids = list(project_members.values_list('user_id', flat=True))
        
        # Project status changed
        if 'status' in changes:
            old_status = changes['status']['old']
            new_status = changes['status']['new']
            message = f"Project status changed: {instance.name} ({old_status} → {new_status})"
            
            send_bulk_notifications.delay(
                user_ids=user_ids,
                message=message,
                notification_type=Notification.TYPE_PROJECT_STATUS_CHANGED,
                related_object_type='projects.Project',
                related_object_id=instance.id,
                metadata={
                    'project_name': instance.name,
                    'old_status': old_status,
                    'new_status': new_status,
                    'team_id': instance.team_id if instance.team else None,
                    'team_name': str(instance.team) if instance.team else None,
                }
            )
            logger.info(f"Project status change bulk notifications queued for {len(user_ids)} project members")
        
        # General project update
        elif changes:
            # Only notify if there were meaningful changes
            message = f"Project updated: {instance.name}"
            if instance.team:
                message += f" in team {instance.team.name}"
            
            send_bulk_notifications.delay(
                user_ids=user_ids,
                message=message,
                notification_type=Notification.TYPE_PROJECT_UPDATED,
                related_object_type='projects.Project',
                related_object_id=instance.id,
                metadata={
                    'project_name': instance.name,
                    'team_id': instance.team_id if instance.team else None,
                    'team_name': str(instance.team) if instance.team else None,
                    'changes': list(changes.keys()),
                }
            )
            logger.info(f"Project update bulk notifications queued for {len(user_ids)} project members")


# ==================== ProjectMember Signals ====================

@receiver(post_save, sender='projects.ProjectMember')
def create_project_member_added_notification(sender, instance, created, **kwargs):
    """
    Create notification when a member is added to a project.
    
    Notifies:
    - The newly added member
    - Other project members (bulk notification)
    """
    if not created:
        return
    
    project = instance.project
    new_member = instance.user
    
    # Notify the newly added member
    message = f"You have been added to project: {project.name}"
    if project.team:
        message += f" in team {project.team.name}"
    if instance.role:
        message += f" as {instance.get_role_display()}"
    
    create_notification.delay(
        user_id=new_member.id,
        message=message,
        notification_type=Notification.TYPE_PROJECT_MEMBER_ADDED,
        related_object_type='projects.Project',
        related_object_id=project.id,
        metadata={
            'project_name': project.name,
            'project_id': project.id,
            'member_role': instance.role,
            'team_id': project.team_id if project.team else None,
            'team_name': str(project.team) if project.team else None,
        }
    )
    logger.info(f"Project member added notification queued for user {new_member.id}")
    
    # Notify other project members
    other_members = project.members.exclude(user=new_member)
    if other_members.exists():
        user_ids = list(other_members.values_list('user_id', flat=True))
        message = f"New member added to project: {project.name}"
        message += f"\n{new_member.get_full_name() or new_member.username} joined as {instance.get_role_display()}"
        
        send_bulk_notifications.delay(
            user_ids=user_ids,
            message=message,
            notification_type=Notification.TYPE_PROJECT_MEMBER_ADDED,
            related_object_type='projects.Project',
            related_object_id=project.id,
            metadata={
                'project_name': project.name,
                'new_member_id': new_member.id,
                'new_member_username': new_member.username,
                'member_role': instance.role,
                'team_id': project.team_id if project.team else None,
            }
        )
        logger.info(f"Project member added bulk notifications queued for {len(user_ids)} project members")


@receiver(post_delete, sender='projects.ProjectMember')
def create_project_member_removed_notification(sender, instance, **kwargs):
    """
    Create notification when a member is removed from a project.
    
    Notifies:
    - The removed member
    - Remaining project members (bulk notification)
    """
    # Store project info before deletion
    project_id = instance.project_id
    project_name = instance.project.name if hasattr(instance, 'project') and instance.project else None
    removed_member_id = instance.user_id
    removed_member_username = instance.user.username if hasattr(instance, 'user') and instance.user else None
    team_id = instance.project.team_id if hasattr(instance, 'project') and instance.project and instance.project.team else None
    
    # Notify the removed member
    message = f"You have been removed from project: {project_name or f'ID {project_id}'}"
    
    create_notification.delay(
        user_id=removed_member_id,
        message=message,
        notification_type=Notification.TYPE_PROJECT_MEMBER_REMOVED,
        related_object_type='projects.Project',
        related_object_id=project_id,
        metadata={
            'project_name': project_name,
            'project_id': project_id,
            'team_id': team_id,
        }
    )
    logger.info(f"Project member removed notification queued for user {removed_member_id}")
    
    # Notify remaining project members (if project still exists and has members)
    try:
        from projects.models import Project
        project = Project.objects.get(pk=project_id)
        remaining_members = project.members.all()
        
        if remaining_members.exists():
            user_ids = list(remaining_members.values_list('user_id', flat=True))
            message = f"Member removed from project: {project.name}"
            if removed_member_username:
                message += f"\n{removed_member_username} has been removed"
            
            send_bulk_notifications.delay(
                user_ids=user_ids,
                message=message,
                notification_type=Notification.TYPE_PROJECT_MEMBER_REMOVED,
                related_object_type='projects.Project',
                related_object_id=project_id,
                metadata={
                    'project_name': project.name,
                    'removed_member_id': removed_member_id,
                    'removed_member_username': removed_member_username,
                    'team_id': team_id,
                }
            )
            logger.info(f"Project member removed bulk notifications queued for {len(user_ids)} project members")
    except Exception as e:
        logger.warning(f"Could not notify remaining project members after member removal: {e}")

