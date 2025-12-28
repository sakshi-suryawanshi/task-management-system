"""
Model tests for Project and ProjectMember models.

This module contains comprehensive tests for the Project and ProjectMember models,
including field validation, model methods, relationships, and edge cases.
"""

import pytest
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from projects.models import Project, ProjectMember
from factories import (
    ProjectFactory, ActiveProjectFactory, CompletedProjectFactory,
    ProjectMemberFactory, TeamFactory, TeamMemberFactory, UserFactory
)


# ============================================================================
# Project Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestProjectModel:
    """Test suite for Project model."""
    
    def test_project_creation(self):
        """Test basic project creation with required fields."""
        team = TeamFactory()
        project = ProjectFactory(
            name='Test Project',
            description='Project description',
            team=team
        )
        
        assert project.name == 'Test Project'
        assert project.description == 'Project description'
        assert project.team == team
        assert project.pk is not None
    
    def test_project_str_representation(self):
        """Test string representation of Project model."""
        team = TeamFactory(name='Test Team')
        project = ProjectFactory(name='Test Project', team=team)
        assert 'Test Project' in str(project)
        assert 'Test Team' in str(project)
    
    def test_project_unique_together_team_and_name(self):
        """Test that project name must be unique within a team."""
        team = TeamFactory()
        ProjectFactory(name='Unique Project', team=team)
        
        # Same name in same team should fail
        with pytest.raises(IntegrityError):
            ProjectFactory(name='Unique Project', team=team)
        
        # Same name in different team should work
        team2 = TeamFactory()
        project2 = ProjectFactory(name='Unique Project', team=team2)
        assert project2.pk is not None
    
    def test_project_default_status(self):
        """Test that status defaults to 'planning'."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        # Note: Factory may set status explicitly, so test default in model
        project = Project(team=team, name='New Project')
        assert project.status == Project.STATUS_PLANNING
    
    def test_project_status_choices(self):
        """Test status field choices."""
        team = TeamFactory()
        statuses = ['planning', 'active', 'on_hold', 'completed', 'cancelled']
        
        for status in statuses:
            project = ProjectFactory(team=team, status=status)
            assert project.status == status
            assert project.get_status_display() in [
                'Planning', 'Active', 'On Hold', 'Completed', 'Cancelled'
            ]
    
    def test_project_default_priority(self):
        """Test that priority defaults to 'medium'."""
        team = TeamFactory()
        project = Project(team=team, name='New Project')
        assert project.priority == Project.PRIORITY_MEDIUM
    
    def test_project_priority_choices(self):
        """Test priority field choices."""
        team = TeamFactory()
        priorities = ['high', 'medium', 'low']
        
        for priority in priorities:
            project = ProjectFactory(team=team, priority=priority)
            assert project.priority == priority
            assert project.get_priority_display() in ['High', 'Medium', 'Low']
    
    def test_project_can_have_null_deadline(self):
        """Test that deadline field can be null."""
        team = TeamFactory()
        project = ProjectFactory(team=team, deadline=None)
        assert project.deadline is None
        assert project.pk is not None
    
    def test_project_can_have_deadline(self):
        """Test that deadline field can be set."""
        team = TeamFactory()
        deadline = timezone.now() + timedelta(days=30)
        project = ProjectFactory(team=team, deadline=deadline)
        assert project.deadline == deadline
    
    def test_project_can_have_empty_description(self):
        """Test that description field can be empty."""
        team = TeamFactory()
        project = ProjectFactory(team=team, description='')
        assert project.description == ''
        assert project.pk is not None
    
    def test_project_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        after = timezone.now()
        
        assert project.created_at is not None
        assert before <= project.created_at <= after
    
    def test_project_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        initial_updated_at = project.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        project.name = 'Updated Name'
        project.save()
        
        assert project.updated_at > initial_updated_at
    
    def test_project_ordering(self):
        """Test that projects are ordered by created_at descending."""
        team = TeamFactory()
        project1 = ProjectFactory(team=team)
        project2 = ProjectFactory(team=team)
        project3 = ProjectFactory(team=team)
        
        projects = list(Project.objects.filter(team=team)[:3])
        # Should be ordered by -created_at (newest first)
        assert projects[0].created_at >= projects[1].created_at
        assert projects[1].created_at >= projects[2].created_at
    
    def test_project_get_members_empty(self):
        """Test get_members method when project has no members."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        members = project.get_members()
        assert members.count() == 0
    
    def test_project_get_members(self):
        """Test get_members method returns all project members."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        ProjectMemberFactory(project=project, user=user1, role='owner')
        ProjectMemberFactory(project=project, user=user2, role='admin')
        ProjectMemberFactory(project=project, user=user3, role='member')
        
        members = project.get_members()
        assert members.count() == 3
    
    def test_project_get_member_count(self):
        """Test get_member_count method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        assert project.get_member_count() == 0
        
        ProjectMemberFactory(project=project, user=UserFactory())
        assert project.get_member_count() == 1
        
        ProjectMemberFactory(project=project, user=UserFactory())
        assert project.get_member_count() == 2
    
    def test_project_get_owner(self):
        """Test get_owner method returns project owner."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        
        project_owner = project.get_owner()
        assert project_owner is not None
        assert project_owner.user == owner
        assert project_owner.role == 'owner'
    
    def test_project_get_owner_none(self):
        """Test get_owner method returns None when no owner exists."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        admin = UserFactory()
        ProjectMemberFactory(project=project, user=admin, role='admin')
        
        owner = project.get_owner()
        assert owner is None
    
    def test_project_get_admins(self):
        """Test get_admins method returns all admin members."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin1 = UserFactory()
        admin2 = UserFactory()
        member = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin1, role='admin')
        ProjectMemberFactory(project=project, user=admin2, role='admin')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        admins = project.get_admins()
        assert admins.count() == 2
        assert all(member.role == 'admin' for member in admins)
    
    def test_project_get_regular_members(self):
        """Test get_regular_members method returns only regular members."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member1 = UserFactory()
        member2 = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        ProjectMemberFactory(project=project, user=member1, role='member')
        ProjectMemberFactory(project=project, user=member2, role='member')
        
        regular_members = project.get_regular_members()
        assert regular_members.count() == 2
        assert all(member.role == 'member' for member in regular_members)
    
    def test_project_is_member(self):
        """Test is_member method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        member_user = UserFactory()
        non_member_user = UserFactory()
        
        ProjectMemberFactory(project=project, user=member_user, role='member')
        
        assert project.is_member(member_user) is True
        assert project.is_member(non_member_user) is False
    
    def test_project_get_member_role(self):
        """Test get_member_role method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        non_member = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        assert project.get_member_role(owner) == 'owner'
        assert project.get_member_role(admin) == 'admin'
        assert project.get_member_role(member) == 'member'
        assert project.get_member_role(non_member) is None
    
    def test_project_is_owner(self):
        """Test is_owner method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        assert project.is_owner(owner) is True
        assert project.is_owner(admin) is False
        assert project.is_owner(member) is False
    
    def test_project_is_admin(self):
        """Test is_admin method checks for admin or owner."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        assert project.is_admin(owner) is True
        assert project.is_admin(admin) is True
        assert project.is_admin(member) is False
    
    def test_project_has_admin_access(self):
        """Test has_admin_access method (alias for is_admin)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        ProjectMemberFactory(project=project, user=owner, role='owner')
        ProjectMemberFactory(project=project, user=admin, role='admin')
        ProjectMemberFactory(project=project, user=member, role='member')
        
        assert project.has_admin_access(owner) is True
        assert project.has_admin_access(admin) is True
        assert project.has_admin_access(member) is False
    
    def test_project_is_overdue_no_deadline(self):
        """Test is_overdue method when project has no deadline."""
        team = TeamFactory()
        project = ProjectFactory(team=team, deadline=None)
        assert project.is_overdue() is False
    
    def test_project_is_overdue_future_deadline(self):
        """Test is_overdue method when deadline is in the future."""
        team = TeamFactory()
        future_deadline = timezone.now() + timedelta(days=7)
        project = ProjectFactory(team=team, deadline=future_deadline, status='active')
        assert project.is_overdue() is False
    
    def test_project_is_overdue_past_deadline_active(self):
        """Test is_overdue method when deadline has passed and project is active."""
        team = TeamFactory()
        past_deadline = timezone.now() - timedelta(days=7)
        project = ProjectFactory(team=team, deadline=past_deadline, status='active')
        assert project.is_overdue() is True
    
    def test_project_is_overdue_past_deadline_completed(self):
        """Test is_overdue method when deadline has passed but project is completed."""
        team = TeamFactory()
        past_deadline = timezone.now() - timedelta(days=7)
        project = ProjectFactory(team=team, deadline=past_deadline, status='completed')
        assert project.is_overdue() is False
    
    def test_project_is_active(self):
        """Test is_active method."""
        team = TeamFactory()
        active_project = ActiveProjectFactory(team=team)
        completed_project = CompletedProjectFactory(team=team)
        
        assert active_project.is_active() is True
        assert completed_project.is_active() is False
    
    def test_project_is_completed(self):
        """Test is_completed method."""
        team = TeamFactory()
        active_project = ActiveProjectFactory(team=team)
        completed_project = CompletedProjectFactory(team=team)
        
        assert active_project.is_completed() is False
        assert completed_project.is_completed() is True
    
    def test_project_get_status_display_class(self):
        """Test get_status_display_class method."""
        team = TeamFactory()
        status_classes = {
            'planning': 'planning',
            'active': 'active',
            'on_hold': 'on-hold',
            'completed': 'completed',
            'cancelled': 'cancelled',
        }
        
        for status, expected_class in status_classes.items():
            project = ProjectFactory(team=team, status=status)
            assert project.get_status_display_class() == expected_class
    
    def test_project_get_priority_display_class(self):
        """Test get_priority_display_class method."""
        team = TeamFactory()
        priority_classes = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
        }
        
        for priority, expected_class in priority_classes.items():
            project = ProjectFactory(team=team, priority=priority)
            assert project.get_priority_display_class() == expected_class
    
    def test_project_cascade_delete_on_team_delete(self):
        """Test that project is deleted when team is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        project_id = project.id
        
        team.delete()
        
        # Project should be deleted (cascade)
        assert not Project.objects.filter(id=project_id).exists()


