"""
Task models for Task Management System.

This module defines the Task model, TaskDependency model, TaskComment model,
and TaskAttachment model for task management functionality.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os


class Task(models.Model):
    """
    Task model for managing individual tasks within projects.
    
    Tasks belong to projects and can be assigned to users.
    Each task has status, priority, due date, and can have dependencies,
    comments, and attachments.
    
    Fields:
        title: Task title
        description: Detailed description of the task
        status: Current task status (todo, in_progress, done, blocked)
        priority: Task priority level (high, medium, low)
        due_date: Task due date (optional)
        project: ForeignKey to Project
        assignee: ForeignKey to User (optional)
        created_by: ForeignKey to User (task creator)
        created_at: Task creation timestamp
        updated_at: Last update timestamp
    """
    
    # Status constants
    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_BLOCKED = 'blocked'
    
    STATUS_CHOICES = [
        (STATUS_TODO, _('To Do')),
        (STATUS_IN_PROGRESS, _('In Progress')),
        (STATUS_DONE, _('Done')),
        (STATUS_BLOCKED, _('Blocked')),
    ]
    
    # Priority constants
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'
    
    PRIORITY_CHOICES = [
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low')),
    ]
    
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text=_('Task title')
    )
    
    description = models.TextField(
        max_length=2000,
        blank=True,
        help_text=_('Detailed description of the task')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_TODO,
        db_index=True,
        help_text=_('Current task status')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Task due date (optional)')
    )
    
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Project'),
        help_text=_('The project this task belongs to')
    )
    
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name=_('Assignee'),
        help_text=_('User assigned to this task')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name=_('Created By'),
        help_text=_('User who created this task')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Task creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last update timestamp')
    )
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['project']),
            models.Index(fields=['assignee']),
            models.Index(fields=['created_at']),
            models.Index(fields=['project', 'status']),
            models.Index(fields=['project', 'priority']),
            models.Index(fields=['assignee', 'status']),
        ]
    
    def __str__(self):
        """Return task title as string representation."""
        return f"{self.title} ({self.project.name})"
    
    def get_dependencies(self):
        """
        Get all tasks that this task depends on.
        
        Returns:
            QuerySet: All Task instances that this task depends on
        """
        return Task.objects.filter(
            taskdependencies__dependent_task=self
        ).distinct()
    
    def get_dependents(self):
        """
        Get all tasks that depend on this task.
        
        Returns:
            QuerySet: All Task instances that depend on this task
        """
        return Task.objects.filter(
            taskdependencies__prerequisite_task=self
        ).distinct()
    
    def get_comments(self):
        """
        Get all comments for this task.
        
        Returns:
            QuerySet: All TaskComment instances for this task
        """
        return self.comments.all()
    
    def get_comment_count(self):
        """
        Get the total number of comments for this task.
        
        Returns:
            int: Number of comments
        """
        return self.comments.count()
    
    def get_attachments(self):
        """
        Get all attachments for this task.
        
        Returns:
            QuerySet: All TaskAttachment instances for this task
        """
        return self.attachments.all()
    
    def get_attachment_count(self):
        """
        Get the total number of attachments for this task.
        
        Returns:
            int: Number of attachments
        """
        return self.attachments.count()
    
    def is_overdue(self):
        """
        Check if the task due date has passed and task is not done.
        
        Returns:
            bool: True if due date has passed and task is not done
        """
        if not self.due_date:
            return False
        if self.status == self.STATUS_DONE:
            return False
        return timezone.now() > self.due_date
    
    def is_done(self):
        """
        Check if the task is completed.
        
        Returns:
            bool: True if task status is done
        """
        return self.status == self.STATUS_DONE
    
    def is_blocked(self):
        """
        Check if the task is blocked.
        
        Returns:
            bool: True if task status is blocked
        """
        return self.status == self.STATUS_BLOCKED
    
    def is_in_progress(self):
        """
        Check if the task is in progress.
        
        Returns:
            bool: True if task status is in progress
        """
        return self.status == self.STATUS_IN_PROGRESS
    
    def is_todo(self):
        """
        Check if the task is in todo status.
        
        Returns:
            bool: True if task status is todo
        """
        return self.status == self.STATUS_TODO
    
    def can_be_completed(self):
        """
        Check if the task can be marked as done.
        
        A task can be completed if all prerequisite tasks are done.
        
        Returns:
            bool: True if all dependencies are completed
        """
        prerequisites = self.get_dependencies()
        if not prerequisites.exists():
            return True
        return prerequisites.filter(status=self.STATUS_DONE).count() == prerequisites.count()
    
    def get_status_display_class(self):
        """
        Get CSS class name for status display (for admin/frontend).
        
        Returns:
            str: CSS class name for status
        """
        status_classes = {
            self.STATUS_TODO: 'todo',
            self.STATUS_IN_PROGRESS: 'in-progress',
            self.STATUS_DONE: 'done',
            self.STATUS_BLOCKED: 'blocked',
        }
        return status_classes.get(self.status, '')
    
    def get_priority_display_class(self):
        """
        Get CSS class name for priority display (for admin/frontend).
        
        Returns:
            str: CSS class name for priority
        """
        priority_classes = {
            self.PRIORITY_HIGH: 'high',
            self.PRIORITY_MEDIUM: 'medium',
            self.PRIORITY_LOW: 'low',
        }
        return priority_classes.get(self.priority, '')
    
    def get_days_until_due(self):
        """
        Get the number of days until the due date.
        
        Returns:
            int or None: Number of days until due, or None if no due date
        """
        if not self.due_date:
            return None
        time_diff = self.due_date - timezone.now()
        return time_diff.days
    
    def is_assigned(self):
        """
        Check if the task is assigned to a user.
        
        Returns:
            bool: True if task has an assignee
        """
        return self.assignee is not None


class TaskDependency(models.Model):
    """
    TaskDependency model representing dependencies between tasks.
    
    This model creates a self-referential relationship between tasks,
    allowing tasks to depend on other tasks. A task cannot be completed
    until all its prerequisite tasks are completed.
    
    Fields:
        prerequisite_task: Task that must be completed first
        dependent_task: Task that depends on the prerequisite
        created_at: Dependency creation timestamp
    """
    
    prerequisite_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='dependent_tasks',
        verbose_name=_('Prerequisite Task'),
        help_text=_('Task that must be completed first')
    )
    
    dependent_task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='prerequisite_tasks',
        verbose_name=_('Dependent Task'),
        help_text=_('Task that depends on the prerequisite')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Dependency creation timestamp')
    )
    
    class Meta:
        db_table = 'task_dependencies'
        unique_together = [['prerequisite_task', 'dependent_task']]
        ordering = ['-created_at']
        verbose_name = _('Task Dependency')
        verbose_name_plural = _('Task Dependencies')
        indexes = [
            models.Index(fields=['prerequisite_task']),
            models.Index(fields=['dependent_task']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return string representation of task dependency."""
        return f"{self.dependent_task.title} depends on {self.prerequisite_task.title}"
    
    def clean(self):
        """
        Validate that a task cannot depend on itself.
        
        Raises:
            ValidationError: If prerequisite and dependent tasks are the same
        """
        from django.core.exceptions import ValidationError
        if self.prerequisite_task == self.dependent_task:
            raise ValidationError(_('A task cannot depend on itself.'))
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation."""
        self.clean()
        super().save(*args, **kwargs)


class TaskComment(models.Model):
    """
    TaskComment model for comments on tasks.
    
    Allows users to add comments to tasks for collaboration and communication.
    
    Fields:
        task: ForeignKey to Task
        author: ForeignKey to User (comment author)
        content: Comment text content
        created_at: Comment creation timestamp
        updated_at: Last update timestamp
    """
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Task'),
        help_text=_('The task this comment belongs to')
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_comments',
        verbose_name=_('Author'),
        help_text=_('User who wrote this comment')
    )
    
    content = models.TextField(
        max_length=2000,
        help_text=_('Comment content')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Comment creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last update timestamp')
    )
    
    class Meta:
        db_table = 'task_comments'
        ordering = ['-created_at']
        verbose_name = _('Task Comment')
        verbose_name_plural = _('Task Comments')
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['author']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return string representation of task comment."""
        author_name = self.author.username if self.author else 'Unknown'
        return f"Comment by {author_name} on {self.task.title}"
    
    def is_edited(self):
        """
        Check if the comment has been edited.
        
        Returns:
            bool: True if comment was edited (updated_at > created_at)
        """
        return self.updated_at > self.created_at


