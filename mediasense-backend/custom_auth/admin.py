from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "user_type", "status", "date_joined", "last_login")
    list_filter = ("user_type", "status", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email", "phone")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("个人信息"), {"fields": ("email", "phone", "avatar")}),
        (_("用户状态"), {"fields": ("user_type", "status")}),
        (
            _("权限"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("重要日期"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "email", "phone", "user_type"),
            },
        ),
    )
