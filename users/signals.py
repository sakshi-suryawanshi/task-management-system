"""
Signals for User models.

This module contains Django signals for automatic actions
when User or UserProfile models are created or updated.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create UserProfile when a User is created.
    
    This signal ensures that every user has an associated profile
    that can be accessed via user.profile.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Automatically save UserProfile when User is saved.
    
    This ensures profile is updated when user is updated.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

