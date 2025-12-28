"""
Serializers for Team API.

This module contains DRF serializers for team management, including
team serialization and team member management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Team, TeamMember

User = get_user_model()


class TeamMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for TeamMember model.
    
    Used to represent team member information within team serialization.
    Includes user details and role information.
    
    Fields:
        id: TeamMember ID
        user: User ID
        username: Username (read-only)
        email: Email (read-only)
        full_name: User's full name (read-only)
        role: Member role (owner, admin, member)
        role_display: Human-readable role name (read-only)
        joined_at: Timestamp when user joined the team (read-only)
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'user',
            'username',
            'email',
            'full_name',
            'role',
            'role_display',
            'joined_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'username',
            'email',
            'full_name',
            'role_display',
            'joined_at',
        ]
    
    def get_full_name(self, obj):
        """Return user's full name or username."""
        return obj.user.get_full_name_or_username() if obj.user else None


class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for Team model.
    
    Handles team creation, updating, and serialization.
    Includes member count and member list information.
    
    Fields:
        id: Team ID (read-only)
        name: Team name (unique, required)
        description: Team description (optional)
        member_count: Number of members (read-only)
        members: List of team members (read-only, nested)
        created_at: Team creation timestamp (read-only)
        updated_at: Last update timestamp (read-only)
    """
    
    member_count = serializers.SerializerMethodField(read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = [
            'id',
            'name',
            'description',
            'member_count',
            'members',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'member_count',
            'members',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'name': {
                'required': True,
                'help_text': 'Team name (must be unique)'
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Detailed description of the team'
            },
        }
    
    def get_member_count(self, obj):
        """Return the number of members in the team."""
        return obj.get_member_count()
    
    def validate_name(self, value):
        """
        Validate team name.
        
        Args:
            value: Team name to validate
            
        Returns:
            str: Validated team name
            
        Raises:
            serializers.ValidationError: If name is invalid or already exists
        """
        # Strip whitespace
        value = value.strip()
        
        # Check minimum length
        if len(value) < 2:
            raise serializers.ValidationError(
                "Team name must be at least 2 characters long."
            )
        
        # Check for uniqueness (exclude current instance if updating)
        instance = self.instance
        if instance:
            # Updating existing team
            if Team.objects.exclude(pk=instance.pk).filter(name__iexact=value).exists():
                raise serializers.ValidationError(
                    "A team with this name already exists."
                )
        else:
            # Creating new team
            if Team.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError(
                    "A team with this name already exists."
                )
        
        return value


class TeamMemberAddSerializer(serializers.Serializer):
    """
    Serializer for adding a member to a team.
    
    Used in POST requests to add members to teams.
    
    Fields:
        user_id: ID of the user to add (required)
        role: Role to assign to the member (optional, defaults to 'member')
    """
    
    user_id = serializers.IntegerField(
        required=True,
        help_text='ID of the user to add to the team'
    )
    role = serializers.ChoiceField(
        choices=TeamMember.ROLE_CHOICES,
        default=TeamMember.ROLE_MEMBER,
        required=False,
        help_text='Role to assign to the member (owner, admin, member)'
    )
    
    def validate_user_id(self, value):
        """
        Validate that user exists.
        
        Args:
            value: User ID to validate
            
        Returns:
            int: Validated user ID
            
        Raises:
            serializers.ValidationError: If user doesn't exist
        """
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "User with this ID does not exist."
            )
        return value
    
    def validate_role(self, value):
        """
        Validate role choice.
        
        Args:
            value: Role value to validate
            
        Returns:
            str: Validated role
        """
        valid_roles = [choice[0] for choice in TeamMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value


class TeamMemberUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a team member's role.
    
    Used in PATCH/PUT requests to update member roles.
    
    Fields:
        role: New role to assign (required)
    """
    
    role = serializers.ChoiceField(
        choices=TeamMember.ROLE_CHOICES,
        required=True,
        help_text='New role to assign to the member (owner, admin, member)'
    )
    
    def validate_role(self, value):
        """
        Validate role choice.
        
        Args:
            value: Role value to validate
            
        Returns:
            str: Validated role
        """
        valid_roles = [choice[0] for choice in TeamMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value

