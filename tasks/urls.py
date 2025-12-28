"""
URL configuration for tasks app.

This module defines all URL patterns for task management.
"""

from django.urls import path
from .views import (
    TaskListCreateView,
    TaskDetailView,
    TaskAssigneeView,
    TaskStatusUpdateView,
    CommentListCreateView,
    CommentDetailView,
)

app_name = 'tasks'

urlpatterns = [
    # Task CRUD endpoints
    path('', TaskListCreateView.as_view(), name='task-list-create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    
    # Task assignment endpoint
    path('<int:task_id>/assign/', TaskAssigneeView.as_view(), name='task-assign'),
    
    # Task status update endpoint
    path('<int:task_id>/status/', TaskStatusUpdateView.as_view(), name='task-status-update'),
    
    # Task comment endpoints
    path('<int:task_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('<int:task_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]

