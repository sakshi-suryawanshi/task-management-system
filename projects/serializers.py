"""
Serializers for Project API.

This module contains DRF serializers for project management, including
project serialization and project member management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, ProjectMember

User = get_user_model()


class ProjectMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectMember model.
    
    Used to represent project member information within project serialization.
    Includes user details and role information.
    
    Fields:
        id: ProjectMember ID
        user: User ID
        username: Username (read-only)
        email: Email (read-only)
        full_name: User's full name (read-only)
        role: Member role (owner, admin, member)
        role_display: Human-readable role name (read-only)
        joined_at: Timestamp when user joined the project (read-only)
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = ProjectMember
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


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    
    Handles project creation, updating, and serialization.
    Includes member count, member list, team information, and task statistics.
    
    Fields:
        id: Project ID (read-only)
        name: Project name (required, unique within team)
        description: Project description (optional)
        status: Project status (planning, active, on_hold, completed, cancelled)
        status_display: Human-readable status (read-only)
        priority: Project priority (high, medium, low)
        priority_display: Human-readable priority (read-only)
        deadline: Project deadline (optional)
        team: Team ID (required)
        team_name: Team name (read-only)
        member_count: Number of members (read-only)
        members: List of project members (read-only, nested)
        task_count: Total number of tasks (read-only)
        completed_task_count: Number of completed tasks (read-only)
        is_overdue: Whether project is overdue (read-only)
        created_at: Project creation timestamp (read-only)
        updated_at: Last update timestamp (read-only)
    """
    
    member_count = serializers.SerializerMethodField(read_only=True)
    members = ProjectMemberSerializer(many=True, read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    task_count = serializers.SerializerMethodField(read_only=True)
    completed_task_count = serializers.SerializerMethodField(read_only=True)
    is_overdue = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'deadline',
            'team',
            'team_name',
            'member_count',
            'members',
            'task_count',
            'completed_task_count',
            'is_overdue',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'member_count',
            'members',
            'team_name',
            'status_display',
            'priority_display',
            'task_count',
            'completed_task_count',
            'is_overdue',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'name': {
                'required': True,
                'help_text': 'Project name (must be unique within team)'
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Detailed description of the project'
            },
            'status': {
                'required': False,
                'help_text': 'Project status (planning, active, on_hold, completed, cancelled)'
            },
            'priority': {
                'required': False,
                'help_text': 'Project priority (high, medium, low)'
            },
            'deadline': {
                'required': False,
                'allow_null': True,
                'help_text': 'Project deadline (optional)'
            },
            'team': {
                'required': True,
                'help_text': 'Team ID that this project belongs to'
            },
        }
    
    def get_member_count(self, obj):
        """Return the number of members in the project."""
        return obj.get_member_count()
    
    def get_task_count(self, obj):
        """Return the total number of tasks in the project."""
        return obj.tasks.count()
    
    def get_completed_task_count(self, obj):
        """Return the number of completed tasks in the project."""
        return obj.tasks.filter(status='done').count()
    
    def get_is_overdue(self, obj):
        """Return whether the project is overdue."""
        return obj.is_overdue()
    
    def validate_name(self, value):
        """
        Validate project name.
        
        Args:
            value: Project name to validate
            
        Returns:
            str: Validated project name
            
        Raises:
            serializers.ValidationError: If name is invalid or already exists in team
        """
        # Strip whitespace
        value = value.strip()
        
        # Check minimum length
        if len(value) < 2:
            raise serializers.ValidationError(
                "Project name must be at least 2 characters long."
            )
        
        # Check maximum length
        if len(value) > 200:
            raise serializers.ValidationError(
                "Project name must not exceed 200 characters."
            )
        
        # Check for uniqueness within team (exclude current instance if updating)
        instance = self.instance
        team = self.initial_data.get('team') or (instance.team if instance else None)
        
        if team:
            # Convert team to ID if it's an object
            team_id = team.id if hasattr(team, 'id') else team
            
            if instance:
                # Updating existing project
                if Project.objects.exclude(pk=instance.pk).filter(
                    team_id=team_id,
                    name__iexact=value
                ).exists():
                    raise serializers.ValidationError(
                        "A project with this name already exists in this team."
                    )
            else:
                # Creating new project
                if Project.objects.filter(
                    team_id=team_id,
                    name__iexact=value
                ).exists():
                    raise serializers.ValidationError(
                        "A project with this name already exists in this team."
                    )
        
        return value
    
    def validate_team(self, value):
        """
        Validate that the team exists and user is a member.
        
        Args:
            value: Team instance to validate
            
        Returns:
            Team: Validated team instance
            
        Raises:
            serializers.ValidationError: If team doesn't exist or user is not a member
        """
        if not value:
            raise serializers.ValidationError("Team is required.")
        
        # Check if user is a member of the team
        request = self.context.get('request')
        if request and request.user:
            from teams.models import TeamMember
            if not TeamMember.objects.filter(team=value, user=request.user).exists():
                raise serializers.ValidationError(
                    "You must be a member of the team to create projects in it."
                )
        
        return value
    
    def validate_deadline(self, value):
        """
        Validate project deadline.
        
        Args:
            value: Deadline datetime to validate
            
        Returns:
            datetime: Validated deadline
            
        Raises:
            serializers.ValidationError: If deadline is in the past
        """
        if value:
            from django.utils import timezone
            if value < timezone.now():
                raise serializers.ValidationError(
                    "Project deadline cannot be in the past."
                )
        return value


class ProjectMemberAddSerializer(serializers.Serializer):
    """
    Serializer for adding a member to a project.
    
    Used in POST requests to add members to projects.
    
    Fields:
        user_id: ID of the user to add (required)
        role: Role to assign to the member (optional, defaults to 'member')
    """
    
    user_id = serializers.IntegerField(
        required=True,
        help_text='ID of the user to add to the project'
    )
    role = serializers.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
        default=ProjectMember.ROLE_MEMBER,
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
        valid_roles = [choice[0] for choice in ProjectMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value


class ProjectMemberUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a project member's role.
    
    Used in PATCH/PUT requests to update member roles.
    
    Fields:
        role: New role to assign (required)
    """
    
    role = serializers.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
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
        valid_roles = [choice[0] for choice in ProjectMember.ROLE_CHOICES]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value

