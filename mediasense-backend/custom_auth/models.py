from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型"""
    
    phone = models.CharField("手机号", max_length=11, blank=True, null=True)
    user_type = models.CharField(
        "用户类型",
        max_length=10,
        choices=[
            ("admin", "管理员"),
            ("editor", "编辑"),
            ("user", "普通用户"),
        ],
        default="user",
    )
    status = models.CharField(
        "用户状态",
        max_length=10,
        choices=[
            ("active", "活跃"),
            ("inactive", "未激活"),
            ("banned", "已封禁"),
        ],
        default="active",
    )
    avatar = models.CharField("头像", max_length=100, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField("最后登录IP", blank=True, null=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        db_table = "custom_auth_user"
        ordering = ["-date_joined"]