# ============================================================================
# ProjectMember Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestProjectMemberModel:
    """Test suite for ProjectMember model."""
    
    def test_projectmember_creation(self):
        """Test basic ProjectMember creation."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        member = ProjectMemberFactory(
            project=project,
            user=user,
            role='owner'
        )
        
        assert member.project == project
        assert member.user == user
        assert member.role == 'owner'
        assert member.pk is not None
    
    def test_projectmember_str_representation(self):
        """Test string representation of ProjectMember model."""
        team = TeamFactory()
        project = ProjectFactory(name='Test Project', team=team)
        user = UserFactory(username='testuser')
        member = ProjectMemberFactory(project=project, user=user, role='admin')
        
        assert 'testuser' in str(member)
        assert 'Test Project' in str(member)
        assert 'Admin' in str(member)
    
    def test_projectmember_unique_together(self):
        """Test that project and user combination must be unique."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        ProjectMemberFactory(project=project, user=user, role='owner')
        
        # Should not be able to create duplicate membership
        with pytest.raises(IntegrityError):
            ProjectMemberFactory(project=project, user=user, role='admin')
    
    def test_projectmember_role_choices(self):
        """Test role field choices."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        roles = ['owner', 'admin', 'member']
        
        for role in roles:
            member = ProjectMemberFactory(project=project, user=user, role=role)
            # Create new user for each role to avoid unique constraint
            user = UserFactory()
            assert member.role == role
    
    def test_projectmember_default_role(self):
        """Test that role defaults to 'member'."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        member = ProjectMember(project=project, user=user)
        assert member.role == ProjectMember.ROLE_MEMBER
    
    def test_projectmember_joined_at_auto_set(self):
        """Test that joined_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        member = ProjectMemberFactory(project=project, user=user)
        after = timezone.now()
        
        assert member.joined_at is not None
        assert before <= member.joined_at <= after
    
    def test_projectmember_ordering(self):
        """Test that ProjectMembers are ordered by joined_at descending."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        member1 = ProjectMemberFactory(project=project, user=user1)
        member2 = ProjectMemberFactory(project=project, user=user2)
        member3 = ProjectMemberFactory(project=project, user=user3)
        
        members = list(ProjectMember.objects.filter(project=project)[:3])
        # Should be ordered by -joined_at (newest first)
        assert members[0].joined_at >= members[1].joined_at
        assert members[1].joined_at >= members[2].joined_at
    
    def test_projectmember_is_owner(self):
        """Test is_owner method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = ProjectMemberFactory(project=project, user=owner, role='owner')
        admin_member = ProjectMemberFactory(project=project, user=admin, role='admin')
        member_member = ProjectMemberFactory(project=project, user=member, role='member')
        
        assert owner_member.is_owner() is True
        assert admin_member.is_owner() is False
        assert member_member.is_owner() is False
    
    def test_projectmember_is_admin(self):
        """Test is_admin method checks for admin or owner."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = ProjectMemberFactory(project=project, user=owner, role='owner')
        admin_member = ProjectMemberFactory(project=project, user=admin, role='admin')
        member_member = ProjectMemberFactory(project=project, user=member, role='member')
        
        assert owner_member.is_admin() is True
        assert admin_member.is_admin() is True
        assert member_member.is_admin() is False
    
    def test_projectmember_is_regular_member(self):
        """Test is_regular_member method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = ProjectMemberFactory(project=project, user=owner, role='owner')
        admin_member = ProjectMemberFactory(project=project, user=admin, role='admin')
        member_member = ProjectMemberFactory(project=project, user=member, role='member')
        
        assert owner_member.is_regular_member() is False
        assert admin_member.is_regular_member() is False
        assert member_member.is_regular_member() is True
    
    def test_projectmember_has_admin_access(self):
        """Test has_admin_access method (alias for is_admin)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = ProjectMemberFactory(project=project, user=owner, role='owner')
        admin_member = ProjectMemberFactory(project=project, user=admin, role='admin')
        member_member = ProjectMemberFactory(project=project, user=member, role='member')
        
        assert owner_member.has_admin_access() is True
        assert admin_member.has_admin_access() is True
        assert member_member.has_admin_access() is False
    
    def test_projectmember_cascade_delete_on_project_delete(self):
        """Test that ProjectMember is deleted when project is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        member = ProjectMemberFactory(project=project, user=user)
        member_id = member.id
        
        project.delete()
        
        # ProjectMember should be deleted (cascade)
        assert not ProjectMember.objects.filter(id=member_id).exists()
    
    def test_projectmember_cascade_delete_on_user_delete(self):
        """Test that ProjectMember is deleted when user is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        member = ProjectMemberFactory(project=project, user=user)
        member_id = member.id
        
        user.delete()
        
        # ProjectMember should be deleted (cascade)
        assert not ProjectMember.objects.filter(id=member_id).exists()


