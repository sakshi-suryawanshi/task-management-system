"""
Comprehensive tests for Celery tasks in projects and teams apps.

This module contains tests for:
- Project analytics generation (generate_project_analytics)
- Project archiving (archive_completed_projects)
- Team report generation (generate_team_report)

All tests use mocking where appropriate to ensure fast execution.
"""

import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from projects.tasks import (
    generate_project_analytics,
    archive_completed_projects,
)
from teams.tasks import generate_team_report
from projects.models import Project, ProjectMember
from teams.models import Team, TeamMember
from tasks.models import Task
from users.models import User
from factories import (
    UserFactory,
    TeamFactory,
    TeamMemberFactory,
    ProjectFactory,
    ProjectMemberFactory,
    TaskFactory,
)


# ============================================================================
# Project Analytics Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestGenerateProjectAnalytics:
    """Test suite for generate_project_analytics task."""

    def test_generate_project_analytics_success(self, project_with_members):
        """Test successful project analytics generation."""
        project, owner, admin, member = project_with_members
        
        # Create various tasks
        TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=admin, status=Task.STATUS_IN_PROGRESS)
        TaskFactory(project=project, assignee=member, status=Task.STATUS_TODO)
        TaskFactory(
            project=project,
            assignee=member,
            status=Task.STATUS_TODO,
            due_date=timezone.now() - timedelta(days=1)  # Overdue
        )
        
        result = generate_project_analytics(
            project_id=project.id,
            include_member_stats=True,
            include_task_breakdown=True,
            include_timeline_stats=True
        )
        
        assert result['project_id'] == project.id
        assert result['project_name'] == project.name
        assert 'summary' in result
        assert 'task_statistics' in result
        assert 'member_statistics' in result
        assert 'timeline_statistics' in result
        assert 'health_metrics' in result
        
        # Verify summary statistics
        assert result['summary']['total_tasks'] == 4
        assert result['summary']['completed_tasks'] == 1
        assert result['summary']['in_progress_tasks'] == 1
        assert result['summary']['todo_tasks'] == 2
        assert result['summary']['overdue_tasks'] == 1
        assert result['summary']['completion_rate'] > 0

    def test_generate_project_analytics_task_breakdown(self, project_with_members):
        """Test analytics with task breakdown."""
        project, owner, admin, member = project_with_members
        
        # Create tasks with different statuses and priorities
        TaskFactory(
            project=project,
            status=Task.STATUS_DONE,
            priority=Task.PRIORITY_HIGH
        )
        TaskFactory(
            project=project,
            status=Task.STATUS_IN_PROGRESS,
            priority=Task.PRIORITY_MEDIUM
        )
        TaskFactory(
            project=project,
            status=Task.STATUS_TODO,
            priority=Task.PRIORITY_LOW
        )
        
        result = generate_project_analytics(
            project_id=project.id,
            include_task_breakdown=True
        )
        
        assert 'task_statistics' in result
        assert 'by_status' in result['task_statistics']
        assert 'by_priority' in result['task_statistics']
        assert Task.STATUS_DONE in result['task_statistics']['by_status']
        assert Task.PRIORITY_HIGH in result['task_statistics']['by_priority']

    def test_generate_project_analytics_member_statistics(self, project_with_members):
        """Test analytics with member statistics."""
        project, owner, admin, member = project_with_members
        
        # Create tasks assigned to different members
        TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=admin, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=member, status=Task.STATUS_TODO)
        
        result = generate_project_analytics(
            project_id=project.id,
            include_member_stats=True
        )
        
        assert 'member_statistics' in result
        assert 'member_contributions' in result['member_statistics']
        
        # Find member contribution
        member_contrib = next(
            (m for m in result['member_statistics']['member_contributions'] 
             if m['user_id'] == member.id),
            None
        )
        assert member_contrib is not None
        assert member_contrib['tasks_assigned'] == 3
        assert member_contrib['tasks_completed'] == 2

    def test_generate_project_analytics_timeline_statistics(self, project_with_members):
        """Test analytics with timeline statistics."""
        project, owner, admin, member = project_with_members
        
        # Create tasks at different times
        old_task = TaskFactory(
            project=project,
            status=Task.STATUS_DONE,
            created_at=timezone.now() - timedelta(days=10),
            updated_at=timezone.now() - timedelta(days=8)
        )
        recent_task = TaskFactory(
            project=project,
            status=Task.STATUS_DONE,
            created_at=timezone.now() - timedelta(days=3),
            updated_at=timezone.now() - timedelta(days=2)
        )
        
        result = generate_project_analytics(
            project_id=project.id,
            include_timeline_stats=True
        )
        
        assert 'timeline_statistics' in result
        assert result['timeline_statistics']['tasks_completed_last_7_days'] >= 1
        assert result['timeline_statistics']['tasks_completed_last_30_days'] >= 2

    def test_generate_project_analytics_health_metrics(self, project_with_members):
        """Test analytics health metrics calculation."""
        project, owner, admin, member = project_with_members
        
        # Create mostly completed tasks (good health)
        for _ in range(8):
            TaskFactory(project=project, status=Task.STATUS_DONE)
        for _ in range(2):
            TaskFactory(project=project, status=Task.STATUS_TODO)
        
        result = generate_project_analytics(project_id=project.id)
        
        assert 'health_metrics' in result
        assert 'on_track' in result['health_metrics']
        assert 'completion_trend' in result['health_metrics']
        assert 'risk_level' in result['health_metrics']
        assert result['health_metrics']['on_track'] is True
        assert result['health_metrics']['risk_level'] in ['low', 'medium', 'high']

    def test_generate_project_analytics_high_risk_project(self, project_with_members):
        """Test analytics for high-risk project."""
        project, owner, admin, member = project_with_members
        
        # Create many overdue and blocked tasks (high risk)
        for _ in range(5):
            TaskFactory(
                project=project,
                status=Task.STATUS_BLOCKED,
                due_date=timezone.now() - timedelta(days=5)
            )
        for _ in range(3):
            TaskFactory(
                project=project,
                status=Task.STATUS_TODO,
                due_date=timezone.now() - timedelta(days=10)
            )
        
        result = generate_project_analytics(project_id=project.id)
        
        assert result['health_metrics']['risk_level'] in ['medium', 'high']
        assert result['summary']['overdue_tasks'] >= 3

    def test_generate_project_analytics_without_options(self, project_with_members):
        """Test analytics generation with all options disabled."""
        project, owner, admin, member = project_with_members
        TaskFactory(project=project, status=Task.STATUS_DONE)
        
        result = generate_project_analytics(
            project_id=project.id,
            include_member_stats=False,
            include_task_breakdown=False,
            include_timeline_stats=False
        )
        
        assert 'summary' in result
        assert 'task_statistics' not in result or not result['task_statistics']
        assert 'member_statistics' not in result
        assert 'timeline_statistics' not in result

    def test_generate_project_analytics_project_not_found(self):
        """Test analytics generation when project doesn't exist."""
        result = generate_project_analytics(project_id=99999)
        
        assert result['status'] == 'error'
        assert result['error'] == 'project_not_found'

    def test_generate_project_analytics_empty_project(self, project_with_members):
        """Test analytics for project with no tasks."""
        project, owner, admin, member = project_with_members
        
        result = generate_project_analytics(project_id=project.id)
        
        assert result['summary']['total_tasks'] == 0
        assert result['summary']['completion_rate'] == 0.0
        assert result['health_metrics']['risk_level'] == 'low'

    def test_generate_project_analytics_completion_rate_calculation(self, project_with_members):
        """Test completion rate calculation."""
        project, owner, admin, member = project_with_members
        
        # Create 10 tasks, 7 completed
        for _ in range(7):
            TaskFactory(project=project, status=Task.STATUS_DONE)
        for _ in range(3):
            TaskFactory(project=project, status=Task.STATUS_TODO)
        
        result = generate_project_analytics(project_id=project.id)
        
        assert result['summary']['completion_rate'] == 70.0
        assert result['summary']['total_tasks'] == 10
        assert result['summary']['completed_tasks'] == 7


