# apps/users/models.py
import os
from typing import cast
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def user_profile_picture_path(instance: models.Model, filename: str) -> str:
    """
    Generate file path for new user profile picture:
    MEDIA_ROOT/profile_pics/<username>_<timestamp>.<ext>

    Args:
        instance (UserProfile): instance of UserProfile class
        filename (str): name of uploaded photow
    Returns:
        str: path where the file will be stored with new name
    """
    ext = filename.split(".")[-1]

    userprofile = cast("UserProfile", instance)

    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    filename = f"{userprofile.user.username}_{timestamp}.{ext}"
    return os.path.join("profile_photos/", filename)


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("super_user", "Super User"),
        ("admin", "Admin"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    photo = models.ImageField(
        upload_to=user_profile_picture_path, blank=True, null=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def is_super_user(self):
        return self.role == "super_user"
