"""
API views for Notification management.

This module contains views for notification listing, marking as read,
and getting notification counts.
"""

from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationMarkReadSerializer,
)


@extend_schema(
    tags=['Notifications'],
    summary='List notifications',
    description='List all notifications for the current authenticated user. Supports filtering, search, and pagination.',
    parameters=[
        OpenApiParameter('read', description='Filter by read status (true/false)'),
        OpenApiParameter('type', description='Filter by notification type (task_assigned, task_completed, etc.)'),
        OpenApiParameter('search', description='Search notifications by message content'),
        OpenApiParameter('ordering', description='Order by field (e.g., -created_at, read, type)'),
    ],
    responses={200: NotificationSerializer(many=True)},
)
class NotificationListView(generics.ListAPIView):
    """
    API endpoint for listing user notifications.
    
    GET /api/notifications/ - List all notifications for current user
    
    Authentication: Required (JWT token)
    Permissions: Users can only see their own notifications
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message']
    ordering_fields = ['created_at', 'read', 'type']
    ordering = ['-created_at']  # Default ordering: newest first
    
    def get_queryset(self):
        """
        Return notifications for the current authenticated user.
        
        Filters notifications based on query parameters:
        - read: Filter by read status
        - type: Filter by notification type
        
        Returns:
            QuerySet: Filtered notifications for current user
        """
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read status
        read_param = self.request.query_params.get('read', None)
        if read_param is not None:
            read_value = read_param.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(read=read_value)
        
        # Filter by notification type
        type_param = self.request.query_params.get('type', None)
        if type_param:
            queryset = queryset.filter(type=type_param)
        
        # Optimize queries with select_related for foreign keys
        queryset = queryset.select_related('user', 'related_content_type')
        
        return queryset


@extend_schema(
    tags=['Notifications'],
    summary='Mark notification as read',
    description='Mark a specific notification as read. Users can only mark their own notifications.',
    responses={
        200: NotificationSerializer,
        403: {'description': 'You can only mark your own notifications as read'},
        404: {'description': 'Notification not found'},
    },
)
class NotificationMarkReadView(APIView):
    """
    API endpoint for marking a notification as read.
    
    PATCH /api/notifications/{id}/mark-read/ - Mark notification as read
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, pk):
        """
        Mark a notification as read.
        
        Args:
            request: HTTP request object
            pk: Notification ID
            
        Returns:
            Response: JSON response with updated notification data
        """
        notification = get_object_or_404(Notification, pk=pk)
        
        # Ensure user can only mark their own notifications as read
        if notification.user != request.user:
            return Response(
                {
                    'error': 'You can only mark your own notifications as read'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark notification as read
        notification.mark_as_read()
        
        # Serialize and return updated notification
        serializer = NotificationSerializer(notification)
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Notification marked as read'
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Notifications'],
    summary='Mark all notifications as read',
    description='Mark all unread notifications for the current user as read.',
    responses={
        200: {
            'description': 'All notifications marked as read',
            'examples': [
                {
                    'message': 'All notifications marked as read',
                    'marked_count': 5,
                },
            ],
        },
    },
)
class NotificationMarkAllReadView(APIView):
    """
    API endpoint for marking all notifications as read.
    
    POST /api/notifications/mark-all-read/ - Mark all notifications as read
    """
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationMarkReadSerializer
    
    def post(self, request):
        """
        Mark all unread notifications for the current user as read.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with success message and count
        """
        user = request.user
        
        # Get count of unread notifications before marking
        unread_count = Notification.get_unread_count(user)
        
        # Mark all notifications as read
        Notification.mark_all_as_read(user)
        
        return Response(
            {
                'message': 'All notifications marked as read',
                'marked_count': unread_count
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Notifications'],
    summary='Get notification counts',
    description='Get unread and total notification counts for the current user. Useful for displaying notification badges.',
    responses={
        200: {
            'description': 'Notification counts',
            'examples': [
                {
                    'unread_count': 5,
                    'total_count': 25,
                },
            ],
        },
    },
)
class NotificationCountView(APIView):
    """
    API endpoint for getting notification counts.
    
    GET /api/notifications/count/
        Get the count of unread and total notifications for the current user.
        
        Response (200 OK):
            {
                "unread_count": 5,
                "total_count": 25
            }
    
    Authentication: Required (JWT token)
    Permissions: Users can only see their own notification counts
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get notification counts for the current user.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with unread and total counts
        """
        user = request.user
        
        # Get counts
        unread_count = Notification.get_unread_count(user)
        total_count = Notification.objects.filter(user=user).count()
        
        return Response(
            {
                'unread_count': unread_count,
                'total_count': total_count
            },
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=['Notifications'],
    summary='Get notification details',
    description="""
    Retrieve detailed information about a specific notification.
    
    Returns complete notification information including:
    - Notification message and type
    - Read status and timestamps
    - Related object information (task, project, etc.)
    - Metadata (additional context)
    - Computed fields (age_in_hours, age_in_days, is_recent)
    - Display helpers (icon, type_display_class)
    
    **Authentication:** Required (JWT Bearer token)
    **Permissions:** Users can only view their own notifications
    
    **Use Cases:**
    - Display notification details in UI
    - Show notification context and related objects
    - Track notification age and status
    """,
    responses={
        200: {
            'description': 'Notification details retrieved successfully',
            'examples': [
                OpenApiExample(
                    'Notification Response',
                    value={
                        'id': 1,
                        'user': 1,
                        'message': "You have been assigned to task 'Implement authentication'",
                        'type': 'task_assigned',
                        'type_display': 'Task Assigned',
                        'read': False,
                        'read_at': None,
                        'related_content_type': 8,
                        'related_object_id': 1,
                        'related_object': 'Task: Implement authentication',
                        'metadata': {'task_id': 1, 'project_id': 1},
                        'created_at': '2025-12-27T15:00:00Z',
                        'age_in_hours': 2,
                        'age_in_days': 0,
                        'is_recent': True,
                        'icon': 'assignment',
                        'type_display_class': 'task-assigned',
                    },
                ),
            ],
        },
        403: {
            'description': 'You can only view your own notifications',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={'detail': 'You do not have permission to perform this action.'},
                ),
            ],
        },
        404: {
            'description': 'Notification not found',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={'detail': 'Not found.'},
                ),
            ],
        },
    },
)
class NotificationDetailView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving a single notification.
    
    GET /api/notifications/{id}/ - Get notification details
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return notifications for the current authenticated user only.
        
        Returns:
            QuerySet: Notifications for current user
        """
        return Notification.objects.filter(user=self.request.user).select_related(
            'user', 'related_content_type'
        )
