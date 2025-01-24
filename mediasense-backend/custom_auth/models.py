from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models
from asgiref.sync import sync_to_async

class AsyncUserManager(BaseUserManager):
    """异步用户管理器"""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """创建普通用户"""
        if not username:
            raise ValueError('用户名不能为空')
        if not email:
            raise ValueError('邮箱不能为空')
        email = self.normalize_email(email)
        extra_fields.setdefault('user_type', 'user')
        return super().create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')

        return super().create_superuser(username, email, password, **extra_fields)
    
    async def acreate_user(self, username, email=None, password=None, **extra_fields):
        """异步创建普通用户"""
        return await sync_to_async(self.create_user)(username, email, password, **extra_fields)
    
    async def acreate_superuser(self, username, email=None, password=None, **extra_fields):
        """异步创建超级用户"""
        return await sync_to_async(self.create_superuser)(username, email, password, **extra_fields)

    def normalize_email(self, email):
        """规范化邮箱地址"""
        if email:
            email = email.lower()
        return email

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

    objects = AsyncUserManager()

    roles = models.ManyToManyField(
        'Role',
        verbose_name="角色列表",
        related_name="users",
        blank=True
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name
        db_table = "custom_auth_user"
        ordering = ["-date_joined"]

class Permission(models.Model):
    """权限模型"""
    name = models.CharField("权限名称", max_length=100, unique=True)
    description = models.CharField("权限描述", max_length=200)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = verbose_name
        db_table = "custom_auth_permission"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Role(models.Model):
    """角色模型"""
    name = models.CharField("角色名称", max_length=100, unique=True)
    description = models.CharField("角色描述", max_length=200, blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name="权限列表",
        related_name="roles",
        blank=True
    )
    parent = models.ForeignKey(
        'self',
        verbose_name="父角色",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children"
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = verbose_name
        db_table = "custom_auth_role"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_all_permissions(self):
        """获取角色的所有权限（包括继承的权限）"""
        permissions = set(self.permissions.all())
        if self.parent:
            permissions.update(self.parent.get_all_permissions())
        return permissions
