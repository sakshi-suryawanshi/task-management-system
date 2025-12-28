"""
Factory classes for generating test data using Factory Boy.

This module provides factory classes for creating test instances of all models
in the Task Management System. Factories make it easy to generate test data
with realistic values using Faker.

Usage:
    from factories import UserFactory, TeamFactory
    
    # Create a user with default values
    user = UserFactory()
    
    # Create a user with custom values
    user = UserFactory(username='john', email='john@example.com')
    
    # Create multiple users
    users = UserFactory.create_batch(5)

Documentation:
    - Factory Boy: https://factoryboy.readthedocs.io/
    - Faker: https://faker.readthedocs.io/
"""

import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
from faker import Faker

from users.models import User, UserProfile
from teams.models import Team, TeamMember
from projects.models import Project, ProjectMember
from tasks.models import Task, TaskComment, TaskDependency
from notifications.models import Notification

fake = Faker()


class UserFactory(DjangoModelFactory):
    """
    Factory for creating User instances.
    
    Generates users with realistic test data including usernames, emails,
    names, and roles.
    """
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    role = fuzzy.FuzzyChoice(['admin', 'manager', 'developer', 'member'])
    phone = factory.Faker('phone_number')
    bio = factory.Faker('text', max_nb_chars=200)
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after user creation."""
        if not create:
            return
        
        password = extracted if extracted else 'testpass123'
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    role = 'admin'
    is_staff = True
    is_superuser = True


class ManagerUserFactory(UserFactory):
    """Factory for creating manager users."""
    role = 'manager'


class DeveloperUserFactory(UserFactory):
    """Factory for creating developer users."""
    role = 'developer'


class MemberUserFactory(UserFactory):
    """Factory for creating regular member users."""
    role = 'member'


class UserProfileFactory(DjangoModelFactory):
    """
    Factory for creating UserProfile instances.
    
    Creates extended profile information for users.
    """
    
    class Meta:
        model = UserProfile
        django_get_or_create = ('user',)
    
    user = factory.SubFactory(UserFactory)
    job_title = factory.Faker('job')
    department = factory.Faker('company')
    location = fuzzy.FuzzyChoice(['remote', 'office', 'hybrid'])
    address = factory.Faker('address')
    city = factory.Faker('city')
    country = factory.Faker('country')
    website = factory.Faker('url')
    linkedin = factory.LazyAttribute(lambda obj: f'https://linkedin.com/in/{obj.user.username}')
    github = factory.LazyAttribute(lambda obj: f'https://github.com/{obj.user.username}')
    twitter = factory.LazyAttribute(lambda obj: f'https://twitter.com/{obj.user.username}')
    timezone = 'UTC'
    language = 'en'
    email_notifications = True
    push_notifications = True


class TeamFactory(DjangoModelFactory):
    """
    Factory for creating Team instances.
    
    Generates teams with realistic names and descriptions.
    """
    
    class Meta:
        model = Team
        django_get_or_create = ('name',)
    
    name = factory.Sequence(lambda n: f'Team {n}')
    description = factory.Faker('text', max_nb_chars=300)


class TeamMemberFactory(DjangoModelFactory):
    """
    Factory for creating TeamMember instances.
    
    Creates team memberships with different roles.
    """
    
    class Meta:
        model = TeamMember
        django_get_or_create = ('team', 'user')
    
    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    role = fuzzy.FuzzyChoice(['owner', 'admin', 'member'])


class ProjectFactory(DjangoModelFactory):
    """
    Factory for creating Project instances.
    
    Generates projects with realistic names, descriptions, and statuses.
    """
    
    class Meta:
        model = Project
        django_get_or_create = ('team', 'name')
    
    name = factory.Sequence(lambda n: f'Project {n}')
    description = factory.Faker('text', max_nb_chars=500)
    status = fuzzy.FuzzyChoice(['planning', 'active', 'on_hold', 'completed', 'cancelled'])
    priority = fuzzy.FuzzyChoice(['high', 'medium', 'low'])
    deadline = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=fake.random_int(min=1, max=90))
    )
    team = factory.SubFactory(TeamFactory)


class ActiveProjectFactory(ProjectFactory):
    """Factory for creating active projects."""
    status = 'active'


class CompletedProjectFactory(ProjectFactory):
    """Factory for creating completed projects."""
    status = 'completed'


class ProjectMemberFactory(DjangoModelFactory):
    """
    Factory for creating ProjectMember instances.
    
    Creates project memberships with different roles.
    """
    
    class Meta:
        model = ProjectMember
        django_get_or_create = ('project', 'user')
    
    project = factory.SubFactory(ProjectFactory)
    user = factory.SubFactory(UserFactory)
    role = fuzzy.FuzzyChoice(['owner', 'admin', 'member'])


class TaskFactory(DjangoModelFactory):
    """
    Factory for creating Task instances.
    
    Generates tasks with realistic titles, descriptions, and statuses.
    """
    
    class Meta:
        model = Task
        django_get_or_create = ('project', 'title')
    
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=500)
    status = fuzzy.FuzzyChoice(['todo', 'in_progress', 'done', 'blocked'])
    priority = fuzzy.FuzzyChoice(['high', 'medium', 'low'])
    due_date = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=fake.random_int(min=1, max=30))
    )
    project = factory.SubFactory(ProjectFactory)
    assignee = factory.SubFactory(UserFactory)
    created_by = factory.SubFactory(UserFactory)


class TodoTaskFactory(TaskFactory):
    """Factory for creating tasks in todo status."""
    status = 'todo'


class InProgressTaskFactory(TaskFactory):
    """Factory for creating tasks in progress."""
    status = 'in_progress'


class DoneTaskFactory(TaskFactory):
    """Factory for creating completed tasks."""
    status = 'done'


class BlockedTaskFactory(TaskFactory):
    """Factory for creating blocked tasks."""
    status = 'blocked'


class HighPriorityTaskFactory(TaskFactory):
    """Factory for creating high priority tasks."""
    priority = 'high'


class TaskCommentFactory(DjangoModelFactory):
    """
    Factory for creating TaskComment instances.
    
    Generates comments with realistic content.
    """
    
    class Meta:
        model = TaskComment
    
    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('text', max_nb_chars=300)


class TaskDependencyFactory(DjangoModelFactory):
    """
    Factory for creating TaskDependency instances.
    
    Creates task dependencies between tasks.
    Note: When using this factory, it's recommended to create prerequisite
    and dependent tasks explicitly to ensure they are different:
    
    Example:
        prerequisite = TaskFactory()
        dependent = TaskFactory(project=prerequisite.project)
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
    """
    
    class Meta:
        model = TaskDependency
    
    prerequisite_task = factory.SubFactory(TaskFactory)
    dependent_task = factory.SubFactory(TaskFactory)


class NotificationFactory(DjangoModelFactory):
    """
    Factory for creating Notification instances.
    
    Generates notifications with realistic messages and types.
    """
    
    class Meta:
        model = Notification
    
    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence', nb_words=10)
    type = fuzzy.FuzzyChoice([
        'task_assigned',
        'task_completed',
        'task_updated',
        'project_updated',
        'comment_added',
        'system',
    ])
    read = False


class UnreadNotificationFactory(NotificationFactory):
    """Factory for creating unread notifications."""
    read = False


class ReadNotificationFactory(NotificationFactory):
    """Factory for creating read notifications."""
    read = True
    read_at = factory.LazyFunction(timezone.now)

