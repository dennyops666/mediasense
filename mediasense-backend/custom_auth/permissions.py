from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    管理员权限
    只允许管理员访问
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == "admin")


class IsStaffOrAdmin(permissions.BasePermission):
    """
    工作人员或管理员权限
    允许工作人员和管理员访问
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type in ["admin", "staff"])


class IsSelfOrAdmin(permissions.BasePermission):
    """
    本人或管理员权限
    只允许用户操作自己的数据，管理员可以操作所有数据
    """

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.id == obj.id or request.user.user_type == "admin")
        )


class ReadOnly(permissions.BasePermission):
    """
    只读权限
    只允许安全的HTTP方法（GET, HEAD, OPTIONS）
    """

    def has_permission(self, request, view):
        return bool(request.method in permissions.SAFE_METHODS)


class ActionBasedPermission(permissions.BasePermission):
    """
    基于动作的权限
    根据不同的动作使用不同的权限类
    """

    def __init__(self, action_permissions=None):
        self.action_permissions = action_permissions or {}

    def has_permission(self, request, view):
        for klass, actions in self.action_permissions.items():
            if view.action in actions:
                return klass().has_permission(request, view)
        return True

    def has_object_permission(self, request, view, obj):
        for klass, actions in self.action_permissions.items():
            if view.action in actions:
                return klass().has_object_permission(request, view, obj)
        return True
