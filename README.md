# MediaSense 新闻舆情监控系统

## 项目概述

MediaSense 是一个功能强大的新闻舆情监控系统，提供新闻数据采集、分析、搜索和监控等综合功能。系统采用前后端分离架构，具备高性能、可扩展性和良好的用户体验。

### 主要功能

1. **多渠道新闻数据采集**
   - 支持主流新闻网站数据采集
   - RSS订阅源自动更新
   - 社交媒体数据抓取
   - 自定义爬虫配置
   - 代理池自动管理

2. **智能新闻分析与分类**
   - 基于机器学习的新闻分类
   - 关键词提取与标签生成
   - 文本相似度分析
   - 热点事件聚类
   - 新闻时间线生成

3. **全文检索与个性化推荐**
   - 基于Elasticsearch的全文检索
   - 多字段组合查询
   - 搜索结果高亮显示
   - 相关新闻推荐
   - 个性化新闻推送

4. **AI驱动的舆情分析**
   - OpenAI驱动的文本分析
   - 情感倾向分析
   - 观点提取与汇总
   - 舆情走势预测
   - 异常事件预警

5. **实时系统监控与告警**
   - 系统资源实时监控
   - 服务健康状态检查
   - 自定义告警规则
   - 多渠道告警通知
   - 告警事件追踪

6. **可视化数据展示**
   - 实时数据大屏展示
   - 多维度数据分析图表
   - 舆情趋势可视化
   - 地理位置热力图
   - 自定义报表导出

## 系统架构

### 技术栈

#### 前端
- Vue.js 3.x：核心前端框架
- Element Plus UI：UI组件库
- Axios：HTTP客户端
- ECharts 5.x：数据可视化
- Pinia：状态管理
- Vue Router：路由管理
- TypeScript：开发语言
- Vite：构建工具
- Vitest：单元测试框架
- Cypress：E2E测试工具

#### 后端
- Python 3.12：开发语言
- Django 4.2.0：Web框架
- Django REST Framework：API框架
- MySQL 8.0+：主数据库
- Redis 5.0+：缓存和消息队列
- Elasticsearch 7.x：搜索引擎
- Celery：异步任务队列
- Scrapy：爬虫框架
- OpenAI API：AI服务集成
- Prometheus：监控系统
- Grafana：监控可视化

### 核心模块

1. **认证模块** (`custom_auth/`)
   - JWT认证机制
     * Token生成与验证
     * Token自动刷新
     * 多端登录控制
   - 基于角色的权限控制
     * 角色管理
     * 权限分配
     * 资源访问控制
   - 用户会话管理
     * 会话状态维护
     * 登录设备管理
     * 安全登出机制

2. **新闻管理模块** (`news/`)
   - 新闻内容管理
     * 新闻采集与入库
     * 内容去重处理
     * 数据清洗规则
   - 分类与标签管理
     * 多级分类体系
     * 智能标签生成
     * 标签关联分析
   - 数据导入导出
     * 批量数据导入
     * 自定义导出模板
     * 数据备份恢复

3. **搜索服务模块** (`news_search/`)
   - 全文检索功能
     * 多字段检索
     * 高亮显示
     * 结果过滤
   - 智能搜索建议
     * 热门搜索推荐
     * 搜索历史记录
     * 相关词推荐
   - 热点新闻推荐
     * 实时热点发现
     * 个性化推荐
     * 相似新闻聚合

4. **爬虫系统模块** (`crawler/`)
   - 多源数据采集
     * 网站爬虫配置
     * RSS源管理
     * API数据接入
   - 任务调度管理
     * 定时任务配置
     * 任务优先级控制
     * 失败重试机制
   - 数据清洗处理
     * 内容提取规则
     * 数据格式转换
     * 质量控制机制

5. **AI服务模块** (`ai_service/`)
   - 文本智能分析
     * 实体识别
     * 关键词提取
     * 文本分类
   - 情感倾向分析
     * 情感极性判断
     * 观点提取
     * 情感趋势分析
   - OpenAI集成服务
     * GPT模型集成
     * 文本生成
     * 内容摘要

6. **监控模块** (`monitoring/`)
   - 系统资源监控
     * CPU/内存监控
     * 磁盘使用监控
     * 网络流量监控
   - 服务状态监控
     * 服务可用性检查
     * 接口响应时间
     * 错误日志监控
   - 告警管理系统
     * 告警规则配置
     * 告警级别管理
     * 通知渠道管理

## 系统要求

### 硬件要求
- CPU: 2核及以上（推荐4核8线程）
- 内存: 8GB及以上（推荐16GB）
- 存储: 50GB及以上（推荐SSD）
- 网络: 可访问外网，带宽建议≥10Mbps

