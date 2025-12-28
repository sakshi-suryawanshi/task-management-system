# Task Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A production-ready, enterprise-grade task and project management system built with Django REST Framework**

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-system-architecture) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

The **Task Management System** is a comprehensive, production-ready backend application designed for managing teams, projects, and tasks efficiently. Built with modern Python and Django best practices, this system demonstrates enterprise-level architecture, scalability, and maintainability.

### Key Highlights

- 🏗️ **Production-Ready Architecture**: Microservices-ready design with Docker containerization
- 🔐 **Enterprise Security**: JWT authentication, role-based access control, and comprehensive security measures
- ⚡ **High Performance**: Redis caching, Celery background processing, and optimized database queries
- 📊 **Comprehensive API**: RESTful API with OpenAPI 3.0 documentation (Swagger/ReDoc)
- 🧪 **Well-Tested**: 80%+ test coverage with pytest
- 🔄 **CI/CD Pipeline**: Automated testing, linting, and Docker builds via GitHub Actions
- 📚 **Complete Documentation**: Extensive documentation for setup, deployment, and API usage
- 🐳 **Docker-First**: Fully containerized with Docker Compose for easy local development

### Use Cases

- **Team Collaboration**: Manage teams, assign projects, and track progress
- **Project Management**: Organize projects with deadlines, priorities, and status tracking
- **Task Tracking**: Create, assign, and monitor tasks with dependencies and comments
- **Notifications**: Real-time in-app and email notifications for important events
- **Analytics**: Project statistics and team performance metrics

---

## 🎯 Features

### 🔐 Authentication & Authorization

- **JWT Authentication**: Secure token-based authentication with refresh token support
- **User Registration & Login**: Complete user management with email validation
- **Profile Management**: User profiles with avatar, bio, and role management
- **Role-Based Access Control (RBAC)**: Fine-grained permissions for teams, projects, and tasks
- **Token Blacklisting**: Secure logout with token invalidation

### 👥 Team Management

- **Team Creation**: Create teams with descriptions and metadata
- **Member Management**: Add/remove team members with role assignment (Owner, Admin, Member)
- **Team Roles**: Hierarchical permission system (Owner → Admin → Member)
- **Team Analytics**: Track team performance and member contributions

### 📁 Project Management

- **Project Lifecycle**: Full project management with status tracking (Planning, Active, On Hold, Completed, Cancelled)
- **Priority Management**: Set project priorities (High, Medium, Low)
- **Deadline Tracking**: Project deadlines with automated reminders
- **Project Members**: Assign team members to projects with specific roles
- **Project Statistics**: Comprehensive analytics including task completion rates, member activity, and timeline tracking

### ✅ Task Management

- **Task Creation**: Create tasks with detailed descriptions, priorities, and due dates
- **Task Assignment**: Assign tasks to team members with notification support
- **Status Tracking**: Track task status (To Do, In Progress, Done, Blocked)
- **Task Dependencies**: Define task dependencies to manage workflow
- **Task Comments**: Collaborative commenting system for task discussions
- **File Attachments**: Upload and manage task-related files
- **Task Filtering**: Advanced filtering by status, priority, assignee, and project

### 🔔 Notification System

- **In-App Notifications**: Real-time notifications for task assignments, updates, and comments
- **Email Notifications**: Automated email notifications for important events
- **Notification Types**: Task assignments, due date reminders, project updates, team invitations
- **Notification Preferences**: Mark as read/unread, bulk operations
- **Notification History**: Complete audit trail of all notifications

### ⚙️ Background Processing

- **Celery Integration**: Asynchronous task processing for long-running operations
- **Email Tasks**: Automated email sending for notifications and reminders
- **Scheduled Tasks**: Daily reminders, weekly digests, and automated cleanup
- **Data Processing**: Background analytics generation and report processing
- **Task Monitoring**: Flower dashboard for monitoring Celery tasks

### 🌐 RESTful API

