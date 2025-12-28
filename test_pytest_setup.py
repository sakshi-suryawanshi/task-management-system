"""
Simple test file to verify pytest setup is working correctly.

This file contains basic tests to ensure:
1. Pytest can discover and run tests
2. Database fixtures work correctly
3. Factory classes work correctly
4. API client fixtures work correctly

Run with: pytest test_pytest_setup.py -v
"""

import pytest
from django.contrib.auth import get_user_model

from factories import UserFactory, TeamFactory, ProjectFactory, TaskFactory

User = get_user_model()


@pytest.mark.django_db
def test_pytest_is_working():
    """Basic test to verify pytest is working."""
    assert True


@pytest.mark.django_db
def test_user_factory(user):
    """Test that UserFactory creates a user correctly."""
    assert user is not None
    assert user.username
    assert user.email
    assert user.is_active is True


@pytest.mark.django_db
def test_user_fixture(user):
    """Test that user fixture works correctly."""
    assert isinstance(user, User)
    assert user.pk is not None
    assert user.username
    assert user.email


@pytest.mark.django_db
def test_admin_user_fixture(admin_user):
    """Test that admin_user fixture works correctly."""
    assert admin_user.is_superuser is True
    assert admin_user.role == 'admin'


@pytest.mark.django_db
def test_team_fixture(team):
    """Test that team fixture works correctly."""
    assert team is not None
    assert team.name
    assert team.pk is not None


@pytest.mark.django_db
def test_project_fixture(project, team):
    """Test that project fixture works correctly."""
    assert project is not None
    assert project.name
    assert project.team == team
    assert project.pk is not None


@pytest.mark.django_db
def test_task_fixture(task, project, user):
    """Test that task fixture works correctly."""
    assert task is not None
    assert task.title
    assert task.project == project
    assert task.assignee == user
    assert task.pk is not None


@pytest.mark.django_db
def test_api_client_fixture(api_client):
    """Test that api_client fixture works correctly."""
    assert api_client is not None
    # Test that unauthenticated request returns 401 or 403
    response = api_client.get('/api/auth/profile/')
    assert response.status_code in [401, 403]


@pytest.mark.django_db
def test_authenticated_api_client_fixture(authenticated_api_client, user):
    """Test that authenticated_api_client fixture works correctly."""
    assert authenticated_api_client is not None
    # Test that authenticated request works
    response = authenticated_api_client.get('/api/auth/profile/')
    assert response.status_code == 200
    assert response.data['username'] == user.username


@pytest.mark.django_db
def test_factories_create_objects():
    """Test that factories can create objects directly."""
    user = UserFactory()
    assert user.pk is not None
    
    team = TeamFactory()
    assert team.pk is not None
    
    project = ProjectFactory(team=team)
    assert project.pk is not None
    assert project.team == team
    
    task = TaskFactory(project=project)
    assert task.pk is not None
    assert task.project == project


@pytest.mark.django_db
def test_team_with_members_fixture(team_with_members):
    """Test that team_with_members fixture works correctly."""
    team, owner, admin, member = team_with_members
    assert team.get_member_count() == 3
    assert team.is_owner(owner) is True
    assert team.is_admin(admin) is True
    assert team.is_member(member) is True


@pytest.mark.django_db
def test_complete_project_setup_fixture(complete_project_setup):
    """Test that complete_project_setup fixture works correctly."""
    setup = complete_project_setup
    assert 'team' in setup
    assert 'project' in setup
    assert 'tasks' in setup
    assert 'owner' in setup
    assert 'admin' in setup
    assert 'member' in setup
    
    assert len(setup['tasks']) == 3
    assert setup['project'].team == setup['team']
    assert all(task.project == setup['project'] for task in setup['tasks'])

