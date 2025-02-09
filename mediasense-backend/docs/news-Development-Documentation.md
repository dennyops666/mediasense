# 新闻舆情监控系统开发文档


### 项目名称： mediasense


## 1. 前言

### 1.1 编写目的

本开发文档面向整个项目团队（后端开发、前端开发、运维人员以及项目管理层），力求：

1. 对系统需求和整体架构做出完整说明，保证成员对各模块的功能和交互有共同认知。  
2. 提供数据库逻辑结构设计与建表脚本，便于团队快速初始化并理解数据层关系。  
3. 指导前端（Vue）实现新闻聚合与可视化展示（ECharts），并说明权限管理、API 交互细节。  
4. 给出运行环境部署方法，确保团队可在 Linux 服务器上顺利安装依赖、部署应用并上线运行。 



### 1.2 当前开发进度

1. **基础设施层**
   - 数据库设计与优化
     * 核心表结构设计与创建
     * 数据库监控
   - 缓存系统
     * Redis 缓存层部署
     * 热点数据缓存策略
     * 缓存自动更新机制

2. **核心功能层**
   - 用户认证系统
     * JWT 认证机制
     * 密码加密存储
     * 角色权限控制
     * 会话管理

3. **搜索与分析层**
   - 搜索系统
     * 全文检索功能
     * 多维度聚合
     * 搜索建议
   - 数据分析
     * 新闻来源分析
     * 热点话题分析
     * 舆情趋势分析
     * 数据可视化

### 1.3 系统性能指标

1. **响应时间**
   - API 平均响应时间 < 100ms
   - 搜索响应时间 < 200ms
   - 页面加载时间 < 1s

2. **可靠性指标**
   - 系统可用性 99.99%
   - 数据可靠性 99.999%
   - 故障恢复时间 < 5分钟
   - 数据一致性保证

## 2. 开发环境与主要依赖

### 2.1 软件与硬件环境

- **操作系统**：Linux (Ubuntu 20.04+ / CentOS 7+)；本地开发可使用 Windows/macOS/Linux  
- **硬件**：2~4 核 CPU，≥8 GB 内存，≥50 GB 磁盘空间  
- **网络**：需可访问外网，以拉取依赖包、抓取新闻站点

### 2.2 主要技术栈（已确定）

1. **后端**：  
   - Python 3.12
   - Django 4.2.0
   - Django REST Framework
2. **前端**：  
   - Vue.js 3
   - Axios
   - ECharts
3. **数据库**：  
   - MySQL 8.0+
   - Redis 5.0+

### 2.3 需要安装的依赖

- **Python**：
  - django==4.2.0
  - djangorestframework==3.14.0
  - mysqlclient==2.2.0
  - requests==2.31.0
  - beautifulsoup4==4.12.2
  - openai==0.28.0
  - redis==5.0.1

## 3. 系统整体架构

### 3.1 功能目标

1. **多渠道数据采集**：爬虫周期性抓取新闻（门户网站、RSS、社交媒体等）  
2. **新闻聚合与可视化**：Django 后端提供数据 API，前端 Vue 显示聚合列表与可视化图表  
3. **用户权限**：管理员可配置爬虫，普通用户仅查看新闻  
4. **运行部署**：在单台 Linux 服务器上完成后端、前端与数据库部署

### 3.2 后端模块架构

1. **认证模块** (`custom_auth/`)
   - 用户认证与授权
   - JWT令牌管理
   - 角色权限控制
   - 会话管理

2. **新闻管理模块** (`news/`)
   - 新闻内容管理
   - 新闻分类管理
   - 新闻元数据管理
   - 数据导入导出

3. **搜索服务模块** (`news_search/`)
   - 新闻全文检索
   - 搜索建议管理
   - 热点新闻推荐
   - ElasticSearch集成

4. **爬虫系统模块** (`crawler/`)
   - 爬虫配置管理
   - 任务调度管理
   - 代理池管理
   - 数据清洗处理

5. **AI服务模块** (`ai_service/`)
   - 文本分析处理
   - 情感分析服务
   - OpenAI集成
   - 分析结果管理

6. **监控模块** (`monitoring/`)
   - 系统资源监控
   - 服务状态监控
   - 性能指标采集
   - 告警管理

