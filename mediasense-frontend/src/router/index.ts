import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layout/MainLayout.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/auth',
    children: [
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/components/auth/Login.vue'),
        meta: { title: '登录' }
      }
    ]
  },
  {
    path: '/',
    component: MainLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '仪表盘', requiresAuth: true }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/monitor/Monitor.vue'),
        meta: { title: '系统监控', requiresAuth: true }
      },
      {
        path: 'alerts',
        name: 'Alerts',
        component: () => import('@/views/alerts/Alerts.vue'),
        meta: { title: '告警管理', requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '系统设置', requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Profile.vue'),
        meta: { title: '个人信息', requiresAuth: true }
      },
      {
        path: 'crawler',
        name: 'Crawler',
        redirect: '/crawler/list',
        meta: { title: '爬虫管理', requiresAuth: true },
        children: [
          {
            path: 'list',
            name: 'CrawlerList',
            component: () => import('@/views/crawler/CrawlerList.vue'),
            meta: { title: '任务列表', requiresAuth: true }
          },
          {
            path: 'config/:id?',
            name: 'CrawlerConfig',
            component: () => import('@/views/crawler/CrawlerConfig.vue'),
            meta: { title: '爬虫配置', requiresAuth: true }
          },
          {
            path: 'data',
            name: 'CrawlerData',
            component: () => import('@/views/crawler/CrawlerData.vue'),
            meta: { title: '数据管理', requiresAuth: true }
          }
        ]
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 设置页面标题
  document.title = `${to.meta.title} - MediaSense监控平台`
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // 需要认证但未登录,跳转到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    // 已登录时访问登录页,跳转到首页
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router 