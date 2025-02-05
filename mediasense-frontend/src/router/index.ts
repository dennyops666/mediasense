import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'news',
        name: 'news-list',
        component: () => import('@/views/news/NewsList.vue'),
        meta: { title: '新闻列表' }
      },
      {
        path: 'news/:id',
        name: 'news-detail',
        component: () => import('@/views/news/NewsDetail.vue'),
        meta: { title: '新闻详情' }
      },
      {
        path: 'search',
        name: 'search',
        component: () => import('@/views/search/Search.vue'),
        meta: { title: '新闻搜索' }
      },
      {
        path: 'monitor',
        name: 'monitor',
        component: () => import('@/views/monitor/Monitor.vue'),
        meta: { 
          title: '系统监控',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: '/ai',
        component: () => import('@/views/layout/MainLayout.vue'),
        meta: { requiresAuth: true },
        children: [
          {
            path: '',
            name: 'AIAnalysis',
            component: () => import('@/views/ai/AIAnalysis.vue'),
            meta: {
              title: 'AI 分析',
              icon: 'brain'
            }
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
        component: () => import('@/views/auth/Login.vue'),
        meta: { title: '登录' }
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/Register.vue'),
        meta: { title: '注册' }
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
  
  // 设置页面标题
  document.title = `${to.meta.title} - MediaSense`

  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    next({ 
      name: 'login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    ElMessage.error('需要管理员权限')
    next({ name: 'home' })
    return
  }

  next()
})

export default router 