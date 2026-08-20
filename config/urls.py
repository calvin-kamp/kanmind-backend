"""Root URL configuration.

Contents:
  * admin/ -- Django's admin site.
  * api/   -- included twice, once from each app's own URL module.

Both apps are mounted under the same ``api/`` prefix, so their routes sit
side by side in one flat namespace: /api/boards/ and /api/tasks/ come from
kanban_app, /api/registration/ and /api/login/ from auth_app. Django tries the
includes in order and falls through to the next one when no pattern matches.

Docs: https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("kanban_app.api.urls")),
    path("api/", include("auth_app.api.urls")),
]
