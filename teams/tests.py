"""
Model tests for Team and TeamMember models.

This module contains comprehensive tests for the Team and TeamMember models,
including field validation, model methods, relationships, and edge cases.
"""

import pytest
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from teams.models import Team, TeamMember
from factories import TeamFactory, TeamMemberFactory, UserFactory


# ============================================================================
# Team Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTeamModel:
    """Test suite for Team model."""
    
    def test_team_creation(self):
        """Test basic team creation with required fields."""
        team = TeamFactory(
            name='Development Team',
            description='Team responsible for development'
        )
        
        assert team.name == 'Development Team'
        assert team.description == 'Team responsible for development'
        assert team.pk is not None
    
    def test_team_str_representation(self):
        """Test string representation of Team model."""
        team = TeamFactory(name='Test Team')
        assert str(team) == 'Test Team'
    
    def test_team_name_unique(self):
        """Test that team name must be unique."""
        TeamFactory(name='Unique Team')
        
        with pytest.raises(IntegrityError):
            TeamFactory(name='Unique Team')
    
    def test_team_name_indexed(self):
        """Test that name field is indexed for faster lookups."""
        team = TeamFactory(name='Indexed Team')
        found_team = Team.objects.get(name='Indexed Team')
        assert found_team == team
    
    def test_team_can_have_empty_description(self):
        """Test that description field can be empty."""
        team = TeamFactory(description='')
        assert team.description == ''
        assert team.pk is not None
    
    def test_team_description_max_length(self):
        """Test that description field has max_length constraint."""
        long_description = 'x' * 501  # Exceeds max_length=500
        team = TeamFactory.build(description=long_description)
        with pytest.raises(Exception):  # Will fail on save
            team.save()
    
    def test_team_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        after = timezone.now()
        
        assert team.created_at is not None
        assert before <= team.created_at <= after
    
    def test_team_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        team = TeamFactory()
        initial_updated_at = team.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        team.name = 'Updated Name'
        team.save()
        
        assert team.updated_at > initial_updated_at
    
    def test_team_ordering(self):
        """Test that teams are ordered by created_at descending."""
        team1 = TeamFactory()
        team2 = TeamFactory()
        team3 = TeamFactory()
        
        teams = list(Team.objects.all()[:3])
        # Should be ordered by -created_at (newest first)
        assert teams[0].created_at >= teams[1].created_at
        assert teams[1].created_at >= teams[2].created_at
    
    def test_team_get_members_empty(self):
        """Test get_members method when team has no members."""
        team = TeamFactory()
        members = team.get_members()
        assert members.count() == 0
    
    def test_team_get_members(self):
        """Test get_members method returns all team members."""
        team = TeamFactory()
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        TeamMemberFactory(team=team, user=user1, role='owner')
        TeamMemberFactory(team=team, user=user2, role='admin')
        TeamMemberFactory(team=team, user=user3, role='member')
        
        members = team.get_members()
        assert members.count() == 3
    
    def test_team_get_member_count(self):
        """Test get_member_count method."""
        team = TeamFactory()
        assert team.get_member_count() == 0
        
        TeamMemberFactory(team=team, user=UserFactory())
        assert team.get_member_count() == 1
        
        TeamMemberFactory(team=team, user=UserFactory())
        assert team.get_member_count() == 2
    
    def test_team_get_owner(self):
        """Test get_owner method returns team owner."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        
        team_owner = team.get_owner()
        assert team_owner is not None
        assert team_owner.user == owner
        assert team_owner.role == 'owner'
    
    def test_team_get_owner_none(self):
        """Test get_owner method returns None when no owner exists."""
        team = TeamFactory()
        admin = UserFactory()
        TeamMemberFactory(team=team, user=admin, role='admin')
        
        owner = team.get_owner()
        assert owner is None
    
    def test_team_get_admins(self):
        """Test get_admins method returns all admin members."""
        team = TeamFactory()
        owner = UserFactory()
        admin1 = UserFactory()
        admin2 = UserFactory()
        member = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin1, role='admin')
        TeamMemberFactory(team=team, user=admin2, role='admin')
        TeamMemberFactory(team=team, user=member, role='member')
        
        admins = team.get_admins()
        assert admins.count() == 2
        assert all(member.role == 'admin' for member in admins)
        assert owner not in [admin.user for admin in admins]  # Owner is separate
    
    def test_team_get_regular_members(self):
        """Test get_regular_members method returns only regular members."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member1 = UserFactory()
        member2 = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        TeamMemberFactory(team=team, user=member1, role='member')
        TeamMemberFactory(team=team, user=member2, role='member')
        
        regular_members = team.get_regular_members()
        assert regular_members.count() == 2
        assert all(member.role == 'member' for member in regular_members)
    
    def test_team_is_member(self):
        """Test is_member method."""
        team = TeamFactory()
        member_user = UserFactory()
        non_member_user = UserFactory()
        
        TeamMemberFactory(team=team, user=member_user, role='member')
        
        assert team.is_member(member_user) is True
        assert team.is_member(non_member_user) is False
    
    def test_team_get_member_role(self):
        """Test get_member_role method."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        non_member = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        TeamMemberFactory(team=team, user=member, role='member')
        
        assert team.get_member_role(owner) == 'owner'
        assert team.get_member_role(admin) == 'admin'
        assert team.get_member_role(member) == 'member'
        assert team.get_member_role(non_member) is None
    
    def test_team_is_owner(self):
        """Test is_owner method."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        TeamMemberFactory(team=team, user=member, role='member')
        
        assert team.is_owner(owner) is True
        assert team.is_owner(admin) is False
        assert team.is_owner(member) is False
    
    def test_team_is_admin(self):
        """Test is_admin method checks for admin or owner."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        TeamMemberFactory(team=team, user=member, role='member')
        
        assert team.is_admin(owner) is True
        assert team.is_admin(admin) is True
        assert team.is_admin(member) is False
    
    def test_team_has_admin_access(self):
        """Test has_admin_access method (alias for is_admin)."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        TeamMemberFactory(team=team, user=owner, role='owner')
        TeamMemberFactory(team=team, user=admin, role='admin')
        TeamMemberFactory(team=team, user=member, role='member')
        
        assert team.has_admin_access(owner) is True
        assert team.has_admin_access(admin) is True
        assert team.has_admin_access(member) is False


