from django.conf import settings
from django.db import models


class Board(models.Model):
    # The user who created / owns the board.
    # CASCADE: if the owner is deleted, their boards are deleted too.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_boards",  # user.owned_boards -> boards this user owns
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=128)
    # Users with access to the board (many-to-many).
    # user.boards -> all boards a user is a member of.
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="boards")

    def __str__(self):
        return self.title


class Task(models.Model):
    # Fixed, allowed values for the status / priority fields.
    class Status(models.TextChoices):
        TO_DO = "to-do", "To Do"
        IN_PROGRESS = "in-progress", "In Progress"
        REVIEW = "review", "Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    # A task always belongs to exactly one board; board.tasks -> all its tasks.
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=128, blank=False)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TO_DO
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )

    # assignee / reviewer / creator are optional user references.
    # SET_NULL keeps the task alive if the referenced user is deleted
    # (the field simply becomes NULL).
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="review_tasks",
        null=True,
        blank=True,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        null=True,
        blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # set once, on creation

    def __str__(self):
        return self.title


class Comment(models.Model):
    # The author of the comment. CASCADE: comments die with their author.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_comments",
    )
    # The task this comment belongs to; task.comments -> all comments of a task.
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Comments are always returned oldest first.
        ordering = ["created_at"]
