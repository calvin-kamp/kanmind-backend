"""Database models for the kanban domain.

Contents:
  * Board   -- owned by one user, shared with its members.
  * Task    -- a card on a board, with the nested TextChoices classes ``Status``
               and ``Priority`` holding the allowed values.
  * Comment -- written by a user on a task, ordered oldest first.

Deletion behaviour: a board dies with its owner and takes its tasks and their
comments with it (CASCADE), while assignee, reviewer and creator are set to NULL
when that user is deleted, so the task itself survives (SET_NULL).
"""

from django.conf import settings
from django.db import models


class Board(models.Model):
    """A kanban board owned by one user and shared with its members.

    ``owner`` is the user who created the board; CASCADE means their boards are
    deleted along with them, and ``user.owned_boards`` lists them.
    ``members`` holds everyone with access; ``user.boards`` lists all boards a
    user is a member of.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_boards",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=128)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="boards")

    def __str__(self):
        """Show the board title in the admin and in shell output."""
        return self.title


class Task(models.Model):
    """A single card on a board.

    A task always belongs to exactly one board; ``board.tasks`` lists them all.
    ``assignee``, ``reviewer`` and ``creator`` are optional user references, and
    SET_NULL keeps the task alive if the referenced user is deleted -- the field
    simply becomes NULL. ``created_at`` is written once, on creation.
    """

    class Status(models.TextChoices):
        """Allowed values for the ``status`` field."""

        TO_DO = "to-do", "To Do"
        IN_PROGRESS = "in-progress", "In Progress"
        REVIEW = "review", "Review"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        """Allowed values for the ``priority`` field."""

        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=128, blank=False)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.TO_DO
    )
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Show the task title in the admin and in shell output."""
        return self.title


class Comment(models.Model):
    """A comment written on a task.

    ``author`` uses CASCADE, so comments are removed together with their author.
    ``task`` points at the task the comment belongs to; ``task.comments`` lists
    all comments of a task. Comments are always returned oldest first.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_comments",
    )
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
        """Return comments oldest first, without an explicit order_by."""

        ordering = ["created_at"]
