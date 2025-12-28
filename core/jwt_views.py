"""
Custom JWT authentication views with OpenAPI documentation.

This module wraps the default JWT views from rest_framework_simplejwt
and adds comprehensive OpenAPI documentation for Swagger/ReDoc.
"""

from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
    TokenVerifyView as BaseTokenVerifyView,
    TokenBlacklistView as BaseTokenBlacklistView,
)
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    tags=['Authentication'],
    summary='Obtain JWT token pair',
    description="""
    Authenticate user credentials and receive JWT access and refresh tokens.
    
    This endpoint is used to login and obtain authentication tokens. You can use
    either username or email along with password to authenticate.
    
    **Request Body:**
    - `username` (optional): Username for authentication
    - `email` (optional): Email for authentication (alternative to username)
    - `password` (required): User password
    
    **Note:** You must provide either `username` OR `email` (not both).
    
    **Response:**
    Returns both access and refresh tokens:
    - `access`: Short-lived token (1 hour) for API authentication
    - `refresh`: Long-lived token (7 days) for obtaining new access tokens
    
    **Token Usage:**
    - Use the `access` token in the Authorization header: `Bearer <access_token>`
    - When the access token expires, use the `refresh` token at `/api/token/refresh/`
    - Access tokens expire after 1 hour
    - Refresh tokens expire after 7 days
    
    **Security:**
    - Tokens are automatically rotated on refresh
    - Old tokens are blacklisted after rotation
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'Username for authentication',
                    'example': 'johndoe',
                },
                'email': {
                    'type': 'string',
                    'format': 'email',
                    'description': 'Email for authentication (alternative to username)',
                    'example': 'john@example.com',
                },
                'password': {
                    'type': 'string',
                    'format': 'password',
                    'description': 'User password',
                    'example': 'securepassword123',
                },
            },
            'required': ['password'],
        },
    },
    responses={
        200: {
            'description': 'Authentication successful',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    },
                ),
            ],
        },
        401: {
            'description': 'Invalid credentials',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={
                        'detail': 'No active account found with the given credentials',
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Login with Username',
            value={
                'username': 'johndoe',
                'password': 'securepassword123',
            },
        ),
        OpenApiExample(
            'Login with Email',
            value={
                'email': 'john@example.com',
                'password': 'securepassword123',
            },
        ),
    ],
)
class TokenObtainPairView(BaseTokenObtainPairView):
    """
    Custom JWT token obtain view with OpenAPI documentation.
    
    POST /api/token/ - Obtain JWT access and refresh tokens
    """
    pass


@extend_schema(
    tags=['Authentication'],
    summary='Refresh JWT access token',
    description="""
    Refresh an expired access token using a valid refresh token.
    
    When your access token expires (after 1 hour), use this endpoint to obtain
    a new access token without requiring the user to login again.
    
    **Request Body:**
    - `refresh` (required): Valid refresh token
    
    **Response:**
    Returns a new access token:
    - `access`: New short-lived token (1 hour) for API authentication
    
    **Token Rotation:**
    - The refresh token is automatically rotated on each use
    - The old refresh token is blacklisted and cannot be reused
    - You should use the new refresh token for subsequent refresh requests
    
    **Security:**
    - Old refresh tokens are automatically blacklisted
    - Each refresh generates a new refresh token for enhanced security
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Valid refresh token',
                    'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                },
            },
            'required': ['refresh'],
        },
    },
    responses={
        200: {
            'description': 'Token refreshed successfully',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                    },
                ),
            ],
        },
        401: {
            'description': 'Invalid or expired refresh token',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={
                        'detail': 'Token is invalid or expired',
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Refresh Token Request',
            value={
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            },
        ),
    ],
)
class TokenRefreshView(BaseTokenRefreshView):
    """
    Custom JWT token refresh view with OpenAPI documentation.
    
    POST /api/token/refresh/ - Refresh JWT access token
    """
    pass


@extend_schema(
    tags=['Authentication'],
    summary='Verify JWT token',
    description="""
    Verify if a JWT token is valid and not expired.
    
    This endpoint allows you to check if a token (access or refresh) is still valid
    without making an actual API request. Useful for token validation in frontend applications.
    
    **Request Body:**
    - `token` (required): JWT token to verify (access or refresh token)
    
    **Response:**
    Returns an empty response with 200 status if token is valid.
    
    **Use Cases:**
    - Frontend token validation
    - Token expiration checking
    - Security validation before making API requests
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'token': {
                    'type': 'string',
                    'description': 'JWT token to verify (access or refresh)',
                    'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                },
            },
            'required': ['token'],
        },
    },
    responses={
        200: {
            'description': 'Token is valid',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={},
                ),
            ],
        },
        401: {
            'description': 'Token is invalid or expired',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={
                        'detail': 'Token is invalid or expired',
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Verify Token Request',
            value={
                'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            },
        ),
    ],
)
class TokenVerifyView(BaseTokenVerifyView):
    """
    Custom JWT token verify view with OpenAPI documentation.
    
    POST /api/token/verify/ - Verify JWT token validity
    """
    pass


@extend_schema(
    tags=['Authentication'],
    summary='Blacklist JWT refresh token',
    description="""
    Blacklist a refresh token to prevent its future use.
    
    This endpoint allows you to explicitly blacklist a refresh token, typically
    used when a user logs out. Once blacklisted, the token cannot be used to
    obtain new access tokens.
    
    **Request Body:**
    - `refresh` (required): Refresh token to blacklist
    
    **Response:**
    Returns an empty response with 200 status if token is successfully blacklisted.
    
    **Use Cases:**
    - User logout
    - Token revocation
    - Security token invalidation
    
    **Note:**
    - Only refresh tokens can be blacklisted
    - Access tokens expire automatically and don't need blacklisting
    - Blacklisted tokens cannot be reused
    """,
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh token to blacklist',
                    'example': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                },
            },
            'required': ['refresh'],
        },
    },
    responses={
        200: {
            'description': 'Token blacklisted successfully',
            'examples': [
                OpenApiExample(
                    'Success Response',
                    value={},
                ),
            ],
        },
        400: {
            'description': 'Invalid token or token already blacklisted',
            'examples': [
                OpenApiExample(
                    'Error Response',
                    value={
                        'detail': 'Token is blacklisted',
                    },
                ),
            ],
        },
    },
    examples=[
        OpenApiExample(
            'Blacklist Token Request',
            value={
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
            },
        ),
    ],
)
class TokenBlacklistView(BaseTokenBlacklistView):
    """
    Custom JWT token blacklist view with OpenAPI documentation.
    
    POST /api/token/blacklist/ - Blacklist JWT refresh token
    """
    pass

