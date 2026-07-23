from django.contrib.auth import authenticate
from rest_framework import serializers

from auth_app.models import User


class UserSerializer(serializers.ModelSerializer):
    """Compact, read-only representation of a user.

    Reused for nested output everywhere: board members, task assignee/reviewer,
    comment author, email-check, etc.
    """

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]


class RegistrationSerializer(serializers.ModelSerializer):
    # Input-only helper field: exists purely to confirm the password.
    # It is not a model field and is never stored.
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "password", "password_confirm"]
        extra_kwargs = {
            "password": {"write_only": True},  # accepted on input, never returned
        }

    def validate(self, data):
        # Object-level validation: both password fields must match.
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        # password_confirm is not a model field -> remove it before creating.
        validated_data.pop("password_confirm")
        # Pull the password out and hash it via set_password instead of writing
        # it to the database in clear text.
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Plain serializer (not model-bound): only validates credentials,
    it does not create or update anything."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # authenticate() checks the password against the stored hash. Since the
        # custom user logs in via email, the email is passed as "username".
        user = authenticate(username=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid Login credentials")
        # Pass the resolved user to the view so it can issue a token.
        data["user"] = user
        return data
