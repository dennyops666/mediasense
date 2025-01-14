import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/index.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'dashboard' }
      }
    ]
  },
  {
    path: '/monitor',
    component: Layout,
    children: [
      {
        path: 'system',
        name: 'SystemMonitor',
        component: () => import('@/views/SystemMonitor.vue'),
        meta: { 
          title: '系统监控',
          icon: 'monitor',
          roles: ['admin']  // 只允许管理员访问
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 