# ============================================================================
# TeamMember Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTeamMemberModel:
    """Test suite for TeamMember model."""
    
    def test_teammember_creation(self):
        """Test basic TeamMember creation."""
        team = TeamFactory()
        user = UserFactory()
        member = TeamMemberFactory(
            team=team,
            user=user,
            role='owner'
        )
        
        assert member.team == team
        assert member.user == user
        assert member.role == 'owner'
        assert member.pk is not None
    
    def test_teammember_str_representation(self):
        """Test string representation of TeamMember model."""
        team = TeamFactory(name='Test Team')
        user = UserFactory(username='testuser')
        member = TeamMemberFactory(team=team, user=user, role='admin')
        
        assert 'testuser' in str(member)
        assert 'Test Team' in str(member)
        assert 'Admin' in str(member)
    
    def test_teammember_unique_together(self):
        """Test that team and user combination must be unique."""
        team = TeamFactory()
        user = UserFactory()
        TeamMemberFactory(team=team, user=user, role='owner')
        
        # Should not be able to create duplicate membership
        with pytest.raises(IntegrityError):
            TeamMemberFactory(team=team, user=user, role='admin')
    
    def test_teammember_role_choices(self):
        """Test role field choices."""
        team = TeamFactory()
        user = UserFactory()
        roles = ['owner', 'admin', 'member']
        
        for role in roles:
            member = TeamMemberFactory(team=team, user=user, role=role)
            # Create new user for each role to avoid unique constraint
            user = UserFactory()
            assert member.role == role
    
    def test_teammember_default_role(self):
        """Test that role defaults to 'member'."""
        team = TeamFactory()
        user = UserFactory()
        member = TeamMemberFactory(team=team, user=user)
        # Note: Factory sets role explicitly, so test default in model
        member = TeamMember(team=team, user=user)
        assert member.role == TeamMember.ROLE_MEMBER
    
    def test_teammember_joined_at_auto_set(self):
        """Test that joined_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        user = UserFactory()
        member = TeamMemberFactory(team=team, user=user)
        after = timezone.now()
        
        assert member.joined_at is not None
        assert before <= member.joined_at <= after
    
    def test_teammember_ordering(self):
        """Test that TeamMembers are ordered by joined_at descending."""
        team = TeamFactory()
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        member1 = TeamMemberFactory(team=team, user=user1)
        member2 = TeamMemberFactory(team=team, user=user2)
        member3 = TeamMemberFactory(team=team, user=user3)
        
        members = list(TeamMember.objects.filter(team=team)[:3])
        # Should be ordered by -joined_at (newest first)
        assert members[0].joined_at >= members[1].joined_at
        assert members[1].joined_at >= members[2].joined_at
    
    def test_teammember_is_owner(self):
        """Test is_owner method."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = TeamMemberFactory(team=team, user=owner, role='owner')
        admin_member = TeamMemberFactory(team=team, user=admin, role='admin')
        member_member = TeamMemberFactory(team=team, user=member, role='member')
        
        assert owner_member.is_owner() is True
        assert admin_member.is_owner() is False
        assert member_member.is_owner() is False
    
    def test_teammember_is_admin(self):
        """Test is_admin method checks for admin or owner."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = TeamMemberFactory(team=team, user=owner, role='owner')
        admin_member = TeamMemberFactory(team=team, user=admin, role='admin')
        member_member = TeamMemberFactory(team=team, user=member, role='member')
        
        assert owner_member.is_admin() is True
        assert admin_member.is_admin() is True
        assert member_member.is_admin() is False
    
    def test_teammember_is_regular_member(self):
        """Test is_regular_member method."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = TeamMemberFactory(team=team, user=owner, role='owner')
        admin_member = TeamMemberFactory(team=team, user=admin, role='admin')
        member_member = TeamMemberFactory(team=team, user=member, role='member')
        
        assert owner_member.is_regular_member() is False
        assert admin_member.is_regular_member() is False
        assert member_member.is_regular_member() is True
    
    def test_teammember_has_admin_access(self):
        """Test has_admin_access method (alias for is_admin)."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        member = UserFactory()
        
        owner_member = TeamMemberFactory(team=team, user=owner, role='owner')
        admin_member = TeamMemberFactory(team=team, user=admin, role='admin')
        member_member = TeamMemberFactory(team=team, user=member, role='member')
        
        assert owner_member.has_admin_access() is True
        assert admin_member.has_admin_access() is True
        assert member_member.has_admin_access() is False
    
    def test_teammember_cascade_delete_on_team_delete(self):
        """Test that TeamMember is deleted when team is deleted."""
        team = TeamFactory()
        user = UserFactory()
        member = TeamMemberFactory(team=team, user=user)
        member_id = member.id
        
        team.delete()
        
        # TeamMember should be deleted (cascade)
        assert not TeamMember.objects.filter(id=member_id).exists()
    
    def test_teammember_cascade_delete_on_user_delete(self):
        """Test that TeamMember is deleted when user is deleted."""
        team = TeamFactory()
        user = UserFactory()
        member = TeamMemberFactory(team=team, user=user)
        member_id = member.id
        
        user.delete()
        
        # TeamMember should be deleted (cascade)
        assert not TeamMember.objects.filter(id=member_id).exists()
    
    def test_teammember_role_indexed(self):
        """Test that role field is indexed for faster lookups."""
        team = TeamFactory()
        owner = UserFactory()
        admin = UserFactory()
        
        owner_member = TeamMemberFactory(team=team, user=owner, role='owner')
        admin_member = TeamMemberFactory(team=team, user=admin, role='admin')
        
        owners = TeamMember.objects.filter(role='owner')
        assert owner_member in owners
        assert admin_member not in owners


# ============================================================================
# API Tests - Team Endpoints
# ============================================================================

@pytest.mark.django_db
@pytest.mark.api
class TestTeamListCreateAPI:
    """Test suite for team list and create API endpoints."""
    
    def test_list_teams_authenticated(self, authenticated_api_client, team_with_members):
        """Test listing teams when authenticated and member."""
        team, owner, admin, member = team_with_members
        # Authenticate as owner
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/teams/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1
        team_names = [t['name'] for t in response.data]
        assert team.name in team_names
    
    def test_list_teams_unauthenticated(self, api_client):
        """Test listing teams fails when unauthenticated."""
        url = '/api/teams/'
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_list_teams_empty_for_non_member(self, authenticated_api_client, user):
        """Test listing teams returns empty for user not in any team."""
        url = '/api/teams/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) == 0
    
    def test_create_team_success(self, authenticated_api_client, user):
        """Test successful team creation."""
        url = '/api/teams/'
        data = {
            'name': 'New Team',
            'description': 'Team description'
        }
        
        response = authenticated_api_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'data' in response.data
        assert response.data['data']['name'] == 'New Team'
        assert response.data['data']['description'] == 'Team description'
        assert response.data['message'] == 'Team created successfully'
        # Creator should be automatically added as owner
        assert response.data['data']['member_count'] == 1
    
    def test_create_team_minimal_fields(self, authenticated_api_client, user):
        """Test team creation with only required fields."""
        url = '/api/teams/'
        data = {'name': 'Minimal Team'}
        
        response = authenticated_api_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['data']['name'] == 'Minimal Team'
    
    def test_create_team_duplicate_name(self, authenticated_api_client, team):
        """Test team creation fails with duplicate name."""
        url = '/api/teams/'
        data = {'name': team.name}
        
        response = authenticated_api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'name' in response.data
    
    def test_create_team_unauthenticated(self, api_client):
        """Test team creation fails when unauthenticated."""
        url = '/api/teams/'
        data = {'name': 'New Team'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401
    
    def test_list_teams_search(self, authenticated_api_client, team_with_members):
        """Test team list with search filter."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/teams/?search=' + team.name
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1


