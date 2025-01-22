from rest_framework import permissions


class ActionBasedPermission(permissions.BasePermission):
    """
    基于动作的权限
    根据不同的动作使用不同的权限类
    """

    def __init__(self, action_permissions=None):
        self.action_permissions = action_permissions or {}

    def get_permission_classes(self, view):
        """获取当前动作的权限类列表"""
        if not self.action_permissions:
            return []

        permission_classes = []
        for permission_class, actions in self.action_permissions.items():
            if view.action in actions:
                permission_classes.append(permission_class)
        return permission_classes

    def has_permission(self, request, view):
        """检查权限"""
        permission_classes = self.get_permission_classes(view)
        
        # 如果没有找到对应的权限类，默认允许访问
        if not permission_classes:
            return True

        # 任一权限类通过即可
        return any(
            permission_class().has_permission(request, view)
            for permission_class in permission_classes
        )

    def has_object_permission(self, request, view, obj):
        """检查对象权限"""
        permission_classes = self.get_permission_classes(view)
        
        # 如果没有找到对应的权限类，默认允许访问
        if not permission_classes:
            return True

        # 任一权限类通过即可
        return any(
            permission_class().has_object_permission(request, view, obj)
            for permission_class in permission_classes
        )
