"""
Serializers for User authentication and management.

This module contains DRF serializers for user registration, login,
and profile management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles user creation with password validation and hashing.
    Automatically creates UserProfile via signal.
    
    Fields:
        username: Unique username (required)
        email: Unique email address (required)
        password: User password (required, write-only)
        password2: Password confirmation (required, write-only)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        role: User role (optional, defaults to 'member')
        phone: Contact phone number (optional)
        bio: Short biography (optional)
    """
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='User password (minimum 8 characters)'
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Password confirmation (must match password)'
    )
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'password2',
            'first_name',
            'last_name',
            'role',
            'phone',
            'bio',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'username': {
                'required': True,
                'help_text': 'Unique username for login'
            },
            'email': {
                'required': True,
                'help_text': 'Valid email address (must be unique)'
            },
            'first_name': {
                'required': False,
                'allow_blank': True
            },
            'last_name': {
                'required': False,
                'allow_blank': True
            },
            'role': {
                'required': False,
                'default': 'member'
            },
            'phone': {
                'required': False,
                'allow_blank': True
            },
            'bio': {
                'required': False,
                'allow_blank': True
            },
        }
    
    def validate_email(self, value):
        """
        Validate email uniqueness and format.
        
        Args:
            value: Email address to validate
            
        Returns:
            str: Validated email address
            
        Raises:
            serializers.ValidationError: If email is already in use
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower().strip()
    
    def validate_username(self, value):
        """
        Validate username uniqueness and format.
        
        Args:
            value: Username to validate
            
        Returns:
            str: Validated username
            
        Raises:
            serializers.ValidationError: If username is already in use
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        # Username should be alphanumeric and underscores only
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )
        return value.lower().strip()
    
    def validate_password(self, value):
        """
        Validate password strength using Django's password validators.
        
        Args:
            value: Password to validate
            
        Returns:
            str: Validated password
            
        Raises:
            serializers.ValidationError: If password doesn't meet requirements
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """
        Validate that passwords match.
        
        Args:
            attrs: Dictionary of validated field values
            
        Returns:
            dict: Validated attributes
            
        Raises:
            serializers.ValidationError: If passwords don't match
        """
        password = attrs.get('password')
        password2 = attrs.get('password2')
        
        if password != password2:
            raise serializers.ValidationError({
                'password2': "Passwords do not match."
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user with hashed password.
        
        Args:
            validated_data: Validated user data
            
        Returns:
            User: Created user instance
        """
        # Remove password2 from validated_data
        validated_data.pop('password2', None)
        
        # Extract password and hash it
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # UserProfile is automatically created via signal
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates user credentials and returns JWT tokens.
    
    Fields:
        username: Username or email for login
        password: User password
    """
    
    username = serializers.CharField(
        required=True,
        help_text='Username or email address'
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text='User password'
    )
    
    def validate(self, attrs):
        """
        Validate user credentials.
        
        Args:
            attrs: Dictionary containing username and password
            
        Returns:
            dict: Validated attributes with user instance
            
        Raises:
            serializers.ValidationError: If credentials are invalid
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise serializers.ValidationError(
                "Both username and password are required."
            )
        
        # Try to authenticate with username or email
        user = None
        
        # Try to get user by username or email
        try:
            user_obj = User.objects.get(username=username)
            user = authenticate(
                username=user_obj.username,
                password=password
            )
        except User.DoesNotExist:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError(
                "Invalid username/email or password."
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                "User account is disabled."
            )
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data (read-only for public endpoints).
    
    Used to return user information in login/registration responses.
    """
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'avatar',
            'bio',
            'phone',
            'is_active',
            'is_staff',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'is_active',
            'is_staff',
            'created_at',
            'updated_at',
        ]
    
    def get_full_name(self, obj):
        """Return user's full name or username."""
        return obj.get_full_name_or_username()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile management.
    
    Combines User and UserProfile fields for comprehensive profile management.
    Supports GET, PUT, and PATCH operations.
    
    User fields (editable):
        first_name: User's first name
        last_name: User's last name
        role: User role (admin, manager, developer, member)
        avatar: Profile picture (ImageField)
        bio: Short biography
        phone: Contact phone number
    
    UserProfile fields (editable):
        job_title: Job title or position
        department: Department or team name
        location: Work location preference (remote, office, hybrid)
        address: Physical address
        city: City
        country: Country
        website: Personal or professional website URL
        linkedin: LinkedIn profile URL
        github: GitHub profile URL
        twitter: Twitter profile URL
        timezone: User timezone
        language: Preferred language code
        email_notifications: Enable email notifications
        push_notifications: Enable push notifications
    """
    
    # User fields (read-only)
    username = serializers.CharField(read_only=True, help_text='Username (read-only)')
    email = serializers.EmailField(read_only=True, help_text='Email address (read-only)')
    full_name = serializers.SerializerMethodField(help_text='User\'s full name')
    
    # UserProfile fields (flattened for easier API usage)
    # Using SerializerMethodField for read, and regular fields for write
    job_title = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='Job title or position'
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='Department or team name'
    )
    location = serializers.ChoiceField(
        choices=UserProfile.LOCATION_CHOICES,
        required=False,
        allow_blank=True,
        help_text='Work location preference'
    )
    address = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='Physical address'
    )
    city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='City'
    )
    country = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='Country'
    )
    website = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='Personal or professional website'
    )
    linkedin = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='LinkedIn profile URL'
    )
    github = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='GitHub profile URL'
    )
    twitter = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text='Twitter profile URL'
    )
    timezone = serializers.CharField(
        max_length=50,
        required=False,
        help_text='User timezone'
    )
    language = serializers.CharField(
        max_length=10,
        required=False,
        help_text='Preferred language code'
    )
    email_notifications = serializers.BooleanField(
        required=False,
        help_text='Enable email notifications'
    )
    push_notifications = serializers.BooleanField(
        required=False,
        help_text='Enable push notifications'
    )
    
    # Profile timestamps (read-only)
    profile_created_at = serializers.SerializerMethodField(
        read_only=True,
        help_text='Profile creation timestamp'
    )
    profile_updated_at = serializers.SerializerMethodField(
        read_only=True,
        help_text='Profile last update timestamp'
    )
    
    def get_profile_created_at(self, obj):
        """Get profile created_at timestamp."""
        try:
            return obj.profile.created_at
        except UserProfile.DoesNotExist:
            return None
    
    def get_profile_updated_at(self, obj):
        """Get profile updated_at timestamp."""
        try:
            return obj.profile.updated_at
        except UserProfile.DoesNotExist:
            return None
    
    def to_representation(self, instance):
        """
        Customize representation to include profile data.
        
        Args:
            instance: User instance
            
        Returns:
            dict: Serialized user data with profile fields
        """
        representation = super().to_representation(instance)
        
        # Ensure profile exists (should always exist due to signals)
        try:
            profile = instance.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist (shouldn't happen)
            profile = UserProfile.objects.create(user=instance)
        
        # Populate profile fields from the profile instance
        representation['job_title'] = profile.job_title
        representation['department'] = profile.department
        representation['location'] = profile.location
        representation['address'] = profile.address
        representation['city'] = profile.city
        representation['country'] = profile.country
        representation['website'] = profile.website
        representation['linkedin'] = profile.linkedin
        representation['github'] = profile.github
        representation['twitter'] = profile.twitter
        representation['timezone'] = profile.timezone
        representation['language'] = profile.language
        representation['email_notifications'] = profile.email_notifications
        representation['push_notifications'] = profile.push_notifications
        representation['profile_created_at'] = profile.created_at
        representation['profile_updated_at'] = profile.updated_at
        
        return representation
    
    class Meta:
        model = User
        fields = [
            # User basic info (read-only)
            'id',
            'username',
            'email',
            'full_name',
            
            # User editable fields
            'first_name',
            'last_name',
            'role',
            'avatar',
            'bio',
            'phone',
            
            # UserProfile fields (flattened)
            'job_title',
            'department',
            'location',
            'address',
            'city',
            'country',
            'website',
            'linkedin',
            'github',
            'twitter',
            'timezone',
            'language',
            'email_notifications',
            'push_notifications',
            'profile_created_at',
            'profile_updated_at',
            
            # Timestamps (read-only)
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'email',
            'created_at',
            'updated_at',
            'profile_created_at',
            'profile_updated_at',
        ]
    
    def get_full_name(self, obj):
        """Return user's full name or username."""
        return obj.get_full_name_or_username()
    
    def validate_phone(self, value):
        """
        Validate phone number format.
        
        Args:
            value: Phone number to validate
            
        Returns:
            str: Validated phone number
        """
        if value:
            # Phone validation is handled by model validator
            return value.strip()
        return value
    
    def validate_role(self, value):
        """
        Validate role choice.
        
        Args:
            value: Role value
            
        Returns:
            str: Validated role
        """
        valid_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value
    
    def validate_website(self, value):
        """Validate website URL format."""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "Website URL must start with http:// or https://"
            )
        return value
    
    def validate_linkedin(self, value):
        """Validate LinkedIn URL format."""
        if value and 'linkedin.com' not in value.lower():
            raise serializers.ValidationError(
                "Please provide a valid LinkedIn URL"
            )
        return value
    
    def validate_github(self, value):
        """Validate GitHub URL format."""
        if value and 'github.com' not in value.lower():
            raise serializers.ValidationError(
                "Please provide a valid GitHub URL"
            )
        return value
    
    def validate_twitter(self, value):
        """Validate Twitter URL format."""
        if value and 'twitter.com' not in value.lower() and 'x.com' not in value.lower():
            raise serializers.ValidationError(
                "Please provide a valid Twitter/X URL"
            )
        return value
    
    def update(self, instance, validated_data):
        """
        Update user and profile information.
        
        Handles nested UserProfile updates along with User updates.
        When using source='profile.field', DRF handles the nested access automatically.
        
        Args:
            instance: User instance to update
            validated_data: Validated data dictionary
            
        Returns:
            User: Updated user instance
        """
        # Ensure profile exists (should always exist due to signals)
        try:
            profile = instance.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist (shouldn't happen due to signals)
            profile = UserProfile.objects.create(user=instance)
        
        # List of profile field names (without 'profile.' prefix)
        profile_fields = [
            'job_title', 'department', 'location', 'address', 'city', 'country',
            'website', 'linkedin', 'github', 'twitter', 'timezone', 'language',
            'email_notifications', 'push_notifications'
        ]
        
        # Separate profile data from user data
        profile_data = {}
        user_data = {}
        
        for key, value in validated_data.items():
            if key in profile_fields:
                profile_data[key] = value
            else:
                user_data[key] = value
        
        # Update User fields
        for attr, value in user_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update UserProfile fields
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        
        profile.save()
        
        return instance
    