@pytest.mark.django_db
@pytest.mark.api
class TestTeamDetailAPI:
    """Test suite for team detail, update, and delete API endpoints."""
    
    def test_get_team_detail_success(self, authenticated_api_client, team_with_members):
        """Test retrieving team details."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['name'] == team.name
    
    def test_get_team_detail_not_member(self, authenticated_api_client, team, user):
        """Test retrieving team details fails when not a member."""
        url = f'/api/teams/{team.id}/'
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 404
    
    def test_update_team_put_success(self, authenticated_api_client, team_with_members):
        """Test full team update using PUT."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        data = {
            'name': 'Updated Team Name',
            'description': 'Updated description'
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['name'] == 'Updated Team Name'
        assert response.data['message'] == 'Team updated successfully'
    
    def test_update_team_patch_success(self, authenticated_api_client, team_with_members):
        """Test partial team update using PATCH."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        data = {'description': 'Patched description'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['description'] == 'Patched description'
    
    def test_update_team_as_member_forbidden(self, authenticated_api_client, team_with_members):
        """Test team update fails when user is only a member (not admin/owner)."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        data = {'description': 'Unauthorized update'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 403
    
    def test_delete_team_as_owner_success(self, authenticated_api_client, team_with_members):
        """Test team deletion by owner."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204
    
    def test_delete_team_as_admin_forbidden(self, authenticated_api_client, team_with_members):
        """Test team deletion fails when user is admin (not owner)."""
        team, owner, admin, member = team_with_members
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(admin)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/'
        response = client.delete(url)
        
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.api
class TestTeamMemberAPI:
    """Test suite for team member management API endpoints."""
    
    def test_add_team_member_success(self, authenticated_api_client, team_with_members):
        """Test adding a new member to team."""
        team, owner, admin, member = team_with_members
        new_user = UserFactory()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/'
        data = {
            'user_id': new_user.id,
            'role': 'member'
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['data']['user'] == new_user.id
        assert response.data['message'] == 'Member added successfully'
    
    def test_add_team_member_as_member_forbidden(self, authenticated_api_client, team_with_members):
        """Test adding member fails when user is only a member."""
        team, owner, admin, member = team_with_members
        new_user = UserFactory()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/'
        data = {'user_id': new_user.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 403
    
    def test_add_team_member_duplicate(self, authenticated_api_client, team_with_members):
        """Test adding member fails when user is already a member."""
        team, owner, admin, member = team_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/'
        data = {'user_id': member.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_update_team_member_role_success(self, authenticated_api_client, team_with_members):
        """Test updating team member role."""
        team, owner, admin, member = team_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/{member.id}/'
        data = {'role': 'admin'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['role'] == 'admin'
        assert response.data['message'] == 'Member role updated successfully'
    
    def test_update_team_member_role_owner_forbidden(self, authenticated_api_client, team_with_members):
        """Test updating owner role fails."""
        team, owner, admin, member = team_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(admin)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/{owner.id}/'
        data = {'role': 'member'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 400
    
    def test_remove_team_member_success(self, authenticated_api_client, team_with_members):
        """Test removing a team member."""
        team, owner, admin, member = team_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/{member.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204
    
    def test_remove_team_member_owner_forbidden(self, authenticated_api_client, team_with_members):
        """Test removing team owner fails."""
        team, owner, admin, member = team_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(admin)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/teams/{team.id}/members/{owner.id}/'
        response = client.delete(url)
        
        assert response.status_code == 400
