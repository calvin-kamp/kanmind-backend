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