- **Complete REST API**: Full CRUD operations for all resources
- **OpenAPI 3.0 Documentation**: Interactive Swagger UI and ReDoc documentation
- **Request/Response Examples**: Comprehensive examples for all endpoints
- **Pagination**: Efficient pagination for large datasets
- **Filtering & Search**: Advanced filtering and search capabilities
- **Error Handling**: Comprehensive error responses with detailed messages

### 🐳 DevOps & Infrastructure

- **Docker Compose**: Multi-container orchestration for all services
- **Production Server**: Gunicorn WSGI server with optimized configuration
- **Reverse Proxy**: Nginx for static file serving and API proxying
- **CI/CD Pipeline**: GitHub Actions for automated testing and builds
- **Health Checks**: Application, database, and Redis health monitoring
- **Logging**: Structured logging with rotation and multiple log levels

### 🧪 Testing & Quality

- **Comprehensive Testing**: Unit tests, integration tests, and API tests
- **Test Coverage**: 80%+ code coverage with pytest
- **Code Quality**: Black formatting, flake8 linting, and type checking
- **Pre-commit Hooks**: Automated code quality checks
- **Test Factories**: Factory pattern for easy test data generation

### 📊 Monitoring & Observability

- **Flower Dashboard**: Real-time Celery task monitoring and management
- **Health Endpoints**: Application, database, and Redis health checks
- **Structured Logging**: Comprehensive logging with different log levels
- **Error Tracking**: Integration-ready for Sentry or similar services
- **Activity Logging**: Complete audit trail of user activities

---

## 🛠️ Tech Stack

### Backend Framework
- **Django 5.2**: High-level Python web framework
- **Django REST Framework 3.15**: Powerful toolkit for building Web APIs
- **Python 3.11+**: Modern Python with type hints and async support

### Database & Caching
- **MySQL 8.0**: Robust relational database with ACID compliance
- **Redis 7.0**: In-memory data structure store for caching and message brokering

### Task Queue & Scheduling
- **Celery 5.4**: Distributed task queue for asynchronous processing
- **Celery Beat**: Periodic task scheduler
- **Flower**: Real-time web-based monitoring tool for Celery

### Web Server & Production
- **Gunicorn 23.0**: Python WSGI HTTP Server for production
- **Nginx**: High-performance web server and reverse proxy

### Containerization & Orchestration
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container Docker application management

### Development & Testing
- **pytest**: Testing framework with fixtures and plugins
- **pytest-django**: Django plugin for pytest
- **pytest-cov**: Coverage plugin for pytest
- **Black**: Uncompromising code formatter
- **flake8**: Linting tool for Python
- **mypy**: Static type checker (optional)

### CI/CD & DevOps
- **GitHub Actions**: Continuous integration and deployment
- **Docker Hub**: Container registry (optional)

### Documentation
- **drf-spectacular**: OpenAPI 3.0 schema generation for Django REST Framework
- **Swagger UI**: Interactive API documentation
- **ReDoc**: Beautiful API documentation

---

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Git** for version control
- **Python 3.11+** (for local development without Docker)

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/task-management-system.git
cd task-management-system
```

#### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# At minimum, set SECRET_KEY for Django
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DEBUG`: Set to `False` for production
- Database credentials (MySQL)
- Redis configuration
- Email settings (for notifications)

