"""
Celery tasks for projects in Task Management System.

This module contains all Celery tasks for:
- Generating project analytics and reports
- Processing project-related data

All tasks are designed to be:
- Async and non-blocking
- Retryable on failure
- Well-logged for debugging
- Production-ready with proper error handling

Data processing tasks:
- generate_project_analytics
"""

import logging
from typing import Optional, Dict, Any
from datetime import timedelta
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from celery import shared_task

from projects.models import Project, ProjectMember
from tasks.models import Task
from users.models import User

logger = logging.getLogger(__name__)


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
def generate_project_analytics(
    self,
    project_id: int,
    include_member_stats: bool = True,
    include_task_breakdown: bool = True,
    include_timeline_stats: bool = True,
    save_to_cache: bool = False
) -> Dict[str, Any]:
    """
    Generate comprehensive analytics for a project.
    
    This task generates detailed analytics data for a project including:
    - Task statistics (total, by status, by priority)
    - Completion rates and trends
    - Member activity and contributions
    - Timeline statistics (tasks created/completed over time)
    - Overdue tasks and deadlines
    - Project health metrics
    
    The analytics can be used for:
    - Project dashboards
    - Progress reports
    - Performance monitoring
    - Decision making
    
    Args:
        self: Celery task instance (for retries)
        project_id: ID of the project to analyze
        include_member_stats: Whether to include member activity statistics
        include_task_breakdown: Whether to include detailed task breakdown
        include_timeline_stats: Whether to include timeline-based statistics
        save_to_cache: Whether to save results to cache (future enhancement)
        
    Returns:
        dict: Comprehensive analytics dictionary with the following structure:
            {
                'project_id': int,
                'project_name': str,
                'generated_at': str (ISO format),
                'summary': {
                    'total_tasks': int,
                    'completed_tasks': int,
                    'in_progress_tasks': int,
                    'todo_tasks': int,
                    'blocked_tasks': int,
                    'completion_rate': float (0-100),
                    'overdue_tasks': int,
                    'total_members': int,
                },
                'task_statistics': {
                    'by_status': {status: count},
                    'by_priority': {priority: count},
                    'by_assignee': {user_id: count},
                },
                'member_statistics': {
                    'active_members': int,
                    'member_contributions': [{user_id, tasks_assigned, tasks_completed}],
                },
                'timeline_statistics': {
                    'tasks_created_last_7_days': int,
                    'tasks_completed_last_7_days': int,
                    'tasks_completed_last_30_days': int,
                },
                'health_metrics': {
                    'on_track': bool,
                    'completion_trend': str ('improving', 'declining', 'stable'),
                    'risk_level': str ('low', 'medium', 'high'),
                }
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        from projects.tasks import generate_project_analytics
        
        # Queue analytics generation task
        result = generate_project_analytics.delay(
            project_id=1,
            include_member_stats=True,
            include_task_breakdown=True
        )
        
        # Get results (wait for completion)
        analytics = result.get(timeout=30)
        print(f"Completion rate: {analytics['summary']['completion_rate']}%")
    """
    try:
        # Get project with related data
        project = Project.objects.select_related('team').get(pk=project_id)
        
        logger.info(f"Generating analytics for project: {project.name} (ID: {project_id})")
        
        # Initialize analytics dictionary
        analytics = {
            'project_id': project.id,
            'project_name': project.name,
            'project_status': project.status,
            'project_priority': project.priority,
            'team_name': project.team.name if project.team else None,
            'generated_at': timezone.now().isoformat(),
            'summary': {},
            'task_statistics': {},
            'health_metrics': {},
        }
        
        # Get all tasks for this project
        tasks = Task.objects.filter(project=project)
        total_tasks = tasks.count()
        
        # Summary statistics
        completed_tasks = tasks.filter(status=Task.STATUS_DONE).count()
        in_progress_tasks = tasks.filter(status=Task.STATUS_IN_PROGRESS).count()
        todo_tasks = tasks.filter(status=Task.STATUS_TODO).count()
        blocked_tasks = tasks.filter(status=Task.STATUS_BLOCKED).count()
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        
        # Count overdue tasks
        now = timezone.now()
        overdue_tasks = tasks.filter(
            due_date__lt=now,
            status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_BLOCKED]
        ).count()
        
        # Get member count
        total_members = project.members.count()
        
        analytics['summary'] = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'todo_tasks': todo_tasks,
            'blocked_tasks': blocked_tasks,
            'completion_rate': round(completion_rate, 2),
            'overdue_tasks': overdue_tasks,
            'total_members': total_members,
            'project_deadline': project.deadline.isoformat() if project.deadline else None,
            'is_overdue': project.is_overdue(),
            'days_until_deadline': (
                (project.deadline - now).days if project.deadline and project.deadline > now else None
            ),
        }
        
        # Task breakdown by status
        if include_task_breakdown:
            status_breakdown = tasks.values('status').annotate(count=Count('id'))
            analytics['task_statistics']['by_status'] = {
                item['status']: item['count'] for item in status_breakdown
            }
            
            # Task breakdown by priority
            priority_breakdown = tasks.values('priority').annotate(count=Count('id'))
            analytics['task_statistics']['by_priority'] = {
                item['priority']: item['count'] for item in priority_breakdown
            }
            
            # Tasks by assignee
            assignee_breakdown = tasks.filter(assignee__isnull=False).values(
                'assignee_id', 'assignee__username'
            ).annotate(count=Count('id')).order_by('-count')
            
            analytics['task_statistics']['by_assignee'] = [
                {
                    'user_id': item['assignee_id'],
                    'username': item['assignee__username'],
                    'tasks_assigned': item['count']
                }
                for item in assignee_breakdown[:10]  # Top 10 assignees
            ]
        
        # Member statistics
        if include_member_stats:
            member_contributions = []
            
            # Get all project members
            project_members = project.members.select_related('user')
            
            for member in project_members:
                user = member.user
                tasks_assigned = tasks.filter(assignee=user).count()
                tasks_completed = tasks.filter(
                    assignee=user,
                    status=Task.STATUS_DONE
                ).count()
                
                # Calculate completion rate for this member
                member_completion_rate = (
                    (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0.0
                )
                
                member_contributions.append({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': member.role,
                    'tasks_assigned': tasks_assigned,
                    'tasks_completed': tasks_completed,
                    'tasks_in_progress': tasks.filter(
                        assignee=user,
                        status=Task.STATUS_IN_PROGRESS
                    ).count(),
                    'completion_rate': round(member_completion_rate, 2),
                    'overdue_tasks': tasks.filter(
                        assignee=user,
                        due_date__lt=now,
                        status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS]
                    ).count(),
                })
            
            # Sort by tasks assigned (descending)
            member_contributions.sort(key=lambda x: x['tasks_assigned'], reverse=True)
            
            analytics['member_statistics'] = {
                'total_members': total_members,
                'active_members': len([m for m in member_contributions if m['tasks_assigned'] > 0]),
                'member_contributions': member_contributions,
            }
        
        # Timeline statistics
        if include_timeline_stats:
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            
            tasks_created_last_7_days = tasks.filter(created_at__gte=seven_days_ago).count()
            tasks_completed_last_7_days = tasks.filter(
                status=Task.STATUS_DONE,
                updated_at__gte=seven_days_ago
            ).count()
            
            tasks_completed_last_30_days = tasks.filter(
                status=Task.STATUS_DONE,
                updated_at__gte=thirty_days_ago
            ).count()
            
            # Calculate average completion time (for completed tasks with due dates)
            completed_with_due = tasks.filter(
                status=Task.STATUS_DONE,
                due_date__isnull=False
            )
            
            avg_completion_time = None
            if completed_with_due.exists():
                # Calculate average days from creation to completion
                completion_times = []
                for task in completed_with_due:
                    if task.updated_at and task.created_at:
                        days = (task.updated_at - task.created_at).days
                        completion_times.append(days)
                
                if completion_times:
                    avg_completion_time = sum(completion_times) / len(completion_times)
            
            analytics['timeline_statistics'] = {
                'tasks_created_last_7_days': tasks_created_last_7_days,
                'tasks_completed_last_7_days': tasks_completed_last_7_days,
                'tasks_completed_last_30_days': tasks_completed_last_30_days,
                'average_completion_time_days': round(avg_completion_time, 2) if avg_completion_time else None,
            }
        
        # Health metrics
        # Determine if project is on track
        is_on_track = (
            completion_rate >= 50 or  # At least 50% complete
            (overdue_tasks / total_tasks < 0.2 if total_tasks > 0 else True)  # Less than 20% overdue
        )
        
        # Determine completion trend (simplified - can be enhanced with historical data)
        if include_timeline_stats and 'timeline_statistics' in analytics:
            tasks_completed_7d = analytics['timeline_statistics']['tasks_completed_last_7_days']
            tasks_completed_30d = analytics['timeline_statistics']['tasks_completed_last_30_days']
            
            if tasks_completed_30d > 0:
                weekly_rate = tasks_completed_7d / (tasks_completed_30d / 4) if tasks_completed_30d > 0 else 0
                if weekly_rate > 1.1:
                    completion_trend = 'improving'
                elif weekly_rate < 0.9:
                    completion_trend = 'declining'
                else:
                    completion_trend = 'stable'
            else:
                completion_trend = 'stable'
        else:
            completion_trend = 'stable'
        
        # Determine risk level
        risk_factors = 0
        if overdue_tasks > 0:
            risk_factors += 1
        if completion_rate < 30 and total_tasks > 5:
            risk_factors += 1
        if blocked_tasks > total_tasks * 0.2:  # More than 20% blocked
            risk_factors += 1
        if project.is_overdue():
            risk_factors += 1
        
        if risk_factors >= 3:
            risk_level = 'high'
        elif risk_factors >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        analytics['health_metrics'] = {
            'on_track': is_on_track,
            'completion_trend': completion_trend,
            'risk_level': risk_level,
            'risk_factors_count': risk_factors,
        }
        
        logger.info(
            f"Analytics generated successfully for project {project.name} (ID: {project_id}). "
            f"Completion rate: {completion_rate:.2f}%, Risk level: {risk_level}"
        )
        
        return analytics
        
    except Project.DoesNotExist:
        logger.error(f"Project with ID {project_id} not found")
        return {
            'status': 'error',
            'error': 'project_not_found',
            'project_id': project_id
        }
    except Exception as exc:
        logger.error(f"Error generating project analytics: {exc}", exc_info=True)
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
def archive_completed_projects(self, days_since_completion: int = 90) -> dict:
    """
    Archive completed projects that have been completed for a specified period.
    
    This scheduled task runs periodically to archive projects that:
    - Have status = 'completed'
    - Have been completed for more than the specified number of days (default: 90 days)
    - Have all tasks completed
    
    Archiving a project typically means:
    - Updating project metadata to indicate it's archived
    - Optionally moving it to a separate archive table (future enhancement)
    - Sending notifications to project members about archiving
    
    This helps keep active project lists clean and focused on current work,
    while preserving historical project data for reference.
    
    Args:
        self: Celery task instance (for retries)
        days_since_completion: Number of days a project must be completed before archiving (default: 90)
        
    Returns:
        dict: Result dictionary with archiving statistics:
            {
                'status': 'success',
                'projects_archived': int,
                'projects_checked': int,
                'days_since_completion': int,
                'cutoff_date': str (ISO format),
                'archived_project_ids': list[int]
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        This task is typically scheduled via Celery Beat to run monthly:
        - Schedule: First day of month at 2:00 AM
        - Task: projects.tasks.archive_completed_projects
        - Arguments: {'days_since_completion': 90}
    """
    try:
        from datetime import timedelta
        from notifications.tasks import send_bulk_notifications
        from notifications.models import Notification
        
        logger.info(
            f"Starting archive of completed projects "
            f"(completed more than {days_since_completion} days ago)"
        )
        now = timezone.now()
        cutoff_date = now - timedelta(days=days_since_completion)
        
        # Get completed projects that haven't been archived yet
        # Note: We'll add an 'archived' field or use a status field
        # For now, we'll use a simple approach: projects completed before cutoff
        completed_projects = Project.objects.filter(
            status=Project.STATUS_COMPLETED,
            updated_at__lt=cutoff_date
        ).select_related('team').prefetch_related('members__user', 'tasks')
        
        projects_checked = completed_projects.count()
        archived_count = 0
        archived_project_ids = []
        
        for project in completed_projects:
            try:
                # Verify all tasks are completed
                incomplete_tasks = project.tasks.exclude(status=Task.STATUS_DONE)
                
                if incomplete_tasks.exists():
                    logger.debug(
                        f"Project {project.id} ({project.name}) has {incomplete_tasks.count()} "
                        f"incomplete tasks, skipping archiving"
                    )
                    continue
                
                # Mark project as archived
                # For now, we'll add a note in the description or use metadata
                # In a production system, you might have an 'archived' boolean field
                # or move to an ArchiveProject model
                
                # Update project description to indicate it's archived
                if 'ARCHIVED' not in project.description.upper():
                    original_description = project.description
                    archived_note = f"\n\n[ARCHIVED on {now.date()}]"
                    project.description = original_description + archived_note
                    project.save(update_fields=['description'])
                
                archived_count += 1
                archived_project_ids.append(project.id)
                
                # Notify project members about archiving
                project_member_ids = list(
                    project.members.values_list('user_id', flat=True)
                )
                
                if project_member_ids:
                    send_bulk_notifications.delay(
                        user_ids=project_member_ids,
                        message=f"Project '{project.name}' has been archived. "
                               f"It was completed on {project.updated_at.date()}.",
                        notification_type=Notification.TYPE_PROJECT_UPDATED,
                        related_object_type='projects.Project',
                        related_object_id=project.id,
                        metadata={
                            'archived': True,
                            'archived_date': now.isoformat(),
                            'completion_date': project.updated_at.isoformat()
                        }
                    )
                
                logger.debug(
                    f"Project {project.id} ({project.name}) archived successfully. "
                    f"Completed {days_since_completion} days ago."
                )
                
            except Exception as e:
                logger.error(
                    f"Error archiving project {project.id}: {e}",
                    exc_info=True
                )
                # Continue with other projects even if one fails
                continue
        
        result = {
            'status': 'success',
            'projects_archived': archived_count,
            'projects_checked': projects_checked,
            'days_since_completion': days_since_completion,
            'cutoff_date': cutoff_date.isoformat(),
            'archived_project_ids': archived_project_ids,
            'executed_at': now.isoformat()
        }
        
        logger.info(
            f"Archive completed projects task finished: {archived_count} projects archived "
            f"out of {projects_checked} checked (completed more than {days_since_completion} days ago)"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in archive completed projects task: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)

