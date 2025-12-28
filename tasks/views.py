"""
API views for Task management.

This module contains views for task CRUD operations, task assignment management,
and task status updates.
"""

from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Task, TaskComment
from .serializers import (
    TaskSerializer,
    TaskAssigneeSerializer,
    TaskStatusUpdateSerializer,
    TaskCommentSerializer,
)
from core.permissions import IsTaskAssignee

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        tags=['Tasks'],
        summary='List tasks',
        description='List all tasks that the current user has access to. Supports filtering, search, and pagination.',
        parameters=[
            OpenApiParameter('search', description='Search tasks by title or description'),
            OpenApiParameter('project', description='Filter by project ID'),
            OpenApiParameter('status', description='Filter by status (todo, in_progress, done, blocked)'),
            OpenApiParameter('priority', description='Filter by priority (high, medium, low)'),
            OpenApiParameter('assignee', description='Filter by assignee user ID'),
            OpenApiParameter('assigned_to_me', description='Filter to show only tasks assigned to current user (true/false)'),
            OpenApiParameter('overdue', description='Filter to show only overdue tasks (true/false)'),
            OpenApiParameter('ordering', description='Order by field (e.g., -created_at, title, due_date, priority)'),
        ],
        responses={200: TaskSerializer(many=True)},
    ),
    post=extend_schema(
        tags=['Tasks'],
        summary='Create a new task',
        description='Create a new task. The creator is automatically set to the current user.',
        request=TaskSerializer,
        responses={201: TaskSerializer},
    ),
)
class TaskListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating tasks.
    
    GET /api/tasks/ - List tasks user has access to
    POST /api/tasks/ - Create a new task
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'status', 'priority', 'due_date', 'created_at', 'updated_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """
        Return tasks that the current user has access to.
        
        Users can see:
        - Tasks in projects where they are members
        - Tasks assigned to them
        - Tasks created by them
        
        Supports filtering by:
        - project: Filter by project ID
        - status: Filter by task status
        - priority: Filter by priority
        - assignee: Filter by assignee user ID
        - assigned_to_me: Filter to show only tasks assigned to current user
        - overdue: Filter to show only overdue tasks
        
        Returns:
            QuerySet: Tasks accessible to the current user
        """
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        # Base queryset: tasks in user's projects OR assigned to user OR created by user
        queryset = Task.objects.filter(
            Q(project_id__in=project_ids) |
            Q(assignee=user) |
            Q(created_by=user)
        ).select_related('project', 'assignee', 'created_by').prefetch_related(
            'comments', 'attachments'
        ).distinct()
        
        # Apply filters
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = self.request.query_params.get('priority', None)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        assignee_id = self.request.query_params.get('assignee', None)
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        
        # Filter by assigned to me
        assigned_to_me = self.request.query_params.get('assigned_to_me', None)
        if assigned_to_me and assigned_to_me.lower() in ('true', '1', 'yes'):
            queryset = queryset.filter(assignee=user)
        
        # Filter by overdue tasks
        overdue = self.request.query_params.get('overdue', None)
        if overdue and overdue.lower() in ('true', '1', 'yes'):
            now = timezone.now()
            queryset = queryset.filter(
                due_date__lt=now,
                status__in=[Task.STATUS_TODO, Task.STATUS_IN_PROGRESS, Task.STATUS_BLOCKED]
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Create a task and set the creator.
        
        Args:
            serializer: TaskSerializer instance with validated data
        """
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new task and return response with success message.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with created task data
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created task
        task = serializer.instance
        response_serializer = self.get_serializer(task)
        
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Task created successfully'
            },
            status=status.HTTP_201_CREATED
        )


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a task.
    
    GET /api/tasks/{id}/
        Retrieve a specific task's details.
        Returns task information including assignee, project, and computed fields.
    
    PUT /api/tasks/{id}/
        Full update of task information.
        All fields must be provided.
        
        Request Body:
            {
                "title": "Updated Task Title",
                "description": "Updated description",
                "status": "in_progress",
                "priority": "medium",
                "due_date": "2025-12-31T23:59:59Z",
                "project": 1,
                "assignee": 2
            }
    
    PATCH /api/tasks/{id}/
        Partial update of task information.
        Only provided fields will be updated.
    
    DELETE /api/tasks/{id}/
        Delete a task. Only project admins/owners or task creator can delete tasks.
        
        Response (204 No Content): Task deleted successfully
    
    Authentication: Required (JWT token)
    Permissions:
        - GET: User must have access to the task (project member, assignee, or creator)
        - PUT/PATCH: User must have access to the task and be project admin/owner or creator
        - DELETE: User must be project admin/owner or task creator
    """
    
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskAssignee]
    
    def get_queryset(self):
        """
        Return tasks that the current user has access to.
        
        Returns:
            QuerySet: Tasks accessible to the current user
        """
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        queryset = Task.objects.filter(
            Q(project_id__in=project_ids) |
            Q(assignee=user) |
            Q(created_by=user)
        ).select_related('project', 'assignee', 'created_by').prefetch_related(
            'comments', 'attachments'
        ).distinct()
        
        return queryset
    
    def get_object(self):
        """
        Get the task object and check permissions.
        
        Returns:
            Task: Task instance
            
        Raises:
            Http404: If task doesn't exist or user doesn't have access
        """
        task = super().get_object()
        return task
    
    def update(self, request, *args, **kwargs):
        """
        Update task information (PUT).
        
        Only project admins/owners or task creator can update tasks.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated task data
        """
        task = self.get_object()
        user = request.user
        
        # Check if user can update (project admin/owner or task creator)
        if not (task.project.is_admin(user) or task.created_by == user):
            return Response(
                {'error': 'Only project admins/owners or task creator can update tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(task, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Task updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update task information (PATCH).
        
        Only project admins/owners or task creator can update tasks.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated task data
        """
        task = self.get_object()
        user = request.user
        
        # Check if user can update (project admin/owner or task creator)
        if not (task.project.is_admin(user) or task.created_by == user):
            return Response(
                {'error': 'Only project admins/owners or task creator can update tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(task, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Task updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a task (DELETE).
        
        Only project admins/owners or task creator can delete tasks.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Empty response with 204 status
        """
        task = self.get_object()
        user = request.user
        
        # Check if user can delete (project admin/owner or task creator)
        if not (task.project.is_admin(user) or task.created_by == user):
            return Response(
                {'error': 'Only project admins/owners or task creator can delete tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        task_title = task.title
        self.perform_destroy(task)
        
        return Response(
            {'message': f'Task "{task_title}" deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


class TaskAssigneeView(APIView):
    """
    API endpoint for assigning/unassigning tasks.
    
    POST /api/tasks/{task_id}/assign/
        Assign or unassign a task to a user.
        
        Request Body:
            {
                "assignee_id": 2  // User ID to assign, or null to unassign
            }
        
        Response (200 OK):
            {
                "data": {
                    "id": 1,
                    "title": "Implement user authentication",
                    ...
                    "assignee": 2,
                    "assignee_username": "johndoe",
                    "is_assigned": true
                },
                "message": "Task assigned successfully"
            }
    
    Authentication: Required (JWT token)
    Permissions:
        - User must be project admin/owner to assign tasks
        - User must be project admin/owner, task creator, or current assignee to unassign
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_task(self, task_id):
        """
        Get task object and verify user has access.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task: Task instance
            
        Raises:
            Http404: If task doesn't exist or user doesn't have access
        """
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        task = get_object_or_404(
            Task.objects.filter(
                Q(project_id__in=project_ids) |
                Q(assignee=user) |
                Q(created_by=user)
            ).select_related('project', 'assignee', 'created_by'),
            pk=task_id
        )
        return task
    
    def post(self, request, task_id):
        """
        Assign or unassign a task.
        
        Args:
            request: HTTP request object
            task_id: Task ID
            
        Returns:
            Response: JSON response with updated task data
        """
        task = self.get_task(task_id)
        user = request.user
        
        # Check if user can assign tasks (project admin/owner)
        if not task.project.is_admin(user):
            return Response(
                {'error': 'Only project admins and owners can assign tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TaskAssigneeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assignee_id = serializer.validated_data.get('assignee_id')
        
        if assignee_id is None:
            # Unassign task
            # Allow unassign if: project admin/owner, task creator, or current assignee
            if not (task.project.is_admin(user) or task.created_by == user or task.assignee == user):
                return Response(
                    {'error': 'You do not have permission to unassign this task.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            task.assignee = None
            message = 'Task unassigned successfully'
        else:
            # Assign task
            try:
                assignee = User.objects.get(pk=assignee_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if assignee is a project member
            if not task.project.is_member(assignee):
                return Response(
                    {'error': 'Assignee must be a member of the project.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            task.assignee = assignee
            message = 'Task assigned successfully'
        
        task.save()
        
        # Serialize and return response
        task_serializer = TaskSerializer(task, context={'request': request})
        
        return Response(
            {
                'data': task_serializer.data,
                'message': message
            },
            status=status.HTTP_200_OK
        )


class TaskStatusUpdateView(APIView):
    """
    API endpoint for updating task status.
    
    PATCH /api/tasks/{task_id}/status/
        Update the status of a task.
        
        Request Body:
            {
                "status": "in_progress"  // todo, in_progress, done, blocked
            }
        
        Response (200 OK):
            {
                "data": {
                    "id": 1,
                    "title": "Implement user authentication",
                    "status": "in_progress",
                    "status_display": "In Progress",
                    ...
                },
                "message": "Task status updated successfully"
            }
    
    Authentication: Required (JWT token)
    Permissions:
        - User must be task assignee, task creator, or project admin/owner
        - For marking as "done", user must be task assignee or project admin/owner
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_task(self, task_id):
        """
        Get task object and verify user has access.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task: Task instance
            
        Raises:
            Http404: If task doesn't exist or user doesn't have access
        """
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        task = get_object_or_404(
            Task.objects.filter(
                Q(project_id__in=project_ids) |
                Q(assignee=user) |
                Q(created_by=user)
            ).select_related('project', 'assignee', 'created_by'),
            pk=task_id
        )
        return task
    
    def patch(self, request, task_id):
        """
        Update task status.
        
        Args:
            request: HTTP request object
            task_id: Task ID
            
        Returns:
            Response: JSON response with updated task data
        """
        task = self.get_task(task_id)
        user = request.user
        
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        
        # Check if user can update status
        # Allow if: task assignee, task creator, or project admin/owner
        can_update = (
            task.assignee == user or
            task.created_by == user or
            task.project.is_admin(user)
        )
        
        if not can_update:
            return Response(
                {'error': 'You do not have permission to update this task status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Additional check for marking as done: must be assignee or project admin/owner
        if new_status == Task.STATUS_DONE:
            if not (task.assignee == user or task.project.is_admin(user)):
                return Response(
                    {'error': 'Only the task assignee or project admins/owners can mark tasks as done.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Update status
        task.status = new_status
        task.save()
        
        # Serialize and return response
        task_serializer = TaskSerializer(task, context={'request': request})
        
        return Response(
            {
                'data': task_serializer.data,
                'message': 'Task status updated successfully'
            },
            status=status.HTTP_200_OK
        )


class CommentListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating task comments.
    
    GET /api/tasks/{task_id}/comments/
        List all comments for a specific task.
        Comments are ordered by creation date (newest first).
        Supports pagination.
        
        Query Parameters:
            - page: Page number for pagination
            - page_size: Number of items per page (default: 20)
        
        Response (200 OK):
            {
                "count": 10,
                "next": "http://example.com/api/tasks/1/comments/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "task": 1,
                        "task_title": "Implement user authentication",
                        "author": 2,
                        "author_username": "johndoe",
                        "author_email": "john@example.com",
                        "author_full_name": "John Doe",
                        "content": "Great progress on this task!",
                        "is_edited": false,
                        "created_at": "2025-12-27T15:00:00Z",
                        "updated_at": "2025-12-27T15:00:00Z"
                    },
                    ...
                ]
            }
    
    POST /api/tasks/{task_id}/comments/
        Create a new comment on a task. The author is automatically set to the current user.
        
        Request Body:
            {
                "content": "This task is progressing well."
            }
        
        Response (201 Created):
            {
                "data": {
                    "id": 1,
                    "task": 1,
                    "task_title": "Implement user authentication",
                    "author": 2,
                    "author_username": "johndoe",
                    "author_email": "john@example.com",
                    "author_full_name": "John Doe",
                    "content": "This task is progressing well.",
                    "is_edited": false,
                    "created_at": "2025-12-27T15:00:00Z",
                    "updated_at": "2025-12-27T15:00:00Z"
                },
                "message": "Comment created successfully"
            }
    
    Authentication: Required (JWT token)
    Permissions: User must have access to the task (project member, assignee, or creator)
    """
    
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_task(self):
        """
        Get task object and verify user has access.
        
        Returns:
            Task: Task instance
            
        Raises:
            Http404: If task doesn't exist or user doesn't have access
        """
        task_id = self.kwargs.get('task_id')
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        task = get_object_or_404(
            Task.objects.filter(
                Q(project_id__in=project_ids) |
                Q(assignee=user) |
                Q(created_by=user)
            ).select_related('project', 'assignee', 'created_by'),
            pk=task_id
        )
        return task
    
    def get_queryset(self):
        """
        Return comments for the specified task.
        
        Returns:
            QuerySet: Comments for the task, ordered by creation date (newest first)
        """
        task = self.get_task()
        return TaskComment.objects.filter(task=task).select_related(
            'task', 'author'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """
        Create a comment and set the task and author.
        
        Args:
            serializer: TaskCommentSerializer instance with validated data
        """
        task = self.get_task()
        serializer.save(task=task)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new comment and return response with success message.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with created comment data
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created comment
        comment = serializer.instance
        response_serializer = self.get_serializer(comment)
        
        return Response(
            {
                'data': response_serializer.data,
                'message': 'Comment created successfully'
            },
            status=status.HTTP_201_CREATED
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a task comment.
    
    GET /api/tasks/{task_id}/comments/{id}/
        Retrieve a specific comment's details.
        Returns comment information including author details.
    
    PUT /api/tasks/{task_id}/comments/{id}/
        Full update of comment information.
        All fields must be provided.
        
        Request Body:
            {
                "content": "Updated comment content"
            }
    
    PATCH /api/tasks/{task_id}/comments/{id}/
        Partial update of comment information.
        Only provided fields will be updated.
    
    DELETE /api/tasks/{task_id}/comments/{id}/
        Delete a comment. Only comment author, project admins/owners, or task creator can delete comments.
        
        Response (204 No Content): Comment deleted successfully
    
    Authentication: Required (JWT token)
    Permissions:
        - GET: User must have access to the task (project member, assignee, or creator)
        - PUT/PATCH: User must be the comment author or project admin/owner
        - DELETE: User must be comment author, project admin/owner, or task creator
    """
    
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_task(self):
        """
        Get task object and verify user has access.
        
        Returns:
            Task: Task instance
            
        Raises:
            Http404: If task doesn't exist or user doesn't have access
        """
        task_id = self.kwargs.get('task_id')
        user = self.request.user
        
        # Get projects where user is a member
        from projects.models import ProjectMember
        project_ids = ProjectMember.objects.filter(user=user).values_list('project_id', flat=True)
        
        task = get_object_or_404(
            Task.objects.filter(
                Q(project_id__in=project_ids) |
                Q(assignee=user) |
                Q(created_by=user)
            ).select_related('project', 'assignee', 'created_by'),
            pk=task_id
        )
        return task
    
    def get_queryset(self):
        """
        Return comments for the specified task.
        
        Returns:
            QuerySet: Comments for the task
        """
        task = self.get_task()
        return TaskComment.objects.filter(task=task).select_related(
            'task', 'author'
        ).order_by('-created_at')
    
    def get_object(self):
        """
        Get the comment object.
        
        Returns:
            TaskComment: Comment instance
            
        Raises:
            Http404: If comment doesn't exist
        """
        queryset = self.get_queryset()
        comment_id = self.kwargs.get('pk')
        comment = get_object_or_404(queryset, pk=comment_id)
        return comment
    
    def update(self, request, *args, **kwargs):
        """
        Update comment information (PUT).
        
        Only comment author or project admins/owners can update comments.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated comment data
        """
        comment = self.get_object()
        user = request.user
        task = comment.task
        
        # Check if user can update (comment author or project admin/owner)
        if not (comment.author == user or task.project.is_admin(user)):
            return Response(
                {'error': 'Only comment author or project admins/owners can update comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(comment, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Comment updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update comment information (PATCH).
        
        Only comment author or project admins/owners can update comments.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated comment data
        """
        comment = self.get_object()
        user = request.user
        task = comment.task
        
        # Check if user can update (comment author or project admin/owner)
        if not (comment.author == user or task.project.is_admin(user)):
            return Response(
                {'error': 'Only comment author or project admins/owners can update comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(comment, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Comment updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a comment (DELETE).
        
        Only comment author, project admins/owners, or task creator can delete comments.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: Empty response with 204 status
        """
        comment = self.get_object()
        user = request.user
        task = comment.task
        
        # Check if user can delete (comment author, project admin/owner, or task creator)
        can_delete = (
            comment.author == user or
            task.project.is_admin(user) or
            task.created_by == user
        )
        
        if not can_delete:
            return Response(
                {'error': 'Only comment author, project admins/owners, or task creator can delete comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        comment_content = comment.content[:50]  # First 50 chars for message
        self.perform_destroy(comment)
        
        return Response(
            {'message': f'Comment "{comment_content}..." deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
