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

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0', 'testserver', 'web'])

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
    'projects.apps.ProjectsConfig',  # Use custom AppConfig to load signals
    'tasks.apps.TasksConfig',  # Use custom AppConfig to load signals
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

# Test database configuration
# Use SQLite for faster test execution (in-memory database)
# This is detected automatically by pytest-django, but we can also set it explicitly
# Pytest-django will override this with its own test database settings if needed
import sys
if 'test' in sys.argv or 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
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

# ============================================================================
# Static Files Configuration
# ============================================================================
# Production-ready static files configuration for serving CSS, JavaScript, images, etc.
# Static files are collected via 'python manage.py collectstatic' and served by Nginx.
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# URL prefix for static files (used in templates and URLs)
# This is the URL path that will be used to access static files
STATIC_URL = '/static/'

# Absolute path to the directory where collectstatic will collect all static files
# This directory is served by Nginx in production
# In Docker: /app/staticfiles (mounted to static_volume)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Additional directories from which to collect static files (project-level static files)
# Django automatically finds static files in app/static/ directories
# Use this if you have project-level static files in a separate directory
# Example: STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_DIRS = []

# The storage engine to use when collecting static files
# Default uses FileSystemStorage which copies files to STATIC_ROOT
# Can be customized for cloud storage (S3, Azure, etc.) in production
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# List of finder classes that Django uses to locate static files
# Default finders include:
# - AppDirectoriesFinder: Finds static files in each app's static/ subdirectory
# - FileSystemFinder: Finds static files in directories listed in STATICFILES_DIRS
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',  # Finds files in STATICFILES_DIRS
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # Finds files in app/static/ directories
]

# ============================================================================
# Media Files Configuration
# ============================================================================
# Configuration for user-uploaded files (user content, attachments, etc.)
# Media files are served directly by Nginx (not through Django)

# URL prefix for media files (used in models and URLs)
# This is the URL path that will be used to access media files
MEDIA_URL = '/media/'

# Absolute path to the directory where user-uploaded files are stored
# In Docker: /app/media (mounted to media_volume)
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
# SMTP backend configuration for sending emails via Celery tasks
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)  # Use SSL instead of TLS if needed
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@taskmanager.com')

# Additional email settings for email templates
SITE_NAME = env('SITE_NAME', default='Task Management System')
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', default=DEFAULT_FROM_EMAIL)

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

# ============================================================================
# Logging Configuration
# ============================================================================
# Production-ready structured logging configuration with log rotation.
# Supports JSON structured logging for production and human-readable format for development.
# Logs are separated by component (Django, Celery, Application) for better organization.

import json
import logging
import logging.config
# Note: RotatingFileHandler and TimedRotatingFileHandler are referenced as strings
# in the LOGGING config, so explicit imports are not required but kept for clarity

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging configuration from environment variables
LOG_LEVEL = env('LOG_LEVEL', default='INFO').upper()
DJANGO_LOG_LEVEL = env('DJANGO_LOG_LEVEL', default=LOG_LEVEL).upper()
CELERY_LOG_LEVEL = env('CELERY_LOG_LEVEL', default=LOG_LEVEL).upper()
APP_LOG_LEVEL = env('APP_LOG_LEVEL', default=LOG_LEVEL).upper()

# Use structured JSON logging in production, verbose in development
USE_JSON_LOGGING = env.bool('USE_JSON_LOGGING', default=not DEBUG)

