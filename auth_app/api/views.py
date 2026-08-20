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
    permission_classes = [AllowAny]  # anyone may register

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # -> automatic 400 on invalid input
        user = serializer.save()
        # Issue a token right away so the client is effectively logged in.
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
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]  # already resolved & verified
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
    """GET /api/email-check/?email=... -> returns the user if that email exists."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # The email comes as a query parameter (?email=...), not in the body.
        email = request.query_params.get("email")
        if not email:
            return Response(
                {"detail": "Query parameter 'email' is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            # Malformed address -> 400, not 404.
            validate_email(email)
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, email=email)  # 404 if no such user exists
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "fullname": user.fullname,
            }
        )
