import os

# 根据环境变量选择配置文件
environment = os.getenv("DJANGO_ENV", "development")

if environment == "production":
    from .production import *
else:
    from .development import *
