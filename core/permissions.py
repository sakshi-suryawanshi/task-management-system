"""
Custom permission classes for Task Management System.

This module defines custom permission classes that extend Django REST Framework's
BasePermission to provide fine-grained access control for teams, projects, and tasks.

Permission Classes:
    - IsTeamMember: Checks if user is a member of a team
    - IsProjectMember: Checks if user is a member of a project
    - IsTaskAssignee: Checks if user is assigned to a task
"""

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsTeamMember(permissions.BasePermission):
    """
    Permission class to check if a user is a member of a team.
    
    This permission class checks if the authenticated user is a member of the
    team associated with the request. It works at both view-level and object-level.
    
    For view-level checks (has_permission):
        - Checks if the request user is authenticated
        - For POST requests, checks if user can create teams (always True for authenticated users)
        
    For object-level checks (has_object_permission):
        - Checks if the user is a member of the team object
        - Uses the Team model's is_member() method to check membership
        
    Usage:
        Add to view's permission_classes:
        
        class TeamDetailView(RetrieveUpdateDestroyAPIView):
            permission_classes = [IsAuthenticated, IsTeamMember]
            
    Note:
        This permission should be used in conjunction with IsAuthenticated
        to ensure the user is logged in.
    """
    
    message = "You must be a member of this team to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        For GET, HEAD, OPTIONS requests:
            - Always returns True (object-level check will handle team membership)
        For POST requests:
            - Returns True for authenticated users (anyone can create a team)
        For PUT, PATCH, DELETE requests:
            - Returns True (object-level check will handle team membership)
            
        Args:
            request: The request instance
            view: The view instance
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list/create views, allow authenticated users
        # Object-level checks will handle team membership for detail views
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access a specific team object.
        
        This method checks if the authenticated user is a member of the team
        by using the Team model's is_member() method.
        
        Args:
            request: The request instance
            view: The view instance
            obj: The Team instance to check
            
        Returns:
            bool: True if user is a team member, False otherwise
            
        Raises:
            PermissionDenied: If obj is not a Team instance (for type safety)
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Import here to avoid circular imports
        from teams.models import Team
        
        # Type check - ensure obj is a Team instance
        if not isinstance(obj, Team):
            raise PermissionDenied("This permission can only be used with Team objects.")
        
        # Check if user is a member of the team
        return obj.is_member(request.user)


