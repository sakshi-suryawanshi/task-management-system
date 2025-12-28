"""
Project models for Task Management System.

This module defines the Project model and ProjectMember model
for project management functionality.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Project(models.Model):
    """
    Project model for organizing tasks within teams.
    
    Projects belong to teams and contain multiple tasks.
    Each project has members with different roles (owner, admin, member).
    
    Fields:
        name: Project name
        description: Detailed description of the project
        status: Current project status (planning, active, on_hold, completed, cancelled)
        priority: Project priority level (high, medium, low)
        deadline: Project deadline (optional)
        team: ForeignKey to Team
        created_at: Project creation timestamp
        updated_at: Last update timestamp
    """
    
    # Status constants
    STATUS_PLANNING = 'planning'
    STATUS_ACTIVE = 'active'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PLANNING, _('Planning')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_ON_HOLD, _('On Hold')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELLED, _('Cancelled')),
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
    
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text=_('Project name')
    )
    
    description = models.TextField(
        max_length=1000,
        blank=True,
        help_text=_('Detailed description of the project')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PLANNING,
        db_index=True,
        help_text=_('Current project status')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        db_index=True,
        help_text=_('Project priority level')
    )
    
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Project deadline (optional)')
    )
    
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name=_('Team'),
        help_text=_('The team this project belongs to')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Project creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last update timestamp')
    )
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['deadline']),
            models.Index(fields=['team']),
            models.Index(fields=['created_at']),
            models.Index(fields=['team', 'status']),
            models.Index(fields=['team', 'priority']),
        ]
        # Ensure unique project names within a team
        unique_together = [['team', 'name']]
    
    def __str__(self):
        """Return project name as string representation."""
        return f"{self.name} ({self.team.name})"
    
    def get_members(self):
        """
        Get all members of this project.
        
        Returns:
            QuerySet: All ProjectMember instances for this project
        """
        return self.members.all()
    
    def get_member_count(self):
        """
        Get the total number of members in this project.
        
        Returns:
            int: Number of project members
        """
        return self.members.count()
    
    def get_owner(self):
        """
        Get the owner of this project.
        
        Returns:
            ProjectMember or None: The project owner, or None if no owner exists
        """
        return self.members.filter(role=ProjectMember.ROLE_OWNER).first()
    
    def get_admins(self):
        """
        Get all admin members of this project.
        
        Returns:
            QuerySet: All admin ProjectMember instances
        """
        return self.members.filter(role=ProjectMember.ROLE_ADMIN)
    
    def get_regular_members(self):
        """
        Get all regular member (non-admin, non-owner) members.
        
        Returns:
            QuerySet: All regular member ProjectMember instances
        """
        return self.members.filter(role=ProjectMember.ROLE_MEMBER)
    
    def is_member(self, user):
        """
        Check if a user is a member of this project.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is a member, False otherwise
        """
        return self.members.filter(user=user).exists()
    
    def get_member_role(self, user):
        """
        Get the role of a user in this project.
        
        Args:
            user: User instance
            
        Returns:
            str or None: User's role in the project, or None if not a member
        """
        try:
            member = self.members.get(user=user)
            return member.role
        except ProjectMember.DoesNotExist:
            return None
    
    def is_owner(self, user):
        """
        Check if a user is the owner of this project.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is the owner, False otherwise
        """
        return self.members.filter(
            user=user,
            role=ProjectMember.ROLE_OWNER
        ).exists()
    
    def is_admin(self, user):
        """
        Check if a user is an admin (or owner) of this project.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is admin or owner, False otherwise
        """
        return self.members.filter(
            user=user,
            role__in=[ProjectMember.ROLE_OWNER, ProjectMember.ROLE_ADMIN]
        ).exists()
    
    def has_admin_access(self, user):
        """
        Check if a user has admin access to this project (admin or owner).
        
        This is an alias for is_admin() for clarity.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user has admin access
        """
        return self.is_admin(user)
    
    def is_overdue(self):
        """
        Check if the project deadline has passed and project is not completed.
        
        Returns:
            bool: True if deadline has passed and project is not completed
        """
        if not self.deadline:
            return False
        if self.status == self.STATUS_COMPLETED:
            return False
        return timezone.now() > self.deadline
    
    def is_active(self):
        """
        Check if the project is currently active.
        
        Returns:
            bool: True if project status is active
        """
        return self.status == self.STATUS_ACTIVE
    
    def is_completed(self):
        """
        Check if the project is completed.
        
        Returns:
            bool: True if project status is completed
        """
        return self.status == self.STATUS_COMPLETED
    
    def get_status_display_class(self):
        """
        Get CSS class name for status display (for admin/frontend).
        
        Returns:
            str: CSS class name for status
        """
        status_classes = {
            self.STATUS_PLANNING: 'planning',
            self.STATUS_ACTIVE: 'active',
            self.STATUS_ON_HOLD: 'on-hold',
            self.STATUS_COMPLETED: 'completed',
            self.STATUS_CANCELLED: 'cancelled',
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


class ProjectMember(models.Model):
    """
    ProjectMember model representing the many-to-many relationship
    between Project and User with additional role information.
    
    This intermediary model allows storing role information
    for each project membership.
    
    Fields:
        project: ForeignKey to Project
        user: ForeignKey to User
        role: Member role (owner, admin, member)
        joined_at: Timestamp when user joined the project
    """
    
    # Role constants
    ROLE_OWNER = 'owner'
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    
    ROLE_CHOICES = [
        (ROLE_OWNER, _('Owner')),
        (ROLE_ADMIN, _('Admin')),
        (ROLE_MEMBER, _('Member')),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('Project'),
        help_text=_('The project this membership belongs to')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name=_('User'),
        help_text=_('The user who is a member of the project')
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        db_index=True,
        help_text=_('Member role in the project')
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Timestamp when user joined the project')
    )
    
    class Meta:
        db_table = 'project_members'
        unique_together = [['project', 'user']]
        ordering = ['-joined_at']
        verbose_name = _('Project Member')
        verbose_name_plural = _('Project Members')
        indexes = [
            models.Index(fields=['project', 'role']),
            models.Index(fields=['user', 'role']),
            models.Index(fields=['joined_at']),
        ]
    
    def __str__(self):
        """Return string representation of project membership."""
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"
    
    def is_owner(self):
        """Check if this member is the project owner."""
        return self.role == self.ROLE_OWNER
    
    def is_admin(self):
        """Check if this member is an admin or owner."""
        return self.role in [self.ROLE_OWNER, self.ROLE_ADMIN]
    
    def is_regular_member(self):
        """Check if this member is a regular member (not admin or owner)."""
        return self.role == self.ROLE_MEMBER
    
    def has_admin_access(self):
        """
        Check if this member has admin access (admin or owner).
        
        Returns:
            bool: True if member has admin access
        """
        return self.is_admin()
