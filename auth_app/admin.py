"""Admin configuration for the custom user model.

Contents:
  * CustomUserAdmin -- registers User in the Django admin.

Django's stock UserAdmin is built around a "username" field, so the fieldsets
have to be redefined for a model that logs in by email; otherwise the admin
raises an error for the field it cannot find.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    """Admin view for User.

    ``fieldsets`` describes the edit form of an existing user, ``add_fieldsets``
    the creation form, which asks for the password twice instead of showing the
    stored hash.
    """

    model = User
    ordering = ("email",)

    list_display = (
        "email",
        "fullname",
        "is_staff",
    )

    search_fields = (
        "email",
        "fullname",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal info",
            {
                "fields": ("fullname",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "fullname",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