# ============================================================================
# API Tests - Project Endpoints
# ============================================================================

@pytest.mark.django_db
@pytest.mark.api
class TestProjectListCreateAPI:
    """Test suite for project list and create API endpoints."""
    
    def test_list_projects_authenticated(self, authenticated_api_client, project_with_members):
        """Test listing projects when authenticated and member."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/projects/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1
        project_names = [p['name'] for p in response.data]
        assert project.name in project_names
    
    def test_list_projects_unauthenticated(self, api_client):
        """Test listing projects fails when unauthenticated."""
        url = '/api/projects/'
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_list_projects_filter_by_team(self, authenticated_api_client, project_with_members):
        """Test listing projects filtered by team."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/?team={project.team.id}'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1
    
    def test_list_projects_filter_by_status(self, authenticated_api_client, project_with_members):
        """Test listing projects filtered by status."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/?status={project.status}'
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_create_project_success(self, authenticated_api_client, team_with_members):
        """Test successful project creation."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/projects/'
        data = {
            'name': 'New Project',
            'description': 'Project description',
            'team': team.id,
            'status': 'planning',
            'priority': 'high'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'data' in response.data
        assert response.data['data']['name'] == 'New Project'
        assert response.data['message'] == 'Project created successfully'
        # Creator should be automatically added as owner
        assert response.data['data']['member_count'] == 1
    
    def test_create_project_unauthenticated(self, api_client, team):
        """Test project creation fails when unauthenticated."""
        url = '/api/projects/'
        data = {'name': 'New Project', 'team': team.id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.api
class TestProjectDetailAPI:
    """Test suite for project detail, update, and delete API endpoints."""
    
    def test_get_project_detail_success(self, authenticated_api_client, project_with_members):
        """Test retrieving project details."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['name'] == project.name
    
    def test_get_project_detail_not_member(self, authenticated_api_client, project, user):
        """Test retrieving project details fails when not a member."""
        url = f'/api/projects/{project.id}/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 404
    
    def test_update_project_put_success(self, authenticated_api_client, project_with_members):
        """Test full project update using PUT."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        data = {
            'name': 'Updated Project',
            'description': 'Updated description',
            'team': project.team.id,
            'status': 'active',
            'priority': 'high'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['name'] == 'Updated Project'
        assert response.data['message'] == 'Project updated successfully'
    
    def test_update_project_patch_success(self, authenticated_api_client, project_with_members):
        """Test partial project update using PATCH."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        data = {'status': 'active'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['status'] == 'active'
    
    def test_update_project_as_member_forbidden(self, authenticated_api_client, project_with_members):
        """Test project update fails when user is only a member."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        data = {'description': 'Unauthorized update'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 403
    
    def test_delete_project_as_owner_success(self, authenticated_api_client, project_with_members):
        """Test project deletion by owner."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204
    
    def test_delete_project_as_admin_forbidden(self, authenticated_api_client, project_with_members):
        """Test project deletion fails when user is admin (not owner)."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(admin)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/'
        response = client.delete(url)
        
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.api
class TestProjectMemberAPI:
    """Test suite for project member management API endpoints."""
    
    def test_add_project_member_success(self, authenticated_api_client, project_with_members):
        """Test adding a new member to project."""
        project, owner, admin, member = project_with_members
        # Ensure new user is in the team
        from teams.models import TeamMember
        new_user = UserFactory()
        TeamMemberFactory(team=project.team, user=new_user, role='member')
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/members/'
        data = {
            'user_id': new_user.id,
            'role': 'member'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['data']['user'] == new_user.id
        assert response.data['message'] == 'Member added successfully'
    
    def test_add_project_member_not_in_team_forbidden(self, authenticated_api_client, project_with_members):
        """Test adding member fails when user is not in project's team."""
        project, owner, admin, member = project_with_members
        new_user = UserFactory()  # Not in team
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/members/'
        data = {'user_id': new_user.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_update_project_member_role_success(self, authenticated_api_client, project_with_members):
        """Test updating project member role."""
        project, owner, admin, member = project_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/members/{member.id}/'
        data = {'role': 'admin'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['role'] == 'admin'
    
    def test_remove_project_member_success(self, authenticated_api_client, project_with_members):
        """Test removing a project member."""
        project, owner, admin, member = project_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/members/{member.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.api
class TestProjectStatsAPI:
    """Test suite for project statistics API endpoint."""
    
    def test_get_project_stats_success(self, authenticated_api_client, project_with_members):
        """Test retrieving project statistics."""
        project, owner, admin, member = project_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/projects/{project.id}/stats/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert 'task_statistics' in response.data['data']
        assert 'member_activity' in response.data['data']
        assert response.data['data']['project_id'] == project.id
        assert response.data['message'] == 'Project statistics retrieved successfully'
    
    def test_get_project_stats_not_member(self, authenticated_api_client, project, user):
        """Test retrieving project stats fails when not a member."""
        url = f'/api/projects/{project.id}/stats/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 404
