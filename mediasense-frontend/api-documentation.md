# MediaSense API 文档

## 基本信息

- 基础URL: `http://backend.mediasense.com/api`
- 认证方式: Bearer Token (JWT)
- 默认响应格式: JSON
超级管理员用户名： admin     密码：admin@123456

## 认证模块 (auth)

### 获取Token
- 端点: `POST /auth/token`
- 描述: 获取访问令牌和刷新令牌
- 请求体:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- 响应:
  ```json
  {
    "access": "string",
    "refresh": "string"
  }
  ```

### 刷新Token
- 端点: `POST /auth/token/refresh`
- 描述: 使用刷新令牌获取新的访问令牌
- 请求体:
  ```json
  {
    "refresh": "string"
  }
  ```
- 响应:
  ```json
  {
    "access": "string"
  }
  ```

### 验证Token
- 端点: `POST /auth/token/verify`
- 描述: 验证访问令牌是否有效
- 请求体:
  ```json
  {
    "token": "string"
  }
  ```

### 用户管理
- 获取个人信息: `GET /auth/me`
- 获取/更新个人信息: `GET/PUT /auth/profile`
- 修改密码: `POST /auth/password/change`
- 重置密码: `POST /auth/password/reset`
- 用户注册: `POST /auth/register`
- 会话信息: `GET /auth/session-info`
- 注销: `POST /auth/logout`
- 权限检查: `POST /auth/check-permission`
- 角色列表: `GET /auth/roles`
- 角色详情: `GET/PUT/DELETE /auth/roles/{id}`
- 权限列表: `GET /auth/permissions`

## 新闻模块 (news)

### 新闻文章管理
- 获取新闻列表: `GET /news/news-articles`
- 获取新闻详情: `GET /news/news-articles/{id}`
- 创建新闻: `POST /news/news-articles`
- 更新新闻: `PUT /news/news-articles/{id}`
- 删除新闻: `DELETE /news/news-articles/{id}`
- 批量创建: `POST /news/news-articles/bulk-create`
- 批量更新: `PUT /news/news-articles/bulk-update`
- 批量删除: `POST /news/news-articles/bulk-delete`

### 新闻分类管理
- 获取分类列表: `GET /news/categories`
- 获取分类详情: `GET /news/categories/{id}`
- 创建分类: `POST /news/categories`
- 更新分类: `PUT /news/categories/{id}`
- 删除分类: `DELETE /news/categories/{id}`
- 批量创建: `POST /news/categories/bulk-create`
- 批量更新: `PUT /news/categories/bulk-update`
- 批量删除: `POST /news/categories/bulk-delete`

## 爬虫模块 (crawler)

### 爬虫配置
- 获取配置列表: `GET /crawler/configs`
- 创建配置: `POST /crawler/configs`
- 更新配置: `PUT /crawler/configs/{id}`
- 删除配置: `DELETE /crawler/configs/{id}`
- 启用配置: `POST /crawler/configs/{id}/enable`
- 禁用配置: `POST /crawler/configs/{id}/disable`
- 测试配置: `POST /crawler/configs/{id}/test`
- 批量创建: `POST /crawler/configs/bulk-create`
- 批量更新: `PUT /crawler/configs/bulk-update`
- 批量删除: `POST /crawler/configs/bulk-delete`
- 获取统计信息: `GET /crawler/configs/stats`

### 爬虫任务
- 获取任务列表: `GET /crawler/tasks`
- 创建任务: `POST /crawler/tasks`
- 更新任务: `PUT /crawler/tasks/{id}`
- 删除任务: `DELETE /crawler/tasks/{id}`
- 重试任务: `POST /crawler/tasks/{id}/retry`
- 批量创建: `POST /crawler/tasks/bulk-create`
- 批量更新: `PUT /crawler/tasks/bulk-update`
- 批量删除: `POST /crawler/tasks/bulk-delete`
- 获取统计信息: `GET /crawler/tasks/stats`

## 搜索模块 (search)

### 新闻搜索
- 端点: `GET /search`
- 参数:
  - q: 搜索关键词
  - page: 页码 (默认: 1)
  - size: 每页数量 (默认: 10)
  - sort: 排序方式 (relevance/date)
  - start_date: 开始日期 (YYYY-MM-DD)
  - end_date: 结束日期 (YYYY-MM-DD)
  - source: 来源
  - category: 分类ID

## AI服务模块 (ai)

### 可用服务
- 获取服务列表: `GET /ai/services`
- 文本分析: `POST /ai/services/text-analysis`
- 新闻分类: `POST /ai/services/classification`
- 内容生成: `POST /ai/services/generation`

## 监控模块 (monitoring)

### 系统指标
- 获取系统指标: `GET /monitoring/system-metrics`
- 获取系统状态: `GET /monitoring/system-status`

### 告警规则
- 获取规则列表: `GET /monitoring/alert-rules`
- 创建规则: `POST /monitoring/alert-rules`
- 更新规则: `PUT /monitoring/alert-rules/{id}`
- 删除规则: `DELETE /monitoring/alert-rules/{id}`
- 启用规则: `POST /monitoring/alert-rules/{id}/enable`
- 禁用规则: `POST /monitoring/alert-rules/{id}/disable`

### 告警历史
- 获取告警历史: `GET /monitoring/alert-history`
- 获取告警详情: `GET /monitoring/alert-history/{id}`
- 确认告警: `POST /monitoring/alert-history/{id}/acknowledge`
- 解决告警: `POST /monitoring/alert-history/{id}/resolve`

### 可视化
- 获取可视化列表: `GET /monitoring/visualizations`
- 创建可视化: `POST /monitoring/visualizations`
- 更新可视化: `PUT /monitoring/visualizations/{id}`
- 删除可视化: `DELETE /monitoring/visualizations/{id}`

### 仪表板
- 获取仪表板列表: `GET /monitoring/dashboards`
- 创建仪表板: `POST /monitoring/dashboards`
- 更新仪表板: `PUT /monitoring/dashboards/{id}`
- 删除仪表板: `DELETE /monitoring/dashboards/{id}`

### 仪表板组件
- 获取组件列表: `GET /monitoring/dashboard-widgets`
- 创建组件: `POST /monitoring/dashboard-widgets`
- 更新组件: `PUT /monitoring/dashboard-widgets/{id}`
- 删除组件: `DELETE /monitoring/dashboard-widgets/{id}`

### 告警通知配置
- 获取配置列表: `GET /monitoring/alert-notification-config`
- 创建配置: `POST /monitoring/alert-notification-config`
- 更新配置: `PUT /monitoring/alert-notification-config/{id}`
- 删除配置: `DELETE /monitoring/alert-notification-config/{id}`

## 错误处理

所有API端点在发生错误时都会返回统一格式的错误响应：

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

常见错误代码：
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 429: 请求过于频繁
- 500: 服务器内部错误

## 分页

支持分页的API端点将返回以下格式的响应：

```json
{
  "count": "integer",
  "next": "string",
  "previous": "string",
  "results": []
}
```

## 版本控制

API使用URL中的版本号进行版本控制，当前版本为v1。未来的版本更新将通过递增版本号（如v2、v3等）来实现。 