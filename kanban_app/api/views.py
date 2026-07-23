from rest_framework import generics, viewsets
from rest_framework.decorators import action
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
    IsCommentBoardMember,
    IsTaskBoardMember,
    IsTaskBoardMemberFromURL,
    IsTaskCreatorOrBoardOwner,
)


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()

    def get_serializer_class(self):
        # Each action returns a different shape, so the serializer is chosen per action:
        #   retrieve -> full detail (nested members + tasks)
        #   update   -> update shape (owner_data / members_data)
        #   list/create -> summary with the count fields
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action in ("update", "partial_update"):
            return BoardUpdateSerializer
        return BoardSerializer

    def get_permissions(self):
        # Instances (with "()") because we override get_permissions ourselves.
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsBoardOwner()]  # only the owner may edit/delete
        if self.action == "create":
            return [IsAuthenticated()]  # any logged-in user may create
        return [IsAuthenticated(), IsBoardMember()]  # members may view

    def perform_create(self, serializer):
        # The owner comes from the request user, never from the body.
        board = serializer.save(owner=self.request.user)
        # Add the creator to the members as well (M2M works only after save()).
        board.members.add(self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()

    def get_serializer_class(self):
        # On update the board must not be changeable, so a serializer without the
        # "board" field is used.
        if self.action in ("update", "partial_update"):
            return TaskUpdateSerializer
        return TaskSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [
                IsAuthenticated(),
                IsTaskCreatorOrBoardOwner(),
            ]  # creator or board owner
        if self.action in ("update", "partial_update", "retrieve"):
            return [IsAuthenticated(), IsTaskBoardMember()]  # board members
        return [IsAuthenticated()]  # list/create and the custom actions below

    def perform_create(self, serializer):
        # Record who created the task (needed for the delete permission).
        serializer.save(creator=self.request.user)

    @action(detail=False, methods=["get"], url_path="assigned-to-me")
    def assigned_to_me(self, request):
        # GET /api/tasks/assigned-to-me/ -> tasks where the current user is the assignee.
        tasks = Task.objects.filter(assignee=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="reviewing")
    def reviewing(self, request):
        # GET /api/tasks/reviewing/ -> tasks where the current user is the reviewer.
        tasks = Task.objects.filter(reviewer=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class CommentListView(generics.ListCreateAPIView):
    """Nested endpoint: /api/tasks/<task_id>/comments/ (list + create)."""

    serializer_class = CommentSerializer
    # These are classes (no "()") because it is the plain attribute form.
    permission_classes = [IsAuthenticated, IsTaskBoardMemberFromURL]

    def get_queryset(self):
        # Only the comments of the task named in the URL.
        return Comment.objects.filter(task_id=self.kwargs["task_id"])

    def perform_create(self, serializer):
        # Author = current user, task = the one from the URL (neither comes from the body).
        serializer.save(author=self.request.user, task_id=self.kwargs["task_id"])


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Nested endpoint: /api/tasks/<task_id>/comments/<comment_id>/."""

    serializer_class = CommentSerializer
    lookup_url_kwarg = "comment_id"  # DRF looks up the object by this URL kwarg

    def get_permissions(self):
        # Deleting is restricted to the author; viewing/editing to board members.
        if self.request.method == "DELETE":
            return [IsAuthenticated(), IsAuthor()]
        return [IsAuthenticated(), IsCommentBoardMember()]

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs["task_id"])
