"""Serializers for the board, task and comment endpoints.

Two patterns run through this module:

  * Two-field relations: the client sends plain IDs on a write-only field
    (``assignee_id``, ``reviewer_id``, ``members``), while the response returns
    the full nested objects under a different key (``assignee``, ``reviewer``,
    ``members_data``). Since the input and output keys differ, both can live on
    the same serializer; ``source`` routes the incoming value into the model
    field.
  * One serializer per response shape: an endpoint that returns different fields
    gets its own serializer instead of conditionals inside one class.

Contents:
  * _has_board_access      -- helper, True for members and the owner of a board.
  * BoardMembershipMixin   -- shared check that assignee and reviewer belong to
                              the task's board.
  * TaskSerializer         -- full task shape for list, create and retrieve.
  * BoardTaskSerializer    -- task shape nested in the board detail, without
                              ``board``.
  * TaskUpdateSerializer   -- update shape, without ``board`` (must not change)
                              and without ``comments_count``.
  * BoardSerializer        -- board summary with the aggregate counts, used for
                              list and create.
  * BoardDetailSerializer  -- full board with nested members and tasks.
  * BoardUpdateSerializer  -- update shape with ``owner_data`` / ``members_data``.
  * CommentSerializer      -- comment with the author rendered as a full name.
"""

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.models import Board, Comment, Task


def _has_board_access(board, user):
    """Return True if the user is a member or the owner of the board."""
    return board.members.filter(id=user.id).exists() or board.owner_id == user.id


class BoardMembershipMixin:
    """Shared validation for the task serializers.

    assignee and reviewer must belong to the board the task lives on.
    """

    def validate(self, data):
        """Reject users that are not part of the task's board."""
        board = data.get("board") or getattr(self.instance, "board", None)
        if board is not None:
            for field in ("assignee", "reviewer"):
                user = data.get(field)
                if user is not None and not _has_board_access(board, user):
                    raise serializers.ValidationError(
                        {f"{field}_id": "User is not a member of this board."}
                    )
        return data


class TaskSerializer(BoardMembershipMixin, serializers.ModelSerializer):
    """Read/write serializer for tasks (list, create, retrieve).

    Two-field pattern for the user relations: the client sends plain IDs
    (assignee_id / reviewer_id, write-only), and the response returns the full
    nested user objects (assignee / reviewer, read-only). Because the input and
    output keys differ, both can live on the same serializer. ``source`` routes
    the incoming ID into the model's own field.
    """

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]

    def validate_board(self, board):
        """Only members of the target board may create tasks on it (403)."""
        user = self.context["request"].user
        if not _has_board_access(board, user):
            raise PermissionDenied("You are not a member of this board.")
        return board

    def get_comments_count(self, obj):
        """Count the task's comments via the ``comments`` related_name."""
        return obj.comments.count()


class BoardTaskSerializer(TaskSerializer):
    """Task shape used inside the board detail response.

    Without ``board``, because the board is already the surrounding object.
    """

    class Meta(TaskSerializer.Meta):
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]


class TaskUpdateSerializer(BoardMembershipMixin, serializers.ModelSerializer):
    """Serializer used for PATCH/PUT on a task.

    Without the ``board`` field: the board a task belongs to must not be changed
    on update, so the field is simply omitted. ``comments_count`` is omitted
    too, the update response does not carry it.
    """

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        source="reviewer",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
        ]


class BoardSerializer(serializers.ModelSerializer):
    """Board summary used for the list and create endpoints.

    ``members`` is write-only (accepts a list of user IDs on create) and does
    not appear in the response; the response only exposes the aggregate counts.
    ``owner_id`` comes for free from the owner foreign key.
    """

    members = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all()
    )
    owner_id = serializers.IntegerField(read_only=True)
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
        ]

    def get_member_count(self, obj):
        """Number of members on the board."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Total number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Number of tasks still in the "to-do" status."""
        return obj.tasks.filter(status=Task.Status.TO_DO).count()

    def get_tasks_high_prio_count(self, obj):
        """Number of tasks with high priority."""
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Full board representation for the retrieve endpoint.

    Members and tasks are nested as complete objects.
    """

    owner_id = serializers.IntegerField(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "owner_id",
            "members",
            "tasks",
        ]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Serializer for PATCH/PUT on a board.

    Same two-field idea as the tasks: ``members`` (write-only) accepts IDs,
    while ``members_data`` / ``owner_data`` (read-only) return the full user
    objects.
    """

    members = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all()
    )
    owner_data = UserSerializer(source="owner", read_only=True)
    members_data = UserSerializer(source="members", many=True, read_only=True)

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "members",
            "owner_data",
            "members_data",
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Comment representation.

    ``author`` is read-only and rendered as the author's full name. It is set in
    the view (``perform_create``) from the request user, not sent by the client.
    """

    author = serializers.CharField(
        source="author.fullname",
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ["id", "created_at", "author", "content"]
