from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(UserManager):
    """Manager for the custom User model that logs in via email instead of username."""

    def create_user(self, email, password, **extra_fields):
        # Email is the login identifier, so it is mandatory.
        if not email:
            raise ValueError("No valid email address provided")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash the password, never store it in clear text
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        # A superuser must have the staff/superuser flags set.
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model: authentication happens through the email address."""

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    full_name = models.CharField(max_length=255)

    objects = CustomUserManager()

    # Use email as the unique login field instead of the default "username".
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = [
        "full_name"
    ]  # prompted for by createsuperuser (besides email/password)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.full_name
