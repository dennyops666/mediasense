# MediaSense 后端部署文档

## 目录
1. [系统要求](#系统要求)
2. [环境准备](#环境准备)
3. [代码部署](#代码部署)
4. [数据库配置](#数据库配置)
5. [Redis配置](#redis配置)
6. [环境变量配置](#环境变量配置)
7. [服务配置](#服务配置)
8. [启动服务](#启动服务)
9. [健康检查](#健康检查)
10. [故障排除](#故障排除)

## 系统要求

### 硬件要求
- CPU: 4核心及以上
- 内存: 8GB及以上
- 磁盘空间: 50GB及以上

### 软件要求
- 操作系统: Ubuntu 20.04 LTS或更高版本
- Python: 3.10或更高版本
- MySQL: 8.0或更高版本
- Redis: 6.0或更高版本
- Nginx: 1.18或更高版本

## 环境准备

### 系统包安装
```bash
# 更新系统包
sudo apt update
sudo apt upgrade -y

# 安装必要的系统包
sudo apt install -y python3-pip python3-venv mysql-server redis-server nginx supervisor
```

### Python虚拟环境设置
```bash
# 创建项目目录
mkdir -p /data/mediasense
cd /data/mediasense

# 克隆代码仓库
git clone https://github.com/dennyops666/mediasense.git
cd mediasense-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 数据库配置

### MySQL配置
```bash
# 创建数据库和用户
mysql -u root -p

CREATE DATABASE mediasense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mediasense'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON mediasense.* TO 'mediasense'@'localhost';
FLUSH PRIVILEGES;
```

### 数据库迁移
```bash
# 执行数据库迁移
python manage.py migrate
```

## Redis配置

### Redis服务配置
```bash
# 编辑Redis配置文件
sudo nano /etc/redis/redis.conf

# 修改以下配置
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### 重启Redis服务
```bash
sudo systemctl restart redis
```

## 环境变量配置

创建 `.env` 文件：
```bash
# 数据库设置
MYSQL_DATABASE=mediasense
MYSQL_USER=mediasense
MYSQL_PASSWORD=你的密码
MYSQL_HOST=localhost
MYSQL_PORT=3306

# Redis设置
REDIS_URL=redis://localhost:6379/1
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery设置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=Asia/Shanghai

# OpenAI API设置
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=https://api.openai-proxy.com/v1
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=2000

# Django设置
DJANGO_SECRET_KEY=生成一个安全的密钥
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=你的域名,localhost,127.0.0.1
```

## 服务配置

### Supervisor配置

创建Supervisor配置文件：
```bash
sudo nano /etc/supervisor/conf.d/mediasense.conf
```

添加以下内容：
```ini
[program:mediasense_gunicorn]
command=/data/mediasense/mediasense-backend/venv/bin/gunicorn mediasense.wsgi:application -w 4 -b 127.0.0.1:8000
directory=/data/mediasense/mediasense-backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/mediasense/gunicorn.err.log
stdout_logfile=/var/log/mediasense/gunicorn.out.log

[program:mediasense_celery]
command=/data/mediasense/mediasense-backend/venv/bin/celery -A mediasense worker -l info
directory=/data/mediasense/mediasense-backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/mediasense/celery.err.log
stdout_logfile=/var/log/mediasense/celery.out.log

[program:mediasense_celery_beat]
command=/data/mediasense/mediasense-backend/venv/bin/celery -A mediasense beat -l info
directory=/data/mediasense/mediasense-backend
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/mediasense/celery_beat.err.log
stdout_logfile=/var/log/mediasense/celery_beat.out.log
```

### Nginx配置

创建Nginx配置文件：
```bash
sudo nano /etc/nginx/sites-available/mediasense
```

添加以下内容：
```nginx
upstream mediasense_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name 你的域名;

    access_log /var/log/nginx/mediasense.access.log;
    error_log /var/log/nginx/mediasense.error.log;

    location /static/ {
        alias /data/mediasense/mediasense-backend/static/;
        expires 30d;
    }

    location /media/ {
        alias /data/mediasense/mediasense-backend/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://mediasense_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/mediasense /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 启动服务

### 收集静态文件
```bash
python manage.py collectstatic
```

### 创建日志目录
```bash
sudo mkdir -p /var/log/mediasense
sudo chown -R www-data:www-data /var/log/mediasense
```

### 启动所有服务
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## 健康检查

### 检查服务状态
```bash
# 检查Supervisor管理的服务
sudo supervisorctl status

# 检查Nginx状态
sudo systemctl status nginx

# 检查Redis状态
sudo systemctl status redis

# 检查MySQL状态
sudo systemctl status mysql
```

### 检查应用日志
```bash
# 查看Gunicorn日志
tail -f /var/log/mediasense/gunicorn.out.log

# 查看Celery日志
tail -f /var/log/mediasense/celery.out.log

# 查看Celery Beat日志
tail -f /var/log/mediasense/celery_beat.out.log
```

## 故障排除

### 常见问题

1. 数据库连接错误
- 检查数据库凭据是否正确
- 确保MySQL服务正在运行
- 检查数据库用户权限

2. Redis连接错误
- 确保Redis服务正在运行
- 检查Redis配置文件
- 验证Redis端口是否正确

3. Celery任务不执行
- 检查Celery Worker状态
- 确认Redis连接正常
- 查看Celery日志中的错误信息

4. 静态文件404错误
- 确保已运行collectstatic命令
- 检查Nginx配置中的静态文件路径
- 验证文件权限是否正确

### 重启服务
```bash
# 重启所有服务
sudo supervisorctl restart all

# 重启单个服务
sudo supervisorctl restart mediasense_gunicorn
sudo supervisorctl restart mediasense_celery
sudo supervisorctl restart mediasense_celery_beat

# 重启Nginx
sudo systemctl restart nginx
```

### 查看错误日志
```bash
# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 查看应用错误日志
sudo tail -f /var/log/mediasense/*.log
``` 