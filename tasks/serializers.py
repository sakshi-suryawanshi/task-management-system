"""
Serializers for Task API.

This module contains DRF serializers for task management, including
task serialization and task assignment management.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Task, TaskComment

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    
    Handles task creation, updating, and serialization.
    Includes assignee information, project information, and computed fields.
    
    Fields:
        id: Task ID (read-only)
        title: Task title (required)
        description: Task description (optional)
        status: Task status (todo, in_progress, done, blocked)
        status_display: Human-readable status (read-only)
        priority: Task priority (high, medium, low)
        priority_display: Human-readable priority (read-only)
        due_date: Task due date (optional)
        project: Project ID (required)
        project_name: Project name (read-only)
        assignee: User ID of assignee (optional)
        assignee_username: Assignee username (read-only)
        assignee_email: Assignee email (read-only)
        assignee_full_name: Assignee full name (read-only)
        created_by: User ID of creator (read-only)
        created_by_username: Creator username (read-only)
        is_overdue: Whether task is overdue (read-only)
        is_assigned: Whether task is assigned (read-only)
        comment_count: Number of comments (read-only)
        attachment_count: Number of attachments (read-only)
        created_at: Task creation timestamp (read-only)
        updated_at: Last update timestamp (read-only)
    """
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    # Assignee information
    assignee_username = serializers.CharField(source='assignee.username', read_only=True)
    assignee_email = serializers.EmailField(source='assignee.email', read_only=True)
    assignee_full_name = serializers.SerializerMethodField(read_only=True)
    
    # Creator information
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    # Computed fields
    is_overdue = serializers.SerializerMethodField(read_only=True)
    is_assigned = serializers.SerializerMethodField(read_only=True)
    comment_count = serializers.SerializerMethodField(read_only=True)
    attachment_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'due_date',
            'project',
            'project_name',
            'assignee',
            'assignee_username',
            'assignee_email',
            'assignee_full_name',
            'created_by',
            'created_by_username',
            'is_overdue',
            'is_assigned',
            'comment_count',
            'attachment_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'project_name',
            'status_display',
            'priority_display',
            'assignee_username',
            'assignee_email',
            'assignee_full_name',
            'created_by',
            'created_by_username',
            'is_overdue',
            'is_assigned',
            'comment_count',
            'attachment_count',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'title': {
                'required': True,
                'help_text': 'Task title (2-200 characters)'
            },
            'description': {
                'required': False,
                'allow_blank': True,
                'help_text': 'Detailed description of the task'
            },
            'status': {
                'required': False,
                'help_text': 'Task status (todo, in_progress, done, blocked)'
            },
            'priority': {
                'required': False,
                'help_text': 'Task priority (high, medium, low)'
            },
            'due_date': {
                'required': False,
                'allow_null': True,
                'help_text': 'Task due date (optional)'
            },
            'project': {
                'required': True,
                'help_text': 'Project ID that this task belongs to'
            },
            'assignee': {
                'required': False,
                'allow_null': True,
                'help_text': 'User ID of the user assigned to this task'
            },
        }
    
    def get_assignee_full_name(self, obj):
        """Return assignee's full name or username."""
        if obj.assignee:
            return obj.assignee.get_full_name_or_username()
        return None
    
    def get_is_overdue(self, obj):
        """Return whether the task is overdue."""
        return obj.is_overdue()
    
    def get_is_assigned(self, obj):
        """Return whether the task is assigned."""
        return obj.is_assigned()
    
    def get_comment_count(self, obj):
        """Return the number of comments for this task."""
        return obj.get_comment_count()
    
    def get_attachment_count(self, obj):
        """Return the number of attachments for this task."""
        return obj.get_attachment_count()
    
    def validate_title(self, value):
        """
        Validate task title.
        
        Args:
            value: Task title to validate
            
        Returns:
            str: Validated task title
            
        Raises:
            serializers.ValidationError: If title is invalid
        """
        # Strip whitespace
        value = value.strip()
        
        # Check minimum length
        if len(value) < 2:
            raise serializers.ValidationError(
                "Task title must be at least 2 characters long."
            )
        
        # Check maximum length
        if len(value) > 200:
            raise serializers.ValidationError(
                "Task title must not exceed 200 characters."
            )
        
        return value
    
    def validate_project(self, value):
        """
        Validate that the project exists and user is a member.
        
        Args:
            value: Project instance to validate
            
        Returns:
            Project: Validated project instance
            
        Raises:
            serializers.ValidationError: If project doesn't exist or user is not a member
        """
        if not value:
            raise serializers.ValidationError("Project is required.")
        
        # Check if user is a member of the project
        request = self.context.get('request')
        if request and request.user:
            if not value.is_member(request.user):
                raise serializers.ValidationError(
                    "You must be a member of the project to create tasks in it."
                )
        
        return value
    
    def validate_assignee(self, value):
        """
        Validate that the assignee is a member of the task's project.
        
        Note: Full validation (checking project membership) is deferred to validate()
        method to ensure project is validated first. This method only validates that
        the user exists if provided.
        
        Args:
            value: User instance to validate (can be None)
            
        Returns:
            User: Validated user instance (or None)
        """
        # Basic validation - user existence is checked by ForeignKey
        # Project membership check is done in validate() method
        return value
    
    def validate(self, data):
        """
        Cross-field validation for task data.
        
        Validates that assignee (if provided) is a member of the project.
        
        Args:
            data: Dictionary of validated field values
            
        Returns:
            dict: Validated data dictionary
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check assignee project membership if assignee is provided
        assignee = data.get('assignee')
        project = data.get('project') or (self.instance.project if self.instance else None)
        
        if assignee and project:
            if not project.is_member(assignee):
                raise serializers.ValidationError({
                    'assignee': 'Assignee must be a member of the project.'
                })
        
        return data
    
    def validate_due_date(self, value):
        """
        Validate task due date (optional validation - allows past dates for flexibility).
        
        Args:
            value: Due date datetime to validate
            
        Returns:
            datetime: Validated due date
        """
        # Due date can be in the past (for historical tasks or flexibility)
        # No strict validation here, but can be added if needed
        return value
    
    def create(self, validated_data):
        """
        Create a new task and set the creator.
        
        Args:
            validated_data: Validated task data
            
        Returns:
            Task: Created task instance
        """
        # Set the creator to the current user
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class TaskAssigneeSerializer(serializers.Serializer):
    """
    Serializer for assigning/unassigning a task.
    
    Used in POST/PATCH requests to assign tasks.
    
    Fields:
        assignee_id: ID of the user to assign (optional, None to unassign)
    """
    
    assignee_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='ID of the user to assign to the task (null to unassign)'
    )
    
    def validate_assignee_id(self, value):
        """
        Validate that user exists.
        
        Args:
            value: User ID to validate (can be None)
            
        Returns:
            int or None: Validated user ID
            
        Raises:
            serializers.ValidationError: If user doesn't exist
        """
        if value is not None:
            try:
                User.objects.get(pk=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    "User with this ID does not exist."
                )
        return value


class TaskStatusUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating task status.
    
    Used in PATCH requests to update task status.
    
    Fields:
        status: New task status (todo, in_progress, done, blocked)
    """
    
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        required=True,
        help_text='New task status (todo, in_progress, done, blocked)'
    )
    
    def validate_status(self, value):
        """
        Validate status choice.
        
        Args:
            value: Status value to validate
            
        Returns:
            str: Validated status
        """
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return value


class TaskCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for TaskComment model.
    
    Handles comment creation, updating, and serialization.
    Includes author information and computed fields.
    
    Fields:
        id: Comment ID (read-only)
        task: Task ID (required, read-only after creation)
        task_title: Task title (read-only)
        author: User ID of author (read-only)
        author_username: Author username (read-only)
        author_email: Author email (read-only)
        author_full_name: Author full name (read-only)
        content: Comment content (required, 1-2000 characters)
        is_edited: Whether comment has been edited (read-only)
        created_at: Comment creation timestamp (read-only)
        updated_at: Last update timestamp (read-only)
    """
    
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    # Author information
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.EmailField(source='author.email', read_only=True)
    author_full_name = serializers.SerializerMethodField(read_only=True)
    
    # Computed fields
    is_edited = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = TaskComment
        fields = [
            'id',
            'task',
            'task_title',
            'author',
            'author_username',
            'author_email',
            'author_full_name',
            'content',
            'is_edited',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'task_title',
            'author',
            'author_username',
            'author_email',
            'author_full_name',
            'is_edited',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'content': {
                'required': True,
                'help_text': 'Comment content (1-2000 characters)'
            },
            'task': {
                'required': True,
                'help_text': 'Task ID that this comment belongs to'
            },
        }
    
    def get_author_full_name(self, obj):
        """Return author's full name or username."""
        if obj.author:
            return obj.author.get_full_name_or_username()
        return None
    
    def get_is_edited(self, obj):
        """Return whether the comment has been edited."""
        return obj.is_edited()
    
    def validate_content(self, value):
        """
        Validate comment content.
        
        Args:
            value: Comment content to validate
            
        Returns:
            str: Validated comment content
            
        Raises:
            serializers.ValidationError: If content is invalid
        """
        # Strip whitespace
        value = value.strip()
        
        # Check minimum length
        if len(value) < 1:
            raise serializers.ValidationError(
                "Comment content cannot be empty."
            )
        
        # Check maximum length
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Comment content must not exceed 2000 characters."
            )
        
        return value
    
    def validate_task(self, value):
        """
        Validate that the task exists and user has access to it.
        
        Args:
            value: Task instance to validate
            
        Returns:
            Task: Validated task instance
            
        Raises:
            serializers.ValidationError: If task doesn't exist or user doesn't have access
        """
        if not value:
            raise serializers.ValidationError("Task is required.")
        
        # For updates, task should not be changed
        if self.instance:
            if value != self.instance.task:
                raise serializers.ValidationError(
                    "Cannot change the task of an existing comment."
                )
        
        # Check if user has access to the task (project member, assignee, or creator)
        request = self.context.get('request')
        if request and request.user:
            # Check if user is project member
            if not value.project.is_member(request.user):
                # Check if user is task assignee or creator
                if value.assignee != request.user and value.created_by != request.user:
                    raise serializers.ValidationError(
                        "You must be a member of the project, task assignee, or task creator to comment on this task."
                    )
        
        return value
    
    def create(self, validated_data):
        """
        Create a new comment and set the author.
        
        Args:
            validated_data: Validated comment data
            
        Returns:
            TaskComment: Created comment instance
        """
        # Set the author to the current user
        request = self.context.get('request')
        if request and request.user:
            validated_data['author'] = request.user
        
        return super().create(validated_data)