### 软件要求
- 操作系统
  * Linux (Ubuntu 20.04+ / CentOS 7+)
  * 支持Docker运行环境
- Docker: 20.10+
- Docker Compose: 2.0+
- Node.js: 16.x+（开发环境）
- Python: 3.12+（开发环境）
- MySQL: 8.0+
- Redis: 5.0+
- Elasticsearch: 7.x

## 环境准备

### 开发环境配置

1. **系统依赖安装**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.12 python3.12-venv nodejs npm mysql-server redis-server

# CentOS/RHEL
sudo yum update
sudo yum install -y python3.12 nodejs mysql-server redis
```

2. **Node.js环境配置**
```bash
# 安装pnpm
npm install -g pnpm

# 设置镜像源（可选）
pnpm config set registry https://registry.npmmirror.com
```

3. **Python环境配置**
```bash
# 创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 设置pip镜像源（可选）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 数据库配置

1. **MySQL配置**
```bash
# 登录MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE mediasense CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'mediasense'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON mediasense.* TO 'mediasense'@'localhost';
FLUSH PRIVILEGES;
```

2. **Redis配置**
```bash
# 修改Redis配置
sudo vim /etc/redis/redis.conf

# 重要配置项
maxmemory 2gb
maxmemory-policy allkeys-lru
```

3. **Elasticsearch配置**
```bash
# 安装Elasticsearch
docker pull elasticsearch:7.17.9

# 运行Elasticsearch
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  elasticsearch:7.17.9
```

## 项目部署

### 开发环境部署

1. **克隆项目**
```bash
git clone https://github.com/dennyops666/mediasense.git
cd mediasense
```

2. **后端服务部署**
```bash
cd mediasense-backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python manage.py migrate
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver 0.0.0.0:8000
```

3. **前端服务部署**
```bash
cd mediasense-frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 生产环境部署

1. **使用Docker Compose部署**
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

2. **环境变量配置**
```bash
# 后端环境变量
DJANGO_SETTINGS_MODULE=config.settings.production
DATABASE_URL=mysql://user:pass@host:3306/dbname
REDIS_URL=redis://host:6379/0
ELASTICSEARCH_URL=http://host:9200

# 前端环境变量
VITE_API_BASE_URL=http://backend.mediasense.com
VITE_WEBSOCKET_URL=ws://backend.mediasense.com/ws
```

3. **Nginx配置**
```nginx
# /etc/nginx/conf.d/mediasense.conf
server {
    listen 80;
    server_name example.com;

    # 前端静态文件
    location / {
        root /var/www/mediasense;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 开发指南

### 代码规范

1. **前端代码规范**
- 遵循 Vue.js 风格指南
- 使用 ESLint + Prettier 进行代码格式化
- 组件命名采用 PascalCase
- Props 定义要详细的类型说明
- 使用 TypeScript 类型注解

2. **后端代码规范**
- 遵循 PEP 8 规范
- 使用 Black 进行代码格式化
- 使用 pylint 进行代码检查
- 函数和类要写文档字符串
- 变量命名采用下划线命名法

3. **Git提交规范**
```bash
# 提交格式
<type>(<scope>): <subject>

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试用例
chore: 构建过程或辅助工具的变动
```

### 分支管理

- main: 主分支，用于生产环境
- develop: 开发分支，用于开发环境
- feature/*: 功能分支，用于新功能开发
- bugfix/*: 修复分支，用于修复bug
- release/*: 发布分支，用于版本发布

### 测试规范

1. **单元测试**
```bash
# 前端单元测试
cd mediasense-frontend
pnpm test:unit

# 后端单元测试
cd mediasense-backend
python manage.py test
```

2. **集成测试**
```bash
# 前端E2E测试
cd mediasense-frontend
pnpm test:e2e

# 后端集成测试
cd mediasense-backend
python manage.py test --tag=integration
```

## 常见问题

1. **环境配置问题**
- Q: 安装依赖时报错
- A: 检查Python/Node.js版本，确保符合要求

2. **数据库问题**
- Q: MySQL连接失败
- A: 检查数据库配置和权限设置

3. **部署问题**
- Q: Docker部署失败
- A: 检查Docker配置和网络设置

## 更新日志

### v1.0.0 (2025-01-25)
- 初始版本发布
- 基础功能实现
- 核心模块开发完成

### v1.1.0 (2025-02-01)
- 添加AI分析功能
- 优化搜索性能
- 修复已知bug

PI网关集成

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目负责人：Denny
- 邮箱：jeywork666@gmail.com
- 项目主页：https://github.com/dennyops666/mediasense

---
© 2025 MediaSense Team. All Rights Reserved. 