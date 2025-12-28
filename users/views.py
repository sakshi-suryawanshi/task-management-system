"""
API views for User authentication and management.

This module contains views for user registration, login, and profile management.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileSerializer,
)

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    description="""
    Register a new user account and receive JWT authentication tokens.
    
    This endpoint allows anyone to create a new user account. Upon successful registration,
    you will receive both access and refresh JWT tokens that can be used to authenticate
    subsequent API requests.
    
    **Required Fields:**
    - `username`: Unique username (3-30 characters, alphanumeric and underscores)
    - `email`: Valid email address (must be unique)
    - `password`: Strong password (minimum 8 characters)
    - `password2`: Password confirmation (must match password)
    
    **Optional Fields:**
    - `first_name`, `last_name`: User's full name
    - `role`: User role (admin, manager, developer, member) - defaults to 'member'
    - `phone`: Phone number with country code
    - `bio`: Short biography or description
    """,
    request=UserRegistrationSerializer,
    responses={
        201: {
            'description': 'User registered successfully',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={
                        'user': {
                            'id': 1,
                            'username': 'johndoe',
                            'email': 'john@example.com',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'role': 'member',
                        },
                        'tokens': {
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                        },
                        'message': 'User registered successfully',
                    },
                ),
            ],
        },
        400: {
            'description': 'Validation error',
            'examples': [
                OpenApiExample(
                    'Validation Error',
                    value={
                        'username': ['A user with this username already exists.'],
                        'email': ['A user with this email already exists.'],
                        'password2': ['Passwords do not match.'],
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Registration Request',
            value={
                'username': 'johndoe',
                'email': 'john@example.com',
                'password': 'securepassword123',
                'password2': 'securepassword123',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'member',
                'phone': '+1234567890',
                'bio': 'Software developer',
            },
        ),
    ],
)
class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    
    Creates a new user account and returns JWT tokens.
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


@extend_schema(
    tags=['Authentication'],
    summary='User login',
    description="""
    Authenticate user credentials and receive JWT tokens.
    
    This endpoint authenticates a user using their username (or email) and password.
    Upon successful authentication, you will receive both access and refresh JWT tokens.
    
    **Authentication:**
    - You can use either `username` or `email` to login
    - Password must match the user's account password
    
    **Token Usage:**
    - Use the `access` token in the Authorization header: `Bearer <access_token>`
    - Access tokens expire after 1 hour
    - Use the `refresh` token at `/api/token/refresh/` to get a new access token
    """,
    request=UserLoginSerializer,
    responses={
        200: {
            'description': 'Login successful',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={
                        'user': {
                            'id': 1,
                            'username': 'johndoe',
                            'email': 'john@example.com',
                            'first_name': 'John',
                            'last_name': 'Doe',
                        },
                        'tokens': {
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                        },
                        'message': 'Login successful',
                    },
                ),
            ],
        },
        400: {
            'description': 'Invalid credentials',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={
                        'error': 'Invalid credentials',
                        'details': {
                            'non_field_errors': ['Invalid username/email or password.'],
                        },
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                'username': 'johndoe',  # or use 'email' field
                'password': 'securepassword123',
            },
        ),
    ],
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def user_login_view(request):
    """
    API endpoint for user login.
    
    POST /api/auth/login/
    
    Authenticates user credentials and returns JWT tokens.
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


@extend_schema_view(
    get=extend_schema(
        tags=['Users'],
        summary='Get current user profile',
        description="""
        Retrieve the authenticated user's complete profile information.
        
        Returns all user and profile data including personal information, preferences,
        and notification settings.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** Users can only access their own profile
        """,
        responses={
            200: UserProfileSerializer,
            401: {'description': 'Authentication required'},
        },
    ),
    put=extend_schema(
        tags=['Users'],
        summary='Update user profile (full)',
        description="""
        Perform a full update of the user profile. All fields must be provided.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** Users can only update their own profile
        
        **Note:** For partial updates, use PATCH method instead.
        """,
        request=UserProfileSerializer,
        responses={
            200: {
                'description': 'Profile updated successfully',
                'examples': [
                    OpenApiExample(
                        'Success Response',
                        value={
                            'data': {
                                'id': 1,
                                'username': 'johndoe',
                                'email': 'john@example.com',
                                'first_name': 'John',
                                'last_name': 'Doe',
                                'role': 'developer',
                                'bio': 'Software developer',
                            },
                            'message': 'Profile updated successfully',
                        },
                    ),
                ],
            },
            400: {'description': 'Validation error'},
            401: {'description': 'Authentication required'},
        },
    ),
    patch=extend_schema(
        tags=['Users'],
        summary='Update user profile (partial)',
        description="""
        Perform a partial update of the user profile. Only provided fields will be updated.
        
        **Authentication:** Required (JWT Bearer token)
        **Permissions:** Users can only update their own profile
        
        **Note:** This is the recommended method for updating profiles as it allows
        updating only specific fields without requiring all fields.
        """,
        request=UserProfileSerializer,
        responses={
            200: {
                'description': 'Profile updated successfully',
            },
            400: {'description': 'Validation error'},
            401: {'description': 'Authentication required'},
        },
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for user profile management.
    
    GET /api/auth/profile/ - Retrieve current user's profile
    PUT /api/auth/profile/ - Full update (all fields required)
    PATCH /api/auth/profile/ - Partial update (only provided fields)
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
