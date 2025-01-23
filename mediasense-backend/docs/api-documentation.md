# MediaSense 后端 API 文档

## 目录
1. [认证模块 API](#1-认证模块-api)
2. [新闻模块 API](#2-新闻模块-api)
3. [监控模块 API](#3-监控模块-api)
4. [爬虫模块 API](#4-爬虫模块-api)
5. [搜索模块 API](#5-搜索模块-api)
6. [AI服务模块 API](#6-ai服务模块-api)

## 1. 认证模块 API

基础路径: `/v1/auth/*`

### 1.1 用户认证

#### 获取令牌
- **路径**: `POST /v1/auth/token/`
- **功能**: 用户登录获取JWT令牌
- **请求体**: 
  ```json
  {
      "username": "string",
      "password": "string"
  }
  ```
- **响应**: 
  ```json
  {
      "access": "string",
      "refresh": "string"
  }
  ```

#### 刷新令牌
- **路径**: `POST /v1/auth/token/refresh/`
- **功能**: 使用refresh token获取新的access token
- **请求体**:
  ```json
  {
      "refresh": "string"
  }
  ```

#### 验证令牌
- **路径**: `POST /v1/auth/token/verify/`
- **功能**: 验证token是否有效
- **请求体**:
  ```json
  {
      "token": "string"
  }
  ```

### 1.2 用户管理

#### 获取当前用户信息
- **路径**: `GET /v1/auth/me/`
- **功能**: 获取当前登录用户的详细信息
- **需要认证**: 是

#### 用户CRUD操作
- **列表**: `GET /v1/auth/users/`
- **详情**: `GET /v1/auth/users/{id}/`
- **创建**: `POST /v1/auth/users/`
- **更新**: `PUT/PATCH /v1/auth/users/{id}/`
- **删除**: `DELETE /v1/auth/users/{id}/`

## 2. 新闻模块 API

基础路径: `/v1/news/*`

### 2.1 新闻文章管理

#### 新闻文章CRUD操作
- **列表**: `GET /v1/news/news-articles/`
- **详情**: `GET /v1/news/news-articles/{id}/`
- **创建**: `POST /v1/news/news-articles/`
- **更新**: `PUT/PATCH /v1/news/news-articles/{id}/`
- **删除**: `DELETE /v1/news/news-articles/{id}/`

#### 批量操作
- **批量更新**: `PUT /v1/news/news-articles/bulk-update/`
- **批量删除**: `POST /v1/news/news-articles/bulk-delete/`

### 2.2 新闻分类管理

#### 分类CRUD操作
- **列表**: `GET /v1/news/categories/`
- **详情**: `GET /v1/news/categories/{id}/`
- **创建**: `POST /v1/news/categories/`
- **更新**: `PUT/PATCH /v1/news/categories/{id}/`
- **删除**: `DELETE /v1/news/categories/{id}/`

## 3. 监控模块 API

基础路径: `/v1/monitoring/*`

### 3.1 系统状态

#### 系统概览
- **路径**: `GET /v1/monitoring/system-status/overview/`
- **功能**: 获取系统整体运行状态
- **响应**: 包含CPU、内存、磁盘使用率等信息

#### 健康检查
- **路径**: `GET /v1/monitoring/system-status/health/`
- **功能**: 获取系统健康状态
- **响应**: 包含各个服务的健康状态

#### 性能指标
- **路径**: `GET /v1/monitoring/system-status/performance/`
- **功能**: 获取系统性能指标
- **响应**: 包含响应时间、吞吐量等性能数据

### 3.2 系统指标

#### 指标管理
- **列表**: `GET /v1/monitoring/system-metrics/`
- **详情**: `GET /v1/monitoring/system-metrics/{id}/`
- **创建**: `POST /v1/monitoring/system-metrics/`
- **更新**: `PUT/PATCH /v1/monitoring/system-metrics/{id}/`
- **删除**: `DELETE /v1/monitoring/system-metrics/{id}/`

#### 指标数据
- **历史数据**: `GET /v1/monitoring/system-metrics/{id}/history/`
- **实时数据**: `GET /v1/monitoring/system-metrics/{id}/realtime/`
- **统计数据**: `GET /v1/monitoring/system-metrics/{id}/statistics/`

### 3.3 告警管理

#### 告警规则CRUD
- **列表**: `GET /v1/monitoring/alert-rules/`
- **详情**: `GET /v1/monitoring/alert-rules/{id}/`
- **创建**: `POST /v1/monitoring/alert-rules/`
- **更新**: `PUT/PATCH /v1/monitoring/alert-rules/{id}/`
- **删除**: `DELETE /v1/monitoring/alert-rules/{id}/`

#### 告警规则操作
- **启用**: `POST /v1/monitoring/alert-rules/{id}/enable/`
- **禁用**: `POST /v1/monitoring/alert-rules/{id}/disable/`

### 3.4 告警历史

#### 告警历史CRUD
- **列表**: `GET /v1/monitoring/alert-history/`
- **详情**: `GET /v1/monitoring/alert-history/{id}/`

#### 告警处理
- **通知**: `POST /v1/monitoring/alert-history/{id}/notify/`
- **确认**: `POST /v1/monitoring/alert-history/{id}/acknowledge/`
- **解决**: `POST /v1/monitoring/alert-history/{id}/resolve/`

### 3.5 错误日志

#### 错误日志管理
- **列表**: `GET /v1/monitoring/error-logs/`
- **统计**: `GET /v1/monitoring/error-logs/statistics/`

### 3.6 可视化

#### 可视化管理
- **列表**: `GET /v1/monitoring/visualization/`
- **详情**: `GET /v1/monitoring/visualization/{id}/`
- **创建**: `POST /v1/monitoring/visualization/`
- **更新**: `PUT/PATCH /v1/monitoring/visualization/{id}/`
- **删除**: `DELETE /v1/monitoring/visualization/{id}/`

#### 可视化数据
- **获取数据**: `GET /v1/monitoring/visualization/{id}/data/`
- **导出数据**: `GET /v1/monitoring/visualization/{id}/export/`
- **刷新数据**: `POST /v1/monitoring/visualization/{id}/refresh/`

## 4. 爬虫模块 API

基础路径: `/v1/crawler/*`

### 4.1 爬虫配置

#### 配置CRUD操作
- **列表**: `GET /v1/crawler/configs/`
- **详情**: `GET /v1/crawler/configs/{id}/`
- **创建**: `POST /v1/crawler/configs/`
- **更新**: `PUT/PATCH /v1/crawler/configs/{id}/`
- **删除**: `DELETE /v1/crawler/configs/{id}/`

#### 配置操作
- **启用**: `POST /v1/crawler/configs/{id}/enable/`
- **禁用**: `POST /v1/crawler/configs/{id}/disable/`
- **测试**: `POST /v1/crawler/configs/{id}/test/`

### 4.2 爬虫任务

#### 任务管理
- **列表**: `GET /v1/crawler/tasks/`
- **详情**: `GET /v1/crawler/tasks/{id}/`
- **重试**: `POST /v1/crawler/tasks/{id}/retry/`

## 5. 搜索模块 API

基础路径: `/v1/search/*`

### 5.1 新闻搜索

#### 搜索功能
- **搜索**: `GET /v1/search/search/`
  - 基础参数：
    - `q`: 搜索关键词
    - `page`: 页码
    - `size`: 每页大小
  - 高级参数：
    - `sort`: 排序字段（relevance/date/title）
    - `order`: 排序方向（asc/desc）
    - `category`: 新闻分类ID
    - `start_date`: 起始日期（YYYY-MM-DD）
    - `end_date`: 结束日期（YYYY-MM-DD）
    - `source`: 新闻来源
    - `highlight`: 是否高亮关键词（true/false）
    - `fields`: 搜索字段（title/content/all）
    - `operator`: 关键词匹配方式（and/or）
    - `min_score`: 最小相关度分数

- **建议**: `GET /v1/search/suggest/`
  - 参数：
    - `q`: 输入前缀
    - `size`: 返回建议数量
    - `type`: 建议类型（title/content/all）
    - `category`: 限定分类
    - `fuzzy`: 是否启用模糊匹配

### 5.2 搜索历史

#### 历史记录
- **列表**: `GET /v1/search/history/`
  - 参数：
    - `page`: 页码
    - `size`: 每页大小
    - `start_date`: 起始日期
    - `end_date`: 结束日期
- **删除**: `DELETE /v1/search/history/{id}/`
- **清空**: `DELETE /v1/search/history/clear/`

#### 热门搜索
- **获取热门**: `GET /v1/search/trending/`
  - 参数：
    - `period`: 统计周期（hour/day/week/month）
    - `size`: 返回数量
    - `category`: 限定分类
- **相关搜索**: `GET /v1/search/related/`
  - 参数：
    - `q`: 当前搜索词
    - `size`: 返回数量

## 6. AI服务模块 API

基础路径: `/v1/ai/*`

### 6.1 AI服务

#### 基础服务
- **列表**: `GET /v1/ai/ai/`
- **详情**: `GET /v1/ai/ai/{id}/`
- **分析**: `POST /v1/ai/ai/{id}/analyze/`

### 6.2 分析规则

#### 规则管理
- **列表**: `GET /v1/ai/rules/`
- **详情**: `GET /v1/ai/rules/{id}/`
- **创建**: `POST /v1/ai/rules/`
- **更新**: `PUT/PATCH /v1/ai/rules/{id}/`
- **删除**: `DELETE /v1/ai/rules/{id}/`

#### 规则操作
- **启用**: `POST /v1/ai/rules/{id}/enable/`
- **禁用**: `POST /v1/ai/rules/{id}/disable/`
- **验证**: `POST /v1/ai/rules/{id}/validate/`

### 6.3 批量分析任务

#### 任务管理
- **列表**: `GET /v1/ai/batch-tasks/`
- **详情**: `GET /v1/ai/batch-tasks/{id}/`
- **创建**: `POST /v1/ai/batch-tasks/`
- **更新**: `PUT/PATCH /v1/ai/batch-tasks/{id}/`
- **删除**: `DELETE /v1/ai/batch-tasks/{id}/`

#### 任务控制
- **启动**: `POST /v1/ai/batch-tasks/{id}/start/`
- **暂停**: `POST /v1/ai/batch-tasks/{id}/pause/`
- **恢复**: `POST /v1/ai/batch-tasks/{id}/resume/`
- **取消**: `POST /v1/ai/batch-tasks/{id}/cancel/`
- **状态**: `GET /v1/ai/batch-tasks/{id}/status/`
- **进度**: `GET /v1/ai/batch-tasks/{id}/progress/`

### 6.4 分析调度

#### 调度管理
- **列表**: `GET /v1/ai/schedules/`
- **详情**: `GET /v1/ai/schedules/{id}/`
- **创建**: `POST /v1/ai/schedules/`
- **更新**: `PUT/PATCH /v1/ai/schedules/{id}/`
- **删除**: `DELETE /v1/ai/schedules/{id}/`

#### 调度控制
- **启用**: `POST /v1/ai/schedules/{id}/enable/`
- **禁用**: `POST /v1/ai/schedules/{id}/disable/`
- **立即执行**: `POST /v1/ai/schedules/{id}/run-now/`
- **下次执行时间**: `GET /v1/ai/schedules/{id}/next-run/`

### 6.5 调度执行记录

#### 执行记录
- **列表**: `GET /v1/ai/executions/`
- **详情**: `GET /v1/ai/executions/{id}/`
- **日志**: `GET /v1/ai/executions/{id}/logs/`
- **结果**: `GET /v1/ai/executions/{id}/results/`

### 6.6 通知管理

#### 通知
- **列表**: `GET /v1/ai/notifications/`
- **详情**: `GET /v1/ai/notifications/{id}/`
- **标记已读**: `POST /v1/ai/notifications/{id}/mark-read/`
- **全部已读**: `POST /v1/ai/notifications/mark-all-read/`

#### 通知订阅设置
- **列表**: `GET /v1/ai/notification-settings/`
- **详情**: `GET /v1/ai/notification-settings/{id}/`
- **创建**: `POST /v1/ai/notification-settings/`
- **更新**: `PUT/PATCH /v1/ai/notification-settings/{id}/`
- **删除**: `DELETE /v1/ai/notification-settings/{id}/`
- **测试**: `POST /v1/ai/notification-settings/{id}/test/`

### 6.7 可视化

#### 可视化管理
- **列表**: `GET /v1/ai/visualizations/`
- **详情**: `GET /v1/ai/visualizations/{id}/`
- **创建**: `POST /v1/ai/visualizations/`
- **更新**: `PUT/PATCH /v1/ai/visualizations/{id}/`
- **删除**: `DELETE /v1/ai/visualizations/{id}/`

#### 数据操作
- **获取数据**: `GET /v1/ai/visualizations/{id}/data/`
- **导出数据**: `GET /v1/ai/visualizations/{id}/export/`
- **数据统计**: `GET /v1/ai/visualizations/{id}/statistics/`
- **刷新数据**: `POST /v1/ai/visualizations/{id}/refresh/`

## 通用说明

1. **认证要求**
   - 除了登录相关的接口外，所有接口都需要在请求头中携带JWT token
   - Token格式: `Authorization: Bearer <access_token>`

2. **响应格式**
   - 所有接口返回JSON格式数据
   - 标准响应结构：
     ```json
     {
         "code": 200,
         "message": "success",
         "data": {}
     }
     ```

3. **错误处理**
   - 4xx错误表示客户端错误
   - 5xx错误表示服务器错误
   - 错误响应格式：
     ```json
     {
         "code": 400,
         "message": "错误信息",
         "errors": []
     }
     ```

4. **分页**
   - 支持分页的接口使用以下查询参数：
     - `page`: 页码，默认1
     - `size`: 每页大小，默认10
   - 分页响应格式：
     ```json
     {
         "code": 200,
         "message": "success",
         "data": {
             "items": [],
             "total": 0,
             "page": 1,
             "size": 10,
             "pages": 1
         }
     }
     ``` 