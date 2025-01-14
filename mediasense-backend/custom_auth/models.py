from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """自定义用户模型"""

    # 用户类型选项
    class UserType(models.TextChoices):
        ADMIN = "admin", _("管理员")
        STAFF = "staff", _("工作人员")
        USER = "user", _("普通用户")

    # 用户状态选项
    class UserStatus(models.TextChoices):
        ACTIVE = "active", _("活跃")
        INACTIVE = "inactive", _("未激活")
        BANNED = "banned", _("已封禁")

    # 自定义字段
    phone = models.CharField(_("手机号"), max_length=11, blank=True, default="")
    user_type = models.CharField(_("用户类型"), max_length=10, choices=UserType.choices, default=UserType.USER)
    status = models.CharField(_("用户状态"), max_length=10, choices=UserStatus.choices, default=UserStatus.ACTIVE)
    avatar = models.CharField(_("头像"), max_length=100, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(_("最后登录IP"), null=True, blank=True)

    # 元数据
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")
        db_table = "auth_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.user_type == self.UserType.ADMIN

    @property
    def is_staff_member(self):
        return self.user_type == self.UserType.STAFF

    def ban_user(self):
        """封禁用户"""
        self.status = self.UserStatus.BANNED
        self.save()

    def activate_user(self):
        """激活用户"""
        self.status = self.UserStatus.ACTIVE
        self.save()
