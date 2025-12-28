"""
Team models for Task Management System.

This module defines the Team model and TeamMember model
for team management functionality.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Team(models.Model):
    """
    Team model for organizing users into collaborative groups.
    
    Teams allow multiple users to work together on projects and tasks.
    Each team has members with different roles (owner, admin, member).
    
    Fields:
        name: Team name (unique)
        description: Detailed description of the team
        created_at: Team creation timestamp
        updated_at: Last update timestamp
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('Team name (must be unique)')
    )
    
    description = models.TextField(
        max_length=500,
        blank=True,
        help_text=_('Detailed description of the team')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Team creation timestamp')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Last update timestamp')
    )
    
    class Meta:
        db_table = 'teams'
        ordering = ['-created_at']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        """Return team name as string representation."""
        return self.name
    
    def get_members(self):
        """
        Get all members of this team.
        
        Returns:
            QuerySet: All TeamMember instances for this team
        """
        return self.members.all()
    
    def get_member_count(self):
        """
        Get the total number of members in this team.
        
        Returns:
            int: Number of team members
        """
        return self.members.count()
    
    def get_owner(self):
        """
        Get the owner of this team.
        
        Returns:
            TeamMember or None: The team owner, or None if no owner exists
        """
        return self.members.filter(role=TeamMember.ROLE_OWNER).first()
    
    def get_admins(self):
        """
        Get all admin members of this team.
        
        Returns:
            QuerySet: All admin TeamMember instances
        """
        return self.members.filter(role=TeamMember.ROLE_ADMIN)
    
    def get_regular_members(self):
        """
        Get all regular member (non-admin, non-owner) members.
        
        Returns:
            QuerySet: All regular member TeamMember instances
        """
        return self.members.filter(role=TeamMember.ROLE_MEMBER)
    
    def is_member(self, user):
        """
        Check if a user is a member of this team.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is a member, False otherwise
        """
        return self.members.filter(user=user).exists()
    
    def get_member_role(self, user):
        """
        Get the role of a user in this team.
        
        Args:
            user: User instance
            
        Returns:
            str or None: User's role in the team, or None if not a member
        """
        try:
            member = self.members.get(user=user)
            return member.role
        except TeamMember.DoesNotExist:
            return None
    
    def is_owner(self, user):
        """
        Check if a user is the owner of this team.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is the owner, False otherwise
        """
        return self.members.filter(
            user=user,
            role=TeamMember.ROLE_OWNER
        ).exists()
    
    def is_admin(self, user):
        """
        Check if a user is an admin (or owner) of this team.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user is admin or owner, False otherwise
        """
        return self.members.filter(
            user=user,
            role__in=[TeamMember.ROLE_OWNER, TeamMember.ROLE_ADMIN]
        ).exists()
    
    def has_admin_access(self, user):
        """
        Check if a user has admin access to this team (admin or owner).
        
        This is an alias for is_admin() for clarity.
        
        Args:
            user: User instance to check
            
        Returns:
            bool: True if user has admin access, False otherwise
        """
        return self.is_admin(user)


class TeamMember(models.Model):
    """
    TeamMember model representing the many-to-many relationship
    between Team and User with additional role information.
    
    This intermediary model allows storing role information
    for each team membership.
    
    Fields:
        team: ForeignKey to Team
        user: ForeignKey to User
        role: Member role (owner, admin, member)
        joined_at: Timestamp when user joined the team
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
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('Team'),
        help_text=_('The team this membership belongs to')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        verbose_name=_('User'),
        help_text=_('The user who is a member of the team')
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        db_index=True,
        help_text=_('Member role in the team')
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text=_('Timestamp when user joined the team')
    )
    
    class Meta:
        db_table = 'team_members'
        unique_together = [['team', 'user']]
        ordering = ['-joined_at']
        verbose_name = _('Team Member')
        verbose_name_plural = _('Team Members')
        indexes = [
            models.Index(fields=['team', 'role']),
            models.Index(fields=['user', 'role']),
            models.Index(fields=['joined_at']),
        ]
    
    def __str__(self):
        """Return string representation of team membership."""
        return f"{self.user.username} - {self.team.name} ({self.get_role_display()})"
    
    def is_owner(self):
        """Check if this member is the team owner."""
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
