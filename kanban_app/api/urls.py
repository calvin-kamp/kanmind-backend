"""URL routes for the board, task and comment endpoints.

The router builds the standard list and detail routes for boards and tasks,
including the two extra task routes declared with ``@action`` in the viewset
(/api/tasks/assigned-to-me/ and /api/tasks/reviewing/). ``basename`` is required
because the viewsets define ``get_queryset`` instead of a ``queryset``
attribute, so the router cannot derive the route names by itself.

The comment routes are written out by hand: they are nested under a task, which
a router does not produce. /api/email-check/ is defined in auth_app but listed
here so it ends up under the same ``api/`` prefix.

Everything in this module is included under ``api/`` in ``config/urls.py``.
"""

from django.urls import path
from rest_framework import routers

from auth_app.api.views import EmailCheckView

from .views import BoardViewSet, CommentDetailView, CommentListView, TaskViewSet

router = routers.SimpleRouter()
router.register(r"boards", BoardViewSet, basename="board")
router.register(r"tasks", TaskViewSet, basename="task")

urlpatterns = router.urls + [
    path("email-check/", EmailCheckView.as_view()),
    path("tasks/<int:task_id>/comments/", CommentListView.as_view()),
    path("tasks/<int:task_id>/comments/<int:comment_id>/", CommentDetailView.as_view()),
]