class IsProjectMember(permissions.BasePermission):
    """
    Permission class to check if a user is a member of a project.
    
    This permission class checks if the authenticated user is a member of the
    project associated with the request. It works at both view-level and object-level.
    
    For view-level checks (has_permission):
        - Checks if the request user is authenticated
        - For POST requests, checks if user can create projects (always True for authenticated users)
        
    For object-level checks (has_object_permission):
        - Checks if the user is a member of the project object
        - Uses the Project model's is_member() method to check membership
        
    Usage:
        Add to view's permission_classes:
        
        class ProjectDetailView(RetrieveUpdateDestroyAPIView):
            permission_classes = [IsAuthenticated, IsProjectMember]
            
    Note:
        This permission should be used in conjunction with IsAuthenticated
        to ensure the user is logged in.
    """
    
    message = "You must be a member of this project to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        For GET, HEAD, OPTIONS requests:
            - Always returns True (object-level check will handle project membership)
        For POST requests:
            - Returns True for authenticated users (anyone can create a project if they're team member)
        For PUT, PATCH, DELETE requests:
            - Returns True (object-level check will handle project membership)
            
        Args:
            request: The request instance
            view: The view instance
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list/create views, allow authenticated users
        # Object-level checks will handle project membership for detail views
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access a specific project object.
        
        This method checks if the authenticated user is a member of the project
        by using the Project model's is_member() method.
        
        Args:
            request: The request instance
            view: The view instance
            obj: The Project instance to check
            
        Returns:
            bool: True if user is a project member, False otherwise
            
        Raises:
            PermissionDenied: If obj is not a Project instance (for type safety)
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Import here to avoid circular imports
        from projects.models import Project
        
        # Type check - ensure obj is a Project instance
        if not isinstance(obj, Project):
            raise PermissionDenied("This permission can only be used with Project objects.")
        
        # Check if user is a member of the project
        return obj.is_member(request.user)


class IsTaskAssignee(permissions.BasePermission):
    """
    Permission class to check if a user is assigned to a task.
    
    This permission class checks if the authenticated user is assigned to the
    task associated with the request. It works at both view-level and object-level.
    
    For view-level checks (has_permission):
        - Checks if the request user is authenticated
        - For POST requests, allows authenticated users (task creator/assigner will be checked separately)
        
    For object-level checks (has_object_permission):
        - Checks if the user is assigned to the task (task.assignee == user)
        - Also allows the task creator (task.created_by == user) to access the task
        - Also allows project members to access the task (they can view tasks in their project)
        
    Usage:
        Add to view's permission_classes:
        
        class TaskDetailView(RetrieveUpdateDestroyAPIView):
            permission_classes = [IsAuthenticated, IsTaskAssignee]
            
        Note: For more restrictive access (only assignee), you can create a
        more specific permission class that only checks assignee.
            
    Note:
        This permission should be used in conjunction with IsAuthenticated
        to ensure the user is logged in.
        
        By default, this permission allows:
        1. Task assignee (user assigned to the task)
        2. Task creator (user who created the task)
        3. Project members (users who are members of the task's project)
    """
    
    message = "You must be assigned to this task, be the task creator, or be a member of the project to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        For GET, HEAD, OPTIONS requests:
            - Always returns True (object-level check will handle task assignment)
        For POST requests:
            - Returns True for authenticated users (task creator/assigner will be set separately)
        For PUT, PATCH, DELETE requests:
            - Returns True (object-level check will handle task assignment)
            
        Args:
            request: The request instance
            view: The view instance
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list/create views, allow authenticated users
        # Object-level checks will handle task assignment for detail views
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access a specific task object.
        
        This method checks if the authenticated user has access to the task by:
        1. Checking if user is assigned to the task (task.assignee == user)
        2. Checking if user created the task (task.created_by == user)
        3. Checking if user is a member of the task's project
        
        Args:
            request: The request instance
            view: The view instance
            obj: The Task instance to check
            
        Returns:
            bool: True if user has access to the task, False otherwise
            
        Raises:
            PermissionDenied: If obj is not a Task instance (for type safety)
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Import here to avoid circular imports
        from tasks.models import Task
        
        # Type check - ensure obj is a Task instance
        if not isinstance(obj, Task):
            raise PermissionDenied("This permission can only be used with Task objects.")
        
        # Check if user is assigned to the task
        if obj.assignee and obj.assignee == request.user:
            return True
        
        # Check if user created the task
        if obj.created_by and obj.created_by == request.user:
            return True
        
        # Check if user is a member of the task's project
        if obj.project and obj.project.is_member(request.user):
            return True
        
        # User doesn't have access
        return False


class IsTaskAssigneeOnly(permissions.BasePermission):
    """
    Permission class to check if a user is assigned to a task (strict version).
    
    This is a stricter version of IsTaskAssignee that only allows access if
    the user is explicitly assigned to the task. It does NOT allow:
    - Task creators (unless they are also assigned)
    - Project members (unless they are also assigned)
    
    This is useful for operations that should only be performed by the assignee,
    such as updating task status or marking tasks as complete.
    
    Usage:
        Add to view's permission_classes:
        
        class TaskStatusUpdateView(UpdateAPIView):
            permission_classes = [IsAuthenticated, IsTaskAssigneeOnly]
            
    Note:
        This permission should be used in conjunction with IsAuthenticated
        to ensure the user is logged in.
    """
    
    message = "You must be assigned to this task to perform this action."
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to access the view.
        
        Args:
            request: The request instance
            view: The view instance
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access a specific task object.
        
        This method only checks if the user is assigned to the task.
        It does NOT check if the user is the creator or project member.
        
        Args:
            request: The request instance
            view: The view instance
            obj: The Task instance to check
            
        Returns:
            bool: True if user is assigned to the task, False otherwise
            
        Raises:
            PermissionDenied: If obj is not a Task instance (for type safety)
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Import here to avoid circular imports
        from tasks.models import Task
        
        # Type check - ensure obj is a Task instance
        if not isinstance(obj, Task):
            raise PermissionDenied("This permission can only be used with Task objects.")
        
        # Only check if user is assigned to the task (strict check)
        return obj.assignee and obj.assignee == request.user

