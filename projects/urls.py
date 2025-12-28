"""
URL configuration for projects app.

This module defines all URL patterns for project management.
"""

from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ProjectMemberView,
    ProjectStatsView,
)

app_name = 'projects'

urlpatterns = [
    # Project CRUD endpoints
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    
    # Project member management endpoints
    path('<int:project_id>/members/', ProjectMemberView.as_view(), name='project-member-add'),
    path('<int:project_id>/members/<int:user_id>/', ProjectMemberView.as_view(), name='project-member-update-delete'),
    
    # Project analytics endpoint
    path('<int:project_id>/stats/', ProjectStatsView.as_view(), name='project-stats'),
]

