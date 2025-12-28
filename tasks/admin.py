"""
Admin configuration for Task models.

This module provides Django admin interface configuration
for Task, TaskDependency, TaskComment, and TaskAttachment models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Task, TaskDependency, TaskComment, TaskAttachment


class TaskCommentInline(admin.TabularInline):
    """
    Inline admin for TaskComment model.
    
    Allows viewing and managing task comments directly from the task admin page.
    """
    model = TaskComment
    extra = 0
    verbose_name_plural = _('Comments')
    fields = ('author', 'content', 'created_at')
    readonly_fields = ['created_at']
    autocomplete_fields = ['author']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for author."""
        qs = super().get_queryset(request)
        return qs.select_related('author')


class TaskAttachmentInline(admin.TabularInline):
    """
    Inline admin for TaskAttachment model.
    
    Allows viewing task attachments directly from the task admin page.
    """
    model = TaskAttachment
    extra = 0
    verbose_name_plural = _('Attachments')
    fields = ('filename', 'file', 'uploaded_by', 'file_size', 'created_at')
    readonly_fields = ['filename', 'uploaded_by', 'file_size', 'created_at']
    autocomplete_fields = ['uploaded_by']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for uploaded_by."""
        qs = super().get_queryset(request)
        return qs.select_related('uploaded_by')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    Admin interface for Task model.
    
    Provides comprehensive task management interface with comments,
    attachments, and dependency management.
    """
    
    list_display = [
        'title',
        'project',
        'get_status_display_colored',
        'get_priority_display_colored',
        'assignee',
        'created_by',
        'due_date',
        'get_due_date_status',
        'get_comment_count',
        'get_attachment_count',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'status',
        'priority',
        'project',
        'project__team',
        'assignee',
        'created_by',
        'created_at',
        'updated_at',
        'due_date'
    ]
    
    search_fields = [
        'title',
        'description',
        'project__name',
        'project__team__name',
        'assignee__username',
        'assignee__email',
        'created_by__username',
        'created_by__email'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'get_dependencies_list',
        'get_dependents_list',
        'get_comments_list',
        'get_attachments_list',
        'get_due_date_info'
    ]
    
    fieldsets = (
        (_('Task Information'), {
            'fields': ('title', 'description', 'project')
        }),
        (_('Task Status'), {
            'fields': ('status', 'priority', 'due_date', 'get_due_date_info')
        }),
        (_('Assignment'), {
            'fields': ('assignee', 'created_by')
        }),
        (_('Dependencies'), {
            'fields': ('get_dependencies_list', 'get_dependents_list'),
            'classes': ('collapse',)
        }),
        (_('Task Statistics'), {
            'fields': ('get_comment_count', 'get_attachment_count', 'get_comments_list', 'get_attachments_list'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    # Inline admin for comments and attachments
    inlines = [TaskCommentInline, TaskAttachmentInline]
    
    autocomplete_fields = ['project', 'assignee', 'created_by']
    
    def get_status_display_colored(self, obj):
        """Display status with color coding."""
        status_colors = {
            Task.STATUS_TODO: '#2271b1',
            Task.STATUS_IN_PROGRESS: '#00a32a',
            Task.STATUS_DONE: '#50575e',
            Task.STATUS_BLOCKED: '#d63638'
        }
        color = status_colors.get(obj.status, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_display_colored.short_description = _('Status')
    get_status_display_colored.admin_order_field = 'status'
    
    def get_priority_display_colored(self, obj):
        """Display priority with color coding."""
        priority_colors = {
            Task.PRIORITY_HIGH: '#d63638',
            Task.PRIORITY_MEDIUM: '#dba617',
            Task.PRIORITY_LOW: '#2271b1'
        }
        color = priority_colors.get(obj.priority, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    get_priority_display_colored.short_description = _('Priority')
    get_priority_display_colored.admin_order_field = 'priority'
    
    def get_due_date_status(self, obj):
        """Display due date with status indicator."""
        if not obj.due_date:
            return format_html('<span style="color: #757575;">No due date</span>')
        
        if obj.is_overdue():
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">{} ⚠ Overdue</span>',
                obj.due_date.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.is_done():
            return format_html(
                '<span style="color: #00a32a;">{} ✓</span>',
                obj.due_date.strftime('%Y-%m-%d %H:%M')
            )
        else:
            days_until = obj.get_days_until_due()
            if days_until is not None and days_until < 3:
                return format_html(
                    '<span style="color: #dba617; font-weight: bold;">{} ⚠ {} day(s)</span>',
                    obj.due_date.strftime('%Y-%m-%d %H:%M'),
                    days_until
                )
            else:
                return format_html(
                    '<span style="color: #2271b1;">{}</span>',
                    obj.due_date.strftime('%Y-%m-%d %H:%M')
                )
    get_due_date_status.short_description = _('Due Date')
    get_due_date_status.admin_order_field = 'due_date'
    
    def get_due_date_info(self, obj):
        """Display detailed due date information."""
        if not obj.due_date:
            return _('No due date set')
        
        from django.utils import timezone
        now = timezone.now()
        time_diff = obj.due_date - now
        
        if obj.is_done():
            return format_html(
                '<span style="color: #00a32a; font-weight: bold;">✓ Task completed</span>'
            )
        elif obj.is_overdue():
            days_overdue = abs(time_diff.days)
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">⚠ Overdue by {} day(s)</span>',
                days_overdue
            )
        else:
            days_remaining = time_diff.days
            if days_remaining < 3:
                return format_html(
                    '<span style="color: #dba617; font-weight: bold;">⚠ {} day(s) remaining</span>',
                    days_remaining
                )
            else:
                return format_html(
                    '<span style="color: #2271b1;">{} day(s) remaining</span>',
                    days_remaining
                )
    get_due_date_info.short_description = _('Due Date Info')
    
    def get_comment_count(self, obj):
        """Display total number of comments."""
        count = obj.get_comment_count()
        return format_html(
            '<span style="font-weight: bold; color: #007cba;">{}</span>',
            count
        )
    get_comment_count.short_description = _('Comments')
    
    def get_attachment_count(self, obj):
        """Display total number of attachments."""
        count = obj.get_attachment_count()
        return format_html(
            '<span style="font-weight: bold; color: #007cba;">{}</span>',
            count
        )
    get_attachment_count.short_description = _('Attachments')
    
    def get_dependencies_list(self, obj):
        """Display formatted list of prerequisite tasks."""
        dependencies = obj.get_dependencies().select_related('project')
        if not dependencies.exists():
            return _('No dependencies')
        
        dep_list = []
        for dep in dependencies:
            status_color = {
                Task.STATUS_TODO: '#2271b1',
                Task.STATUS_IN_PROGRESS: '#00a32a',
                Task.STATUS_DONE: '#50575e',
                Task.STATUS_BLOCKED: '#d63638'
            }.get(dep.status, '#50575e')
            
            dep_url = reverse('admin:tasks_task_change', args=[dep.id])
            dep_list.append(
                format_html(
                    '<li style="margin-bottom: 5px;">'
                    '<a href="{}" style="text-decoration: none;">{}</a> '
                    '<span style="color: {};">({})</span>'
                    '</li>',
                    dep_url,
                    dep.title,
                    status_color,
                    dep.get_status_display()
                )
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          format_html('').join(dep_list))
    get_dependencies_list.short_description = _('Dependencies (Prerequisites)')
    
    def get_dependents_list(self, obj):
        """Display formatted list of tasks that depend on this task."""
        dependents = obj.get_dependents().select_related('project')
        if not dependents.exists():
            return _('No dependents')
        
        dep_list = []
        for dep in dependents:
            status_color = {
                Task.STATUS_TODO: '#2271b1',
                Task.STATUS_IN_PROGRESS: '#00a32a',
                Task.STATUS_DONE: '#50575e',
                Task.STATUS_BLOCKED: '#d63638'
            }.get(dep.status, '#50575e')
            
            dep_url = reverse('admin:tasks_task_change', args=[dep.id])
            dep_list.append(
                format_html(
                    '<li style="margin-bottom: 5px;">'
                    '<a href="{}" style="text-decoration: none;">{}</a> '
                    '<span style="color: {};">({})</span>'
                    '</li>',
                    dep_url,
                    dep.title,
                    status_color,
                    dep.get_status_display()
                )
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          format_html('').join(dep_list))
    get_dependents_list.short_description = _('Dependents')
    
    def get_comments_list(self, obj):
        """Display formatted list of all task comments."""
        comments = obj.get_comments().select_related('author')
        if not comments.exists():
            return _('No comments yet')
        
        comment_list = []
        for comment in comments[:5]:  # Show only first 5 comments
            author_name = comment.author.username if comment.author else 'Unknown'
            comment_list.append(
                format_html(
                    '<li style="margin-bottom: 10px; padding: 5px; background: #f5f5f5; border-radius: 3px;">'
                    '<strong>{}</strong> <span style="color: #757575;">({})</span><br>'
                    '<span style="color: #50575e;">{}</span>'
                    '</li>',
                    author_name,
                    comment.created_at.strftime('%Y-%m-%d %H:%M'),
                    comment.content[:100] + ('...' if len(comment.content) > 100 else '')
                )
            )
        
        if comments.count() > 5:
            comment_list.append(
                format_html(
                    '<li style="color: #757575; font-style: italic;">... and {} more comments</li>',
                    comments.count() - 5
                )
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          format_html('').join(comment_list))
    get_comments_list.short_description = _('Comments List')
    
    def get_attachments_list(self, obj):
        """Display formatted list of all task attachments."""
        attachments = obj.get_attachments().select_related('uploaded_by')
        if not attachments.exists():
            return _('No attachments yet')
        
        attach_list = []
        for attachment in attachments[:5]:  # Show only first 5 attachments
            uploader_name = attachment.uploaded_by.username if attachment.uploaded_by else 'Unknown'
            attach_list.append(
                format_html(
                    '<li style="margin-bottom: 5px;">'
                    '<strong>{}</strong> '
                    '<span style="color: #757575;">({})</span> '
                    '<span style="color: #757575;">by {}</span>'
                    '</li>',
                    attachment.filename,
                    attachment.get_file_size_display(),
                    uploader_name
                )
            )
        
        if attachments.count() > 5:
            attach_list.append(
                format_html(
                    '<li style="color: #757575; font-style: italic;">... and {} more attachments</li>',
                    attachments.count() - 5
                )
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          format_html('').join(attach_list))
    get_attachments_list.short_description = _('Attachments List')
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related and select_related."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'project',
            'project__team',
            'assignee',
            'created_by'
        ).prefetch_related(
            'comments__author',
            'attachments__uploaded_by'
        )


@admin.register(TaskDependency)
class TaskDependencyAdmin(admin.ModelAdmin):
    """
    Admin interface for TaskDependency model.
    
    Provides a dedicated admin interface for managing task dependencies.
    """
    
    list_display = [
        'prerequisite_task',
        'dependent_task',
        'get_prerequisite_status',
        'get_dependent_status',
        'created_at'
    ]
    
    list_filter = [
        'created_at',
        'prerequisite_task__project',
        'dependent_task__project'
    ]
    
    search_fields = [
        'prerequisite_task__title',
        'prerequisite_task__project__name',
        'dependent_task__title',
        'dependent_task__project__name'
    ]
    
    readonly_fields = ['created_at']
    
    fieldsets = (
        (_('Dependency Information'), {
            'fields': ('prerequisite_task', 'dependent_task')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    autocomplete_fields = ['prerequisite_task', 'dependent_task']
    
    def get_prerequisite_status(self, obj):
        """Display prerequisite task status with color coding."""
        status_colors = {
            Task.STATUS_TODO: '#2271b1',
            Task.STATUS_IN_PROGRESS: '#00a32a',
            Task.STATUS_DONE: '#50575e',
            Task.STATUS_BLOCKED: '#d63638'
        }
        color = status_colors.get(obj.prerequisite_task.status, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.prerequisite_task.get_status_display()
        )
    get_prerequisite_status.short_description = _('Prerequisite Status')
    
    def get_dependent_status(self, obj):
        """Display dependent task status with color coding."""
        status_colors = {
            Task.STATUS_TODO: '#2271b1',
            Task.STATUS_IN_PROGRESS: '#00a32a',
            Task.STATUS_DONE: '#50575e',
            Task.STATUS_BLOCKED: '#d63638'
        }
        color = status_colors.get(obj.dependent_task.status, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.dependent_task.get_status_display()
        )
    get_dependent_status.short_description = _('Dependent Status')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for tasks and projects."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'prerequisite_task',
            'prerequisite_task__project',
            'dependent_task',
            'dependent_task__project'
        )


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """
    Admin interface for TaskComment model.
    
    Provides a dedicated admin interface for managing task comments.
    """
    
    list_display = [
        'task',
        'author',
        'get_content_preview',
        'is_edited',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'created_at',
        'updated_at',
        'task__project',
        'task__status'
    ]
    
    search_fields = [
        'content',
        'task__title',
        'task__project__name',
        'author__username',
        'author__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'is_edited']
    
    fieldsets = (
        (_('Comment Information'), {
            'fields': ('task', 'author', 'content')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    autocomplete_fields = ['task', 'author']
    
    def get_content_preview(self, obj):
        """Display comment content preview (first 50 characters)."""
        preview = obj.content[:50]
        if len(obj.content) > 50:
            preview += '...'
        return preview
    get_content_preview.short_description = _('Content')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for task, author, and project."""
        qs = super().get_queryset(request)
        return qs.select_related('task', 'task__project', 'author')


@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    """
    Admin interface for TaskAttachment model.
    
    Provides a dedicated admin interface for managing task attachments.
    """
    
    list_display = [
        'filename',
        'task',
        'uploaded_by',
        'get_file_size_display',
        'file_type',
        'created_at'
    ]
    
    list_filter = [
        'file_type',
        'created_at',
        'task__project',
        'task__status'
    ]
    
    search_fields = [
        'filename',
        'task__title',
        'task__project__name',
        'uploaded_by__username',
        'uploaded_by__email'
    ]
    
    readonly_fields = ['created_at', 'file_size', 'file_type', 'get_file_size_display']
    
    fieldsets = (
        (_('Attachment Information'), {
            'fields': ('task', 'file', 'uploaded_by', 'filename')
        }),
        (_('File Information'), {
            'fields': ('file_size', 'get_file_size_display', 'file_type')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    autocomplete_fields = ['task', 'uploaded_by']
    
    def get_file_size_display(self, obj):
        """Display human-readable file size."""
        return obj.get_file_size_display()
    get_file_size_display.short_description = _('File Size')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for task, uploaded_by, and project."""
        qs = super().get_queryset(request)
        return qs.select_related('task', 'task__project', 'uploaded_by')
