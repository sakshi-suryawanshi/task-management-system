"""
Model tests for Task, TaskDependency, TaskComment, and TaskAttachment models.

This module contains comprehensive tests for all task-related models,
including field validation, model methods, relationships, and edge cases.
"""

import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import tempfile
import os

from tasks.models import Task, TaskDependency, TaskComment, TaskAttachment
from factories import (
    TaskFactory, TodoTaskFactory, InProgressTaskFactory, DoneTaskFactory,
    BlockedTaskFactory, HighPriorityTaskFactory, TaskCommentFactory,
    TaskDependencyFactory, ProjectFactory, ProjectMemberFactory, TeamFactory, UserFactory
)
from django.core.files.uploadedfile import SimpleUploadedFile


# ============================================================================
# Task Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTaskModel:
    """Test suite for Task model."""
    
    def test_task_creation(self):
        """Test basic task creation with required fields."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(
            title='Test Task',
            description='Task description',
            project=project,
            assignee=user,
            created_by=user
        )
        
        assert task.title == 'Test Task'
        assert task.description == 'Task description'
        assert task.project == project
        assert task.assignee == user
        assert task.created_by == user
        assert task.pk is not None
    
    def test_task_str_representation(self):
        """Test string representation of Task model."""
        team = TeamFactory()
        project = ProjectFactory(name='Test Project', team=team)
        user = UserFactory()
        task = TaskFactory(title='Test Task', project=project, created_by=user)
        assert 'Test Task' in str(task)
        assert 'Test Project' in str(task)
    
    def test_task_default_status(self):
        """Test that status defaults to 'todo'."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = Task(project=project, title='New Task', created_by=user)
        assert task.status == Task.STATUS_TODO
    
    def test_task_status_choices(self):
        """Test status field choices."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        statuses = ['todo', 'in_progress', 'done', 'blocked']
        
        for status in statuses:
            task = TaskFactory(project=project, status=status, created_by=user)
            assert task.status == status
            assert task.get_status_display() in [
                'To Do', 'In Progress', 'Done', 'Blocked'
            ]
    
    def test_task_default_priority(self):
        """Test that priority defaults to 'medium'."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = Task(project=project, title='New Task', created_by=user)
        assert task.priority == Task.PRIORITY_MEDIUM
    
    def test_task_priority_choices(self):
        """Test priority field choices."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        priorities = ['high', 'medium', 'low']
        
        for priority in priorities:
            task = TaskFactory(project=project, priority=priority, created_by=user)
            assert task.priority == priority
            assert task.get_priority_display() in ['High', 'Medium', 'Low']
    
    def test_task_can_have_null_assignee(self):
        """Test that assignee field can be null."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, assignee=None, created_by=user)
        assert task.assignee is None
        assert task.pk is not None
    
    def test_task_can_have_null_due_date(self):
        """Test that due_date field can be null."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, due_date=None, created_by=user)
        assert task.due_date is None
        assert task.pk is not None
    
    def test_task_can_have_due_date(self):
        """Test that due_date field can be set."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        due_date = timezone.now() + timedelta(days=7)
        task = TaskFactory(project=project, due_date=due_date, created_by=user)
        assert task.due_date == due_date
    
    def test_task_can_have_empty_description(self):
        """Test that description field can be empty."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, description='', created_by=user)
        assert task.description == ''
        assert task.pk is not None
    
    def test_task_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        after = timezone.now()
        
        assert task.created_at is not None
        assert before <= task.created_at <= after
    
    def test_task_updated_at_auto_set(self):
        """Test that updated_at is automatically set and updated."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        initial_updated_at = task.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        task.title = 'Updated Title'
        task.save()
        
        assert task.updated_at > initial_updated_at
    
    def test_task_ordering(self):
        """Test that tasks are ordered by created_at descending."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task1 = TaskFactory(project=project, created_by=user)
        task2 = TaskFactory(project=project, created_by=user)
        task3 = TaskFactory(project=project, created_by=user)
        
        tasks = list(Task.objects.filter(project=project)[:3])
        # Should be ordered by -created_at (newest first)
        assert tasks[0].created_at >= tasks[1].created_at
        assert tasks[1].created_at >= tasks[2].created_at
    
    def test_task_get_dependencies_empty(self):
        """Test get_dependencies method when task has no dependencies."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        dependencies = task.get_dependencies()
        assert dependencies.count() == 0
    
    def test_task_get_dependencies(self):
        """Test get_dependencies method returns prerequisite tasks."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        
        prerequisite1 = TaskFactory(project=project, created_by=user)
        prerequisite2 = TaskFactory(project=project, created_by=user)
        dependent_task = TaskFactory(project=project, created_by=user)
        
        TaskDependencyFactory(prerequisite_task=prerequisite1, dependent_task=dependent_task)
        TaskDependencyFactory(prerequisite_task=prerequisite2, dependent_task=dependent_task)
        
        dependencies = dependent_task.get_dependencies()
        assert dependencies.count() == 2
        assert prerequisite1 in dependencies
        assert prerequisite2 in dependencies
    
    def test_task_get_dependents(self):
        """Test get_dependents method returns tasks that depend on this task."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        
        prerequisite_task = TaskFactory(project=project, created_by=user)
        dependent1 = TaskFactory(project=project, created_by=user)
        dependent2 = TaskFactory(project=project, created_by=user)
        
        TaskDependencyFactory(prerequisite_task=prerequisite_task, dependent_task=dependent1)
        TaskDependencyFactory(prerequisite_task=prerequisite_task, dependent_task=dependent2)
        
        dependents = prerequisite_task.get_dependents()
        assert dependents.count() == 2
        assert dependent1 in dependents
        assert dependent2 in dependents
    
    def test_task_get_comments_empty(self):
        """Test get_comments method when task has no comments."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comments = task.get_comments()
        assert comments.count() == 0
    
    def test_task_get_comments(self):
        """Test get_comments method returns all task comments."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user1 = UserFactory()
        user2 = UserFactory()
        task = TaskFactory(project=project, created_by=user1)
        
        comment1 = TaskCommentFactory(task=task, author=user1)
        comment2 = TaskCommentFactory(task=task, author=user2)
        
        comments = task.get_comments()
        assert comments.count() == 2
        assert comment1 in comments
        assert comment2 in comments
    
    def test_task_get_comment_count(self):
        """Test get_comment_count method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        assert task.get_comment_count() == 0
        
        TaskCommentFactory(task=task, author=user)
        assert task.get_comment_count() == 1
        
        TaskCommentFactory(task=task, author=user)
        assert task.get_comment_count() == 2
    
    def test_task_get_attachments_empty(self):
        """Test get_attachments method when task has no attachments."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        attachments = task.get_attachments()
        assert attachments.count() == 0
    
    def test_task_get_attachment_count(self):
        """Test get_attachment_count method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        assert task.get_attachment_count() == 0
    
    def test_task_is_overdue_no_due_date(self):
        """Test is_overdue method when task has no due date."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, due_date=None, created_by=user)
        assert task.is_overdue() is False
    
    def test_task_is_overdue_future_due_date(self):
        """Test is_overdue method when due date is in the future."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        future_due_date = timezone.now() + timedelta(days=7)
        task = TaskFactory(project=project, due_date=future_due_date, status='todo', created_by=user)
        assert task.is_overdue() is False
    
    def test_task_is_overdue_past_due_date_todo(self):
        """Test is_overdue method when due date has passed and task is todo."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        past_due_date = timezone.now() - timedelta(days=7)
        task = TaskFactory(project=project, due_date=past_due_date, status='todo', created_by=user)
        assert task.is_overdue() is True
    
    def test_task_is_overdue_past_due_date_done(self):
        """Test is_overdue method when due date has passed but task is done."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        past_due_date = timezone.now() - timedelta(days=7)
        task = TaskFactory(project=project, due_date=past_due_date, status='done', created_by=user)
        assert task.is_overdue() is False
    
    def test_task_is_done(self):
        """Test is_done method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        done_task = DoneTaskFactory(project=project, created_by=user)
        todo_task = TodoTaskFactory(project=project, created_by=user)
        
        assert done_task.is_done() is True
        assert todo_task.is_done() is False
    
    def test_task_is_blocked(self):
        """Test is_blocked method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        blocked_task = BlockedTaskFactory(project=project, created_by=user)
        todo_task = TodoTaskFactory(project=project, created_by=user)
        
        assert blocked_task.is_blocked() is True
        assert todo_task.is_blocked() is False
    
    def test_task_is_in_progress(self):
        """Test is_in_progress method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        in_progress_task = InProgressTaskFactory(project=project, created_by=user)
        todo_task = TodoTaskFactory(project=project, created_by=user)
        
        assert in_progress_task.is_in_progress() is True
        assert todo_task.is_in_progress() is False
    
    def test_task_is_todo(self):
        """Test is_todo method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        todo_task = TodoTaskFactory(project=project, created_by=user)
        done_task = DoneTaskFactory(project=project, created_by=user)
        
        assert todo_task.is_todo() is True
        assert done_task.is_todo() is False
    
    def test_task_can_be_completed_no_dependencies(self):
        """Test can_be_completed method when task has no dependencies."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        assert task.can_be_completed() is True
    
    def test_task_can_be_completed_all_dependencies_done(self):
        """Test can_be_completed method when all dependencies are done."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        
        prerequisite1 = DoneTaskFactory(project=project, created_by=user)
        prerequisite2 = DoneTaskFactory(project=project, created_by=user)
        dependent_task = TaskFactory(project=project, created_by=user)
        
        TaskDependencyFactory(prerequisite_task=prerequisite1, dependent_task=dependent_task)
        TaskDependencyFactory(prerequisite_task=prerequisite2, dependent_task=dependent_task)
        
        assert dependent_task.can_be_completed() is True
    
    def test_task_can_be_completed_some_dependencies_not_done(self):
        """Test can_be_completed method when some dependencies are not done."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        
        prerequisite1 = DoneTaskFactory(project=project, created_by=user)
        prerequisite2 = TodoTaskFactory(project=project, created_by=user)
        dependent_task = TaskFactory(project=project, created_by=user)
        
        TaskDependencyFactory(prerequisite_task=prerequisite1, dependent_task=dependent_task)
        TaskDependencyFactory(prerequisite_task=prerequisite2, dependent_task=dependent_task)
        
        assert dependent_task.can_be_completed() is False
    
    def test_task_get_status_display_class(self):
        """Test get_status_display_class method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        status_classes = {
            'todo': 'todo',
            'in_progress': 'in-progress',
            'done': 'done',
            'blocked': 'blocked',
        }
        
        for status, expected_class in status_classes.items():
            task = TaskFactory(project=project, status=status, created_by=user)
            assert task.get_status_display_class() == expected_class
    
    def test_task_get_priority_display_class(self):
        """Test get_priority_display_class method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        priority_classes = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
        }
        
        for priority, expected_class in priority_classes.items():
            task = TaskFactory(project=project, priority=priority, created_by=user)
            assert task.get_priority_display_class() == expected_class
    
    def test_task_get_days_until_due(self):
        """Test get_days_until_due method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        
        # Task with due date in future
        future_due_date = timezone.now() + timedelta(days=7)
        task = TaskFactory(project=project, due_date=future_due_date, created_by=user)
        days_until = task.get_days_until_due()
        assert days_until is not None
        assert 6 <= days_until <= 8  # Allow some tolerance for timing
        
        # Task with no due date
        task_no_due = TaskFactory(project=project, due_date=None, created_by=user)
        assert task_no_due.get_days_until_due() is None
    
    def test_task_is_assigned(self):
        """Test is_assigned method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        assigned_task = TaskFactory(project=project, assignee=user, created_by=user)
        unassigned_task = TaskFactory(project=project, assignee=None, created_by=user)
        
        assert assigned_task.is_assigned() is True
        assert unassigned_task.is_assigned() is False
    
    def test_task_cascade_delete_on_project_delete(self):
        """Test that task is deleted when project is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        task_id = task.id
        
        project.delete()
        
        # Task should be deleted (cascade)
        assert not Task.objects.filter(id=task_id).exists()
    
    def test_task_set_null_on_assignee_delete(self):
        """Test that assignee is set to null when user is deleted (SET_NULL)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, assignee=user, created_by=user)
        task_id = task.id
        
        user.delete()
        
        # Task should still exist but assignee should be None
        task.refresh_from_db()
        assert task.assignee is None
        assert Task.objects.filter(id=task_id).exists()
    
    def test_task_set_null_on_created_by_delete(self):
        """Test that created_by is set to null when user is deleted (SET_NULL)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        creator = UserFactory()
        task = TaskFactory(project=project, created_by=creator)
        task_id = task.id
        
        creator.delete()
        
        # Task should still exist but created_by should be None
        task.refresh_from_db()
        assert task.created_by is None
        assert Task.objects.filter(id=task_id).exists()


# ============================================================================
# TaskDependency Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTaskDependencyModel:
    """Test suite for TaskDependency model."""
    
    def test_taskdependency_creation(self):
        """Test basic TaskDependency creation."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
        
        assert dependency.prerequisite_task == prerequisite
        assert dependency.dependent_task == dependent
        assert dependency.pk is not None
    
    def test_taskdependency_str_representation(self):
        """Test string representation of TaskDependency model."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(title='Prerequisite Task', project=project, created_by=user)
        dependent = TaskFactory(title='Dependent Task', project=project, created_by=user)
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
        
        assert 'Dependent Task' in str(dependency)
        assert 'Prerequisite Task' in str(dependency)
    
    def test_taskdependency_unique_together(self):
        """Test that prerequisite and dependent combination must be unique."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        
        TaskDependencyFactory(prerequisite_task=prerequisite, dependent_task=dependent)
        
        # Should not be able to create duplicate dependency
        with pytest.raises(IntegrityError):
            TaskDependencyFactory(prerequisite_task=prerequisite, dependent_task=dependent)
    
    def test_taskdependency_cannot_depend_on_itself(self):
        """Test that a task cannot depend on itself."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        dependency = TaskDependency(prerequisite_task=task, dependent_task=task)
        with pytest.raises(ValidationError):
            dependency.clean()
    
    def test_taskdependency_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
        after = timezone.now()
        
        assert dependency.created_at is not None
        assert before <= dependency.created_at <= after
    
    def test_taskdependency_ordering(self):
        """Test that TaskDependencies are ordered by created_at descending."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite1 = TaskFactory(project=project, created_by=user)
        prerequisite2 = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        
        dep1 = TaskDependencyFactory(prerequisite_task=prerequisite1, dependent_task=dependent)
        dep2 = TaskDependencyFactory(prerequisite_task=prerequisite2, dependent_task=dependent)
        
        dependencies = list(TaskDependency.objects.filter(dependent_task=dependent)[:2])
        # Should be ordered by -created_at (newest first)
        assert dependencies[0].created_at >= dependencies[1].created_at
    
    def test_taskdependency_cascade_delete_on_prerequisite_delete(self):
        """Test that TaskDependency is deleted when prerequisite task is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
        dependency_id = dependency.id
        
        prerequisite.delete()
        
        # TaskDependency should be deleted (cascade)
        assert not TaskDependency.objects.filter(id=dependency_id).exists()
    
    def test_taskdependency_cascade_delete_on_dependent_delete(self):
        """Test that TaskDependency is deleted when dependent task is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        prerequisite = TaskFactory(project=project, created_by=user)
        dependent = TaskFactory(project=project, created_by=user)
        dependency = TaskDependencyFactory(
            prerequisite_task=prerequisite,
            dependent_task=dependent
        )
        dependency_id = dependency.id
        
        dependent.delete()
        
        # TaskDependency should be deleted (cascade)
        assert not TaskDependency.objects.filter(id=dependency_id).exists()


