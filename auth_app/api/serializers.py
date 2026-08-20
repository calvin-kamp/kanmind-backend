"""Serializers for the authentication endpoints.

Contents:
  * UserSerializer         -- compact, read-only user representation, reused for
                              all nested user output across the API.
  * RegistrationSerializer -- creates a user, confirms the password via the
                              input-only field ``repeated_password`` and stores
                              it hashed.
  * LoginSerializer        -- plain serializer that only verifies credentials
                              and passes the resolved user on to the view.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers

from auth_app.models import User


class UserSerializer(serializers.ModelSerializer):
    """Compact, read-only representation of a user.

    Reused for nested output everywhere: board members, task assignee/reviewer,
    comment author, email-check, etc.
    """

    class Meta:
        """Expose only the three fields other endpoints nest."""

        model = User
        fields = ["id", "email", "fullname"]


class RegistrationSerializer(serializers.ModelSerializer):
    """Creates a new user account.

    ``repeated_password`` is an input-only helper field: it exists purely to
    confirm the password, is not a model field and is never stored. ``password``
    is accepted on input but never returned.
    """

    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        """Accept both password fields on input, return neither."""

        model = User
        fields = ["id", "fullname", "email", "password", "repeated_password"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def validate(self, data):
        """Object-level validation: both password fields must match."""
        if data["password"] != data["repeated_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """Create the user with a hashed password.

        ``repeated_password`` is dropped because it is not a model field, and
        the password goes through ``set_password`` instead of being written to
        the database in clear text.
        """
        validated_data.pop("repeated_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Validates login credentials.

    Plain serializer (not model-bound): it only checks the credentials, it does
    not create or update anything.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Verify the credentials and hand the resolved user to the view.

        ``authenticate`` checks the password against the stored hash. Since the
        custom user logs in via email, the email is passed as ``username``.
        """
        user = authenticate(username=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid Login credentials")
        data["user"] = user
        return data