7. **API模块** (`api_v1/`)
   - 统一API路由管理
   - API响应格式标准化
   - API文档自动生成
   - API版本控制

### 3.3 模块交互流程

1. **数据采集流程**
   - 爬虫模块读取配置 → 执行采集任务 → 数据清洗 → 存入数据库
   - 监控模块记录任务执行状态和性能指标

2. **搜索服务流程**
   - 用户发起搜索 → 搜索模块查询ES → 返回结果 → 更新搜索建议
   - AI模块对搜索结果进行分析和处理

3. **系统监控流程**
   - 监控模块定期采集指标 → 分析性能数据 → 触发告警规则 → 通知管理员

## 4. 数据库设计

### 4.1 核心模型

1. **新闻模型** (`news.models.News`)
```sql
CREATE TABLE news (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT,
    summary TEXT,
    source VARCHAR(100),
    author VARCHAR(100),
    publish_time DATETIME,
    status VARCHAR(20) DEFAULT 'draft',
    category VARCHAR(50),
    tags JSON,
    url VARCHAR(500) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_publish_time (publish_time),
    INDEX idx_status (status),
    INDEX idx_category (category),
    FULLTEXT INDEX ft_title_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

2. **爬虫配置模型** (`crawler.models.CrawlerConfig`)
```sql
CREATE TABLE crawler_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    frequency VARCHAR(10) DEFAULT 'daily',
    status VARCHAR(10) DEFAULT 'active',
    config_type VARCHAR(10) DEFAULT 'rss',
    use_proxy BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run DATETIME NULL,
    next_run DATETIME NULL,
    error_count INT DEFAULT 0,
    last_error TEXT,
    config JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_site_name (site_name),
    INDEX idx_status (status),
    INDEX idx_next_run (next_run)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

