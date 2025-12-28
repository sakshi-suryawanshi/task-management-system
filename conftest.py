"""
Pytest configuration and fixtures for Task Management System.

This module provides pytest fixtures for testing the Task Management System.
Fixtures are reusable test resources that pytest automatically provides to test functions.

Fixtures defined here are automatically available to all test files in the project.

Usage:
    def test_something(user, api_client):
        # user and api_client are automatically provided by pytest
        response = api_client.get('/api/some-endpoint/')
        assert response.status_code == 200

Documentation:
    - Pytest Fixtures: https://docs.pytest.org/en/stable/fixture.html
    - pytest-django: https://pytest-django.readthedocs.io/
"""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from factories import (
    UserFactory,
    AdminUserFactory,
    ManagerUserFactory,
    DeveloperUserFactory,
    MemberUserFactory,
    UserProfileFactory,
    TeamFactory,
    TeamMemberFactory,
    ProjectFactory,
    ProjectMemberFactory,
    TaskFactory,
    TaskCommentFactory,
    NotificationFactory,
)

User = get_user_model()


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configure database setup for tests.
    
    This fixture ensures the test database is properly set up.
    Pytest-django handles most of this automatically, but we can customize here.
    """
    pass


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def user(db):
    """
    Create a regular user for testing.
    
    Returns:
        User: A regular user instance with default role (member)
    
    Example:
        def test_user_profile(user):
            assert user.role == 'member'
            assert user.is_active is True
    """
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """
    Create an admin user for testing.
    
    Returns:
        User: An admin user instance with superuser privileges
    
    Example:
        def test_admin_access(admin_user):
            assert admin_user.is_superuser is True
            assert admin_user.role == 'admin'
    """
    return AdminUserFactory()


@pytest.fixture
def manager_user(db):
    """
    Create a manager user for testing.
    
    Returns:
        User: A manager user instance
    
    Example:
        def test_manager_permissions(manager_user):
            assert manager_user.role == 'manager'
    """
    return ManagerUserFactory()


@pytest.fixture
def developer_user(db):
    """
    Create a developer user for testing.
    
    Returns:
        User: A developer user instance
    
    Example:
        def test_developer_access(developer_user):
            assert developer_user.role == 'developer'
    """
    return DeveloperUserFactory()


@pytest.fixture
def member_user(db):
    """
    Create a regular member user for testing.
    
    Returns:
        User: A member user instance
    
    Example:
        def test_member_access(member_user):
            assert member_user.role == 'member'
    """
    return MemberUserFactory()


@pytest.fixture
def user_with_profile(db):
    """
    Create a user with a complete profile for testing.
    
    Returns:
        User: A user instance with associated UserProfile
    
    Example:
        def test_profile_completeness(user_with_profile):
            assert hasattr(user_with_profile, 'profile')
            assert user_with_profile.profile.job_title
    """
    user = UserFactory()
    UserProfileFactory(user=user)
    return user


# ============================================================================
# Team Fixtures
# ============================================================================

@pytest.fixture
def team(db):
    """
    Create a team for testing.
    
    Returns:
        Team: A team instance
    
    Example:
        def test_team_creation(team):
            assert team.name
            assert team.description
    """
    return TeamFactory()


@pytest.fixture
def team_with_members(db):
    """
    Create a team with multiple members for testing.
    
    Returns:
        tuple: (team, owner, admin, member) - Team and three members with different roles
    
    Example:
        def test_team_members(team_with_members):
            team, owner, admin, member = team_with_members
            assert team.get_member_count() == 3
    """
    team = TeamFactory()
    owner = UserFactory()
    admin = UserFactory()
    member = UserFactory()
    
    TeamMemberFactory(team=team, user=owner, role='owner')
    TeamMemberFactory(team=team, user=admin, role='admin')
    TeamMemberFactory(team=team, user=member, role='member')
    
    return team, owner, admin, member


# ============================================================================
# Project Fixtures
# ============================================================================

@pytest.fixture
def project(db, team):
    """
    Create a project for testing.
    
    Args:
        team: Team fixture (automatically provided)
    
    Returns:
        Project: A project instance belonging to the team
    
    Example:
        def test_project_creation(project, team):
            assert project.team == team
            assert project.name
    """
    return ProjectFactory(team=team)


@pytest.fixture
def project_with_members(db, team_with_members):
    """
    Create a project with members for testing.
    
    Args:
        team_with_members: Team with members fixture (automatically provided)
    
    Returns:
        tuple: (project, owner, admin, member) - Project and three members with different roles
    
    Example:
        def test_project_members(project_with_members):
            project, owner, admin, member = project_with_members
            assert project.is_member(owner) is True
    """
    team, team_owner, team_admin, team_member = team_with_members
    project = ProjectFactory(team=team)
    
    ProjectMemberFactory(project=project, user=team_owner, role='owner')
    ProjectMemberFactory(project=project, user=team_admin, role='admin')
    ProjectMemberFactory(project=project, user=team_member, role='member')
    
    return project, team_owner, team_admin, team_member


# ============================================================================
# Task Fixtures
# ============================================================================

@pytest.fixture
def task(db, project, user):
    """
    Create a task for testing.
    
    Args:
        project: Project fixture (automatically provided)
        user: User fixture (automatically provided)
    
    Returns:
        Task: A task instance belonging to the project
    
    Example:
        def test_task_creation(task, project):
            assert task.project == project
            assert task.title
    """
    return TaskFactory(project=project, assignee=user, created_by=user)


@pytest.fixture
def task_with_comment(db, task, user):
    """
    Create a task with a comment for testing.
    
    Args:
        task: Task fixture (automatically provided)
        user: User fixture (automatically provided)
    
    Returns:
        tuple: (task, comment) - Task and its comment
    
    Example:
        def test_task_comments(task_with_comment):
            task, comment = task_with_comment
            assert task.comments.count() == 1
    """
    comment = TaskCommentFactory(task=task, author=user)
    return task, comment


# ============================================================================
# Notification Fixtures
# ============================================================================

@pytest.fixture
def notification(db, user):
    """
    Create a notification for testing.
    
    Args:
        user: User fixture (automatically provided)
    
    Returns:
        Notification: A notification instance for the user
    
    Example:
        def test_notification_creation(notification, user):
            assert notification.user == user
            assert notification.read is False
    """
    return NotificationFactory(user=user)


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """
    Create an unauthenticated API client for testing.
    
    Returns:
        APIClient: Django REST Framework API client instance
    
    Example:
        def test_unauthenticated_request(api_client):
            response = api_client.get('/api/some-endpoint/')
            assert response.status_code == 401
    """
    return APIClient()


@pytest.fixture
def authenticated_api_client(user):
    """
    Create an authenticated API client for testing.
    
    Args:
        user: User fixture (automatically provided)
    
    Returns:
        APIClient: Authenticated API client with JWT token
    
    Example:
        def test_authenticated_request(authenticated_api_client):
            response = authenticated_api_client.get('/api/auth/profile/')
            assert response.status_code == 200
    """
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def admin_api_client(admin_user):
    """
    Create an authenticated API client for admin user.
    
    Args:
        admin_user: Admin user fixture (automatically provided)
    
    Returns:
        APIClient: Authenticated API client with admin JWT token
    
    Example:
        def test_admin_endpoint(admin_api_client):
            response = admin_api_client.get('/api/admin/endpoint/')
            assert response.status_code == 200
    """
    client = APIClient()
    refresh = RefreshToken.for_user(admin_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def manager_api_client(manager_user):
    """
    Create an authenticated API client for manager user.
    
    Args:
        manager_user: Manager user fixture (automatically provided)
    
    Returns:
        APIClient: Authenticated API client with manager JWT token
    """
    client = APIClient()
    refresh = RefreshToken.for_user(manager_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


@pytest.fixture
def developer_api_client(developer_user):
    """
    Create an authenticated API client for developer user.
    
    Args:
        developer_user: Developer user fixture (automatically provided)
    
    Returns:
        APIClient: Authenticated API client with developer JWT token
    """
    client = APIClient()
    refresh = RefreshToken.for_user(developer_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


# ============================================================================
# Complex Fixtures (Combining Multiple Models)
# ============================================================================

@pytest.fixture
def complete_project_setup(db):
    """
    Create a complete project setup with team, members, project, and tasks.
    
    This fixture creates a realistic test scenario with:
    - A team with multiple members (owner, admin, member)
    - A project belonging to the team
    - Project members with different roles
    - Multiple tasks in the project
    
    Returns:
        dict: Dictionary containing all created objects
        
    Example:
        def test_complete_workflow(complete_project_setup):
            team = complete_project_setup['team']
            project = complete_project_setup['project']
            tasks = complete_project_setup['tasks']
            assert project.team == team
            assert len(tasks) == 3
    """
    # Create team with members
    team = TeamFactory()
    owner = UserFactory()
    admin = UserFactory()
    member = UserFactory()
    
    TeamMemberFactory(team=team, user=owner, role='owner')
    TeamMemberFactory(team=team, user=admin, role='admin')
    TeamMemberFactory(team=team, user=member, role='member')
    
    # Create project
    project = ProjectFactory(team=team)
    
    # Add project members
    ProjectMemberFactory(project=project, user=owner, role='owner')
    ProjectMemberFactory(project=project, user=admin, role='admin')
    ProjectMemberFactory(project=project, user=member, role='member')
    
    # Create tasks
    tasks = [
        TaskFactory(project=project, assignee=member, created_by=owner),
        TaskFactory(project=project, assignee=admin, created_by=owner),
        TaskFactory(project=project, assignee=member, created_by=admin),
    ]
    
    return {
        'team': team,
        'project': project,
        'owner': owner,
        'admin': admin,
        'member': member,
        'tasks': tasks,
    }


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def sample_users(db):
    """
    Create a batch of sample users for testing.
    
    Returns:
        list: List of 5 User instances
    
    Example:
        def test_user_list(sample_users):
            assert len(sample_users) == 5
    """
    return UserFactory.create_batch(5)


@pytest.fixture
def sample_teams(db):
    """
    Create a batch of sample teams for testing.
    
    Returns:
        list: List of 3 Team instances
    
    Example:
        def test_team_list(sample_teams):
            assert len(sample_teams) == 3
    """
    return TeamFactory.create_batch(3)


@pytest.fixture
def sample_tasks(db, project):
    """
    Create a batch of sample tasks for testing.
    
    Args:
        project: Project fixture (automatically provided)
    
    Returns:
        list: List of 5 Task instances
    
    Example:
        def test_task_list(sample_tasks, project):
            assert len(sample_tasks) == 5
            assert all(task.project == project for task in sample_tasks)
    """
    return TaskFactory.create_batch(5, project=project)