See [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for complete configuration guide.

#### 3. Build and Start Services

```bash
# Build all Docker containers
docker-compose build

# Start all services in detached mode
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

#### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create a superuser (admin account)
docker-compose exec web python manage.py createsuperuser
```

#### 5. Access the Application

Once all services are running, access the application at:

| Service | URL | Description |
|---------|-----|-------------|
| **API Documentation (Swagger)** | http://localhost:8000/api/docs/ | Interactive API explorer |
| **API Documentation (ReDoc)** | http://localhost:8000/api/redoc/ | Clean, readable docs |
| **Django Admin** | http://localhost:8000/admin/ | Admin interface |
| **API Base** | http://localhost:8000/api/ | REST API endpoints |
| **Flower (Celery)** | http://localhost:5555 | Task monitoring |
| **Nginx** | http://localhost/ | Web server (proxies to API) |
| **Health Check** | http://localhost:8000/health/ | Application health |

### Quick Verification

```bash
# Check all services are running
docker-compose ps

# Test API health endpoint
curl http://localhost:8000/health/

# Test database connection
docker-compose exec web python manage.py dbshell
```

### Next Steps

- 📖 Read the [Quick Start Guide](QUICK_START.md) for detailed setup
- 📚 Explore [Setup Documentation](docs/SETUP.md) for advanced configuration
- 🔌 Check [API Documentation](docs/API_DOCUMENTATION_GUIDE.md) for API usage
- 🏗️ Review [Architecture Documentation](ARCHITECTURE.md) for system design

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Network                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐     │
│  │    Nginx     │────────▶│   Django     │────────▶│    MySQL     │     │
│  │  (Port 80)   │  Proxy  │  (Gunicorn)  │   ORM   │  (Port 3306) │     │
│  │              │         │  (Port 8000) │         │              │     │
│  └──────────────┘         └──────┬───────┘         └──────────────┘     │
│         │                         │                                     │
│    Static Files              ┌─────▼─────┐                              │
│    (CSS/JS/Images)           │   Redis   │                              │
│                              │ (Port     │                              │
│                              │  6379)    │                              │
│                              └─────┬─────┘                              │
│                                    │                                    │
│                              ┌─────▼─────┐                              │
│                              │  Celery   │                              │
│                              │  Worker   │                              │
│                              └───────────┘                              │
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐                              │
│  │ Celery Beat  │         │   Flower     │                              │
│  │ (Scheduler)  │         │ (Monitoring) │                              │
│  │              │         │ (Port 5555)  │                              │
│  └──────────────┘         └──────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

#### 1. API Request Flow
```
Client Request
    │
    ▼
┌─────────┐
│  Nginx  │  ← Static files served directly
└────┬────┘
     │ API requests
     ▼
┌─────────┐
│Gunicorn │  ← WSGI server
└────┬────┘
     │
     ▼
┌─────────┐
│ Django  │  ← Request processing
└────┬────┘
     │
     ├───▶ MySQL (Database queries)
     │
     └───▶ Redis (Caching, sessions)
```

#### 2. Background Task Flow
```
Django View/Model Signal
    │
    ▼
┌─────────┐
│ Celery  │  ← Task queued
│  Task   │
└────┬────┘
     │
     ▼
┌─────────┐
│  Redis  │  ← Message broker
│  Queue  │
└────┬────┘
     │
     ▼
┌─────────┐
│ Celery  │  ← Task execution
│ Worker  │
└────┬────┘
     │
     ├───▶ Send Email
     ├───▶ Process Data
     └───▶ Generate Reports
```

### Component Architecture

#### Database Schema
```
User
├── Profile (avatar, bio, role)
├── Teams (Many-to-Many via TeamMember)
├── Projects (Many-to-Many via ProjectMember)
└── Tasks (assigned_tasks, created_tasks)

Team
├── Members (Many-to-Many via TeamMember with roles)
└── Projects (One-to-Many)

Project
├── Team (ForeignKey)
├── Members (Many-to-Many via ProjectMember with roles)
└── Tasks (One-to-Many)

Task
├── Project (ForeignKey)
├── Assignee (ForeignKey to User)
├── Created By (ForeignKey to User)
├── Dependencies (Many-to-Many with Task)
├── Comments (One-to-Many)
└── Attachments (One-to-Many)

Notification
└── User (ForeignKey)

ActivityLog
├── User (ForeignKey)
└── Generic Foreign Key (any model)
```

### Technology Stack Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  (Nginx, Static Files, API Gateway)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Application Layer               │
│  (Django, DRF, Gunicorn, Views)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Business Logic Layer            │
│  (Models, Serializers, Permissions)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer                      │
│  (MySQL, Redis, File Storage)           │
└─────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Background Processing           │
│  (Celery, Celery Beat, Workers)         │
└─────────────────────────────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---
### API Documentation (Swagger UI)
*Screenshot placeholder for Swagger UI interface*

The interactive Swagger UI provides a comprehensive API explorer where you can:
- Browse all available endpoints
- View request/response schemas
- Test endpoints directly from the browser
- Authenticate using JWT tokens

Access at: http://localhost:8000/api/docs/

### API Documentation (ReDoc)
*Screenshot placeholder for ReDoc interface*

ReDoc provides a clean, readable documentation interface with:
- Organized endpoint groups
- Request/response examples
- Authentication instructions
- Error response documentation

Access at: http://localhost:8000/api/redoc/

### Flower Dashboard (Celery Monitoring)
*Screenshot placeholder for Flower dashboard*

Monitor Celery tasks in real-time with:
- Task execution status
- Worker status and statistics
- Task history and logs
- Performance metrics

Access at: http://localhost:5555

### Django Admin Interface
*Screenshot placeholder for Django Admin*

Manage all system data through Django's admin interface:
- User management
- Team and project administration
- Task oversight
- Notification management

Access at: http://localhost:8000/admin/

---

## 🔌 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication

All API endpoints (except registration and login) require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_access_token>
```

### Endpoint Categories

#### 🔐 Authentication Endpoints
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login (returns JWT tokens)
- `POST /api/token/refresh/` - Refresh access token
- `POST /api/token/verify/` - Verify token validity
- `POST /api/token/blacklist/` - Blacklist refresh token (logout)

#### 👥 User Endpoints
- `GET /api/auth/profile/` - Get current user profile
- `PUT /api/auth/profile/` - Update profile (full)
- `PATCH /api/auth/profile/` - Update profile (partial)

#### 🏢 Team Endpoints
- `GET /api/teams/` - List teams (with pagination and filtering)
- `POST /api/teams/` - Create new team
- `GET /api/teams/{id}/` - Get team details
- `PUT /api/teams/{id}/` - Update team (full)
- `PATCH /api/teams/{id}/` - Update team (partial)
- `DELETE /api/teams/{id}/` - Delete team
- `POST /api/teams/{team_id}/members/` - Add team member
- `PATCH /api/teams/{team_id}/members/{user_id}/` - Update member role
- `DELETE /api/teams/{team_id}/members/{user_id}/` - Remove member

#### 📁 Project Endpoints
- `GET /api/projects/` - List projects (with filtering)
- `POST /api/projects/` - Create new project
- `GET /api/projects/{id}/` - Get project details
- `PUT /api/projects/{id}/` - Update project (full)
- `PATCH /api/projects/{id}/` - Update project (partial)
- `DELETE /api/projects/{id}/` - Delete project
- `GET /api/projects/{project_id}/stats/` - Get project statistics
- `POST /api/projects/{project_id}/members/` - Add project member
- `PATCH /api/projects/{project_id}/members/{user_id}/` - Update member role
- `DELETE /api/projects/{project_id}/members/{user_id}/` - Remove member

#### ✅ Task Endpoints
- `GET /api/tasks/` - List tasks (with advanced filtering)
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}/` - Get task details
- `PUT /api/tasks/{id}/` - Update task (full)
- `PATCH /api/tasks/{id}/` - Update task (partial)
- `DELETE /api/tasks/{id}/` - Delete task
- `POST /api/tasks/{task_id}/assign/` - Assign/unassign task
- `PATCH /api/tasks/{task_id}/status/` - Update task status
- `GET /api/tasks/{task_id}/comments/` - List task comments
- `POST /api/tasks/{task_id}/comments/` - Create comment
- `GET /api/tasks/{task_id}/comments/{id}/` - Get comment details
- `PUT /api/tasks/{task_id}/comments/{id}/` - Update comment (full)
- `PATCH /api/tasks/{task_id}/comments/{id}/` - Update comment (partial)
- `DELETE /api/tasks/{task_id}/comments/{id}/` - Delete comment

#### 🔔 Notification Endpoints
- `GET /api/notifications/` - List notifications (with filtering)
- `GET /api/notifications/{id}/` - Get notification details
- `PATCH /api/notifications/{id}/mark-read/` - Mark notification as read
- `POST /api/notifications/mark-all-read/` - Mark all as read
- `GET /api/notifications/count/` - Get unread notification count

#### 🏥 Health Check Endpoints
- `GET /health/` - Overall application health
- `GET /health/db/` - Database health check
- `GET /health/redis/` - Redis health check

### Interactive Documentation

**Swagger UI**: http://localhost:8000/api/docs/
- Interactive API explorer
- "Try it out" functionality
- JWT authentication support
- Request/response examples

**ReDoc**: http://localhost:8000/api/redoc/
- Clean, readable documentation
- Organized by tags
- Complete schema documentation

**OpenAPI Schema**: http://localhost:8000/api/schema/
- Raw OpenAPI 3.0 JSON/YAML
- Import into Postman, Insomnia, etc.

### Example API Usage

#### Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123",
    "password2": "securepassword123"
  }'