3. **爬虫任务模型** (`crawler.models.CrawlerTask`)
```sql
CREATE TABLE crawler_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_id BIGINT NOT NULL,
    priority VARCHAR(10) DEFAULT 'normal',
    status VARCHAR(20) DEFAULT 'pending',
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    error_message TEXT,
    items_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (config_id) REFERENCES crawler_config(id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

4. **搜索建议模型** (`news_search.models.SearchSuggestion`)
```sql
CREATE TABLE search_suggestion (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL UNIQUE,
    frequency INT DEFAULT 1,
    category VARCHAR(50),
    source VARCHAR(50),
    is_hot BOOLEAN DEFAULT FALSE,
    last_used DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_keyword (keyword),
    INDEX idx_frequency (frequency DESC),
    INDEX idx_category (category),
    INDEX idx_is_hot (is_hot),
    INDEX idx_last_used (last_used DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

5. **AI分析结果模型** (`ai_service.models.AnalysisResult`)
```sql
CREATE TABLE analysis_result (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    news_id BIGINT NOT NULL,
    sentiment VARCHAR(20) DEFAULT 'neutral',
    keywords JSON,
    named_entities JSON,
    summary TEXT,
    confidence FLOAT,
    model_version VARCHAR(50),
    processing_time INT,
    analysis_time DATETIME,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (news_id) REFERENCES news(id),
    INDEX idx_news_id (news_id),
    INDEX idx_sentiment (sentiment),
    INDEX idx_status (status),
    INDEX idx_analysis_time (analysis_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

6. **系统监控模型** (`monitoring.models.SystemMetrics`)
```sql
CREATE TABLE system_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    network_io JSON,
    process_count INT,
    error_count INT DEFAULT 0,
    collection_time DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_collection_time (collection_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 4.2 模型关系

1. **一对一关系**
   - News ↔ AnalysisResult：每篇新闻对应一个AI分析结果

2. **一对多关系**
   - CrawlerConfig → CrawlerTask：一个爬虫配置对应多个爬虫任务
   - CrawlerConfig → News：一个爬虫配置可对应多篇新闻
   - News → SearchSuggestion：多篇新闻可能关联到同一个搜索建议

### 4.3 索引优化

1. **主键索引**
   - 所有表都使用自增的BIGINT作为主键
   - 使用InnoDB引擎确保主键索引的高效性

2. **外键索引**
   - CrawlerTask.config_id → CrawlerConfig.id
   - AnalysisResult.news_id → News.id

3. **复合索引**
   - News：`(category, publish_time)` 用于分类查询和时间排序
   - SearchSuggestion：`(is_hot, frequency)` 用于热门搜索推荐
   - CrawlerConfig：`(status, next_run)` 用于任务调度

4. **全文索引**
   - News：`(title, content)` 用于全文检索
   - SearchSuggestion：`keyword` 用于关键词匹配

### 4.4 数据完整性

1. **必填字段**
   - News：`title`, `content`, `url`(唯一)
   - CrawlerConfig：`name`, `site_name`, `site_url`
   - SearchSuggestion：`keyword`(唯一)
   - SystemMetrics：`collection_time`

2. **默认值**
   - News.status：`draft`
   - CrawlerConfig.frequency：`daily`
   - CrawlerTask.priority：`normal`
   - CrawlerTask.status：`pending`
   - AnalysisResult.sentiment：`neutral`

3. **约束条件**
   - 唯一约束：
     * News.url
     * SearchSuggestion.keyword
   - 外键约束：
     * CrawlerTask → CrawlerConfig
     * AnalysisResult → News
   - 时间约束：
     * CrawlerTask.end_time >= CrawlerTask.start_time
     * 所有created_at字段自动设置为当前时间
     * 所有updated_at字段在更新时自动更新

4. **数据清理策略**
   - SystemMetrics数据定期归档
   - CrawlerTask历史记录定期清理
   - News表支持软删除
   - SearchSuggestion过期数据自动清理

## 5. 后端模块架构

### 5.1 核心模块划分

1. **新闻管理模块** (`news/`)
   - 新闻内容管理
     * 新闻创建、更新、删除
     * 新闻状态管理（草稿、已发布、已归档）
     * 新闻分类管理
   - 新闻元数据处理
     * 自动提取关键信息
     * 标签管理
     * 来源管理
   - 数据导入导出
     * 批量导入功能
     * 数据导出接口
     * 格式转换工具

2. **搜索服务模块** (`news_search/`)
   - 搜索功能实现
     * 全文检索
     * 高级过滤
     * 结果排序
   - 搜索优化
     * 搜索建议实现
     * 热门搜索缓存
     * 搜索历史记录
   - ElasticSearch 集成
     * 索引管理
     * 查询优化
     * 同步机制

3. **爬虫系统模块** (`crawler/`)
   - 多类型爬虫支持
     * RSS 爬虫（`rss_crawler.py`）
     * HTML 爬虫（`crawlers.py`）
     * API 数据采集
   - 任务管理系统
     * 任务调度（`task_manager.py`）
     * 错误重试机制
     * 任务优先级
   - 数据处理
     * 内容提取
     * 数据清洗
     * 去重处理
   - 监控与报告
     * 爬虫状态监控
     * 性能统计
     * 错误追踪

4. **AI 服务模块** (`ai_service/`)
   - 文本分析服务
     * 分词处理
     * 停用词过滤
     * 关键词提取
   - 情感分析
     * 文本情感识别
     * 观点提取
     * 情感趋势分析
   - OpenAI 集成
     * API 调用管理
     * 响应处理
     * 错误处理
   - 批处理服务
     * 队列管理
     * 异步处理
     * 结果缓存

5. **监控系统模块** (`monitoring/`)
   - 系统监控
     * 资源使用监控
     * 服务状态检查
     * 性能指标收集
   - 告警系统
     * 告警规则配置
     * 通知机制
     * 告警级别管理
   - 日志管理
     * 日志收集
     * 日志分析
     * 日志存储

6. **认证授权模块** (`auth/`)
   - 用户认证
     * JWT 实现
     * 会话管理
     * 密码加密
   - 权限管理
     * 角色管理
     * 权限分配
     * 访问控制
   - 安全特性
     * 密码重置
     * 登录保护
     * 操作审计

### 5.2 模块间交互

1. **数据流转**
   - 爬虫模块 → 新闻模块：原始数据存储
   - 新闻模块 → AI服务：内容分析请求
   - AI服务 → 搜索模块：分析结果索引

2. **服务调用**
   - 认证模块：横向服务，被其他模块调用
   - 监控模块：全局监控，收集各模块数据
   - AI服务：按需提供分析服务

3. **缓存策略**
   - Redis 缓存层
   - 本地缓存
   - 分布式缓存

### 5.3 扩展性设计

1. **模块化原则**
   - 低耦合设计
   - 标准化接口
   - 可插拔组件

2. **性能优化**
   - 异步处理
   - 任务队列
   - 数据库优化

### 5.4 开发环境

1. **Python版本要求**
   - 最低支持: Python 3.8+
   - 推荐版本: Python 3.12
   - 虚拟环境: venv

2. **数据库支持**
   - MySQL 8.0+
   - 搜索引擎: Elasticsearch 7.x+

3. **缓存系统**
   - Redis 5.0+
   - 缓存策略配置
   - 会话存储

4. **部署要求**
   - Linux服务器 (Ubuntu 20.04+ / CentOS 7+)
   - Nginx 1.18+
   - Gunicorn 20.0+
   - Supervisor

### 5.5 安全机制

1. **认证与授权**
   - JWT认证
   - 基于角色的访问控制
   - Session管理
   - API密钥管理

2. **数据安全**
   - 密码加密存储
   - 敏感信息加密
   - HTTPS传输
   - SQL注入防护

3. **访问控制**
   - CORS策略
   - API访问频率限制
   - IP白名单
   - 请求来源验证

4. **日志与审计**
   - 操作日志记录
   - 安全审计
   - 异常监控
   - 入侵检测

### 5.6 接口定义

- **认证接口**
  - POST `/api/auth/login`
  - POST `/api/auth/register`
  - POST `/api/auth/refresh`

- **新闻接口**
  - GET `/api/news/list`
  - GET `/api/news/detail/<id>`
  - POST `/api/news/create`

- **搜索接口**
  - GET `/api/search/news`
  - GET `/api/search/hot`

- **AI分析接口**
  - POST `/api/ai/analyze/<news_id>`
  - GET `/api/ai/result/<news_id>`

- **爬虫管理接口**
  - GET `/api/crawler/config`
  - POST `/api/crawler/start`
  - POST `/api/crawler/stop`

- **监控接口**
  - GET `/api/monitor/status`
  - GET `/api/monitor/metrics`

### 5.7 安全与权限

- **Django REST Framework**：使用 JWT 认证
- **角色权限**：admin/user/guest 三级权限控制
- **敏感信息**：所有密钥和API Key存储在环境变量中 

### 5.8 项目目录结构

```
后端目录结构：
mediasense-backend/
├── mediasense/              # 项目核心配置
│   ├── settings/           # 多环境配置
│   │   ├── base.py        # 基础配置
│   │   ├── development.py # 开发环境配置
│   │   └── production.py  # 生产环境配置
│   ├── middleware/        # 中间件
│   │   ├── rate_limit.py  # 请求频率限制
│   │   └── exception_handler.py # 异常处理
│   ├── urls.py            # 主路由配置
│   └── wsgi.py            # WSGI配置
│
├── api_v1/                 # API模块
│   ├── middleware.py      # API响应格式中间件
│   ├── urls.py           # API路由配置
│   ├── views.py          # API文档视图
│   └── tests.py          # API测试
│
├── custom_auth/            # 认证模块
│   ├── models.py          # 用户模型
│   ├── serializers.py     # 序列化器
│   ├── views.py           # 视图函数
│   └── urls.py            # 路由配置
│
├── news/                   # 新闻管理模块
│   ├── models.py          # 新闻模型
│   ├── services.py        # 业务逻辑
│   ├── views.py           # 视图函数
│   └── urls.py            # 路由配置
│
├── news_search/           # 搜索服务模块
│   ├── models.py          # 搜索相关模型
│   ├── documents.py       # ES文档映射
│   ├── services.py        # 搜索服务
│   └── views.py           # 视图函数
│
├── crawler/               # 爬虫系统模块
│   ├── models.py          # 爬虫配置模型
│   ├── tasks.py           # Celery任务
│   ├── crawlers.py        # 爬虫实现
│   ├── services.py        # 业务逻辑
│   └── task_manager.py    # 任务管理器
│
├── ai_service/            # AI服务模块
│   ├── models.py          # AI分析模型
│   ├── services.py        # AI服务实现
│   ├── tasks.py           # 异步任务
│   └── views.py           # API接口
│
├── monitoring/            # 监控系统模块
│   ├── models.py          # 监控指标模型
│   ├── services.py        # 监控服务
│   └── views.py           # 监控接口
│
├── logs/                  # 日志文件目录
│   ├── django.log         # Django日志
│   ├── celery.log        # Celery日志
│   └── crawler.log       # 爬虫日志
│
├── tests/                 # 测试用例目录
│   ├── test_news.py      # 新闻模块测试
│   ├── test_crawler.py   # 爬虫模块测试
│   └── test_ai.py        # AI服务测试
│
├── docs/                  # 文档目录
│   ├── requirements.md    # 需求文档
│   └── development.md     # 开发文档
│
├── manage.py              # Django管理脚本
├── requirements.txt       # 项目依赖
└── .env                   # 环境变量配置
```

主要目录说明：

1. **核心配置目录** (`mediasense/`)
   - 包含项目的基础配置文件
   - 多环境配置支持
   - 主路由配置

2. **功能模块目录**
   - `custom_auth/`: 用户认证与授权
   - `news/`: 新闻内容管理
   - `news_search/`: 搜索服务实现
   - `crawler/`: 爬虫系统
   - `ai_service/`: AI分析服务
   - `monitoring/`: 系统监控

3. **资源目录**
   - `logs/`: 日志文件存储
   - `tests/`: 测试用例
   - `docs/`: 项目文档

4. **根目录文件**
   - `manage.py`: Django命令行工具
   - `requirements.txt`: 依赖管理
   - `.env`: 环境变量

目录结构特点：

1. **模块化组织**
   - 每个功能模块独立成包
   - 清晰的职责划分
   - 便于维护和扩展

2. **配置分离**
   - 开发和生产环境配置分离
   - 敏感信息通过环境变量管理
   - 多环境部署支持

3. **资源管理**
   - 集中的日志管理
   - 统一的测试用例组织
   - 完整的文档支持 

## 6. 前端开发架构

### 6.1 技术栈选型

1. **核心框架**
   - Vue.js 3.x
   - Vue Router 4.x
   - Pinia 2.x (状态管理)
   - TypeScript 5.x

2. **UI组件库**
   - Element Plus 2.x
   - TailwindCSS 3.x
   - IconPark (图标库)

3. **数据可视化**
   - ECharts 5.x
   - Vue-ECharts
   - D3.js (复杂可视化)

4. **开发工具**
   - Vite 5.x (构建工具)
   - ESLint (代码规范)
   - Prettier (代码格式化)
   - Husky (Git Hooks)

### 6.2 前端项目结构

前端目录结构：
```
mediasense-frontend/
├── .vscode/                # VSCode配置
├── docs/                   # 项目文档
├── public/                 # 静态资源
│   ├── favicon.ico
│   └── images/
├── src/
│   ├── api/               # API接口封装
│   │   ├── auth.ts        # 认证相关接口
│   │   ├── news.ts        # 新闻相关接口
│   │   ├── search.ts      # 搜索相关接口
│   │   ├── monitor.ts     # 监控相关接口
│   │   └── ai.ts          # AI分析相关接口
│   ├── assets/            # 项目资源
│   │   ├── styles/        # 全局样式
│   │   └── images/        # 图片资源
│   ├── components/        # 公共组件
│   │   ├── common/        # 通用组件
│   │   ├── news/          # 新闻相关组件
│   │   ├── charts/        # 图表组件
│   │   ├── layout/        # 布局组件
│   │   └── ai/            # AI相关组件
│   │       ├── AISentimentAnalysis.vue    # 情感分析组件
│   │       ├── AIKeywordsCloud.vue        # 关键词云图组件
│   │       ├── AIEntityTable.vue          # 实体识别表格组件
│   │       ├── AIBatchProgress.vue        # 批量分析进度组件
│   │       └── AIConfigForm.vue           # AI配置表单组件
│   ├── composables/       # 组合式函数
│   │   ├── useAuth.ts     # 认证相关
│   │   ├── useNews.ts     # 新闻相关
│   │   ├── useChart.ts    # 图表相关
│   │   └── useAI.ts       # AI分析相关
│   ├── router/            # 路由配置
│   │   ├── index.ts       # 路由主文件
│   │   └── guards.ts      # 路由守卫
│   ├── stores/            # 状态管理
│   │   ├── auth.ts        # 认证状态
│   │   ├── news.ts        # 新闻状态
│   │   ├── app.ts         # 应用状态
│   │   └── ai.ts          # AI分析状态
│   ├── types/             # TypeScript类型
│   │   ├── api.ts         # API相关类型
│   │   ├── models.ts      # 数据模型类型
│   │   └── ai.ts          # AI相关类型定义
│   ├── utils/             # 工具函数
│   │   ├── request.ts     # axios封装
│   │   ├── auth.ts        # 认证工具
│   │   ├── date.ts        # 日期工具
│   │   └── ai.ts          # AI工具函数
│   ├── views/             # 页面组件
│   │   ├── auth/          # 认证相关页面
│   │   ├── news/          # 新闻相关页面
│   │   ├── search/        # 搜索相关页面
│   │   ├── monitor/       # 监控相关页面
│   │   └── ai/            # AI相关页面
│   │       ├── AIDashboard.vue           # AI分析仪表盘
│   │       ├── Analysis.vue              # 单篇新闻分析
│   │       ├── BatchAnalysis.vue         # 批量新闻分析
│   │       ├── AIConfig.vue              # AI配置管理
│   │       ├── AnalysisHistory.vue       # 分析历史记录
│   │       └── AnalysisComparison.vue    # 分析结果对比
│   ├── App.vue            # 根组件
│   ├── main.ts            # 入口文件
│   ├── style.css          # 全局样式
│   └── vite-env.d.ts      # Vite环境类型声明
├── tests/                 # 测试目录
├── .env                   # 环境变量
├── .env.development       # 开发环境变量
├── .env.production        # 生产环境变量
├── .eslintrc.js          # ESLint配置
├── .gitignore            # Git忽略配置
├── .prettierrc           # Prettier配置
├── auto-imports.d.ts     # 自动导入类型声明
├── components.d.ts       # 组件类型声明
├── index.html            # HTML模板
├── package.json          # 项目配置
├── tsconfig.json         # TypeScript配置
├── tsconfig.app.json     # 应用TypeScript配置
├── tsconfig.node.json    # Node TypeScript配置
├── vitest.config.ts      # Vitest测试配置
├── vitest.setup.ts       # Vitest测试设置
├── vite.config.ts        # Vite配置
└── README.md             # 项目说明
```

### 6.3 功能模块设计

1. **认证模块**
   - 登录/注册页面
   - 用户信息管理
   - 权限控制组件
   - Token管理

2. **新闻管理模块**
   - 新闻列表页
   - 新闻详情页
   - 新闻分类管理
   - 新闻编辑器

3. **搜索模块**
   - 搜索页面
   - 高级搜索组件
   - 搜索结果展示
   - 搜索建议组件

4. **数据可视化模块**
   - 数据仪表板
   - 趋势分析图表
   - 实时监控面板
   - 交互式图表

5. **AI分析模块**
   - 情感分析展示
     * 情感趋势图表
     * 情感分布统计
     * 关键词云图
   - AI分析控制
     * 单篇新闻分析
     * 批量新闻分析
     * 分析进度监控
   - 分析结果管理
     * 历史分析记录
     * 结果对比视图
     * 导出分析报告
   - AI配置管理
     * 模型参数设置
     * API密钥配置
     * 分析规则定制

6. **系统监控模块**
   - 资源监控
     * CPU使用率监控
     * 内存使用监控
     * 磁盘使用监控
     * 网络流量监控
   - 服务监控
     * 爬虫服务状态
     * AI服务状态
     * 数据库服务状态
     * API服务响应时间
   - 告警管理
     * 告警规则配置
     * 告警级别设置
     * 告警通知方式
     * 告警历史记录
   - 性能分析
     * 系统性能报告
     * 性能瓶颈分析
     * 性能优化建议
     * 历史性能趋势
   - 日志管理
     * 实时日志查看
     * 日志级别过滤
     * 日志搜索分析
     * 日志导出功能
   - 监控面板
     * 实时监控大屏
     * 自定义监控视图
     * 监控数据导出
     * 监控报表生成

### 6.4 组件设计规范

1. **基础组件**
```vue
<!-- 示例：BaseButton.vue -->
<template>
  <button
    :class="[
      'base-button',
      `base-button--${type}`,
      { 'base-button--loading': loading }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <slot name="icon"></slot>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
interface Props {
  type?: 'primary' | 'secondary' | 'danger'
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  loading: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const handleClick = (event: MouseEvent) => {
  if (!props.loading && !props.disabled) {
    emit('click', event)
  }
}
</script>
```

2. **业务组件**
```vue
<!-- 示例：NewsCard.vue -->
<template>
  <div class="news-card">
    <div class="news-card__header">
      <h3 class="news-card__title">{{ title }}</h3>
      <span class="news-card__date">{{ formatDate(publishDate) }}</span>
    </div>
    <p class="news-card__summary">{{ summary }}</p>
    <div class="news-card__footer">
      <span class="news-card__source">{{ source }}</span>
      <base-button @click="handleReadMore">阅读更多</base-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '@/utils/date'
import BaseButton from '@/components/common/BaseButton.vue'

interface Props {
  id: string
  title: string
  summary: string
  source: string
  publishDate: string
}

defineProps<Props>()
const emit = defineEmits<{
  (e: 'read-more', id: string): void
}>()

const handleReadMore = () => {
  emit('read-more', props.id)
}
</script>
```

3. **AI组件**
```vue
<!-- 示例：AISentimentAnalysis.vue -->
<template>
  <div class="ai-sentiment-analysis">
    <div class="analysis-header">
      <h3>{{ title }}</h3>
      <el-tag :type="sentimentType">{{ sentimentLabel }}</el-tag>
    </div>
    
    <div class="analysis-content">
      <div class="sentiment-chart">
        <echarts :option="chartOption" height="300px" />
      </div>
      
      <div class="keywords-cloud">
        <word-cloud :words="keywords" />
      </div>
      
      <div class="named-entities">
        <el-table :data="entities" stripe>
          <el-table-column prop="text" label="实体" />
          <el-table-column prop="type" label="类型" />
          <el-table-column prop="confidence" label="置信度">
            <template #default="{ row }">
              <el-progress :percentage="row.confidence * 100" />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <div class="analysis-actions">
      <el-button @click="handleReAnalyze" :loading="analyzing">
        重新分析
      </el-button>
      <el-button @click="handleExport" type="primary">
        导出报告
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AnalysisResult } from '@/types/ai'
import { useAIStore } from '@/stores/ai'
import WordCloud from './WordCloud.vue'

interface Props {
  newsId: string
  title: string
  result?: AnalysisResult
}

const props = defineProps<Props>()
const aiStore = useAIStore()
const analyzing = ref(false)

const sentimentType = computed(() => {
  switch (props.result?.sentiment) {
    case 'positive': return 'success'
    case 'negative': return 'danger'
    default: return 'info'
  }
})

const sentimentLabel = computed(() => {
  const labels = {
    positive: '正面',
    negative: '负面',
    neutral: '中性'
  }
  return labels[props.result?.sentiment || 'neutral']
})

const chartOption = computed(() => ({
  // ECharts配置...
}))

const handleReAnalyze = async () => {
  analyzing.value = true
  try {
    await aiStore.analyzeNews(props.newsId)
  } finally {
    analyzing.value = false
  }
}

const handleExport = () => {
  // 导出逻辑...
}
</script>
```

### 6.5 状态管理

1. **Pinia Store设计**
```typescript
// stores/news.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { News, NewsFilter } from '@/types/models'
import { fetchNewsList, fetchNewsDetail } from '@/api/news'

export const useNewsStore = defineStore('news', () => {
  // 状态
  const newsList = ref<News[]>([])
  const currentNews = ref<News | null>(null)
  const loading = ref(false)
  const filter = ref<NewsFilter>({
    category: '',
    source: '',
    dateRange: null
  })

  // 计算属性
  const categorizedNews = computed(() => {
    return newsList.value.reduce((acc, news) => {
      const category = news.category || '未分类'
      if (!acc[category]) acc[category] = []
      acc[category].push(news)
      return acc
    }, {} as Record<string, News[]>)
  })

  // 动作
  const fetchNews = async (params?: Partial<NewsFilter>) => {
    loading.value = true
    try {
      const data = await fetchNewsList(params)
      newsList.value = data
    } finally {
      loading.value = false
    }
  }

  const fetchDetail = async (id: string) => {
    loading.value = true
    try {
      currentNews.value = await fetchNewsDetail(id)
    } finally {
      loading.value = false
    }
  }

  return {
    newsList,
    currentNews,
    loading,
    filter,
    categorizedNews,
    fetchNews,
    fetchDetail
  }
})
```

2. **AI Store设计**
```typescript
// stores/ai.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AnalysisResult, AIConfig } from '@/types/ai'
import { 
  analyzeNewsContent, 
  fetchAnalysisHistory,
  updateAIConfig 
} from '@/api/ai'

export const useAIStore = defineStore('ai', () => {
  // 状态
  const analysisResults = ref<Record<string, AnalysisResult>>({})
  const analysisQueue = ref<string[]>([])
  const loading = ref(false)
  const config = ref<AIConfig>({
    model: 'gpt-4',
    language: 'zh',
    confidenceThreshold: 0.8
  })

  // 计算属性
  const pendingAnalysis = computed(() => analysisQueue.value.length)
  
  const getResult = computed(() => (newsId: string) => {
    return analysisResults.value[newsId]
  })

  // 动作
  const analyzeNews = async (newsId: string) => {
    loading.value = true
    try {
      const result = await analyzeNewsContent(newsId)
      analysisResults.value[newsId] = result
    } finally {
      loading.value = false
    }
  }

  const batchAnalyze = async (newsIds: string[]) => {
    analysisQueue.value.push(...newsIds)
    for (const id of newsIds) {
      await analyzeNews(id)
      analysisQueue.value = analysisQueue.value.filter(qid => qid !== id)
    }
  }

  const loadHistory = async (newsId: string) => {
    const history = await fetchAnalysisHistory(newsId)
    analysisResults.value[newsId] = history
  }

  const updateConfig = async (newConfig: Partial<AIConfig>) => {
    Object.assign(config.value, newConfig)
    await updateAIConfig(config.value)
  }

  return {
    analysisResults,
    analysisQueue,
    loading,
    config,
    pendingAnalysis,
    getResult,
    analyzeNews,
    batchAnalyze,
    loadHistory,
    updateConfig
  }
})
```

### 6.6 路由配置

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/Home.vue')
      },
      {
        path: 'news',
        name: 'news-list',
        component: () => import('@/views/news/NewsList.vue')
      },
      {
        path: 'news/:id',
        name: 'news-detail',
        component: () => import('@/views/news/NewsDetail.vue')
      },
      {
        path: 'search',
        name: 'search',
        component: () => import('@/views/search/Search.vue')
      },
      {
        path: 'monitor',
        name: 'monitor',
        component: () => import('@/views/monitor/Monitor.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'ai',
        name: 'ai-dashboard',
        component: () => import('@/views/ai/AIDashboard.vue'),
        meta: { requiresAuth: true },
        children: [
          {
            path: 'analysis/:id',
            name: 'ai-analysis',
            component: () => import('@/views/ai/Analysis.vue')
          },
          {
            path: 'batch',
            name: 'ai-batch',
            component: () => import('@/views/ai/BatchAnalysis.vue')
          },
          {
            path: 'config',
            name: 'ai-config',
            component: () => import('@/views/ai/AIConfig.vue')
          }
        ]
      }
    ]
  },
  {
    path: '/auth',
    component: () => import('@/views/layout/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/Login.vue')
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/Register.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
```

### 6.7 API请求封装

```typescript
// utils/request.ts
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    if (data.status === 'success') {
      return data.data
    } else {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
  },
  (error) => {
    const { response } = error
    let message = '网络错误'
    if (response?.data?.message) {
      message = response.data.message
    }
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service
```

### 6.8 开发规范

1. **代码风格**
   - 使用TypeScript编写
   - 遵循ESLint规则
   - 使用Prettier格式化
   - 组件使用PascalCase命名

2. **提交规范**
   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式
   - refactor: 重构
   - test: 测试
   - chore: 构建过程或辅助工具的变动

3. **注释规范**
   - 组件必须包含功能说明
   - 复杂逻辑需要详细注释
   - API方法需要类型注释
   - 保持注释的及时更新

### 6.9 构建与部署

1. **开发环境**
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

2. **生产环境**
```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

3. **环境变量配置**
```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000/api

# .env.production
VITE_API_BASE_URL=http://api.mediasense.com/api
```

4. **Docker部署**
```dockerfile
# Dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
``` 