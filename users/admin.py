"""
Admin configuration for User models.

This module provides Django admin interface configuration
for User and UserProfile models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for UserProfile model.
    
    Allows editing user profile information directly from the user admin page.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profile Information')
    fieldsets = (
        (_('Professional Information'), {
            'fields': ('job_title', 'department', 'location')
        }),
        (_('Contact Information'), {
            'fields': ('address', 'city', 'country', 'timezone')
        }),
        (_('Social Links'), {
            'fields': ('website', 'linkedin', 'github', 'twitter'),
            'classes': ('collapse',)
        }),
        (_('Preferences'), {
            'fields': ('email_notifications', 'push_notifications', 'language')
        }),
    )
    extra = 0
    max_num = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    
    Extends Django's default UserAdmin to include custom fields
    and improved organization.
    """
    
    # List display configuration
    list_display = [
        'username',
        'email',
        'get_full_name',
        'role',
        'is_active',
        'is_staff',
        'created_at',
        'get_profile_status'
    ]
    
    list_filter = [
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
        'date_joined'
    ]
    
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'phone'
    ]
    
    ordering = ['-created_at']
    
    # Fieldsets for add/edit forms
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'email', 'avatar', 'bio', 'phone')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Role & Status'), {
            'fields': ('role',)
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']
    
    # Inline admin for UserProfile
    inlines = [UserProfileInline]
    
    def get_full_name(self, obj):
        """Return user's full name or username."""
        return obj.get_full_name() or obj.username
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'first_name'
    
    def get_profile_status(self, obj):
        """Display profile completion status."""
        try:
            profile = obj.profile
            if profile.has_complete_profile():
                return format_html(
                    '<span style="color: green;">✓ Complete</span>'
                )
            else:
                return format_html(
                    '<span style="color: orange;">⚠ Incomplete</span>'
                )
        except UserProfile.DoesNotExist:
            return format_html(
                '<span style="color: red;">✗ No Profile</span>'
            )
    get_profile_status.short_description = _('Profile Status')
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for profile."""
        qs = super().get_queryset(request)
        return qs.select_related('profile')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    
    Provides a dedicated admin interface for managing user profiles.
    """
    
    list_display = [
        'user',
        'job_title',
        'department',
        'location',
        'email_notifications',
        'created_at'
    ]
    
    list_filter = [
        'location',
        'email_notifications',
        'push_notifications',
        'created_at',
        'country'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'job_title',
        'department',
        'city',
        'country'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('User'), {
            'fields': ('user',)
        }),
        (_('Professional Information'), {
            'fields': ('job_title', 'department', 'location')
        }),
        (_('Contact Information'), {
            'fields': ('address', 'city', 'country', 'timezone')
        }),
        (_('Social Links'), {
            'fields': ('website', 'linkedin', 'github', 'twitter'),
            'classes': ('collapse',)
        }),
        (_('Preferences'), {
            'fields': ('email_notifications', 'push_notifications', 'language')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for user."""
        qs = super().get_queryset(request)
        return qs.select_related('user')