```

#### Login and Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

#### Create a Team (Authenticated)
```bash
curl -X POST http://localhost:8000/api/teams/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_access_token>" \
  -d '{
    "name": "Development Team",
    "description": "Our awesome development team"
  }'
```


---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage report
docker-compose exec web pytest --cov

# Run with verbose output
docker-compose exec web pytest -v

# Run specific test file
docker-compose exec web pytest users/tests.py

# Run specific test class
docker-compose exec web pytest users/tests.py::TestUserRegistration

# Run specific test method
docker-compose exec web pytest users/tests.py::TestUserRegistration::test_registration_success

# Run tests matching a pattern
docker-compose exec web pytest -k "test_registration"

# Run with coverage and generate HTML report
docker-compose exec web pytest --cov --cov-report=html
```

### Test Coverage

The project maintains **80%+ test coverage**. View coverage reports:

```bash
# Generate coverage report
docker-compose exec web pytest --cov --cov-report=html

# Coverage report will be available at
# htmlcov/index.html (open in browser)
```

### Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── users/
│   └── tests.py         # User model and API tests
├── teams/
│   └── tests.py         # Team model and API tests
├── projects/
│   └── tests.py         # Project model and API tests
├── tasks/
│   └── tests.py         # Task model and API tests
└── notifications/
    └── tests.py         # Notification tests
