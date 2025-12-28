"""
URL configuration for teams app.

This module defines all URL patterns for team management.
"""

from django.urls import path
from .views import (
    TeamListCreateView,
    TeamDetailView,
    TeamMemberView,
)

app_name = 'teams'

urlpatterns = [
    # Team CRUD endpoints
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    
    # Team member management endpoints
    path('<int:team_id>/members/', TeamMemberView.as_view(), name='team-member-add'),
    path('<int:team_id>/members/<int:user_id>/', TeamMemberView.as_view(), name='team-member-update-delete'),
]

