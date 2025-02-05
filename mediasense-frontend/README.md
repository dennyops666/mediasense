# MediaSense 前端项目

MediaSense 是一个智能新闻聚合与舆情监控平台的前端项目。

## 功能特点

- 多源新闻聚合
  - 支持多家媒体平台的新闻聚合
  - 新闻分类和标签管理
  - 新闻详情展示

- 智能搜索分析
  - 多维度新闻搜索
  - 搜索结果聚合分析
  - 热门搜索推荐

- 舆情监控
  - 系统性能监控
  - 爬虫任务管理
  - 数据趋势分析

## 技术栈

- Vue 3.5
- TypeScript
- Vite 6.0
- Element Plus
- Pinia
- Vue Router
- ECharts
- Axios

## 开发环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0

## 项目设置

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 项目结构

```
mediasense-frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口封装
│   ├── assets/            # 项目资源
│   ├── components/        # 公共组件
│   ├── composables/       # 组合式函数
│   ├── router/            # 路由配置
│   ├── stores/            # 状态管理
│   ├── types/             # TypeScript类型
│   ├── utils/             # 工具函数
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── .env.development       # 开发环境配置
├── .env.production        # 生产环境配置
├── index.html             # HTML模板
└── package.json           # 项目配置
```

## 开发规范

- 使用 ESLint 进行代码规范检查
- 使用 Prettier 进行代码格式化
- 使用 Husky 进行 Git 提交检查

## 部署说明

1. 构建项目
```bash
npm run build
```

2. 将 `dist` 目录下的文件部署到 Web 服务器

3. 配置 Web 服务器
   - 启用 HTTPS
   - 配置 API 反向代理
   - 设置适当的缓存策略

## 环境变量

- `VITE_API_BASE_URL`: API 服务器地址
  - 开发环境: `http://localhost:8000/api`
  - 生产环境: `http://api.mediasense.com/api`

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)