# Log rotation settings
LOG_MAX_BYTES = env.int('LOG_MAX_BYTES', default=10 * 1024 * 1024)  # 10MB
LOG_BACKUP_COUNT = env.int('LOG_BACKUP_COUNT', default=10)  # Keep 10 backup files
LOG_ROTATION_WHEN = env('LOG_ROTATION_WHEN', default='midnight')  # Rotate at midnight
LOG_ROTATION_INTERVAL = env.int('LOG_ROTATION_INTERVAL', default=1)  # Daily rotation


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Formats log records as JSON for easy parsing and analysis.
    """
    
    def format(self, record):
        """
        Format log record as JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            str: JSON-formatted log entry
        """
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'process_id': record.process,
            'thread_id': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        
        return json.dumps(log_data, default=str)


# Configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{name}] {module}.{funcName}:{lineno} {process:d} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {asctime} [{name}] - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'json': {
            '()': JSONFormatter,
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'detailed': {
            'format': '{levelname} {asctime} [{name}] {pathname}:{lineno} {funcName}() {process:d} {thread:d} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose' if DEBUG else 'simple',
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'django_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'django.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'json' if USE_JSON_LOGGING else 'verbose',
            'level': DJANGO_LOG_LEVEL,
        },
        'celery_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'celery.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'json' if USE_JSON_LOGGING else 'verbose',
            'level': CELERY_LOG_LEVEL,
        },
        'application_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'application.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'json' if USE_JSON_LOGGING else 'verbose',
            'level': APP_LOG_LEVEL,
        },
        'error_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'errors.log'),
            'when': LOG_ROTATION_WHEN,
            'interval': LOG_ROTATION_INTERVAL,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'json' if USE_JSON_LOGGING else 'detailed',
            'level': 'ERROR',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'security.log'),
            'maxBytes': LOG_MAX_BYTES,
            'backupCount': LOG_BACKUP_COUNT,
            'formatter': 'json' if USE_JSON_LOGGING else 'detailed',
            'level': 'WARNING',
        },
    },
    'root': {
        'handlers': ['console', 'application_file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        # Django framework logger
        'django': {
            'handlers': ['console', 'django_file'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False,
        },
        # Django database queries (can be verbose, disabled by default)
        'django.db.backends': {
            'handlers': ['console', 'django_file'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        # Django request/response logging
        'django.request': {
            'handlers': ['console', 'django_file', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Django server (runserver) logging
        'django.server': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django template system
        'django.template': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django security (CSRF, etc.)
        'django.security': {
            'handlers': ['console', 'security_file', 'error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Celery logger
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': CELERY_LOG_LEVEL,
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console', 'celery_file'],
            'level': CELERY_LOG_LEVEL,
            'propagate': False,
        },
        'celery.worker': {
            'handlers': ['console', 'celery_file'],
            'level': CELERY_LOG_LEVEL,
            'propagate': False,
        },
        # Application-specific loggers
        'users': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        'teams': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        'projects': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        'tasks': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        'notifications': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'application_file'],
            'level': APP_LOG_LEVEL,
            'propagate': False,
        },
        # Third-party loggers
        'PIL': {  # Pillow (image processing)
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {  # HTTP library
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ============================================================================
# Sentry Error Tracking Configuration
# ============================================================================
# Production-ready error tracking and performance monitoring using Sentry.
# Sentry provides real-time error tracking, performance monitoring, release tracking,
# and user context for debugging production issues.
#
# Features:
# - Automatic error capture from Django views, Celery tasks, and background jobs
# - User context (user ID, username, email) attached to errors
# - Request context (URL, method, headers, IP address) attached to errors
# - Performance monitoring (transaction tracking, slow queries)
# - Release tracking (version, deployment tracking)
# - Environment-based configuration (development vs production)
#
# Setup:
# 1. Sign up for a free account at https://sentry.io
# 2. Create a new project and get your DSN (Data Source Name)
# 3. Set SENTRY_DSN environment variable with your DSN
# 4. Optionally configure other Sentry settings via environment variables
#
# Documentation: https://docs.sentry.io/platforms/python/guides/django/

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# Sentry DSN (Data Source Name) - Get this from your Sentry project settings
# Format: https://<key>@<organization>.ingest.sentry.io/<project-id>
# If not set, Sentry will be disabled (useful for local development)
SENTRY_DSN = env('SENTRY_DSN', default='')

# Sentry environment (development, staging, production)
SENTRY_ENVIRONMENT = env('SENTRY_ENVIRONMENT', default='development' if DEBUG else 'production')

# Sentry release version (optional, useful for tracking deployments)
# Can be set to git commit hash, version number, or deployment identifier
SENTRY_RELEASE = env('SENTRY_RELEASE', default=None)

# Sentry sample rate for performance monitoring (0.0 to 1.0)
# 1.0 = 100% of transactions are sampled (can be expensive)
# 0.1 = 10% of transactions are sampled (recommended for production)
SENTRY_TRACES_SAMPLE_RATE = env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1 if not DEBUG else 1.0)

# Sentry sample rate for profiling (0.0 to 1.0)
# Profiling provides detailed performance data but is resource-intensive
# Only enable in production if needed for performance debugging
SENTRY_PROFILES_SAMPLE_RATE = env.float('SENTRY_PROFILES_SAMPLE_RATE', default=0.0)

# Enable Sentry (useful for disabling in local development)
# Set to 'false' to disable Sentry even if DSN is provided
SENTRY_ENABLED = env.bool('SENTRY_ENABLED', default=bool(SENTRY_DSN))

# Initialize Sentry SDK if DSN is provided and enabled
if SENTRY_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
        
        # Performance monitoring
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        
        # Integrations
        integrations=[
            # Django integration - captures exceptions, request context, user context
            DjangoIntegration(
                transaction_style='url',  # Use URL as transaction name
                middleware_spans=True,  # Track middleware execution
                signals_spans=True,  # Track Django signals
                cache_spans=True,  # Track cache operations
            ),
            # Celery integration - captures task exceptions and context
            CeleryIntegration(
                monitor_beat_tasks=True,  # Monitor Celery Beat scheduled tasks
            ),
            # Logging integration - captures log messages as Sentry events
            LoggingIntegration(
                level=logging.INFO,  # Capture INFO and above
                event_level=logging.ERROR,  # Send ERROR and above as events
            ),
            # Redis integration - captures Redis operation errors
            RedisIntegration(),
        ],
        
        # User context
        # Automatically captures user information from Django's request.user
        send_default_pii=True,  # Send personally identifiable information (email, username)
        
        # Error filtering
        # Ignore common errors that don't need tracking
        ignore_errors=[
            # Django built-in exceptions
            'django.http.Http404',
            'django.http.Http403',
            'django.http.Http400',
            'django.core.exceptions.PermissionDenied',
            'django.core.exceptions.ValidationError',
            # DRF exceptions
            'rest_framework.exceptions.ValidationError',
            'rest_framework.exceptions.PermissionDenied',
            'rest_framework.exceptions.AuthenticationFailed',
            'rest_framework.exceptions.NotFound',
            'rest_framework.exceptions.Throttled',
        ],
        
        # Before send callback - filter or modify events before sending
        before_send=lambda event, hint: event,  # Can be customized to filter events
        
        # Debug mode (only enable in development)
        debug=DEBUG,
        
        # Additional options
        attach_stacktrace=True,  # Include stack traces in events
        max_breadcrumbs=50,  # Maximum number of breadcrumbs (user actions) to track
        max_value_length=250,  # Maximum length of string values in events
    )
    
    # Log Sentry initialization
    logger = logging.getLogger(__name__)
    logger.info(
        f'Sentry initialized successfully',
        extra={
            'environment': SENTRY_ENVIRONMENT,
            'release': SENTRY_RELEASE,
            'traces_sample_rate': SENTRY_TRACES_SAMPLE_RATE,
        }
    )
elif SENTRY_DSN and not SENTRY_ENABLED:
    logger = logging.getLogger(__name__)
    logger.info('Sentry DSN provided but Sentry is disabled via SENTRY_ENABLED=false')
else:
    logger = logging.getLogger(__name__)
    logger.info('Sentry not configured (SENTRY_DSN not set)')
