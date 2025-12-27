"""
User models for Task Management System.

This module defines the custom User model and UserProfile model
for the task management application.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending AbstractUser.
    
    This model extends Django's AbstractUser to add custom fields
    for role-based access control and basic user information.
    
    Fields:
        role: User role for permission management (admin, manager, developer, member)
        avatar: Profile picture
        bio: Short biography/description
        phone: Contact phone number
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    
    # Role choices for role-based access control
    ROLE_CHOICES = [
        ('admin', _('Admin')),
        ('manager', _('Manager')),
        ('developer', _('Developer')),
        ('member', _('Member')),
    ]
    
    # Phone number validator (supports international format)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    # Custom fields
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        help_text=_('User role for permission management')
    )
    
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text=_('Profile picture')
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('Short biography or description')
    )
    
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Contact phone number')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Account creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last update timestamp')
    )
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return username as string representation."""
        return self.username
    
    def get_full_name_or_username(self):
        """Return full name if available, otherwise username."""
        full_name = self.get_full_name()
        return full_name if full_name else self.username
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_manager(self):
        """Check if user has manager role."""
        return self.role == 'manager'
    
    def is_developer(self):
        """Check if user has developer role."""
        return self.role == 'developer'
    
    def is_member(self):
        """Check if user has member role."""
        return self.role == 'member'
    
    def has_management_permissions(self):
        """Check if user has management-level permissions."""
        return self.role in ['admin', 'manager']


class UserProfile(models.Model):
    """
    Extended user profile information.
    
    This model stores additional profile information that is not
    required for authentication but provides richer user data.
    Uses OneToOne relationship with User model.
    """
    
    # Location fields
    LOCATION_CHOICES = [
        ('remote', _('Remote')),
        ('office', _('Office')),
        ('hybrid', _('Hybrid')),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('User'),
        help_text=_('Associated user account')
    )
    
    # Professional information
    job_title = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Job title or position')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Department or team name')
    )
    
    location = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES,
        blank=True,
        help_text=_('Work location preference')
    )
    
    # Contact information
    address = models.TextField(
        max_length=200,
        blank=True,
        help_text=_('Physical address')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('City')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Country')
    )
    
    # Social links
    website = models.URLField(
        blank=True,
        help_text=_('Personal or professional website')
    )
    
    linkedin = models.URLField(
        blank=True,
        help_text=_('LinkedIn profile URL')
    )
    
    github = models.URLField(
        blank=True,
        help_text=_('GitHub profile URL')
    )
    
    twitter = models.URLField(
        blank=True,
        help_text=_('Twitter profile URL')
    )
    
    # Additional information
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text=_('User timezone')
    )
    
    language = models.CharField(
        max_length=10,
        default='en',
        help_text=_('Preferred language code')
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_('Enable email notifications')
    )
    
    push_notifications = models.BooleanField(
        default=True,
        help_text=_('Enable push notifications')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Profile creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last profile update timestamp')
    )
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return user's username as string representation."""
        return f"{self.user.username}'s Profile"
    
    def get_display_name(self):
        """Return user's display name."""
        return self.user.get_full_name_or_username()
    
    def has_complete_profile(self):
        """Check if profile has essential information filled."""
        return bool(
            self.job_title and
            self.department and
            self.user.email
        )
