"""Custom permission classes.

DRF calls two different hooks depending on the action:
  * has_permission(request, view)          -> runs on every action (list/create/...),
                                              before any object is loaded.
  * has_object_permission(request, view, obj) -> runs only for single-object actions
                                              (retrieve/update/destroy).

Each class below documents which object type it expects as `obj`, because a
permission written for a Board will crash if attached to a Task view (a Task has
no `.members`), and vice versa.
"""

from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission

from kanban_app.models import Task


class IsBoardMember(BasePermission):
    """obj = Board. Allowed for members and the owner of the board."""

    def has_object_permission(self, request, view, obj):
        return (
            obj.members.filter(id=request.user.id).exists()
            or obj.owner_id == request.user.id
        )


class IsBoardOwner(BasePermission):
    """obj = Board. Allowed for the owner only."""

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id


class IsTaskBoardMember(BasePermission):
    """obj = Task. Member/owner of the board the task belongs to."""

    def has_object_permission(self, request, view, obj):
        board = obj.board  # step up from the task to its board
        return (
            board.members.filter(id=request.user.id).exists()
            or board.owner_id == request.user.id
        )


class IsTaskCreatorOrBoardOwner(BasePermission):
    """obj = Task. Allowed for the task creator OR the board owner (used for delete)."""

    def has_object_permission(self, request, view, obj):
        return (
            obj.creator_id == request.user.id or obj.board.owner_id == request.user.id
        )


class IsTaskBoardMemberFromURL(BasePermission):
    """View-level check for the nested comment list/create endpoints.

    Those actions have no single object, so object-level permissions never run.
    Instead we read the task_id from the URL, load the task and check board
    membership.
    """

    def has_permission(self, request, view):
        task = get_object_or_404(Task, id=view.kwargs["task_id"])
        board = task.board
        return (
            board.members.filter(id=request.user.id).exists()
            or board.owner_id == request.user.id
        )


class IsAuthor(BasePermission):
    """obj = Comment. Allowed for the author of the comment only (used for delete)."""

    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id
