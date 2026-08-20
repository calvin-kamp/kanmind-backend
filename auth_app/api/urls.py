"""URL routes for the authentication endpoints.

Both routes are included under the ``api/`` prefix in ``config/urls.py``, which
gives /api/registration/ and /api/login/. Neither requires a token, since the
client has none yet at that point.
"""

from django.urls import path

from .views import LoginView, RegistrationView

urlpatterns = [
    path("registration/", RegistrationView.as_view()),
    path("login/", LoginView.as_view()),
]
