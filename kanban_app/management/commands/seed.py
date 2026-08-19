from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from kanban_app.models import Board, Comment, Task

User = get_user_model()

USERS = [
    ("max.mustermann@example.com", "Max Mustermann"),
    ("marie.musterfrau@example.com", "Marie Musterfrau"),
    ("john.doe@example.com", "John Doe"),
    ("erika.beispiel@example.com", "Erika Beispiel"),
    ("kevin@kovacsi.de", "Kevin Kovacsi"),
]
DEFAULT_PASSWORD = "mysecretpassword1234"


class Command(BaseCommand):
    help = "Seeds the database with dummy data (users, boards, tasks, comments)."

    def handle(self, *args, **options):
        # Remove existing kanban data (users are kept)
        Comment.objects.all().delete()
        Task.objects.all().delete()
        Board.objects.all().delete()

        # Create users (idempotent via email)
        users = {}
        for email, fullname in USERS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"fullname": fullname}
            )
            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
            users[email] = user
        self.stdout.write(f"Users: {User.objects.count()} total")

        max_u = users["max.mustermann@example.com"]
        marie = users["marie.musterfrau@example.com"]
        john = users["john.doe@example.com"]
        erika = users["erika.beispiel@example.com"]

        # Boards
        board1 = Board.objects.create(owner=max_u, title="Project X")
        board1.members.add(max_u, marie, john)
        board2 = Board.objects.create(owner=marie, title="Marketing")
        board2.members.add(marie, erika)

        # Tasks
        Task.objects.create(
            board=board1,
            title="Write API documentation",
            description="Complete the API documentation for the backend",
            status=Task.Status.TO_DO,
            priority=Task.Priority.HIGH,
            creator=max_u,
            assignee=marie,
            reviewer=max_u,
            due_date="2025-02-25",
        )
        t2 = Task.objects.create(
            board=board1,
            title="Perform code review",
            description="Review the new PR for feature X",
            status=Task.Status.REVIEW,
            priority=Task.Priority.MEDIUM,
            creator=marie,
            assignee=max_u,
            reviewer=None,
            due_date="2025-02-27",
        )
        Task.objects.create(
            board=board2,
            title="Plan campaign",
            description="Set up the Q2 campaign",
            status=Task.Status.IN_PROGRESS,
            priority=Task.Priority.LOW,
            creator=marie,
            assignee=erika,
            reviewer=marie,
            due_date="2025-03-10",
        )

        # Comments
        Comment.objects.create(
            task=t2, author=max_u, content="Looks good, one small note."
        )
        Comment.objects.create(
            task=t2, author=marie, content="Adjusted, please take another look."
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {Board.objects.count()} boards, "
                f"{Task.objects.count()} tasks, {Comment.objects.count()} comments. "
                f"Password for all seeded users: '{DEFAULT_PASSWORD}'"
            )
        )
