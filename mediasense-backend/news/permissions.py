from rest_framework import permissions


class NewsArticlePermission(permissions.BasePermission):
    """新闻文章权限控制"""

    def has_permission(self, request, view):
        # 检查基本权限
        if not request.user or not request.user.is_authenticated:
            return False

        # 管理员具有所有权限
        if request.user.is_superuser:
            return True

        # 根据不同action检查权限
        if view.action in ["create", "update", "partial_update", "destroy"]:
            return request.user.has_perm("news.change_newsarticle")
        elif view.action in ["submit_review", "withdraw"]:
            return request.user.has_perm("news.submit_review")
        elif view.action in ["assign_reviewer"]:
            return request.user.has_perm("news.assign_review")
        elif view.action in ["approve", "reject"]:
            return request.user.has_perm("news.review_article")
        elif view.action in ["audit_logs"]:
            return request.user.has_perm("news.view_audit_logs")

        return True

    def has_object_permission(self, request, view, obj):
        # 管理员具有所有权限
        if request.user.is_superuser:
            return True

        # 作者可以编辑自己的草稿文章
        if view.action in ["update", "partial_update", "destroy"]:
            return obj.author == request.user and obj.status == "draft"

        # 作者可以提交/撤回自己的文章
        if view.action in ["submit_review", "withdraw"]:
            return obj.author == request.user

        # 审核人可以审核分配给自己的文章
        if view.action in ["approve", "reject"]:
            return obj.reviewer == request.user

        return True