def task_attachment_upload_path(instance, filename):
    """
    Generate upload path for task attachments.
    
    Args:
        instance: TaskAttachment instance
        filename: Original filename
        
    Returns:
        str: Upload path for the file
    """
    # Organize by task ID and date
    task_id = instance.task.id
    date_path = timezone.now().strftime('%Y/%m/%d')
    return f'task_attachments/{task_id}/{date_path}/{filename}'


class TaskAttachment(models.Model):
    """
    TaskAttachment model for file attachments on tasks.
    
    Allows users to attach files to tasks for documentation and collaboration.
    
    Fields:
        task: ForeignKey to Task
        uploaded_by: ForeignKey to User (uploader)
        file: FileField for the attachment
        filename: Original filename
        file_size: File size in bytes
        file_type: File type/extension
        created_at: Attachment creation timestamp
    """
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Task'),
        help_text=_('The task this attachment belongs to')
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        verbose_name=_('Uploaded By'),
        help_text=_('User who uploaded this attachment')
    )
    
    file = models.FileField(
        upload_to=task_attachment_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                                  'txt', 'csv', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif',
                                  'svg', 'mp4', 'avi', 'mov', 'mp3', 'wav']
            )
        ],
        help_text=_('File attachment')
    )
    
    filename = models.CharField(
        max_length=255,
        help_text=_('Original filename')
    )
    
    file_size = models.PositiveIntegerField(
        help_text=_('File size in bytes')
    )
    
    file_type = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('File type/extension')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Attachment creation timestamp')
    )
    
    class Meta:
        db_table = 'task_attachments'
        ordering = ['-created_at']
        verbose_name = _('Task Attachment')
        verbose_name_plural = _('Task Attachments')
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['created_at']),
            models.Index(fields=['file_type']),
        ]
    
    def __str__(self):
        """Return string representation of task attachment."""
        return f"{self.filename} ({self.task.title})"
    
    def save(self, *args, **kwargs):
        """
        Override save to extract filename and file size.
        
        Automatically extracts filename and file size from the uploaded file.
        """
        if self.file and not self.filename:
            self.filename = os.path.basename(self.file.name)
        
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (AttributeError, OSError):
                pass
        
        if self.file and not self.file_type:
            ext = os.path.splitext(self.filename)[1].lower().lstrip('.')
            self.file_type = ext
        
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """
        Get human-readable file size.
        
        Returns:
            str: Human-readable file size (e.g., "1.5 MB")
        """
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_file_icon(self):
        """
        Get icon class name for file type (for frontend display).
        
        Returns:
            str: Icon class name based on file type
        """
        icon_map = {
            'pdf': 'file-pdf',
            'doc': 'file-word',
            'docx': 'file-word',
            'xls': 'file-excel',
            'xlsx': 'file-excel',
            'ppt': 'file-powerpoint',
            'pptx': 'file-powerpoint',
            'txt': 'file-text',
            'csv': 'file-csv',
            'zip': 'file-archive',
            'rar': 'file-archive',
            'jpg': 'file-image',
            'jpeg': 'file-image',
            'png': 'file-image',
            'gif': 'file-image',
            'svg': 'file-image',
            'mp4': 'file-video',
            'avi': 'file-video',
            'mov': 'file-video',
            'mp3': 'file-audio',
            'wav': 'file-audio',
        }
        return icon_map.get(self.file_type.lower(), 'file')
