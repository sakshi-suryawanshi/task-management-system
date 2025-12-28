"""
API views for User authentication and management.

This module contains views for user registration, login, and profile management.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    
    Creates a new user account and returns JWT tokens.
    
    Request Body:
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "securepassword123",
            "password2": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "member",  # optional
            "phone": "+1234567890",  # optional
            "bio": "Software developer"  # optional
        }
    
    Response (201 Created):
        {
            "user": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "member",
                ...
            },
            "tokens": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            },
            "message": "User registered successfully"
        }
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated registration
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user and return JWT tokens.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with user data and tokens
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response(
            {
                'user': user_serializer.data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'message': 'User registered successfully'
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login_view(request):
    """
    API endpoint for user login.
    
    POST /api/auth/login/
    
    Authenticates user credentials and returns JWT tokens.
    
    Request Body:
        {
            "username": "johndoe",  # or email
            "password": "securepassword123"
        }
    
    Response (200 OK):
        {
            "user": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                ...
            },
            "tokens": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            },
            "message": "Login successful"
        }
    
    Error Response (400 Bad Request):
        {
            "error": "Invalid username/email or password."
        }
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Invalid credentials',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = serializer.validated_data['user']
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    # Serialize user data
    user_serializer = UserSerializer(user)
    
    return Response(
        {
            'user': user_serializer.data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Login successful'
        },
        status=status.HTTP_200_OK
    )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for user profile management.
    
    GET /api/auth/profile/
        Retrieve current user's profile information.
        Returns complete user and profile data.
    
    PUT /api/auth/profile/
        Update user profile (full update - all fields required).
        Updates both User and UserProfile fields.
    
    PATCH /api/auth/profile/
        Partial update of user profile.
        Only provided fields will be updated.
    
    Authentication: Required (JWT token)
    Permissions: User can only access their own profile
    
    Request Body (PUT/PATCH):
        {
            "first_name": "John",
            "last_name": "Doe",
            "role": "developer",
            "bio": "Software developer",
            "phone": "+1234567890",
            "job_title": "Senior Developer",
            "department": "Engineering",
            "location": "remote",
            "city": "San Francisco",
            "country": "USA",
            "website": "https://johndoe.com",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "timezone": "America/Los_Angeles",
            "language": "en",
            "email_notifications": true,
            "push_notifications": true
        }
    
    Response (200 OK):
        {
            "id": 1,
            "username": "johndoe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "role": "developer",
            "avatar": null,
            "bio": "Software developer",
            "phone": "+1234567890",
            "job_title": "Senior Developer",
            "department": "Engineering",
            "location": "remote",
            "address": "",
            "city": "San Francisco",
            "country": "USA",
            "website": "https://johndoe.com",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe",
            "twitter": "",
            "timezone": "America/Los_Angeles",
            "language": "en",
            "email_notifications": true,
            "push_notifications": true,
            "profile_created_at": "2025-12-27T15:00:00Z",
            "profile_updated_at": "2025-12-27T16:00:00Z",
            "created_at": "2025-12-27T15:00:00Z",
            "updated_at": "2025-12-27T16:00:00Z"
        }
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the current authenticated user.
        
        Returns:
            User: Current authenticated user instance
        """
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve current user's profile.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with user profile data
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """
        Full update of user profile (PUT).
        
        All fields must be provided for PUT request.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated user profile data
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Profile updated successfully'
            },
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partial update of user profile (PATCH).
        
        Only provided fields will be updated.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response: JSON response with updated user profile data
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {
                'data': serializer.data,
                'message': 'Profile updated successfully'
            },
            status=status.HTTP_200_OK
        )
