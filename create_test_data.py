#!/usr/bin/env python
"""
Script to create test data for testing data processing tasks.

This script creates:
- 3 test users
- 1 team with members
- 1 project with members
- 6 tasks with different statuses and priorities

Usage:
    docker-compose exec web python create_test_data.py
"""

import os
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings')
django.setup()

from django.db.models import Count
from users.models import User
from teams.models import Team, TeamMember
from projects.models import Project, ProjectMember
from tasks.models import Task


def create_test_data():
    """Create comprehensive test data for testing."""
    
    print("=" * 70)
    print("Creating Test Data for Data Processing Tasks")
    print("=" * 70)
    
    # Create users
    print("\n1. Creating users...")
    users = []
    for i in range(1, 4):
        username = f'testuser{i}'
        email = f'test{i}@example.com'
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            print(f"   User '{username}' already exists, skipping...")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123',
                first_name='Test',
                last_name=f'User {i}',
                role='developer'
            )
            print(f"   ✅ Created user: {username}")
        
        users.append(user)
    
    # Create team
    print("\n2. Creating team...")
    team_name = 'Development Team'
    
    if Team.objects.filter(name=team_name).exists():
        team = Team.objects.get(name=team_name)
        print(f"   Team '{team_name}' already exists, using existing...")
    else:
        team = Team.objects.create(
            name=team_name,
            description='A test development team for testing analytics and reports'
        )
        print(f"   ✅ Created team: {team_name}")
    
    # Add team members
    print("\n3. Adding team members...")
    roles = [TeamMember.ROLE_OWNER, TeamMember.ROLE_ADMIN, TeamMember.ROLE_MEMBER]
    for user, role in zip(users, roles):
        if not TeamMember.objects.filter(team=team, user=user).exists():
            TeamMember.objects.create(team=team, user=user, role=role)
            print(f"   ✅ Added {user.username} as {role}")
        else:
            print(f"   {user.username} already a member")
    
    # Create project
    print("\n4. Creating project...")
    project_name = 'Test Project'
    
    if Project.objects.filter(team=team, name=project_name).exists():
        project = Project.objects.get(team=team, name=project_name)
        print(f"   Project '{project_name}' already exists, using existing...")
    else:
        project = Project.objects.create(
            name=project_name,
            description='A test project for analytics and reporting',
            team=team,
            status=Project.STATUS_ACTIVE,
            priority=Project.PRIORITY_HIGH,
            deadline=timezone.now() + timedelta(days=30)
        )
        print(f"   ✅ Created project: {project_name}")
    
    # Add project members
    print("\n5. Adding project members...")
    roles = [ProjectMember.ROLE_OWNER, ProjectMember.ROLE_ADMIN, ProjectMember.ROLE_MEMBER]
    for user, role in zip(users, roles):
        if not ProjectMember.objects.filter(project=project, user=user).exists():
            ProjectMember.objects.create(project=project, user=user, role=role)
            print(f"   ✅ Added {user.username} as {role}")
        else:
            print(f"   {user.username} already a project member")
    
    # Create tasks
    print("\n6. Creating tasks...")
    tasks_data = [
        {
            'title': 'Complete User Authentication',
            'status': Task.STATUS_DONE,
            'priority': Task.PRIORITY_HIGH,
            'assignee': users[0],
            'due_date': timezone.now() - timedelta(days=2)  # Past due (completed)
        },
        {
            'title': 'Implement API Endpoints',
            'status': Task.STATUS_IN_PROGRESS,
            'priority': Task.PRIORITY_HIGH,
            'assignee': users[1],
            'due_date': timezone.now() + timedelta(days=5)
        },
        {
            'title': 'Write Unit Tests',
            'status': Task.STATUS_TODO,
            'priority': Task.PRIORITY_MEDIUM,
            'assignee': users[2],
            'due_date': timezone.now() + timedelta(days=10)
        },
        {
            'title': 'Setup CI/CD Pipeline',
            'status': Task.STATUS_DONE,
            'priority': Task.PRIORITY_MEDIUM,
            'assignee': users[0],
            'due_date': timezone.now() - timedelta(days=1)  # Past due (completed)
        },
        {
            'title': 'Fix Database Migration Issue',
            'status': Task.STATUS_BLOCKED,
            'priority': Task.PRIORITY_HIGH,
            'assignee': users[1],
            'due_date': timezone.now() + timedelta(days=3)
        },
        {
            'title': 'Update Documentation',
            'status': Task.STATUS_TODO,
            'priority': Task.PRIORITY_LOW,
            'assignee': None,  # Unassigned
            'due_date': timezone.now() + timedelta(days=15)
        },
        {
            'title': 'Code Review',
            'status': Task.STATUS_IN_PROGRESS,
            'priority': Task.PRIORITY_MEDIUM,
            'assignee': users[2],
            'due_date': timezone.now() + timedelta(days=7)
        },
    ]
    
    created_count = 0
    for task_data in tasks_data:
        if not Task.objects.filter(project=project, title=task_data['title']).exists():
            Task.objects.create(
                title=task_data['title'],
                description=f"Description for {task_data['title']}",
                project=project,
                status=task_data['status'],
                priority=task_data['priority'],
                assignee=task_data.get('assignee'),
                created_by=users[0],
                due_date=task_data.get('due_date')
            )
            created_count += 1
            print(f"   ✅ Created task: {task_data['title']}")
        else:
            print(f"   Task '{task_data['title']}' already exists")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Data Summary")
    print("=" * 70)
    print(f"✅ Users: {User.objects.count()}")
    print(f"✅ Teams: {Team.objects.count()}")
    print(f"✅ Projects: {Project.objects.count()}")
    print(f"✅ Tasks: {Task.objects.filter(project=project).count()}")
    print(f"\n📊 Project Statistics:")
    print(f"   Project: {project.name} (ID: {project.id})")
    print(f"   Team: {team.name} (ID: {team.id})")
    print(f"   Tasks by Status:")
    for status, count in Task.objects.filter(project=project).values('status').annotate(
        count=Count('id')
    ).values_list('status', 'count'):
        print(f"      - {status}: {count}")
    
    print("\n" + "=" * 70)
    print("✅ Test data created successfully!")
    print("=" * 70)
    print(f"\nYou can now test the tasks with:")
    print(f"  - Project ID: {project.id}")
    print(f"  - Team ID: {team.id}")
    print(f"  - Task IDs: {list(Task.objects.filter(project=project).values_list('id', flat=True))}")
    print("\nRun: docker-compose exec web python test_data_processing_tasks.py")


if __name__ == '__main__':
    create_test_data()

