"""
Admin configuration for Project models.

This module provides Django admin interface configuration
for Project and ProjectMember models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    """
    Inline admin for ProjectMember model.
    
    Allows editing project members directly from the project admin page.
    """
    model = ProjectMember
    extra = 1
    verbose_name_plural = _('Project Members')
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ['joined_at']
    autocomplete_fields = ['user']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for user."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
    Admin interface for Project model.
    
    Provides comprehensive project management interface with member management.
    """
    
    list_display = [
        'name',
        'team',
        'get_status_display_colored',
        'get_priority_display_colored',
        'get_member_count',
        'get_owner_display',
        'deadline',
        'get_deadline_status',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'status',
        'priority',
        'team',
        'created_at',
        'updated_at',
        'deadline'
    ]
    
    search_fields = [
        'name',
        'description',
        'team__name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'get_member_list', 'get_deadline_info']
    
    fieldsets = (
        (_('Project Information'), {
            'fields': ('name', 'description', 'team')
        }),
        (_('Project Status'), {
            'fields': ('status', 'priority', 'deadline', 'get_deadline_info')
        }),
        (_('Project Statistics'), {
            'fields': ('get_member_count', 'get_member_list'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    # Inline admin for ProjectMember
    inlines = [ProjectMemberInline]
    
    def get_member_count(self, obj):
        """Display total number of project members."""
        count = obj.get_member_count()
        return format_html(
            '<span style="font-weight: bold; color: #007cba;">{}</span>',
            count
        )
    get_member_count.short_description = _('Members')
    
    def get_owner_display(self, obj):
        """Display project owner."""
        owner = obj.get_owner()
        if owner:
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">{}</span>',
                owner.user.username
            )
        return format_html('<span style="color: #d63638;">No owner</span>')
    get_owner_display.short_description = _('Owner')
    
    def get_status_display_colored(self, obj):
        """Display status with color coding."""
        status_colors = {
            Project.STATUS_PLANNING: '#2271b1',
            Project.STATUS_ACTIVE: '#00a32a',
            Project.STATUS_ON_HOLD: '#dba617',
            Project.STATUS_COMPLETED: '#50575e',
            Project.STATUS_CANCELLED: '#d63638'
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
            Project.PRIORITY_HIGH: '#d63638',
            Project.PRIORITY_MEDIUM: '#dba617',
            Project.PRIORITY_LOW: '#2271b1'
        }
        color = priority_colors.get(obj.priority, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    get_priority_display_colored.short_description = _('Priority')
    get_priority_display_colored.admin_order_field = 'priority'
    
    def get_deadline_status(self, obj):
        """Display deadline with status indicator."""
        if not obj.deadline:
            return format_html('<span style="color: #757575;">No deadline</span>')
        
        if obj.is_overdue():
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">{} ⚠ Overdue</span>',
                obj.deadline.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.is_completed():
            return format_html(
                '<span style="color: #00a32a;">{} ✓</span>',
                obj.deadline.strftime('%Y-%m-%d %H:%M')
            )
        else:
            return format_html(
                '<span style="color: #2271b1;">{}</span>',
                obj.deadline.strftime('%Y-%m-%d %H:%M')
            )
    get_deadline_status.short_description = _('Deadline')
    get_deadline_status.admin_order_field = 'deadline'
    
    def get_deadline_info(self, obj):
        """Display detailed deadline information."""
        if not obj.deadline:
            return _('No deadline set')
        
        from django.utils import timezone
        now = timezone.now()
        time_diff = obj.deadline - now
        
        if obj.is_completed():
            return format_html(
                '<span style="color: #00a32a; font-weight: bold;">✓ Project completed</span>'
            )
        elif obj.is_overdue():
            days_overdue = abs(time_diff.days)
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">⚠ Overdue by {} day(s)</span>',
                days_overdue
            )
        else:
            days_remaining = time_diff.days
            if days_remaining < 7:
                return format_html(
                    '<span style="color: #dba617; font-weight: bold;">⚠ {} day(s) remaining</span>',
                    days_remaining
                )
            else:
                return format_html(
                    '<span style="color: #2271b1;">{} day(s) remaining</span>',
                    days_remaining
                )
    get_deadline_info.short_description = _('Deadline Info')
    
    def get_member_list(self, obj):
        """Display formatted list of all project members with their roles."""
        members = obj.get_members().select_related('user')
        if not members.exists():
            return _('No members yet')
        
        member_list = []
        for member in members:
            role_color = {
                ProjectMember.ROLE_OWNER: '#d63638',
                ProjectMember.ROLE_ADMIN: '#2271b1',
                ProjectMember.ROLE_MEMBER: '#50575e'
            }.get(member.role, '#50575e')
            
            member_list.append(
                format_html(
                    '<li style="margin-bottom: 5px;">'
                    '<span style="color: {}; font-weight: bold;">{}:</span> {} '
                    '<span style="color: #757575;">({})</span>'
                    '</li>',
                    role_color,
                    member.get_role_display(),
                    member.user.username,
                    member.user.email if member.user.email else 'No email'
                )
            )
        
        return format_html('<ul style="margin: 0; padding-left: 20px;">{}</ul>', 
                          format_html('').join(member_list))
    get_member_list.short_description = _('Member List')
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related and select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('team').prefetch_related('members__user')


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for ProjectMember model.
    
    Provides a dedicated admin interface for managing project memberships.
    """
    
    list_display = [
        'project',
        'user',
        'role',
        'joined_at',
        'get_role_display_colored'
    ]
    
    list_filter = [
        'role',
        'joined_at',
        'project',
        'project__team'
    ]
    
    search_fields = [
        'project__name',
        'project__team__name',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    
    readonly_fields = ['joined_at']
    
    fieldsets = (
        (_('Membership Information'), {
            'fields': ('project', 'user', 'role')
        }),
        (_('Timestamps'), {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-joined_at']
    
    autocomplete_fields = ['user', 'project']
    
    def get_role_display_colored(self, obj):
        """Display role with color coding."""
        role_colors = {
            ProjectMember.ROLE_OWNER: '#d63638',
            ProjectMember.ROLE_ADMIN: '#2271b1',
            ProjectMember.ROLE_MEMBER: '#50575e'
        }
        color = role_colors.get(obj.role, '#50575e')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    get_role_display_colored.short_description = _('Role')
    get_role_display_colored.admin_order_field = 'role'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for project, team, and user."""
        qs = super().get_queryset(request)
        return qs.select_related('project', 'project__team', 'user')