```

### Writing Tests

Tests follow pytest conventions and use factories for test data:

```python
import pytest
from django.contrib.auth import get_user_model
from factories import UserFactory, TeamFactory

User = get_user_model()

@pytest.mark.django_db
def test_create_team(client, user):
    """Test creating a team via API"""
    client.force_authenticate(user=user)
    response = client.post('/api/teams/', {
        'name': 'Test Team',
        'description': 'Test Description'
    })
    assert response.status_code == 201
    assert response.data['name'] == 'Test Team'
```


### Daily Development Commands

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f web

# Run migrations (after model changes)
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access Django shell
docker-compose exec web python manage.py shell

# Run tests
docker-compose exec web pytest

# Format code
docker-compose exec web black .

# Lint code
docker-compose exec web flake8 .

# Stop services
docker-compose down
```

### Code Quality Standards

- **Formatting**: Use Black for consistent code formatting
- **Linting**: Follow flake8 guidelines (see `setup.cfg`)
- **Type Hints**: Use type hints where applicable
- **Docstrings**: Document all functions and classes
- **Tests**: Write tests for all new features

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add: descriptive commit message"

# Push to remote
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Pre-commit Hooks

The project includes pre-commit hooks for code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```


---

## 🐳 Docker Commands

### Basic Commands

```bash
# Build all containers
docker-compose build

# Build specific service
docker-compose build web

# Start all services
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart a service
docker-compose restart web

