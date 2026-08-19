from rest_framework import serializers

from auth_app.api.serializers import UserSerializer
from auth_app.models import User
from kanban_app.models import Board, Comment, Task


class TaskSerializer(serializers.ModelSerializer):
    """Read/write serializer for tasks (list, create, retrieve).

    Two-field pattern for the user relations: the client sends plain IDs
    (assignee_id / reviewer_id, write-only), and the response returns the full
    nested user objects (assignee / reviewer, read-only). Because the input and
    output keys differ, both can live on the same serializer.
    """

    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",  # write the value into the model's "assignee" field
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
    assignee = UserSerializer(read_only=True)  # full object on output
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

    def get_comments_count(self, obj):
        return obj.comments.count()  # uses the Comment.task related_name "comments"


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer used for PATCH/PUT on a task.

    Identical to TaskSerializer but without the "board" field: the board a task
    belongs to must not be changed on update, so the field is simply omitted.
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

    def get_comments_count(self, obj):
        return obj.comments.count()


class BoardSerializer(serializers.ModelSerializer):
    """Board summary used for the list and create endpoints.

    members is write-only (accepts a list of user IDs on create) and does not
    appear in the response; the response only exposes the aggregate counts.
    """

    members = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all()
    )
    owner_id = serializers.IntegerField(
        read_only=True
    )  # comes for free from the owner FK
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
        return obj.members.count()

    def get_ticket_count(self, obj):
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status=Task.Status.TO_DO).count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority=Task.Priority.HIGH).count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Full board representation for the retrieve endpoint: nested members and tasks."""

    owner_id = serializers.IntegerField(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

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

    Same two-field idea as the tasks: "members" (write-only) accepts IDs, while
    "members_data" / "owner_data" (read-only) return the full user objects.
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
    # author is read-only and rendered as the author's full name. It is set in the
    # view (perform_create) from the request user, not sent by the client.
    author = serializers.CharField(
        source="author.fullname",
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]