# ============================================================================
# Archive Completed Projects Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestArchiveCompletedProjects:
    """Test suite for archive_completed_projects task."""

    @patch('projects.tasks.send_bulk_notifications')
    def test_archive_completed_projects_success(self, mock_bulk_notify):
        """Test successful archiving of completed projects."""
        team = TeamFactory()
        project = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=100)
        )
        
        # All tasks completed
        TaskFactory(project=project, status=Task.STATUS_DONE)
        TaskFactory(project=project, status=Task.STATUS_DONE)
        
        # Add project members
        owner = UserFactory()
        member = UserFactory()
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 1
        assert result['archived_project_ids'] == [project.id]
        
        # Verify project description was updated
        project.refresh_from_db()
        assert 'ARCHIVED' in project.description.upper()
        
        # Verify notifications were sent
        assert mock_bulk_notify.called

    def test_archive_completed_projects_skips_recent_completions(self):
        """Test that recently completed projects are not archived."""
        team = TeamFactory()
        project = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=30)  # Only 30 days ago
        )
        
        TaskFactory(project=project, status=Task.STATUS_DONE)
        
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 0

    def test_archive_completed_projects_skips_incomplete_tasks(self):
        """Test that projects with incomplete tasks are not archived."""
        team = TeamFactory()
        project = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=100)
        )
        
        # Mix of completed and incomplete tasks
        TaskFactory(project=project, status=Task.STATUS_DONE)
        TaskFactory(project=project, status=Task.STATUS_TODO)  # Incomplete
        
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 0

    def test_archive_completed_projects_custom_days(self):
        """Test archiving with custom days_since_completion."""
        team = TeamFactory()
        project = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=50)
        )
        
        TaskFactory(project=project, status=Task.STATUS_DONE)
        
        result = archive_completed_projects(days_since_completion=30)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 1
        assert result['days_since_completion'] == 30

    def test_archive_completed_projects_multiple_projects(self):
        """Test archiving multiple projects."""
        team = TeamFactory()
        
        # Project 1: Should be archived
        project1 = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=100)
        )
        TaskFactory(project=project1, status=Task.STATUS_DONE)
        
        # Project 2: Should be archived
        project2 = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=120)
        )
        TaskFactory(project=project2, status=Task.STATUS_DONE)
        
        # Project 3: Too recent, should not be archived
        project3 = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=50)
        )
        TaskFactory(project=project3, status=Task.STATUS_DONE)
        
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 2
        assert project1.id in result['archived_project_ids']
        assert project2.id in result['archived_project_ids']
        assert project3.id not in result['archived_project_ids']

    def test_archive_completed_projects_no_projects_to_archive(self):
        """Test archiving when no projects meet criteria."""
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert result['projects_archived'] == 0

    @patch('projects.tasks.send_bulk_notifications')
    def test_archive_completed_projects_sends_notifications(self, mock_bulk_notify):
        """Test that notifications are sent to project members."""
        team = TeamFactory()
        project = ProjectFactory(
            team=team,
            status=Project.STATUS_COMPLETED,
            updated_at=timezone.now() - timedelta(days=100)
        )
        
        TaskFactory(project=project, status=Task.STATUS_DONE)
        
        owner = UserFactory()
        member1 = UserFactory()
        member2 = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=member1, role='member')
        ProjectMemberFactory(project=project, user=member2, role='member')
        
        result = archive_completed_projects(days_since_completion=90)
        
        assert result['status'] == 'success'
        assert mock_bulk_notify.called
        
        # Verify notification was sent with correct parameters
        call_args = mock_bulk_notify.call_args
        assert call_args is not None
        assert len(call_args[1]['user_ids']) == 3


