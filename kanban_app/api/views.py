"""Views for the board, task and comment endpoints.

Two rules recur in this module:

  * Serializer per action: ``get_serializer_class`` picks the serializer that
    matches the response shape the endpoint is documented to return.
  * Queryset per action: the list routes are filtered down to the boards and
    tasks the user may see, while single-object actions keep the full queryset
    so the permission classes answer with 403 rather than hiding the object
    behind a 404.

Contents:
  * BoardViewSet     -- /api/boards/ and /api/boards/<id>/. Anyone logged in may
                        create, members may view and edit, only the owner may
                        delete.
  * TaskViewSet      -- /api/tasks/ and /api/tasks/<id>/, plus the filter routes
                        /assigned-to-me/ and /reviewing/. Board members may view
                        and edit, the creator or the board owner may delete.
  * CommentListView  -- /api/tasks/<task_id>/comments/, list and create.
  * CommentDetailView -- /api/tasks/<task_id>/comments/<comment_id>/, delete
                        only, restricted to the author.
"""

from django.db.models import Q
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.api.serializers import (
    BoardDetailSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
    CommentSerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)
from kanban_app.models import Board, Comment, Task

from .permissions import (
    IsAuthor,
    IsBoardMember,
    IsBoardOwner,
    IsTaskBoardMember,
    IsTaskBoardMemberFromURL,
    IsTaskCreatorOrBoardOwner,
)


class BoardViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for boards under /api/boards/."""

    def get_queryset(self):
        """Restrict the list to boards the user has access to.

        Single-object actions keep the full queryset, otherwise a board the user
        may not see would give 404 instead of the documented 403.
        """
        if self.action != "list":
            return Board.objects.all()
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_class(self):
        """Pick the serializer per action, since each returns a different shape.

        retrieve -> full detail (nested members + tasks),
        update -> update shape (owner_data / members_data),
        list/create -> summary with the count fields.
        """
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action in ("update", "partial_update"):
            return BoardUpdateSerializer
        return BoardSerializer

    def get_permissions(self):
        """Owner may delete, members may view and edit, anyone may create.

        The permissions are returned as instances (with "()") because this is
        the ``get_permissions`` form, not the ``permission_classes`` attribute.
        """
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), IsBoardMember()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsBoardOwner()]
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsBoardMember()]

    def perform_create(self, serializer):
        """Set the owner from the request user and add them to the members.

        The owner never comes from the body, and the M2M relation only works
        after ``save()``.
        """
        board = serializer.save(owner=self.request.user)
        board.members.add(self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for tasks under /api/tasks/, plus the two filter routes."""

    def get_queryset(self):
        """Restrict the list routes to tasks on boards the user can access.

        Detail actions keep the full queryset so the permission classes can
        answer with 403 instead of hiding the task behind a 404.
        """
        if self.action not in ("list", "assigned_to_me", "reviewing"):
            return Task.objects.all()
        user = self.request.user
        return Task.objects.filter(
            Q(board__owner=user) | Q(board__members=user)
        ).distinct()

    def get_serializer_class(self):
        """Use the serializer without ``board`` on update, so it cannot change."""
        if self.action in ("update", "partial_update"):
            return TaskUpdateSerializer
        return TaskSerializer

    def get_permissions(self):
        """Creator or board owner may delete, board members may view and edit."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        if self.action in ("update", "partial_update", "retrieve"):
            return [IsAuthenticated(), IsTaskBoardMember()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Turn an unknown board id into 404 instead of a 400 from the field.

        Membership itself is checked in ``TaskSerializer.validate_board``.
        """
        board_id = request.data.get("board")
        if board_id is not None and not Board.objects.filter(id=board_id).exists():
            raise NotFound("Board not found.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Record who created the task, needed for the delete permission."""
        serializer.save(creator=self.request.user)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        """GET /api/tasks/assigned-to-me/ -- tasks the user is the assignee of."""
        tasks = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reviewing")
    def reviewing(self, request):
        """GET /api/tasks/reviewing/ -- tasks the user is the reviewer of."""
        tasks = self.get_queryset().filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class CommentListView(generics.ListCreateAPIView):
    """Nested endpoint: /api/tasks/<task_id>/comments/ (list + create).

    The permissions are given as classes (no "()") because this is the plain
    attribute form.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardMemberFromURL]

    def get_queryset(self):
        """Only the comments of the task named in the URL."""
        return Comment.objects.filter(task_id=self.kwargs["task_id"])

    def perform_create(self, serializer):
        """Take the author from the request and the task from the URL.

        Neither comes from the request body.
        """
        serializer.save(author=self.request.user, task_id=self.kwargs["task_id"])


class CommentDetailView(generics.DestroyAPIView):
    """Nested endpoint: /api/tasks/<task_id>/comments/<comment_id>/ (delete only).

    ``lookup_url_kwarg`` tells DRF which URL kwarg identifies the object.
    """

    serializer_class = CommentSerializer
    lookup_url_kwarg = "comment_id"
    permission_classes = [IsAuthenticated, IsAuthor]

    def get_queryset(self):
        """Only the comments of the task named in the URL."""
        return Comment.objects.filter(task_id=self.kwargs["task_id"])
