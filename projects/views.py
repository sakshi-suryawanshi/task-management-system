"""
API views for Project management.

This module contains views for project CRUD operations, project member management,
and project analytics/statistics.
"""

from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Project, ProjectMember
from .serializers import (
    ProjectSerializer,
    ProjectMemberSerializer,
    ProjectMemberAddSerializer,
    ProjectMemberUpdateSerializer,
)
from core.permissions import IsProjectMember

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Projects'],
        summary='List projects',
        description='List all projects that the current user is a member of. Supports filtering, search, and pagination.',
        parameters=[
            OpenApiParameter('search', description='Search projects by name or description'),
            OpenApiParameter('team', description='Filter by team ID'),
            OpenApiParameter('status', description='Filter by status (planning, active, on_hold, completed, cancelled)'),
            OpenApiParameter('priority', description='Filter by priority (high, medium, low)'),
            OpenApiParameter('ordering', description='Order by field (e.g., -created_at, name, deadline)'),
        ],
        responses={200: ProjectSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Projects'],
        summary='Create a new project',
        description='Create a new project. The creator automatically becomes the project owner.',
        request=ProjectSerializer,
        responses={201: ProjectSerializer},
    ),
)
class ProjectListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating projects.
    
    GET /api/projects/ - List projects user is a member of
    POST /api/projects/ - Create a new project
    """
    
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'team__name']
    ordering_fields = ['name', 'status', 'priority', 'deadline', 'created_at', 'updated_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Return projects that the current user is a member of.
        
        Supports filtering by:
        - team: Filter by team ID
        - status: Filter by project status
        - priority: Filter by priority
        
        Returns:
            QuerySet: Projects where the current user is a member
        """
        user = self.request.user
        
        # Get projects where user is a member
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        queryset = Project.objects.filter(
            id__in=project_ids
        ).select_related('team').prefetch_related('members__user', 'tasks')
        
        # Apply filters
        team_id = self.request.query_params.get('team', None)
        if team_id:
            queryset = queryset.filter(team_id=team_id)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = self.request.query_params.get('priority', None)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Create a project and automatically add the creator as owner.
        
        Args:
            serializer: ProjectSerializer instance with validated data
        """
        project = serializer.save()
        # Automatically add creator as owner
        ProjectMember.objects.create(
            project=project,
            user=self.request.user,
            role=ProjectMember.ROLE_OWNER
        )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new project and return response with success message.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with created project data
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created project with members
        project = serializer.instance
        response_serializer = self.get_serializer(project)
        
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Project created successfully'
            },
            status=status.HTTP_201_CREATED
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a project.
    
    GET /api/projects/{id}/
        Retrieve a specific project's details.
        Returns project information including all members and task statistics.
    
    PUT /api/projects/{id}/
        Full update of project information.
        All fields must be provided.
        
        Request Body:
            {
                "name": "Updated Project Name",
                "description": "Updated description",
                "status": "active",
                "priority": "medium",
                "deadline": "2025-12-31T23:59:59Z",
                "team": 1
            }
    
    PATCH /api/projects/{id}/
        Partial update of project information.
        Only provided fields will be updated.
    
    DELETE /api/projects/{id}/
        Delete a project. Only project owners can delete projects.
        
        Response (204 No Content): Project deleted successfully
    
    Authentication: Required (JWT token)
    Permissions:
        - GET: User must be a member of the project
        - PUT/PATCH: User must be an admin or owner of the project
        - DELETE: User must be the owner of the project
    """
    
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_queryset(self):
        """
        Return projects that the current user is a member of.
        
        Returns:
            QuerySet: Projects where the current user is a member
        """
        user = self.request.user
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        queryset = Project.objects.filter(
            id__in=project_ids
        ).select_related('team').prefetch_related('members__user', 'tasks')
        return queryset
    
    def get_object(self):
        """
        Get the project object and check permissions.
        
        Returns:
            Project: Project instance
            
        Raises:
            Http404: If project doesn't exist or user is not a member
        """
        project = super().get_object()
        return project
    
    def update(self, request, *args, **kwargs):
        """
        Update project information (PUT).
        
        Only project admins and owners can update projects.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated project data
        """
        project = self.get_object()
        user = request.user
        
        # Check if user is admin or owner
        if not project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can update project information.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(project, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Project updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update project information (PATCH).
        
        Only project admins and owners can update projects.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated project data
        """
        project = self.get_object()
        user = request.user
        
        # Check if user is admin or owner
        if not project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can update project information.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(project, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Project updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a project (DELETE).
        
        Only project owners can delete projects.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Empty response with 204 status
        """
        project = self.get_object()
        user = request.user
        
        # Check if user is the owner
        if not project.is_owner(user):
            return Response(
                {'error': 'Only project owners can delete projects.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        project_name = project.name
        self.perform_destroy(project)
        
        return Response(
            {'message': f'Project "{project_name}" deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class ProjectMemberView(APIView):
    """
    API endpoint for managing project members.
    
    POST /api/projects/{project_id}/members/
        Add a new member to the project.
        
        Request Body:
            {
                "user_id": 2,
                "role": "member"  // optional, defaults to "member"
            }
        
        Response (201 Created):
            {
                "data": {
                    "id": 1,
                    "user": 2,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "role": "member",
                    "role_display": "Member",
                    "joined_at": "2025-12-27T15:00:00Z"
                },
                "message": "Member added successfully"
            }
    
    DELETE /api/projects/{project_id}/members/{user_id}/
        Remove a member from the project.
        
        Response (204 No Content): Member removed successfully
    
    PATCH /api/projects/{project_id}/members/{user_id}/
        Update a member's role in the project.
        
        Request Body:
            {
                "role": "admin"
            }
        
        Response (200 OK):
            {
                "data": {
                    "id": 1,
                    "user": 2,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "role": "admin",
                    "role_display": "Admin",
                    "joined_at": "2025-12-27T15:00:00Z"
                },
                "message": "Member role updated successfully"
            }
    
    Authentication: Required (JWT token)
    Permissions:
        - POST (add member): User must be an admin or owner of the project
        - PATCH (update role): User must be an admin or owner of the project
        - DELETE (remove member): User must be an admin or owner of the project
        - Cannot remove project owner
        - Cannot change owner role
        - User must be a member of the project's team to be added
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_project(self, project_id):
        """
        Get project object and verify user is a member.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project: Project instance
            
        Raises:
            Http404: If project doesn't exist or user is not a member
        """
        user = self.request.user
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        project = get_object_or_404(Project.objects.filter(id__in=project_ids), pk=project_id)
        return project
    
    def post(self, request, project_id):
        """
        Add a new member to the project.
        
        Args:
            request: HTTP request object
            project_id: Project ID
            
        Returns:
            Response: JSON response with created member data
        """
        project = self.get_project(project_id)
        user = request.user
        
        # Check if user is admin or owner
        if not project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can add members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectMemberAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        role = serializer.validated_data.get('role', ProjectMember.ROLE_MEMBER)
        
        # Get the user to add
        try:
            user_to_add = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if project.is_member(user_to_add):
            return Response(
                {'error': 'User is already a member of this project.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a member of the project's team
        from teams.models import TeamMember
        if not TeamMember.objects.filter(team=project.team, user=user_to_add).exists():
            return Response(
                {'error': 'User must be a member of the project\'s team to be added to the project.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent non-owners from assigning owner role
        if role == ProjectMember.ROLE_OWNER and not project.is_owner(user):
            return Response(
                {'error': 'Only project owners can assign owner role.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create project membership
        project_member = ProjectMember.objects.create(
            project=project,
            user=user_to_add,
            role=role
        )
        
        # Serialize and return response
        member_serializer = ProjectMemberSerializer(project_member)
        
        return Response(
            {
                'data': member_serializer.data,
                'message': 'Member added successfully'
            },
            status=status.HTTP_201_CREATED
        )
    
    def patch(self, request, project_id, user_id):
        """
        Update a member's role in the project.
        
        Args:
            request: HTTP request object
            project_id: Project ID
            user_id: User ID of the member to update
            
        Returns:
            Response: JSON response with updated member data
        """
        project = self.get_project(project_id)
        user = request.user
        
        # Check if user is admin or owner
        if not project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can update member roles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the project member to update
        try:
            project_member = ProjectMember.objects.get(project=project, user_id=user_id)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': 'Member not found in this project.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot change owner role
        if project_member.role == ProjectMember.ROLE_OWNER:
            return Response(
                {'error': 'Cannot change the role of the project owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProjectMemberUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_role = serializer.validated_data['role']
        
        # Prevent non-owners from assigning owner role
        if new_role == ProjectMember.ROLE_OWNER and not project.is_owner(user):
            return Response(
                {'error': 'Only project owners can assign owner role.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update role
        project_member.role = new_role
        project_member.save()
        
        # Serialize and return response
        member_serializer = ProjectMemberSerializer(project_member)
        
        return Response(
            {
                'data': member_serializer.data,
                'message': 'Member role updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, project_id, user_id):
        """
        Remove a member from the project.
        
        Args:
            request: HTTP request object
            project_id: Project ID
            user_id: User ID of the member to remove
            
        Returns:
            Response: Empty response with 204 status
        """
        project = self.get_project(project_id)
        user = request.user
        
        # Check if user is admin or owner
        if not project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can remove members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the project member to remove
        try:
            project_member = ProjectMember.objects.get(project=project, user_id=user_id)
        except ProjectMember.DoesNotExist:
            return Response(
                {'error': 'Member not found in this project.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot remove project owner
        if project_member.role == ProjectMember.ROLE_OWNER:
            return Response(
                {'error': 'Cannot remove the project owner. Transfer ownership first or delete the project.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot remove yourself (use leave project endpoint if needed)
        if project_member.user == user:
            return Response(
                {'error': 'You cannot remove yourself from the project. Please contact another admin or owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove member
        username = project_member.user.username
        project_member.delete()
        
        return Response(
            {'message': f'Member "{username}" removed from project successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class ProjectStatsView(APIView):
    """
    API endpoint for project analytics and statistics.
    
    GET /api/projects/{project_id}/stats/
        Get comprehensive statistics and analytics for a project.
        
        Response (200 OK):
            {
                "data": {
                    "project_id": 1,
                    "project_name": "Website Redesign",
                    "status": "active",
                    "priority": "high",
                    "deadline": "2025-12-31T23:59:59Z",
                    "is_overdue": false,
                    "days_until_deadline": 5,
                    "member_count": 5,
                    "task_statistics": {
                        "total": 20,
                        "todo": 5,
                        "in_progress": 8,
                        "done": 6,
                        "blocked": 1,
                        "completion_percentage": 30.0
                    },
                    "priority_distribution": {
                        "high": 8,
                        "medium": 10,
                        "low": 2
                    },
                    "task_status_timeline": {
                        "created_this_week": 5,
                        "completed_this_week": 3,
                        "created_this_month": 12,
                        "completed_this_month": 8
                    },
                    "member_activity": [
                        {
                            "user_id": 1,
                            "username": "johndoe",
                            "tasks_assigned": 5,
                            "tasks_completed": 3
                        },
                        ...
                    ],
                    "overdue_tasks": 2,
                    "upcoming_deadlines": [
                        {
                            "task_id": 1,
                            "title": "Design mockups",
                            "due_date": "2025-12-28T23:59:59Z",
                            "days_until_due": 1
                        },
                        ...
                    ]
                }
            }
    
    Authentication: Required (JWT token)
    Permissions: User must be a member of the project
    """
    
    permission_classes = [permissions.IsAuthenticated, IsProjectMember]
    
    def get_project(self, project_id):
        """
        Get project object and verify user is a member.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project: Project instance
            
        Raises:
            Http404: If project doesn't exist or user is not a member
        """
        user = self.request.user
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        project = get_object_or_404(
            Project.objects.filter(id__in=project_ids).select_related('team').prefetch_related(
                'members__user',
                'tasks',
                'tasks__assignee'
            ),
            pk=project_id
        )
        return project
    
    def get(self, request, project_id):
        """
        Get project statistics and analytics.
        
        Args:
            request: HTTP request object
            project_id: Project ID
            
        Returns:
            Response: JSON response with project statistics
        """
        project = self.get_project(project_id)
        
        # Calculate days until deadline
        days_until_deadline = None
        if project.deadline:
            time_diff = project.deadline - timezone.now()
            days_until_deadline = time_diff.days
        
        # Task statistics
        tasks = project.tasks.all()
        total_tasks = tasks.count()
        task_status_counts = tasks.values('status').annotate(count=Count('id'))
        task_status_dict = {item['status']: item['count'] for item in task_status_counts}
        
        completion_percentage = 0.0
        if total_tasks > 0:
            completed_tasks = task_status_dict.get('done', 0)
            completion_percentage = round((completed_tasks / total_tasks) * 100, 2)
        
        # Priority distribution
        priority_counts = tasks.values('priority').annotate(count=Count('id'))
        priority_dict = {item['priority']: item['count'] for item in priority_counts}
        
        # Task status timeline
        now = timezone.now()
        week_ago = now - timezone.timedelta(days=7)
        month_ago = now - timezone.timedelta(days=30)
        
        created_this_week = tasks.filter(created_at__gte=week_ago).count()
        completed_this_week = tasks.filter(
            status='done',
            updated_at__gte=week_ago
        ).count()
        created_this_month = tasks.filter(created_at__gte=month_ago).count()
        completed_this_month = tasks.filter(
            status='done',
            updated_at__gte=month_ago
        ).count()
        
        # Member activity
        member_activity = []
        for member in project.members.all():
            user_tasks = tasks.filter(assignee=member.user)
            member_activity.append({
                'user_id': member.user.id,
                'username': member.user.username,
                'full_name': member.user.get_full_name_or_username(),
                'role': member.role,
                'tasks_assigned': user_tasks.count(),
                'tasks_completed': user_tasks.filter(status='done').count(),
            })
        
        # Overdue tasks
        overdue_tasks = tasks.filter(
            due_date__lt=now,
            status__in=['todo', 'in_progress', 'blocked']
        ).count()
        
        # Upcoming deadlines (next 7 days)
        upcoming_deadline = now + timezone.timedelta(days=7)
        upcoming_tasks = tasks.filter(
            due_date__gte=now,
            due_date__lte=upcoming_deadline,
            status__in=['todo', 'in_progress']
        ).order_by('due_date')[:10]  # Limit to 10 tasks
        
        upcoming_deadlines = []
        for task in upcoming_tasks:
            if task.due_date:
                time_diff = task.due_date - now
                upcoming_deadlines.append({
                    'task_id': task.id,
                    'title': task.title,
                    'due_date': task.due_date.isoformat(),
                    'days_until_due': time_diff.days,
                    'priority': task.priority,
                    'status': task.status,
                })
        
        # Build response data
        stats_data = {
            'project_id': project.id,
            'project_name': project.name,
            'status': project.status,
            'status_display': project.get_status_display(),
            'priority': project.priority,
            'priority_display': project.get_priority_display(),
            'deadline': project.deadline.isoformat() if project.deadline else None,
            'is_overdue': project.is_overdue(),
            'days_until_deadline': days_until_deadline,
            'member_count': project.get_member_count(),
            'task_statistics': {
                'total': total_tasks,
                'todo': task_status_dict.get('todo', 0),
                'in_progress': task_status_dict.get('in_progress', 0),
                'done': task_status_dict.get('done', 0),
                'blocked': task_status_dict.get('blocked', 0),
                'completion_percentage': completion_percentage,
            },
            'priority_distribution': {
                'high': priority_dict.get('high', 0),
                'medium': priority_dict.get('medium', 0),
                'low': priority_dict.get('low', 0),
            },
            'task_status_timeline': {
                'created_this_week': created_this_week,
                'completed_this_week': completed_this_week,
                'created_this_month': created_this_month,
                'completed_this_month': completed_this_month,
            },
            'member_activity': member_activity,
            'overdue_tasks': overdue_tasks,
            'upcoming_deadlines': upcoming_deadlines,
        }
        
        return Response(
            {
                'data': stats_data,
                'message': 'Project statistics retrieved successfully'
            },
            status=status.HTTP_200_OK
        )