# ============================================================================
# Team Report Task Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.celery
class TestGenerateTeamReport:
    """Test suite for generate_team_report task."""

    def test_generate_team_report_success(self, team_with_members):
        """Test successful team report generation."""
        team, owner, admin, member = team_with_members
        
        # Create projects and tasks
        project1 = ProjectFactory(team=team, status=Project.STATUS_ACTIVE)
        project2 = ProjectFactory(team=team, status=Project.STATUS_COMPLETED)
        
        TaskFactory(project=project1, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project1, assignee=admin, status=Task.STATUS_IN_PROGRESS)
        TaskFactory(project=project2, assignee=member, status=Task.STATUS_DONE)
        
        result = generate_team_report(
            team_id=team.id,
            include_project_details=True,
            include_member_performance=True,
            include_task_statistics=True
        )
        
        assert result['team_id'] == team.id
        assert result['team_name'] == team.name
        assert 'overview' in result
        assert 'member_statistics' in result
        assert 'project_statistics' in result
        assert 'task_statistics' in result
        assert 'member_performance' in result
        assert 'activity_timeline' in result
        assert 'team_health' in result
        
        # Verify overview
        assert result['overview']['total_members'] == 3
        assert result['overview']['total_projects'] == 2
        assert result['overview']['active_projects'] == 1
        assert result['overview']['total_tasks'] == 3

    def test_generate_team_report_member_statistics(self, team_with_members):
        """Test team report member statistics."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team)
        ProjectMemberFactory(project=project, user=member, role='member')
        
        # Create tasks for different members
        TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        TaskFactory(project=project, assignee=admin, status=Task.STATUS_DONE)
        
        result = generate_team_report(
            team_id=team.id,
            include_member_performance=True
        )
        
        assert 'member_statistics' in result
        assert 'member_list' in result['member_statistics']
        
        # Find member in list
        member_info = next(
            (m for m in result['member_statistics']['member_list'] 
             if m['user_id'] == member.id),
            None
        )
        assert member_info is not None
        assert member_info['tasks_assigned'] >= 2

    def test_generate_team_report_project_statistics(self, team_with_members):
        """Test team report project statistics."""
        team, owner, admin, member = team_with_members
        
        project1 = ProjectFactory(team=team, status=Project.STATUS_ACTIVE, priority=Project.PRIORITY_HIGH)
        project2 = ProjectFactory(team=team, status=Project.STATUS_COMPLETED, priority=Project.PRIORITY_MEDIUM)
        project3 = ProjectFactory(team=team, status=Project.STATUS_ON_HOLD, priority=Project.PRIORITY_LOW)
        
        result = generate_team_report(
            team_id=team.id,
            include_project_details=True
        )
        
        assert 'project_statistics' in result
        assert 'by_status' in result['project_statistics']
        assert 'by_priority' in result['project_statistics']
        assert Project.STATUS_ACTIVE in result['project_statistics']['by_status']
        assert Project.PRIORITY_HIGH in result['project_statistics']['by_priority']

    def test_generate_team_report_task_statistics(self, team_with_members):
        """Test team report task statistics."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team)
        
        # Create tasks with different statuses
        TaskFactory(project=project, status=Task.STATUS_DONE)
        TaskFactory(project=project, status=Task.STATUS_IN_PROGRESS)
        TaskFactory(project=project, status=Task.STATUS_TODO)
        TaskFactory(
            project=project,
            status=Task.STATUS_TODO,
            due_date=timezone.now() - timedelta(days=1)  # Overdue
        )
        
        result = generate_team_report(
            team_id=team.id,
            include_task_statistics=True
        )
        
        assert 'task_statistics' in result
        assert 'by_status' in result['task_statistics']
        assert 'by_priority' in result['task_statistics']
        assert result['task_statistics']['overdue_tasks'] >= 1
        assert result['task_statistics']['completion_rate'] > 0

    def test_generate_team_report_member_performance(self, team_with_members):
        """Test team report member performance metrics."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team)
        ProjectMemberFactory(project=project, user=member, role='member')
        
        # Create tasks showing performance
        for _ in range(5):
            TaskFactory(project=project, assignee=member, status=Task.STATUS_DONE)
        for _ in range(2):
            TaskFactory(project=project, assignee=member, status=Task.STATUS_TODO)
        
        result = generate_team_report(
            team_id=team.id,
            include_member_performance=True
        )
        
        assert 'member_performance' in result
        assert 'top_contributors' in result['member_performance']
        
        # Find member in top contributors
        contributor = next(
            (c for c in result['member_performance']['top_contributors'] 
             if c['user_id'] == member.id),
            None
        )
        if contributor:
            assert contributor['tasks_completed'] >= 5

    def test_generate_team_report_team_health(self, team_with_members):
        """Test team report health assessment."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team, status=Project.STATUS_ACTIVE)
        
        # Create mostly completed tasks (good health)
        for _ in range(8):
            TaskFactory(project=project, status=Task.STATUS_DONE)
        for _ in range(2):
            TaskFactory(project=project, status=Task.STATUS_TODO)
        
        result = generate_team_report(team_id=team.id)
        
        assert 'team_health' in result
        assert 'overall_health' in result['team_health']
        assert 'productivity_score' in result['team_health']
        assert 'active_engagement' in result['team_health']
        assert result['team_health']['overall_health'] in ['excellent', 'good', 'fair', 'poor']
        assert 0 <= result['team_health']['productivity_score'] <= 100

    def test_generate_team_report_activity_timeline(self, team_with_members):
        """Test team report activity timeline."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team)
        
        # Create tasks at different times
        TaskFactory(
            project=project,
            created_at=timezone.now() - timedelta(days=3)
        )
        TaskFactory(
            project=project,
            status=Task.STATUS_DONE,
            updated_at=timezone.now() - timedelta(days=2)
        )
        
        result = generate_team_report(team_id=team.id)
        
        assert 'activity_timeline' in result
        assert 'tasks_created_last_7_days' in result['activity_timeline']
        assert 'tasks_completed_last_7_days' in result['activity_timeline']
        assert result['activity_timeline']['tasks_created_last_7_days'] >= 1
        assert result['activity_timeline']['tasks_completed_last_7_days'] >= 1

    def test_generate_team_report_without_options(self, team_with_members):
        """Test team report generation with options disabled."""
        team, owner, admin, member = team_with_members
        
        result = generate_team_report(
            team_id=team.id,
            include_project_details=False,
            include_member_performance=False,
            include_task_statistics=False
        )
        
        assert 'overview' in result
        assert 'member_statistics' in result
        # Project and task statistics may be empty but keys should exist

    def test_generate_team_report_team_not_found(self):
        """Test team report generation when team doesn't exist."""
        result = generate_team_report(team_id=99999)
        
        assert result['status'] == 'error'
        assert result['error'] == 'team_not_found'

    def test_generate_team_report_empty_team(self):
        """Test team report for team with no projects or tasks."""
        team = TeamFactory()
        
        result = generate_team_report(team_id=team.id)
        
        assert result['overview']['total_projects'] == 0
        assert result['overview']['total_tasks'] == 0
        assert result['overview']['completion_rate'] == 0.0

    def test_generate_team_report_date_range(self, team_with_members):
        """Test team report with date range filter."""
        team, owner, admin, member = team_with_members
        
        project = ProjectFactory(team=team)
        
        # Create old and recent tasks
        TaskFactory(
            project=project,
            created_at=timezone.now() - timedelta(days=50)
        )
        TaskFactory(
            project=project,
            created_at=timezone.now() - timedelta(days=5)
        )
        
        result = generate_team_report(
            team_id=team.id,
            date_range_days=30
        )
        
        assert result['date_range_days'] == 30
        # Activity timeline should still work
        assert 'activity_timeline' in result

