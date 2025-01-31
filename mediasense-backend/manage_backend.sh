#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志文件路径
LOG_DIR="/data/mediasense/logs"
BACKEND_DIR="/data/mediasense/mediasense-backend"

# 确保日志目录存在
mkdir -p $LOG_DIR

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查服务状态
check_status() {
    print_message $YELLOW "检查服务状态..."
    echo "=== Supervisor 服务状态 ==="
    sudo supervisorctl status
    echo -e "\n=== Nginx 服务状态 ==="
    sudo systemctl status nginx | grep Active
}

# 启动所有服务
start() {
    print_message $YELLOW "启动所有服务..."
    
    # 启动 Nginx
    print_message $GREEN "启动 Nginx..."
    sudo systemctl start nginx
    
    # 启动 Supervisor 管理的服务
    print_message $GREEN "启动 Supervisor 服务..."
    sudo supervisorctl start mediasense_gunicorn mediasense_celery mediasense_celerybeat
    
    # 检查状态
    sleep 2
    check_status
}

# 停止所有服务
stop() {
    print_message $YELLOW "停止所有服务..."
    
    # 停止 Supervisor 管理的服务
    print_message $GREEN "停止 Supervisor 服务..."
    sudo supervisorctl stop mediasense_gunicorn mediasense_celery mediasense_celerybeat
    
    # 停止 Nginx
    print_message $GREEN "停止 Nginx..."
    sudo systemctl stop nginx
    
    # 检查状态
    sleep 2
    check_status
}

# 重启所有服务
restart() {
    print_message $YELLOW "重启所有服务..."
    stop
    sleep 2
    start
}

# 重载配置
reload() {
    print_message $YELLOW "重载配置..."
    
    # 重载 Nginx 配置
    print_message $GREEN "重载 Nginx 配置..."
    sudo nginx -t && sudo systemctl reload nginx
    
    # 重载 Supervisor 配置
    print_message $GREEN "重载 Supervisor 配置..."
    sudo supervisorctl reread
    sudo supervisorctl update
    
    # 检查状态
    sleep 2
    check_status
}

# 收集静态文件
collect_static() {
    print_message $YELLOW "收集静态文件..."
    cd $BACKEND_DIR
    python manage.py collectstatic --noinput
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 {start|stop|restart|reload|status|collect_static}"
    echo "  start          - 启动所有服务"
    echo "  stop           - 停止所有服务"
    echo "  restart        - 重启所有服务"
    echo "  reload         - 重载配置文件"
    echo "  status         - 查看服务状态"
    echo "  collect_static - 收集静态文件"
}

# 主程序
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    reload)
        reload
        ;;
    status)
        check_status
        ;;
    collect_static)
        collect_static
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit 0 