# View logs
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f nginx

# View logs for all services
docker-compose logs -f
```

### Service-Specific Commands

```bash
# Django commands
docker-compose exec web python manage.py <command>

# Access Django shell
docker-compose exec web python manage.py shell

# Access Django shell (with IPython)
docker-compose exec web python manage.py shell_plus

# Run tests
docker-compose exec web pytest

# Database shell
docker-compose exec web python manage.py dbshell

# Redis CLI
docker-compose exec redis redis-cli

# MySQL CLI
docker-compose exec db mysql -u root -p
```

### Development Commands

```bash
# Rebuild after dependency changes
docker-compose build --no-cache web

# View service status
docker-compose ps

# View resource usage
docker stats

# Execute command in running container
docker-compose exec web bash

# Copy file from container
docker-compose cp web:/app/file.txt ./

# Copy file to container
docker-compose cp ./file.txt web:/app/
```

---

## 📊 Monitoring

### Application Monitoring

- **Health Checks**: http://localhost:8000/health/
  - Overall application health
  - Database connectivity
  - Redis connectivity

- **Flower Dashboard**: http://localhost:5555
  - Real-time Celery task monitoring
  - Worker status and statistics
  - Task execution history
  - Performance metrics

### Logging

Structured logging is configured with multiple log levels:

```bash
# View application logs
docker-compose logs -f web

# View Celery logs
docker-compose logs -f celery

# View Nginx logs
docker-compose logs -f nginx

