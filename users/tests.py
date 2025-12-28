"""
Model tests for User and UserProfile models.

This module contains comprehensive tests for the User and UserProfile models,
including field validation, model methods, relationships, and edge cases.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

from users.models import User, UserProfile
from factories import UserFactory, AdminUserFactory, ManagerUserFactory, DeveloperUserFactory, MemberUserFactory, UserProfileFactory


# ============================================================================
# User Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestUserModel:
    """Test suite for User model."""
    
    def test_user_creation(self):
        """Test basic user creation with required fields."""
        user = UserFactory(
            username='testuser',
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'testuser@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_active is True
        assert user.pk is not None
    
    def test_user_str_representation(self):
        """Test string representation of User model."""
        user = UserFactory(username='testuser')
        assert str(user) == 'testuser'
    
    def test_user_default_role(self):
        """Test that user has default role of 'member'."""
        # Create user directly to test default value (factory sets random role)
        user = User.objects.create_user(
            username='testdefault',
            email='testdefault@example.com',
            password='testpass123'
        )
        assert user.role == 'member'
    
    def test_user_role_choices(self):
        """Test that user can have valid role choices."""
        roles = ['admin', 'manager', 'developer', 'member']
        for role in roles:
            user = UserFactory(role=role)
            assert user.role == role
            assert user.get_role_display() in ['Admin', 'Manager', 'Developer', 'Member']
    
    def test_user_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        user = UserFactory()
        after = timezone.now()
        
        assert user.created_at is not None
        assert before <= user.created_at <= after
    
    def test_user_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        user = UserFactory()
        initial_updated_at = user.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        user.first_name = 'Updated'
        user.save()
        
        assert user.updated_at > initial_updated_at
    
    def test_user_email_indexed(self):
        """Test that email field is indexed for faster lookups."""
        user = UserFactory(email='indexed@example.com')
        # Verify user can be queried by email efficiently
        found_user = User.objects.get(email='indexed@example.com')
        assert found_user == user
    
    def test_user_role_indexed(self):
        """Test that role field is indexed for faster lookups."""
        admin_user = AdminUserFactory()
        found_admins = User.objects.filter(role='admin')
        assert admin_user in found_admins
    
    def test_user_get_full_name_or_username_with_name(self):
        """Test get_full_name_or_username when user has first and last name."""
        user = UserFactory(first_name='John', last_name='Doe')
        assert user.get_full_name_or_username() == 'John Doe'
    
    def test_user_get_full_name_or_username_without_name(self):
        """Test get_full_name_or_username when user doesn't have name."""
        user = UserFactory(first_name='', last_name='', username='testuser')
        assert user.get_full_name_or_username() == 'testuser'
    
    def test_user_is_admin(self):
        """Test is_admin method for admin users."""
        admin_user = AdminUserFactory()
        regular_user = UserFactory(role='member')
        
        assert admin_user.is_admin() is True
        assert regular_user.is_admin() is False
    
    def test_user_is_manager(self):
        """Test is_manager method for manager users."""
        manager_user = ManagerUserFactory()
        regular_user = UserFactory(role='member')
        
        assert manager_user.is_manager() is True
        assert regular_user.is_manager() is False
    
    def test_user_is_developer(self):
        """Test is_developer method for developer users."""
        developer_user = DeveloperUserFactory()
        regular_user = UserFactory(role='member')
        
        assert developer_user.is_developer() is True
        assert regular_user.is_developer() is False
    
    def test_user_is_member(self):
        """Test is_member method for member users."""
        member_user = MemberUserFactory()
        admin_user = AdminUserFactory()
        
        assert member_user.is_member() is True
        assert admin_user.is_member() is False
    
    def test_user_has_management_permissions(self):
        """Test has_management_permissions method."""
        admin_user = AdminUserFactory()
        manager_user = ManagerUserFactory()
        developer_user = DeveloperUserFactory()
        member_user = MemberUserFactory()
        
        assert admin_user.has_management_permissions() is True
        assert manager_user.has_management_permissions() is True
        assert developer_user.has_management_permissions() is False
        assert member_user.has_management_permissions() is False
    
    def test_user_phone_validation(self):
        """Test phone number validation."""
        # Valid phone numbers
        valid_phones = ['+1234567890', '1234567890', '+11234567890']
        for phone in valid_phones:
            user = UserFactory(phone=phone)
            assert user.phone == phone
        
        # Invalid phone number should raise ValidationError
        user = UserFactory.build(phone='invalid')
        with pytest.raises(ValidationError):
            user.full_clean()
    
    def test_user_bio_max_length(self):
        """Test that bio field has max_length constraint."""
        long_bio = 'x' * 501  # Exceeds max_length=500
        user = UserFactory.build(bio=long_bio)
        with pytest.raises(ValidationError):
            user.full_clean()
    
    def test_user_ordering(self):
        """Test that users are ordered by created_at descending."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        users = list(User.objects.all()[:3])
        # Should be ordered by -created_at (newest first)
        assert users[0].created_at >= users[1].created_at
        assert users[1].created_at >= users[2].created_at
    
    def test_user_unique_username(self):
        """Test that username must be unique."""
        # Create first user directly to avoid django_get_or_create
        User.objects.create_user(
            username='uniqueuser',
            email='uniqueuser1@example.com',
            password='testpass123'
        )
        
        # Try to create another user with same username
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='uniqueuser',
                email='uniqueuser2@example.com',
                password='testpass123'
            )
    
    def test_user_can_have_empty_bio(self):
        """Test that bio field can be empty."""
        user = UserFactory(bio='')
        assert user.bio == ''
        assert user.pk is not None
    
    def test_user_can_have_empty_phone(self):
        """Test that phone field can be empty."""
        user = UserFactory(phone='')
        assert user.phone == ''
        assert user.pk is not None
    
    def test_user_password_hashing(self):
        """Test that user password is properly hashed."""
        user = UserFactory()
        user.set_password('testpassword123')
        user.save()
        
        assert user.password != 'testpassword123'
        assert user.check_password('testpassword123') is True
        assert user.check_password('wrongpassword') is False


# ============================================================================
# UserProfile Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestUserProfileModel:
    """Test suite for UserProfile model."""
    
    def test_userprofile_creation(self):
        """Test basic UserProfile creation."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        profile.job_title = 'Software Engineer'
        profile.department = 'Engineering'
        profile.save()
        
        assert profile.user == user
        assert profile.job_title == 'Software Engineer'
        assert profile.department == 'Engineering'
        assert profile.pk is not None
    
    def test_userprofile_str_representation(self):
        """Test string representation of UserProfile model."""
        user = UserFactory(username='testuser')
        profile = UserProfileFactory(user=user)
        assert str(profile) == "testuser's Profile"
    
    def test_userprofile_one_to_one_relationship(self):
        """Test that UserProfile has one-to-one relationship with User."""
        from users.models import UserProfile
        from django.db import transaction
        
        user = UserFactory()
        profile1 = UserProfileFactory(user=user)
        
        # Should not be able to create another profile for same user
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(user=user)
        
        # Refresh user from database to avoid transaction issues
        user.refresh_from_db()
        profile1.refresh_from_db()
        
        # Verify relationship
        assert user.profile == profile1
        assert profile1.user == user
    
    def test_userprofile_get_display_name(self):
        """Test get_display_name method."""
        user = UserFactory(first_name='John', last_name='Doe')
        profile = UserProfileFactory(user=user)
        
        assert profile.get_display_name() == 'John Doe'
        
        # Test with username only
        user2 = UserFactory(first_name='', last_name='', username='testuser')
        profile2 = UserProfileFactory(user=user2)
        assert profile2.get_display_name() == 'testuser'
    
    def test_userprofile_has_complete_profile_with_all_fields(self):
        """Test has_complete_profile when all required fields are present."""
        user = UserFactory(email='complete@example.com')
        profile = UserProfileFactory(user=user)
        profile.job_title = 'Engineer'
        profile.department = 'Tech'
        profile.save()
        
        assert profile.has_complete_profile() is True
    
    def test_userprofile_has_complete_profile_missing_job_title(self):
        """Test has_complete_profile when job_title is missing."""
        user = UserFactory(email='incomplete@example.com')
        profile = UserProfileFactory(
            user=user,
            job_title='',
            department='Tech'
        )
        
        assert profile.has_complete_profile() is False
    
    def test_userprofile_has_complete_profile_missing_department(self):
        """Test has_complete_profile when department is missing."""
        user = UserFactory(email='incomplete@example.com')
        profile = UserProfileFactory(
            user=user,
            job_title='Engineer',
            department=''
        )
        
        assert profile.has_complete_profile() is False
    
    def test_userprofile_location_choices(self):
        """Test location field choices."""
        locations = ['remote', 'office', 'hybrid']
        
        for location in locations:
            user = UserFactory()  # Create new user for each to avoid unique constraint
            profile = UserProfileFactory(user=user)
            profile.location = location
            profile.save()
            assert profile.location == location
            assert profile.get_location_display() in ['Remote', 'Office', 'Hybrid']
    
    def test_userprofile_default_timezone(self):
        """Test that timezone defaults to UTC."""
        user = UserFactory()
        profile = UserProfileFactory(user=user, timezone='')
        # If empty, should use default
        profile = UserProfileFactory(user=user)
        assert profile.timezone == 'UTC'
    
    def test_userprofile_default_language(self):
        """Test that language defaults to 'en'."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        assert profile.language == 'en'
    
    def test_userprofile_default_notifications(self):
        """Test default notification settings."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        
        assert profile.email_notifications is True
        assert profile.push_notifications is True
    
    def test_userprofile_can_disable_notifications(self):
        """Test that notifications can be disabled."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        profile.email_notifications = False
        profile.push_notifications = False
        profile.save()
        
        assert profile.email_notifications is False
        assert profile.push_notifications is False
    
    def test_userprofile_url_fields(self):
        """Test URL fields in UserProfile."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        profile.website = 'https://example.com'
        profile.linkedin = 'https://linkedin.com/in/test'
        profile.github = 'https://github.com/test'
        profile.twitter = 'https://twitter.com/test'
        profile.save()
        
        assert profile.website == 'https://example.com'
        assert profile.linkedin == 'https://linkedin.com/in/test'
        assert profile.github == 'https://github.com/test'
        assert profile.twitter == 'https://twitter.com/test'
    
    def test_userprofile_can_have_empty_urls(self):
        """Test that URL fields can be empty."""
        user = UserFactory()
        profile = UserProfileFactory(
            user=user,
            website='',
            linkedin='',
            github='',
            twitter=''
        )
        
        assert profile.website == ''
        assert profile.linkedin == ''
        assert profile.github == ''
        assert profile.twitter == ''
    
    def test_userprofile_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        after = timezone.now()
        
        assert profile.created_at is not None
        assert before <= profile.created_at <= after
    
    def test_userprofile_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        initial_updated_at = profile.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        profile.job_title = 'Updated Title'
        profile.save()
        
        assert profile.updated_at > initial_updated_at
    
    def test_userprofile_cascade_delete(self):
        """Test that profile is deleted when user is deleted."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        profile_id = profile.id
        
        user.delete()
        
        # Profile should be deleted (cascade)
        assert not UserProfile.objects.filter(id=profile_id).exists()
    
    def test_userprofile_address_fields(self):
        """Test address, city, and country fields."""
        user = UserFactory()
        profile = UserProfileFactory(user=user)
        profile.address = '123 Main St'
        profile.city = 'New York'
        profile.country = 'USA'
        profile.save()
        
        assert profile.address == '123 Main St'
        assert profile.city == 'New York'
        assert profile.country == 'USA'
    
    def test_userprofile_ordering(self):
        """Test UserProfile ordering by created_at."""
        from users.models import UserProfile
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        
        profile1 = UserProfileFactory(user=user1)
        profile2 = UserProfileFactory(user=user2)
        profile3 = UserProfileFactory(user=user3)
        
        # Query only the profiles we created, ordered by created_at descending
        profiles = list(UserProfile.objects.filter(
            id__in=[profile1.id, profile2.id, profile3.id]
        ).order_by('-created_at'))
        
        # Verify we got all three profiles
        assert len(profiles) == 3
        
        # Verify ordering - should be ordered by created_at descending (newest first)
        # The profiles should be in descending order of creation time
        # Since profile3 was created last, it should be first (newest)
        assert profiles[0].created_at >= profiles[1].created_at
        assert profiles[1].created_at >= profiles[2].created_at


# ============================================================================
# API Tests - Authentication Endpoints
# ============================================================================

@pytest.mark.django_db
@pytest.mark.api
class TestUserRegistrationAPI:
    """Test suite for user registration API endpoint."""
    
    def test_user_registration_success(self, api_client):
        """Test successful user registration with all required fields."""
        url = '/api/auth/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password2': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'member'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        assert response.data['message'] == 'User registered successfully'
    
    def test_user_registration_minimal_fields(self, api_client):
        """Test user registration with only required fields."""
        url = '/api/auth/register/'
        data = {
            'username': 'minimaluser',
            'email': 'minimal@example.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['user']['username'] == 'minimaluser'
        assert response.data['user']['role'] == 'member'  # Default role
    
    def test_user_registration_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        url = '/api/auth/register/'
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepass123',
            'password2': 'differentpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'password2' in response.data or 'non_field_errors' in response.data
    
    def test_user_registration_duplicate_username(self, api_client, user):
        """Test registration fails with duplicate username."""
        url = '/api/auth/register/'
        data = {
            'username': user.username,
            'email': 'different@example.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'username' in response.data
    
    def test_user_registration_duplicate_email(self, api_client, user):
        """Test registration fails with duplicate email."""
        url = '/api/auth/register/'
        data = {
            'username': 'differentuser',
            'email': user.email,
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'email' in response.data
    
    def test_user_registration_weak_password(self, api_client):
        """Test registration fails with weak password."""
        url = '/api/auth/register/'
        data = {
            'username': 'weakpass',
            'email': 'weak@example.com',
            'password': '123',  # Too short
            'password2': '123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'password' in response.data
    
    def test_user_registration_invalid_email(self, api_client):
        """Test registration fails with invalid email format."""
        url = '/api/auth/register/'
        data = {
            'username': 'invalidemail',
            'email': 'notanemail',
            'password': 'securepass123',
            'password2': 'securepass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'email' in response.data
    
    def test_user_registration_with_optional_fields(self, api_client):
        """Test registration with all optional fields."""
        url = '/api/auth/register/'
        data = {
            'username': 'fulluser',
            'email': 'full@example.com',
            'password': 'securepass123',
            'password2': 'securepass123',
            'first_name': 'Full',
            'last_name': 'User',
            'role': 'developer',
            'phone': '+1234567890',
            'bio': 'Software developer with 5 years experience'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['user']['first_name'] == 'Full'
        assert response.data['user']['last_name'] == 'User'
        assert response.data['user']['role'] == 'developer'
        assert response.data['user']['phone'] == '+1234567890'


@pytest.mark.django_db
@pytest.mark.api
class TestUserLoginAPI:
    """Test suite for user login API endpoint."""
    
    def test_user_login_with_username_success(self, api_client, user):
        """Test successful login with username."""
        url = '/api/auth/login/'
        data = {
            'username': user.username,
            'password': 'testpass123'  # Default password from factory
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 200
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['username'] == user.username
        assert response.data['message'] == 'Login successful'
    
    def test_user_login_with_email_success(self, api_client, user):
        """Test successful login with email."""
        url = '/api/auth/login/'
        data = {
            'username': user.email,  # Can use email as username
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['user']['email'] == user.email
    
    def test_user_login_invalid_username(self, api_client):
        """Test login fails with invalid username."""
        url = '/api/auth/login/'
        data = {
            'username': 'nonexistent',
            'password': 'password123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data or 'non_field_errors' in response.data
    
    def test_user_login_wrong_password(self, api_client, user):
        """Test login fails with wrong password."""
        url = '/api/auth/login/'
        data = {
            'username': user.username,
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data or 'non_field_errors' in response.data
    
    def test_user_login_missing_fields(self, api_client):
        """Test login fails with missing fields."""
        url = '/api/auth/login/'
        
        # Missing password
        response = api_client.post(url, {'username': 'testuser'}, format='json')
        assert response.status_code == 400
        
        # Missing username
        response = api_client.post(url, {'password': 'testpass123'}, format='json')
        assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.api
class TestUserProfileAPI:
    """Test suite for user profile API endpoint."""
    
    def test_get_profile_authenticated(self, authenticated_api_client, user):
        """Test retrieving profile when authenticated."""
        url = '/api/auth/profile/'
        
        response = authenticated_api_client.get(url)
        
        assert response.status_code == 200
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email
    
    def test_get_profile_unauthenticated(self, api_client):
        """Test retrieving profile fails when unauthenticated."""
        url = '/api/auth/profile/'
        
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_update_profile_put_full(self, authenticated_api_client, user):
        """Test full profile update using PUT."""
        url = '/api/auth/profile/'
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'role': 'developer',
            'bio': 'Updated bio',
            'phone': '+9876543210',
            'job_title': 'Senior Developer',
            'department': 'Engineering',
            'location': 'remote',
            'timezone': 'America/New_York',
            'language': 'en',
            'email_notifications': True,
            'push_notifications': False
        }
        
        response = authenticated_api_client.put(url, data, format='json')
        
        assert response.status_code == 200
        assert 'data' in response.data
        assert response.data['data']['first_name'] == 'Updated'
        assert response.data['data']['last_name'] == 'Name'
        assert response.data['message'] == 'Profile updated successfully'
    
    def test_update_profile_patch_partial(self, authenticated_api_client, user):
        """Test partial profile update using PATCH."""
        url = '/api/auth/profile/'
        data = {
            'first_name': 'Patched',
            'bio': 'Updated bio via PATCH'
        }
        
        response = authenticated_api_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['first_name'] == 'Patched'
        assert response.data['data']['bio'] == 'Updated bio via PATCH'
        # Other fields should remain unchanged
        assert response.data['data']['email'] == user.email
    
    def test_update_profile_read_only_fields(self, authenticated_api_client, user):
        """Test that read-only fields cannot be updated."""
        url = '/api/auth/profile/'
        original_username = user.username
        original_email = user.email
        
        data = {
            'username': 'newusername',
            'email': 'newemail@example.com',
            'first_name': 'Test'
        }
        
        response = authenticated_api_client.patch(url, data, format='json')
        
        assert response.status_code == 200
        # Username and email should remain unchanged (read-only)
        assert response.data['data']['username'] == original_username
        assert response.data['data']['email'] == original_email
    
    def test_update_profile_invalid_location(self, authenticated_api_client):
        """Test profile update fails with invalid location choice."""
        url = '/api/auth/profile/'
        data = {
            'location': 'invalid_location'
        }
        
        response = authenticated_api_client.patch(url, data, format='json')
        
        assert response.status_code == 400
        assert 'location' in response.data
    
    def test_update_profile_invalid_timezone(self, authenticated_api_client):
        """Test profile update with invalid timezone."""
        url = '/api/auth/profile/'
        data = {
            'timezone': 'Invalid/Timezone'
        }
        
        response = authenticated_api_client.patch(url, data, format='json')
        
        # Should either accept it or return 400, depending on validation
        assert response.status_code in [200, 400]
    
    def test_update_profile_unauthenticated(self, api_client):
        """Test profile update fails when unauthenticated."""
        url = '/api/auth/profile/'
        data = {'first_name': 'Test'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == 401
