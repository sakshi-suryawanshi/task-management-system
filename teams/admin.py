"""
Admin configuration for Team models.

This module provides Django admin interface configuration
for Team and TeamMember models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Team, TeamMember


class TeamMemberInline(admin.TabularInline):
    """
    Inline admin for TeamMember model.
    
    Allows editing team members directly from the team admin page.
    """
    model = TeamMember
    extra = 1
    verbose_name_plural = _('Team Members')
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ['joined_at']
    autocomplete_fields = ['user']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for user."""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """
    Admin interface for Team model.
    
    Provides comprehensive team management interface with member management.
    """
    
    list_display = [
        'name',
        'get_member_count',
        'get_owner_display',
        'get_admin_count',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'name',
        'description'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'get_member_list']
    
    fieldsets = (
        (_('Team Information'), {
            'fields': ('name', 'description')
        }),
        (_('Team Statistics'), {
            'fields': ('get_member_count', 'get_member_list'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    # Inline admin for TeamMember
    inlines = [TeamMemberInline]
    
    def get_member_count(self, obj):
        """Display total number of team members."""
        count = obj.get_member_count()
        return format_html(
            '<span style="font-weight: bold; color: #007cba;">{}</span>',
            count
        )
    get_member_count.short_description = _('Members')
    
    def get_owner_display(self, obj):
        """Display team owner."""
        owner = obj.get_owner()
        if owner:
            return format_html(
                '<span style="color: #d63638; font-weight: bold;">{}</span>',
                owner.user.username
            )
        return format_html('<span style="color: #d63638;">No owner</span>')
    get_owner_display.short_description = _('Owner')
    
    def get_admin_count(self, obj):
        """Display number of admin members (excluding owner)."""
        count = obj.get_admins().exclude(role=TeamMember.ROLE_OWNER).count()
        if count > 0:
            return format_html(
                '<span style="color: #2271b1;">{}</span>',
                count
            )
        return '-'
    get_admin_count.short_description = _('Admins')
    
    def get_member_list(self, obj):
        """Display formatted list of all team members with their roles."""
        members = obj.get_members().select_related('user')
        if not members.exists():
            return _('No members yet')
        
        member_list = []
        for member in members:
            role_color = {
                TeamMember.ROLE_OWNER: '#d63638',
                TeamMember.ROLE_ADMIN: '#2271b1',
                TeamMember.ROLE_MEMBER: '#50575e'
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
        """Optimize queryset with prefetch_related for members."""
        qs = super().get_queryset(request)
        return qs.prefetch_related('members__user')


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for TeamMember model.
    
    Provides a dedicated admin interface for managing team memberships.
    """
    
    list_display = [
        'team',
        'user',
        'role',
        'joined_at',
        'get_role_display_colored'
    ]
    
    list_filter = [
        'role',
        'joined_at',
        'team'
    ]
    
    search_fields = [
        'team__name',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    
    readonly_fields = ['joined_at']
    
    fieldsets = (
        (_('Membership Information'), {
            'fields': ('team', 'user', 'role')
        }),
        (_('Timestamps'), {
            'fields': ('joined_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-joined_at']
    
    autocomplete_fields = ['user', 'team']
    
    def get_role_display_colored(self, obj):
        """Display role with color coding."""
        role_colors = {
            TeamMember.ROLE_OWNER: '#d63638',
            TeamMember.ROLE_ADMIN: '#2271b1',
            TeamMember.ROLE_MEMBER: '#50575e'
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
        """Optimize queryset with select_related for team and user."""
        qs = super().get_queryset(request)
        return qs.select_related('team', 'user')
