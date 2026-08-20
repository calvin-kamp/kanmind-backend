"""Database models for authentication.

Contents:
  * CustomUserManager -- creates users and superusers, keyed on email.
  * User              -- the project's user model, authenticated by email.

Django expects the user model to be reachable through ``settings.AUTH_USER_MODEL``;
this module is what that setting points at.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(UserManager):
    """Manager for the custom User model that logs in via email instead of username."""

    def create_user(self, email, password, **extra_fields):
        """Create a regular user.

        The email is the login identifier, so it is mandatory and gets
        normalised. The password goes through ``set_password`` and is stored as
        a hash, never in clear text.
        """
        if not email:
            raise ValueError("No valid email address provided")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        """Create a user with admin access.

        The staff and superuser flags default to True and are rejected if they
        are explicitly passed as anything else.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model: authentication happens through the email address.

    ``USERNAME_FIELD`` replaces Django's default "username" with the email, so
    that is what login and ``createsuperuser`` ask for. ``REQUIRED_FIELDS``
    lists what ``createsuperuser`` additionally prompts for, besides the login
    field and the password.

    ``PermissionsMixin`` supplies the groups and permissions machinery the admin
    relies on, ``AbstractBaseUser`` the password and last-login handling.
    """

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    fullname = models.CharField(max_length=255)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["fullname"]

    class Meta:
        """Human-readable names shown in the admin."""

        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        """Show the user's full name in the admin and in shell output."""
        return self.fullname
