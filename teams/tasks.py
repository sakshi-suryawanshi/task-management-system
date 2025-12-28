"""
Celery tasks for teams in Task Management System.

This module contains all Celery tasks for:
- Generating team reports and analytics
- Processing team-related data

All tasks are designed to be:
- Async and non-blocking
- Retryable on failure
- Well-logged for debugging
- Production-ready with proper error handling

Data processing tasks:
- generate_team_report
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import timedelta
from django.db.models import Count, Q, Avg, Sum, Prefetch
from django.utils import timezone
from celery import shared_task

from teams.models import Team, TeamMember
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
def generate_team_report(
    self,
    team_id: int,
    include_project_details: bool = True,
    include_member_performance: bool = True,
    include_task_statistics: bool = True,
    date_range_days: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive report for a team.
    
    This task generates a detailed report for a team including:
    - Team overview and member statistics
    - Project statistics and status breakdown
    - Task statistics across all team projects
    - Member performance metrics
    - Activity timeline
    - Team health indicators
    
    The report can be used for:
    - Team performance reviews
    - Resource allocation decisions
    - Progress tracking
    - Management reporting
    
    Args:
        self: Celery task instance (for retries)
        team_id: ID of the team to generate report for
        include_project_details: Whether to include detailed project information
        include_member_performance: Whether to include member performance metrics
        include_task_statistics: Whether to include task statistics
        date_range_days: Optional number of days to include in timeline (default: all time)
        
    Returns:
        dict: Comprehensive team report dictionary with the following structure:
            {
                'team_id': int,
                'team_name': str,
                'generated_at': str (ISO format),
                'overview': {
                    'total_members': int,
                    'total_projects': int,
                    'active_projects': int,
                    'total_tasks': int,
                    'completed_tasks': int,
                },
                'member_statistics': {
                    'total_members': int,
                    'by_role': {role: count},
                    'member_list': [{user_id, username, role, projects_count, tasks_count}],
                },
                'project_statistics': {
                    'total_projects': int,
                    'by_status': {status: count},
                    'by_priority': {priority: count},
                    'project_list': [{project_id, name, status, tasks_count, completion_rate}],
                },
                'task_statistics': {
                    'total_tasks': int,
                    'by_status': {status: count},
                    'by_priority': {priority: count},
                    'completion_rate': float,
                    'overdue_tasks': int,
                },
                'member_performance': {
                    'top_contributors': [{user_id, username, tasks_completed, completion_rate}],
                    'member_activity': [{user_id, username, recent_activity_count}],
                },
                'activity_timeline': {
                    'tasks_created_last_7_days': int,
                    'tasks_completed_last_7_days': int,
                    'projects_created_last_30_days': int,
                },
                'team_health': {
                    'overall_health': str ('excellent', 'good', 'fair', 'poor'),
                    'active_engagement': bool,
                    'productivity_score': float (0-100),
                }
            }
        
    Raises:
        Retry: If task should be retried
        Exception: For other errors
        
    Example:
        from teams.tasks import generate_team_report
        
        # Queue team report generation task
        result = generate_team_report.delay(
            team_id=1,
            include_project_details=True,
            include_member_performance=True,
            date_range_days=30
        )
        
        # Get results (wait for completion)
        report = result.get(timeout=60)
        print(f"Team completion rate: {report['task_statistics']['completion_rate']}%")
    """
    try:
        # Get team with related data
        team = Team.objects.prefetch_related(
            'members__user',
            'projects'
        ).get(pk=team_id)
        
        logger.info(f"Generating report for team: {team.name} (ID: {team_id})")
        
        # Initialize report dictionary
        report = {
            'team_id': team.id,
            'team_name': team.name,
            'team_description': team.description,
            'generated_at': timezone.now().isoformat(),
            'date_range_days': date_range_days,
            'overview': {},
            'member_statistics': {},
            'project_statistics': {},
            'task_statistics': {},
            'team_health': {},
        }
        
        # Get all team members
        team_members = team.members.select_related('user')
        total_members = team_members.count()
        
        # Get all team projects
        team_projects = Project.objects.filter(team=team)
        total_projects = team_projects.count()
        active_projects = team_projects.filter(status=Project.STATUS_ACTIVE).count()
        
        # Get all tasks across team projects
        team_tasks = Task.objects.filter(project__team=team)
        total_tasks = team_tasks.count()
        completed_tasks = team_tasks.filter(status=Task.STATUS_DONE).count()
        
        # Overview
        report['overview'] = {
            'total_members': total_members,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': team_projects.filter(status=Project.STATUS_COMPLETED).count(),
            'on_hold_projects': team_projects.filter(status=Project.STATUS_ON_HOLD).count(),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0, 2),
        }
        
        # Member statistics
        member_by_role = team_members.values('role').annotate(count=Count('id'))
        report['member_statistics'] = {
            'total_members': total_members,
            'by_role': {
                item['role']: item['count'] for item in member_by_role
            },
            'member_list': [],
        }
        
        # Detailed member list with project and task counts
        member_list = []
        for member in team_members:
            user = member.user
            # Count projects where user is a member
            user_projects = ProjectMember.objects.filter(
                user=user,
                project__team=team
            ).count()
            
            # Count tasks assigned to user in team projects
            user_tasks = team_tasks.filter(assignee=user).count()
            user_completed_tasks = team_tasks.filter(
                assignee=user,
                status=Task.STATUS_DONE
            ).count()
            
            member_list.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() or user.username,
                'role': member.role,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None,
                'projects_count': user_projects,
                'tasks_assigned': user_tasks,
                'tasks_completed': user_completed_tasks,
                'completion_rate': round(
                    (user_completed_tasks / user_tasks * 100) if user_tasks > 0 else 0.0, 2
                ),
            })
        
        # Sort by tasks assigned (descending)
        member_list.sort(key=lambda x: x['tasks_assigned'], reverse=True)
        report['member_statistics']['member_list'] = member_list
        
        # Project statistics
        if include_project_details:
            project_by_status = team_projects.values('status').annotate(count=Count('id'))
            project_by_priority = team_projects.values('priority').annotate(count=Count('id'))
            
            report['project_statistics'] = {
                'total_projects': total_projects,
                'by_status': {
                    item['status']: item['count'] for item in project_by_status
                },
                'by_priority': {
                    item['priority']: item['count'] for item in project_by_priority
                },
                'project_list': [],
            }
            
            # Detailed project list
            project_list = []
            for project in team_projects.select_related('team'):
                project_tasks = Task.objects.filter(project=project)
                project_total_tasks = project_tasks.count()
                project_completed_tasks = project_tasks.filter(status=Task.STATUS_DONE).count()
                
                project_list.append({
                    'project_id': project.id,
                    'name': project.name,
                    'status': project.status,
                    'priority': project.priority,
                    'deadline': project.deadline.isoformat() if project.deadline else None,
                    'is_overdue': project.is_overdue(),
                    'tasks_count': project_total_tasks,
                    'completed_tasks': project_completed_tasks,
                    'completion_rate': round(
                        (project_completed_tasks / project_total_tasks * 100) if project_total_tasks > 0 else 0.0, 2
                    ),
                    'members_count': project.members.count(),
                })
            
            # Sort by completion rate (descending)
            project_list.sort(key=lambda x: x['completion_rate'], reverse=True)
            report['project_statistics']['project_list'] = project_list
        
        # Task statistics
        if include_task_statistics:
            now = timezone.now()
            task_by_status = team_tasks.values('status').annotate(count=Count('id'))
            task_by_priority = team_tasks.values('priority').annotate(count=Count('id'))
            
            overdue_tasks = team_tasks.filter(
                due_date__lt=now,
                status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_BLOCKED]
            ).count()
            
            report['task_statistics'] = {
                'total_tasks': total_tasks,
                'by_status': {
                    item['status']: item['count'] for item in task_by_status
                },
                'by_priority': {
                    item['priority']: item['count'] for item in task_by_priority
                },
                'completion_rate': report['overview']['completion_rate'],
                'overdue_tasks': overdue_tasks,
                'overdue_percentage': round(
                    (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0.0, 2
                ),
            }
        
        # Member performance
        if include_member_performance:
            # Top contributors (by tasks completed)
            top_contributors = []
            for member in team_members:
                user = member.user
                user_completed = team_tasks.filter(
                    assignee=user,
                    status=Task.STATUS_DONE
                ).count()
                user_assigned = team_tasks.filter(assignee=user).count()
                
                if user_assigned > 0:
                    top_contributors.append({
                        'user_id': user.id,
                        'username': user.username,
                        'tasks_completed': user_completed,
                        'tasks_assigned': user_assigned,
                        'completion_rate': round(
                            (user_completed / user_assigned * 100) if user_assigned > 0 else 0.0, 2
                        ),
                    })
            
            # Sort by tasks completed (descending)
            top_contributors.sort(key=lambda x: x['tasks_completed'], reverse=True)
            
            # Recent activity (tasks created/completed in last 7 days)
            seven_days_ago = now - timedelta(days=7)
            member_activity = []
            
            for member in team_members:
                user = member.user
                recent_tasks_created = Task.objects.filter(
                    project__team=team,
                    created_by=user,
                    created_at__gte=seven_days_ago
                ).count()
                
                recent_tasks_completed = team_tasks.filter(
                    assignee=user,
                    status=Task.STATUS_DONE,
                    updated_at__gte=seven_days_ago
                ).count()
                
                recent_activity = recent_tasks_created + recent_tasks_completed
                
                if recent_activity > 0:
                    member_activity.append({
                        'user_id': user.id,
                        'username': user.username,
                        'recent_activity_count': recent_activity,
                        'tasks_created': recent_tasks_created,
                        'tasks_completed': recent_tasks_completed,
                    })
            
            # Sort by recent activity (descending)
            member_activity.sort(key=lambda x: x['recent_activity_count'], reverse=True)
            
            report['member_performance'] = {
                'top_contributors': top_contributors[:10],  # Top 10
                'member_activity': member_activity[:10],  # Top 10
            }
        
        # Activity timeline
        if date_range_days:
            start_date = now - timedelta(days=date_range_days)
        else:
            start_date = None
        
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)
        
        tasks_created_last_7d = team_tasks.filter(created_at__gte=seven_days_ago).count()
        tasks_completed_last_7d = team_tasks.filter(
            status=Task.STATUS_DONE,
            updated_at__gte=seven_days_ago
        ).count()
        
        projects_created_last_30d = team_projects.filter(created_at__gte=thirty_days_ago).count()
        
        report['activity_timeline'] = {
            'tasks_created_last_7_days': tasks_created_last_7d,
            'tasks_completed_last_7_days': tasks_completed_last_7d,
            'projects_created_last_30_days': projects_created_last_30d,
        }
        
        # Team health assessment
        completion_rate = report['overview']['completion_rate']
        overdue_percentage = report['task_statistics'].get('overdue_percentage', 0) if include_task_statistics else 0
        
        # Calculate productivity score (0-100)
        # Based on completion rate, active projects, and member engagement
        productivity_score = 0
        
        # Completion rate component (40% weight)
        productivity_score += min(completion_rate * 0.4, 40)
        
        # Active projects component (20% weight)
        if total_projects > 0:
            active_ratio = active_projects / total_projects
            productivity_score += active_ratio * 20
        
        # Low overdue tasks component (20% weight)
        if total_tasks > 0:
            overdue_ratio = 1 - (overdue_percentage / 100)
            productivity_score += max(overdue_ratio * 20, 0)
        
        # Member engagement component (20% weight)
        if include_member_performance and 'member_performance' in report:
            active_members = len([m for m in report['member_performance'].get('member_activity', [])])
            if total_members > 0:
                engagement_ratio = active_members / total_members
                productivity_score += engagement_ratio * 20
        
        productivity_score = round(min(productivity_score, 100), 2)
        
        # Determine overall health
        if productivity_score >= 80:
            overall_health = 'excellent'
        elif productivity_score >= 60:
            overall_health = 'good'
        elif productivity_score >= 40:
            overall_health = 'fair'
        else:
            overall_health = 'poor'
        
        # Active engagement (at least 50% of members have recent activity)
        active_engagement = False
        if include_member_performance and 'member_performance' in report:
            active_members_count = len(report['member_performance'].get('member_activity', []))
            if total_members > 0:
                active_engagement = (active_members_count / total_members) >= 0.5
        
        report['team_health'] = {
            'overall_health': overall_health,
            'productivity_score': productivity_score,
            'active_engagement': active_engagement,
            'completion_rate': completion_rate,
            'overdue_percentage': overdue_percentage,
        }
        
        logger.info(
            f"Team report generated successfully for team {team.name} (ID: {team_id}). "
            f"Productivity score: {productivity_score}, Health: {overall_health}"
        )
        
        return report
        
    except Team.DoesNotExist:
        logger.error(f"Team with ID {team_id} not found")
        return {
            'status': 'error',
            'error': 'team_not_found',
            'team_id': team_id
        }
    except Exception as exc:
        logger.error(f"Error generating team report: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc)

