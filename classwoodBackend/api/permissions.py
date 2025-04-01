from rest_framework import permissions

from api.models import BlackListedToken, SchoolModel, StaffModel, StudentModel


class AdminPermission(permissions.BasePermission):
    """Allows access only to school admin users."""

    def has_permission(self, request, view):
        return SchoolModel.objects.filter(user=request.user).exists()


class IsTokenValid(permissions.BasePermission):
    """Denies access if the token has been blacklisted."""

    def has_permission(self, request, view):
        if not request.auth:
            return False
        return not BlackListedToken.objects.filter(user=request.user, token=request.auth).exists()


class StaffLevelPermission(permissions.BasePermission):
    """Allows access only to staff users."""

    def has_permission(self, request, view):
        return StaffModel.objects.filter(user=request.user).exists()


class StudentLevelPermission(permissions.BasePermission):
    """Allows access only to student users."""

    def has_permission(self, request, view):
        return StudentModel.objects.filter(user=request.user).exists()


class ReadOnlyStaffPermission(StaffLevelPermission):
    """Staff users with list/retrieve access only."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.method in permissions.SAFE_METHODS


class ReadOnlyStudentPermission(StudentLevelPermission):
    """Student users with list/retrieve access only."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.method in permissions.SAFE_METHODS
