from rest_framework import permissions


class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_admin or request.user.is_superuser


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение на изменение только для автора.
    Остальным только чтение.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