# View all logs
docker-compose logs -f
```

Log files are also available in the `logs/` directory:
- `logs/django.log` - Django application logs

### Performance Monitoring

- **Database Queries**: Use Django Debug Toolbar (development)
- **API Performance**: Monitor response times via logs
- **Celery Tasks**: Monitor via Flower dashboard
- **Resource Usage**: Use `docker stats` for container metrics

---

## 🔒 Security

### Authentication & Authorization

- **JWT Authentication**: Secure token-based authentication
- **Token Refresh**: Automatic token refresh mechanism
- **Token Blacklisting**: Secure logout with token invalidation
- **Password Security**: Django's PBKDF2 password hashing
- **Role-Based Access Control**: Fine-grained permissions

### Security Features

- **CORS Configuration**: Configured for allowed origins
- **CSRF Protection**: Enabled for state-changing operations
- **XSS Protection**: Django's built-in XSS protection
- **SQL Injection Protection**: Django ORM prevents SQL injection
- **Secure Headers**: Security headers via Nginx
- **Input Validation**: Comprehensive input validation and sanitization

### Security Best Practices

- Never commit `.env` files or secrets
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Use HTTPS in production (configure SSL/TLS)
- Regularly update dependencies
- Review and audit permissions regularly


---


---

## 🏗️ Project Structure

```
task-management-system/
├── taskmanager/              # Django project configuration
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI configuration
│   ├── asgi.py               # ASGI configuration
│   └── celery.py             # Celery configuration
│
├── users/                     # User management app
│   ├── models.py             # User and UserProfile models
│   ├── views.py              # User views and API endpoints
│   ├── serializers.py        # User serializers
│   ├── urls.py               # User URL routes
│   ├── admin.py              # Admin configuration
│   └── tests.py              # User tests
│
├── teams/                     # Team management app
│   ├── models.py             # Team and TeamMember models
│   ├── views.py              # Team views and API endpoints
│   ├── serializers.py        # Team serializers
│   ├── urls.py               # Team URL routes
│   ├── admin.py              # Admin configuration
│   └── tests.py              # Team tests
│
├── projects/                  # Project management app
│   ├── models.py             # Project and ProjectMember models
│   ├── views.py              # Project views and API endpoints
│   ├── serializers.py        # Project serializers
│   ├── urls.py               # Project URL routes
│   ├── admin.py              # Admin configuration
│   ├── tasks.py              # Celery tasks for projects
│   └── tests.py              # Project tests
│
├── tasks/                     # Task management app
│   ├── models.py             # Task, TaskComment, TaskAttachment models
│   ├── views.py              # Task views and API endpoints
│   ├── serializers.py        # Task serializers
│   ├── urls.py               # Task URL routes
│   ├── admin.py              # Admin configuration
│   ├── signals.py            # Task signals
│   └── tests.py              # Task tests
│
├── notifications/             # Notification system app
│   ├── models.py             # Notification model
│   ├── views.py              # Notification views and API endpoints
│   ├── serializers.py        # Notification serializers
│   ├── urls.py               # Notification URL routes
│   ├── admin.py              # Admin configuration
│   ├── tasks.py              # Celery tasks for notifications
│   ├── templates/            # Email templates
│   └── tests.py              # Notification tests
│
├── core/                      # Core utilities and shared code
│   ├── models.py             # ActivityLog and other core models
│   ├── views.py              # Health check and utility views
│   ├── permissions.py        # Custom permission classes
│   ├── jwt_views.py          # Custom JWT views
│   ├── logging_utils.py      # Logging utilities
│   ├── admin.py              # Core admin configuration
│   └── tests.py              # Core tests
│
├── nginx/                     # Nginx configuration
│   └── nginx.conf             # Nginx server configuration
│
├── .github/                    # GitHub configuration
│   └── workflows/            # GitHub Actions CI/CD
│       └── ci.yml            # CI/CD pipeline
│
├── docs/                       # Documentation
│   ├── SETUP.md              # Setup guide
│   ├── DEPLOYMENT.md         # Deployment guide
│   ├── ENVIRONMENT_VARIABLES.md  # Environment variables
│   ├── API_DOCUMENTATION_GUIDE.md # API docs guide
│   ├── SWAGGER_QUICK_START.md    # Swagger guide
│   └── CI_CD_GUIDE.md        # CI/CD guide
│
├── logs/                       # Application logs
│   └── django.log             # Django application logs
│
├── media/                      # User-uploaded files
├── staticfiles/                # Collected static files
│
├── Dockerfile                  # Docker image configuration
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pytest.ini                  # Pytest configuration
├── pyproject.toml              # Black, isort, mypy configuration
├── setup.cfg                   # flake8 configuration
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .env.example                # Environment variables template
├── gunicorn_config.py          # Gunicorn configuration
├── conftest.py                 # Pytest fixtures
├── factories.py                # Test data factories
│
├── README.md                   # This file
├── ARCHITECTURE.md             # Architecture documentation
├── TASK_LIST.md                # Development task list
├── QUICK_START.md              # Quick start guide
└── IMPLEMENTATION_GUIDE.md     # Implementation guide
```

---

## 👤 Author

**Your Name**

- GitHub: [@sakshi-suryawanshi](https://github.com/sakshi-suryawanshi)


### About This Project

This project was built as a comprehensive portfolio piece to demonstrate:
- **Backend Development**: Django REST Framework, API design, database modeling
- **DevOps Skills**: Docker, CI/CD, containerization, infrastructure
- **Best Practices**: Testing, code quality, documentation, security
- **System Design**: Scalable architecture, microservices-ready design
- **Production Readiness**: Monitoring, logging, error handling, performance optimization

---

## 🙏 Acknowledgments

### Technologies & Frameworks

- **[Django](https://www.djangoproject.com/)** - The web framework for perfectionists with deadlines
- **[Django REST Framework](https://www.django-rest-framework.org/)** - Powerful toolkit for building Web APIs
- **[Celery](https://docs.celeryproject.org/)** - Distributed task queue
- **[Docker](https://www.docker.com/)** - Containerization platform
- **[Redis](https://redis.io/)** - In-memory data structure store

### Communities

- **Django Community** - For excellent documentation and support
- **Docker Community** - For containerization best practices
- **Open Source Contributors** - For inspiration and learning resources

### Learning Resources

- Django Documentation
- DRF Documentation
- Docker Documentation
- Various tutorials and blog posts from the community

---
