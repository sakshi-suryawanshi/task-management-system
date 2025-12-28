"""
Django settings for taskmanager project.

Production-ready configuration for Task Management System.
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, ''),
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0', 'testserver'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Token blacklist for enhanced security
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',
    
    # Local apps
    'users.apps.UsersConfig',  # Use custom AppConfig to load signals
    'teams',
    'projects',
    'tasks',
    'notifications',
    'core.apps.CoreConfig',  # Use custom AppConfig to load signals
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'taskmanager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'taskmanager.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('MYSQL_DATABASE', default='taskmanager'),
        'USER': env('MYSQL_USER', default='taskuser'),
        'PASSWORD': env('MYSQL_PASSWORD', default='taskpass'),
        'HOST': env('MYSQL_HOST', default='db'),
        'PORT': env('MYSQL_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
# https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = 'users.User'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# JWT Settings
# Comprehensive JWT configuration for production-ready authentication
SIMPLE_JWT = {
    # Token lifetimes
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Short-lived access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # Longer-lived refresh tokens
    'ROTATE_REFRESH_TOKENS': True,  # Rotate refresh token on each use
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist old tokens after rotation
    
    # Token algorithm and signing
    'ALGORITHM': 'HS256',  # HMAC with SHA-256
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,  # For symmetric algorithms, same as SIGNING_KEY
    'AUDIENCE': None,
    'ISSUER': None,
    
    # Token header configuration
    'AUTH_HEADER_TYPES': ('Bearer',),  # Authorization: Bearer <token>
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',  # Field in User model to use as token identifier
    'USER_ID_CLAIM': 'user_id',  # Claim name in token payload
    
    # Token type
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    # JTI (JWT ID) claim for token blacklisting
    'JTI_CLAIM': 'jti',
    
    # Token sliding (optional, for session-like behavior)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
    
    # Additional claims (optional)
    'TOKEN_OBTAIN_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenObtainPairSerializer',
    'TOKEN_REFRESH_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenRefreshSerializer',
    'TOKEN_VERIFY_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenVerifySerializer',
    'TOKEN_BLACKLIST_SERIALIZER': 'rest_framework_simplejwt.serializers.TokenBlacklistSerializer',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ============================================================================
# Celery Configuration
# ============================================================================
# Production-ready Celery configuration for distributed task queue.
# Celery uses Redis as both message broker and result backend.

# Broker and Result Backend URLs
# Redis is used for both message queuing and storing task results
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')

# Serialization Configuration
# JSON is the recommended format for security and compatibility
CELERY_ACCEPT_CONTENT = ['json']  # Only accept JSON serialized tasks
CELERY_TASK_SERIALIZER = 'json'  # Serialize task data as JSON
CELERY_RESULT_SERIALIZER = 'json'  # Serialize result data as JSON

# Timezone Configuration
CELERY_TIMEZONE = 'UTC'  # Use UTC for consistent scheduling across timezones
CELERY_ENABLE_UTC = True  # Enable UTC timezone support

# Task Execution Configuration
CELERY_TASK_TRACK_STARTED = True  # Track when tasks are started (not just received)
CELERY_TASK_TIME_LIMIT = 30 * 60  # Hard time limit: 30 minutes (task is killed after this)
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # Soft time limit: 25 minutes (raises exception, allows cleanup)
CELERY_TASK_ACKS_LATE = True  # Acknowledge tasks only after completion (prevents task loss on worker crash)
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Reject tasks if worker connection is lost

# Task Result Configuration
CELERY_RESULT_EXPIRES = 3600  # Result expiration time: 1 hour (prevents Redis memory buildup)
CELERY_RESULT_EXTENDED = True  # Store more result metadata (useful for monitoring)

# Worker Configuration
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # Prefetch 4 tasks per worker process (balance between throughput and fairness)
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # Restart worker child process after 1000 tasks (prevents memory leaks)
CELERY_WORKER_SEND_TASK_EVENTS = True  # Send task events for monitoring (required for Flower)
CELERY_WORKER_DISABLE_RATE_LIMITS = False  # Enable rate limiting for tasks

# Task Event Configuration
CELERY_TASK_SEND_SENT_EVENT = True  # Send 'task-sent' event (required for Flower monitoring)
CELERY_TASK_IGNORE_RESULT = False  # Store task results (can be set per-task for better performance)

# Task Routing (Optional - for future use with multiple queues)
# CELERY_TASK_ROUTES = {
#     'notifications.tasks.*': {'queue': 'notifications'},
#     'projects.tasks.*': {'queue': 'projects'},
# }

# Task Retry Configuration
# Note: Retry logic should be configured per-task using @task decorator parameters
# Example: @app.task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # Default retry delay: 60 seconds (used if retry_backoff is False)

# ============================================================================
# Celery Beat Configuration (Periodic Task Scheduler)
# ============================================================================
# Uses django-celery-beat for database-backed periodic task scheduling.
# This allows dynamic scheduling without code changes.
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Beat Schedule (Optional - can also be managed via Django admin)
# For static schedules, use CELERY_BEAT_SCHEDULE dictionary here.
# For dynamic schedules, use django-celery-beat PeriodicTask model.
# CELERY_BEAT_SCHEDULE = {
#     'send-daily-reminders': {
#         'task': 'notifications.tasks.send_daily_reminders',
#         'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
#     },
# }

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@taskmanager.com')

# API Documentation (drf-spectacular)
# Comprehensive OpenAPI 3.0 schema configuration for Swagger/ReDoc documentation
SPECTACULAR_SETTINGS = {
    # Basic Information
    'TITLE': 'Task Management System API',
    'DESCRIPTION': """
    # Task Management System API Documentation
    
    A comprehensive REST API for managing tasks, projects, teams, and notifications.
    
    ## Features
    
    - **User Management**: Registration, authentication, and profile management with JWT
    - **Team Management**: Create teams, manage members, role-based access control
    - **Project Management**: Create projects, assign teams, track progress, analytics
    - **Task Management**: Create tasks, assignees, priorities, dependencies, comments, attachments
    - **Notifications**: Real-time in-app notifications with filtering and search
    
    ## Authentication
    
    This API uses JWT (JSON Web Tokens) for authentication. To authenticate:
    
    1. Register a new user at `/api/auth/register/` or login at `/api/auth/login/`
    2. Use the returned `access` token in the Authorization header: `Bearer <access_token>`
    3. Refresh tokens using `/api/token/refresh/` when access token expires
    
    ## Rate Limiting
    
    API requests are rate-limited to ensure fair usage. Contact support if you need higher limits.
    
    ## Pagination
    
    List endpoints support pagination with default page size of 20 items. Use `page` and `page_size` query parameters.
    
    ## Filtering & Search
    
    Most list endpoints support filtering and search. See individual endpoint documentation for available filters.
    
    ## Error Responses
    
    The API uses standard HTTP status codes:
    - `200 OK`: Successful request
    - `201 Created`: Resource created successfully
    - `400 Bad Request`: Invalid request data
    - `401 Unauthorized`: Authentication required
    - `403 Forbidden`: Insufficient permissions
    - `404 Not Found`: Resource not found
    - `500 Internal Server Error`: Server error
    
    ## Support
    
    For issues or questions, please contact the development team.
    """,
    'VERSION': '1.0.0',
    'CONTACT': {
        'name': 'API Support',
        'email': 'support@taskmanager.com',
    },
    'LICENSE': {
        'name': 'MIT License',
    },
    
    # Schema Generation
    'SERVE_INCLUDE_SCHEMA': False,  # Don't include schema in response
    'COMPONENT_SPLIT_REQUEST': True,  # Split request/response schemas
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,  # Don't require read-only fields
    'SCHEMA_PATH_PREFIX': '/api',  # API path prefix
    
    # UI Configuration
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,  # Enable deep linking
        'displayOperationId': True,  # Show operation IDs
        'defaultModelsExpandDepth': 2,  # Expand models by default
        'defaultModelExpandDepth': 2,  # Expand model properties
        'displayRequestDuration': True,  # Show request duration
        'docExpansion': 'list',  # Expand tags by default
        'filter': True,  # Enable filter box
        'showExtensions': True,  # Show extensions
        'showCommonExtensions': True,  # Show common extensions
        'tryItOutEnabled': True,  # Enable "Try it out" by default
    },
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,  # Show download button
        'hideHostname': False,  # Show hostname
        'hideSingleRequestSampleTab': False,  # Show single request sample
        'expandResponses': '200,201',  # Expand successful responses
        'pathInMiddlePanel': True,  # Show path in middle panel
        'requiredPropsFirst': True,  # Show required props first
        'sortOperationsAlphabetically': False,  # Keep original order
        'sortTagsAlphabetically': False,  # Keep original order
    },
    
    # Security
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'JWT authentication using Bearer token. Format: "Bearer {token}"',
            }
        }
    },
    'SECURITY': [{'BearerAuth': []}],  # Apply Bearer auth to all endpoints
    
    # Tags for organizing endpoints
    'TAGS': [
        {
            'name': 'Authentication',
            'description': 'User registration, login, and token management endpoints',
        },
        {
            'name': 'Users',
            'description': 'User profile management endpoints',
        },
        {
            'name': 'Teams',
            'description': 'Team management and team member operations',
        },
        {
            'name': 'Projects',
            'description': 'Project management, analytics, and project member operations',
        },
        {
            'name': 'Tasks',
            'description': 'Task management, assignment, comments, and attachments',
        },
        {
            'name': 'Notifications',
            'description': 'Notification listing, marking as read, and counts',
        },
        {
            'name': 'Health',
            'description': 'System health check endpoints',
        },
    ],
    
    # Response Examples
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],  # Allow access to docs
    'SERVE_AUTHENTICATION': None,  # No auth required for docs
    
    # Schema Customization
    'TAGS_META': [
        {
            'name': 'Authentication',
            'externalDocs': {
                'description': 'JWT Authentication Guide',
                'url': 'https://django-rest-framework-simplejwt.readthedocs.io/',
            },
        },
    ],
    
    # Extensions
    'EXTENSIONS_INFO': {
        'x-logo': {
            'url': 'https://via.placeholder.com/200x50?text=Task+Manager',
            'altText': 'Task Management System',
        },
    },
    
    # Customization
    'SORT_OPERATIONS': False,  # Keep original operation order
    'SORT_TAGS': False,  # Keep original tag order
    'ENUM_NAME_OVERRIDES': {
        'TaskStatusEnum': 'tasks.models.Task.STATUS_CHOICES',
        'TaskPriorityEnum': 'tasks.models.Task.PRIORITY_CHOICES',
        'ProjectStatusEnum': 'projects.models.Project.STATUS_CHOICES',
        'ProjectPriorityEnum': 'projects.models.Project.PRIORITY_CHOICES',
        'NotificationTypeEnum': 'notifications.models.Notification.NOTIFICATION_TYPES',
    },
    
    # Advanced Settings
    'PREPROCESSING_HOOKS': [],  # Custom preprocessing hooks
    'POSTPROCESSING_HOOKS': [],  # Custom postprocessing hooks
    'SERVE_URLCONF': None,  # Use default URL conf
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.generators.SchemaGenerator',
}

# Security Settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