# ============================================================================
# TaskComment Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTaskCommentModel:
    """Test suite for TaskComment model."""
    
    def test_taskcomment_creation(self):
        """Test basic TaskComment creation."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(
            task=task,
            author=user,
            content='This is a comment'
        )
        
        assert comment.task == task
        assert comment.author == user
        assert comment.content == 'This is a comment'
        assert comment.pk is not None
    
    def test_taskcomment_str_representation(self):
        """Test string representation of TaskComment model."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory(username='testuser')
        task = TaskFactory(title='Test Task', project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        
        assert 'testuser' in str(comment)
        assert 'Test Task' in str(comment)
    
    def test_taskcomment_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        after = timezone.now()
        
        assert comment.created_at is not None
        assert before <= comment.created_at <= after
    
    def test_taskcomment_updated_at_auto_set(self):
        """Test that updated_at is automatically set on creation."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        
        assert comment.updated_at is not None
        assert comment.updated_at == comment.created_at
    
    def test_taskcomment_updated_at_changes_on_update(self):
        """Test that updated_at changes when comment is updated."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        initial_updated_at = comment.updated_at
        
        # Wait a moment to ensure time difference
        import time
        time.sleep(0.01)
        
        comment.content = 'Updated content'
        comment.save()
        
        assert comment.updated_at > initial_updated_at
    
    def test_taskcomment_is_edited(self):
        """Test is_edited method."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        
        # Initially not edited
        assert comment.is_edited() is False
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        comment.content = 'Updated'
        comment.save()
        
        # Now should be edited
        assert comment.is_edited() is True
    
    def test_taskcomment_ordering(self):
        """Test that TaskComments are ordered by created_at descending."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        comment1 = TaskCommentFactory(task=task, author=user)
        comment2 = TaskCommentFactory(task=task, author=user)
        comment3 = TaskCommentFactory(task=task, author=user)
        
        comments = list(TaskComment.objects.filter(task=task)[:3])
        # Should be ordered by -created_at (newest first)
        assert comments[0].created_at >= comments[1].created_at
        assert comments[1].created_at >= comments[2].created_at
    
    def test_taskcomment_cascade_delete_on_task_delete(self):
        """Test that TaskComment is deleted when task is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=user)
        comment_id = comment.id
        
        task.delete()
        
        # TaskComment should be deleted (cascade)
        assert not TaskComment.objects.filter(id=comment_id).exists()
    
    def test_taskcomment_set_null_on_author_delete(self):
        """Test that author is set to null when user is deleted (SET_NULL)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        author = UserFactory()
        task = TaskFactory(project=project, created_by=author)
        comment = TaskCommentFactory(task=task, author=author)
        comment_id = comment.id
        
        author.delete()
        
        # Comment should still exist but author should be None
        comment.refresh_from_db()
        assert comment.author is None
        assert TaskComment.objects.filter(id=comment_id).exists()
    
    def test_taskcomment_can_have_null_author(self):
        """Test that author field can be null."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        comment = TaskCommentFactory(task=task, author=None)
        assert comment.author is None
        assert comment.pk is not None


# ============================================================================
# TaskAttachment Model Tests
# ============================================================================

@pytest.mark.django_db
@pytest.mark.model
class TestTaskAttachmentModel:
    """Test suite for TaskAttachment model."""
    
    def test_taskattachment_creation(self):
        """Test basic TaskAttachment creation."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        # Create a simple file for testing
        test_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        attachment = TaskAttachment(
            task=task,
            uploaded_by=user,
            file=test_file,
            filename='test.txt'
        )
        attachment.save()
        
        assert attachment.task == task
        assert attachment.uploaded_by == user
        assert attachment.filename == 'test.txt'
        assert attachment.pk is not None
    
    def test_taskattachment_str_representation(self):
        """Test string representation of TaskAttachment model."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(title='Test Task', project=project, created_by=user)
        
        test_file = SimpleUploadedFile("document.pdf", b"content", content_type="application/pdf")
        attachment = TaskAttachment(
            task=task,
            uploaded_by=user,
            file=test_file,
            filename='document.pdf'
        )
        attachment.save()
        
        assert 'document.pdf' in str(attachment)
        assert 'Test Task' in str(attachment)
    
    def test_taskattachment_filename_auto_extracted(self):
        """Test that filename is automatically extracted from file."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("auto_extract.txt", b"content", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        
        assert attachment.filename == 'auto_extract.txt'
    
    def test_taskattachment_file_size_auto_extracted(self):
        """Test that file_size is automatically extracted from file."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        file_content = b"x" * 1024  # 1KB content
        test_file = SimpleUploadedFile("size_test.txt", file_content, content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        
        assert attachment.file_size == 1024
    
    def test_taskattachment_file_type_auto_extracted(self):
        """Test that file_type is automatically extracted from filename."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("document.pdf", b"content", content_type="application/pdf")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        
        assert attachment.file_type == 'pdf'
    
    def test_taskattachment_get_file_size_display_bytes(self):
        """Test get_file_size_display method for bytes."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("small.txt", b"x" * 512, content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_size = 512
        attachment.save()
        
        assert 'B' in attachment.get_file_size_display()
        assert '512' in attachment.get_file_size_display()
    
    def test_taskattachment_get_file_size_display_kb(self):
        """Test get_file_size_display method for kilobytes."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("medium.txt", b"x", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_size = 2048  # 2KB
        attachment.save()
        
        display = attachment.get_file_size_display()
        assert 'KB' in display
    
    def test_taskattachment_get_file_size_display_mb(self):
        """Test get_file_size_display method for megabytes."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("large.txt", b"x", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_size = 2 * 1024 * 1024  # 2MB
        attachment.save()
        
        display = attachment.get_file_size_display()
        assert 'MB' in display
    
    def test_taskattachment_get_file_icon_pdf(self):
        """Test get_file_icon method for PDF files."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("document.pdf", b"content", content_type="application/pdf")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_type = 'pdf'
        attachment.save()
        
        assert attachment.get_file_icon() == 'file-pdf'
    
    def test_taskattachment_get_file_icon_image(self):
        """Test get_file_icon method for image files."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("image.jpg", b"content", content_type="image/jpeg")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_type = 'jpg'
        attachment.save()
        
        assert attachment.get_file_icon() == 'file-image'
    
    def test_taskattachment_get_file_icon_video(self):
        """Test get_file_icon method for video files."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("video.mp4", b"content", content_type="video/mp4")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_type = 'mp4'
        attachment.save()
        
        assert attachment.get_file_icon() == 'file-video'
    
    def test_taskattachment_get_file_icon_default(self):
        """Test get_file_icon method returns default for unknown file types."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("unknown.xyz", b"content", content_type="application/octet-stream")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.file_type = 'xyz'
        attachment.save()
        
        assert attachment.get_file_icon() == 'file'
    
    def test_taskattachment_created_at_auto_set(self):
        """Test that created_at is automatically set on creation."""
        before = timezone.now()
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        after = timezone.now()
        
        assert attachment.created_at is not None
        assert before <= attachment.created_at <= after
    
    def test_taskattachment_ordering(self):
        """Test that TaskAttachments are ordered by created_at descending."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        file1 = SimpleUploadedFile("file1.txt", b"content1", content_type="text/plain")
        file2 = SimpleUploadedFile("file2.txt", b"content2", content_type="text/plain")
        file3 = SimpleUploadedFile("file3.txt", b"content3", content_type="text/plain")
        
        attachment1 = TaskAttachment(task=task, uploaded_by=user, file=file1, filename='file1.txt')
        attachment1.save()
        attachment2 = TaskAttachment(task=task, uploaded_by=user, file=file2, filename='file2.txt')
        attachment2.save()
        attachment3 = TaskAttachment(task=task, uploaded_by=user, file=file3, filename='file3.txt')
        attachment3.save()
        
        attachments = list(TaskAttachment.objects.filter(task=task)[:3])
        # Should be ordered by -created_at (newest first)
        assert attachments[0].created_at >= attachments[1].created_at
        assert attachments[1].created_at >= attachments[2].created_at
    
    def test_taskattachment_cascade_delete_on_task_delete(self):
        """Test that TaskAttachment is deleted when task is deleted."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        attachment_id = attachment.id
        
        task.delete()
        
        # TaskAttachment should be deleted (cascade)
        assert not TaskAttachment.objects.filter(id=attachment_id).exists()
    
    def test_taskattachment_set_null_on_uploader_delete(self):
        """Test that uploaded_by is set to null when user is deleted (SET_NULL)."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        uploader = UserFactory()
        task = TaskFactory(project=project, created_by=uploader)
        
        test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=uploader, file=test_file)
        attachment.save()
        attachment_id = attachment.id
        
        uploader.delete()
        
        # Attachment should still exist but uploaded_by should be None
        attachment.refresh_from_db()
        assert attachment.uploaded_by is None
        assert TaskAttachment.objects.filter(id=attachment_id).exists()
    
    def test_taskattachment_can_have_null_uploaded_by(self):
        """Test that uploaded_by field can be null."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        test_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        attachment = TaskAttachment(task=task, uploaded_by=None, file=test_file)
        attachment.save()
        assert attachment.uploaded_by is None
        assert attachment.pk is not None
    
    def test_taskattachment_file_validation_allowed_extensions(self):
        """Test that file validation allows allowed extensions."""
        team = TeamFactory()
        project = ProjectFactory(team=team)
        user = UserFactory()
        task = TaskFactory(project=project, created_by=user)
        
        # Test allowed extension
        test_file = SimpleUploadedFile("document.pdf", b"content", content_type="application/pdf")
        attachment = TaskAttachment(task=task, uploaded_by=user, file=test_file)
        attachment.save()
        assert attachment.pk is not None


# ============================================================================
# API Tests - Task Endpoints
# ============================================================================

@pytest.mark.django_db
@pytest.mark.api
class TestTaskListCreateAPI:
    """Test suite for task list and create API endpoints."""
    
    def test_list_tasks_authenticated(self, authenticated_api_client, project_with_members):
        """Test listing tasks when authenticated and project member."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/tasks/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1
    
    def test_list_tasks_unauthenticated(self, api_client):
        """Test listing tasks fails when unauthenticated."""
        url = '/api/tasks/'
        response = api_client.get(url)
        
        assert response.status_code == 401
    
    def test_list_tasks_filter_by_project(self, authenticated_api_client, project_with_members):
        """Test listing tasks filtered by project."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/?project={project.id}'
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_list_tasks_filter_by_status(self, authenticated_api_client, project_with_members):
        """Test listing tasks filtered by status."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, status='in_progress')
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/tasks/?status=in_progress'
        response = client.get(url)
        
        assert response.status_code == 200
    
    def test_list_tasks_assigned_to_me(self, authenticated_api_client, project_with_members):
        """Test listing tasks assigned to current user."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/tasks/?assigned_to_me=true'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data) >= 1
    
    def test_create_task_success(self, authenticated_api_client, project_with_members):
        """Test successful task creation."""
        project, owner, admin, member = project_with_members
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = '/api/tasks/'
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'project': project.id,
            'status': 'todo',
            'priority': 'high',
            'assignee': member.id
        }
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert 'data' in response.data
        assert response.data['data']['title'] == 'New Task'
        assert response.data['message'] == 'Task created successfully'
    
    def test_create_task_unauthenticated(self, api_client, project):
        """Test task creation fails when unauthenticated."""
        url = '/api/tasks/'
        data = {'title': 'New Task', 'project': project.id}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == 401


@pytest.mark.django_db
@pytest.mark.api
class TestTaskDetailAPI:
    """Test suite for task detail, update, and delete API endpoints."""
    
    def test_get_task_detail_success(self, authenticated_api_client, project_with_members):
        """Test retrieving task details."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert response.data['title'] == task.title
    
    def test_get_task_detail_not_accessible(self, authenticated_api_client, project, user):
        """Test retrieving task details fails when not accessible."""
        task = TaskFactory(project=project, created_by=user)
        other_user = UserFactory()
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(other_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        response = client.get(url)
        
        assert response.status_code == 404
    
    def test_update_task_put_success(self, authenticated_api_client, project_with_members):
        """Test full task update using PUT."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        data = {
            'title': 'Updated Task',
            'description': 'Updated description',
            'project': project.id,
            'status': 'in_progress',
            'priority': 'high',
            'assignee': member.id
        }
        
        response = client.put(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['title'] == 'Updated Task'
        assert response.data['message'] == 'Task updated successfully'
    
    def test_update_task_patch_success(self, authenticated_api_client, project_with_members):
        """Test partial task update using PATCH."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        data = {'status': 'in_progress'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['status'] == 'in_progress'
    
    def test_update_task_as_member_forbidden(self, authenticated_api_client, project_with_members):
        """Test task update fails when user is only a member (not admin/owner/creator)."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        data = {'description': 'Unauthorized update'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 403
    
    def test_delete_task_as_creator_success(self, authenticated_api_client, project_with_members):
        """Test task deletion by creator."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204


@pytest.mark.django_db
@pytest.mark.api
class TestTaskAssigneeAPI:
    """Test suite for task assignment API endpoint."""
    
    def test_assign_task_success(self, authenticated_api_client, project_with_members):
        """Test assigning a task to a user."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/assign/'
        data = {'assignee_id': member.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['assignee'] == member.id
        assert response.data['message'] == 'Task assigned successfully'
    
    def test_unassign_task_success(self, authenticated_api_client, project_with_members):
        """Test unassigning a task."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/assign/'
        data = {'assignee_id': None}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['assignee'] is None
        assert response.data['message'] == 'Task unassigned successfully'
    
    def test_assign_task_as_member_forbidden(self, authenticated_api_client, project_with_members):
        """Test task assignment fails when user is only a member."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        other_member = UserFactory()
        from projects.models import ProjectMember
        ProjectMemberFactory(project=project, user=other_member, role='member')
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/assign/'
        data = {'assignee_id': other_member.id}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.api
class TestTaskStatusUpdateAPI:
    """Test suite for task status update API endpoint."""
    
    def test_update_task_status_success(self, authenticated_api_client, project_with_members):
        """Test updating task status."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member, status='todo')
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/status/'
        data = {'status': 'in_progress'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['status'] == 'in_progress'
        assert response.data['message'] == 'Task status updated successfully'
    
    def test_mark_task_done_as_assignee(self, authenticated_api_client, project_with_members):
        """Test marking task as done by assignee."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner, assignee=member, status='in_progress')
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(member)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/status/'
        data = {'status': 'done'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['status'] == 'done'


@pytest.mark.django_db
@pytest.mark.api
class TestTaskCommentAPI:
    """Test suite for task comment API endpoints."""
    
    def test_list_task_comments_success(self, authenticated_api_client, project_with_members):
        """Test listing task comments."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        comment = TaskCommentFactory(task=task, author=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/comments/'
        response = client.get(url)
        
        assert response.status_code == 200
        assert len(response.data['results']) >= 1
    
    def test_create_task_comment_success(self, authenticated_api_client, project_with_members):
        """Test creating a task comment."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/comments/'
        data = {'content': 'This is a test comment'}
        
        response = client.post(url, data, format='json')
        
        assert response.status_code == 201
        assert response.data['data']['content'] == 'This is a test comment'
        assert response.data['message'] == 'Comment created successfully'
    
    def test_update_task_comment_success(self, authenticated_api_client, project_with_members):
        """Test updating a task comment."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        comment = TaskCommentFactory(task=task, author=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/comments/{comment.id}/'
        data = {'content': 'Updated comment'}
        
        response = client.patch(url, data, format='json')
        
        assert response.status_code == 200
        assert response.data['data']['content'] == 'Updated comment'
        assert response.data['message'] == 'Comment updated successfully'
    
    def test_delete_task_comment_success(self, authenticated_api_client, project_with_members):
        """Test deleting a task comment."""
        project, owner, admin, member = project_with_members
        task = TaskFactory(project=project, created_by=owner)
        comment = TaskCommentFactory(task=task, author=owner)
        
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework.test import APIClient
        client = APIClient()
        refresh = RefreshToken.for_user(owner)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = f'/api/tasks/{task.id}/comments/{comment.id}/'
        response = client.delete(url)
        
        assert response.status_code == 204
