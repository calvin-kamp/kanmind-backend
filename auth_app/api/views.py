"""Views for the authentication endpoints.

Contents:
  * RegistrationView -- POST /api/registration/, open to anyone, creates the
                        user and returns a token right away.
  * LoginView        -- POST /api/login/, exchanges email and password for a
                        token.
  * EmailCheckView   -- GET /api/email-check/?email=..., returns the user
                        belonging to an email address. Requires a token.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import User

from .serializers import LoginSerializer, RegistrationSerializer


class RegistrationView(APIView):
    """POST /api/registration/ -- creates a new user account.

    Open to anyone, since an unregistered visitor cannot be authenticated yet.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Create the user and issue a token so the client is logged in already.

        ``raise_exception=True`` turns invalid input into an automatic 400.
        """
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "fullname": user.fullname,
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/login/ -- exchanges email and password for an auth token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Return the token of the user the serializer already resolved."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "fullname": user.fullname,
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )


class EmailCheckView(APIView):
    """GET /api/email-check/?email=... -- returns the user if that email exists."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Look the user up by email.

        The address comes as a query parameter, not in the body. A missing or
        malformed address gives 400, an unknown one gives 404.
        """
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, email=email)
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": user.fullname,
            }
        )
