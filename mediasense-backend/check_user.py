import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediasense.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 检查管理员用户
admin_user = User.objects.filter(username='admin').first()
if admin_user:
    print(f"Found admin user:")
    print(f"Username: {admin_user.username}")
    print(f"Is active: {admin_user.is_active}")
    print(f"Is staff: {admin_user.is_staff}")
    print(f"Is superuser: {admin_user.is_superuser}")
else:
    print("Admin user not found")

# 列出所有用户
print("\nAll users in database:")
for user in User.objects.all():
    print(f"- {user.username} (active: {user.is_active}, staff: {user.is_staff}, superuser: {user.is_superuser})") 