"""
URL configuration for notifications app.

This module defines all URL patterns for notification management.
"""

from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationCountView,
)

app_name = 'notifications'

urlpatterns = [
    # Notification list endpoint
    path('', NotificationListView.as_view(), name='notification-list'),
    
    # Notification detail endpoint
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    
    # Mark notification as read
    path('<int:pk>/mark-read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    
    # Mark all notifications as read
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    
    # Notification count endpoint
    path('count/', NotificationCountView.as_view(), name='notification-count'),
]

