"""
URL configuration for users app.

This module defines all URL patterns for user authentication and management.
"""

from django.urls import path
from .views import (
    UserRegistrationView,
    user_login_view,
    UserProfileView,
)

app_name = 'users'

urlpatterns = [
    # User Registration
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # User Login
    path('login/', user_login_view, name='login'),
    
    # User Profile Management
    path('profile/', UserProfileView.as_view(), name='profile'),
]

