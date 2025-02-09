<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <el-aside class="sidebar" :width="isCollapse ? '64px' : '200px'">
      <div class="logo-container">
        <img v-if="!isCollapse" src="@/assets/logo.png" alt="Logo" class="logo">
        <el-icon class="collapse-icon" @click="toggleCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        :collapse="isCollapse"
        @select="handleSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Monitor /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/monitor">
          <el-icon><DataLine /></el-icon>
          <template #title>系统监控</template>
        </el-menu-item>
        
        <el-sub-menu index="/crawler">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>爬虫管理</span>
          </template>
          <el-menu-item index="/crawler/list">任务列表</el-menu-item>
          <el-menu-item index="/crawler/data">数据管理</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/alerts">
          <el-icon><Warning /></el-icon>
          <template #title>告警管理</template>
        </el-menu-item>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-tooltip content="全屏" placement="bottom">
            <el-icon class="header-icon" @click="toggleFullscreen">
              <FullScreen v-if="!isFullscreen" />
              <Aim v-else />
            </el-icon>
          </el-tooltip>
          
          <el-tooltip content="消息" placement="bottom">
            <el-badge :value="unreadCount" :max="99" class="header-badge">
              <el-icon class="header-icon"><Bell /></el-icon>
            </el-badge>
          </el-tooltip>
          
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="userAvatar" />
              <span class="username">{{ username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="settings">账号设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessageBox } from 'element-plus'
import {
  Monitor,
  DataLine,
  Warning,
  Setting,
  Bell,
  FullScreen,
  Aim,
  Fold,
  Expand,
  Connection
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isCollapse = ref(false)
const isFullscreen = ref(false)
const unreadCount = ref(0)

// 计算属性
const activeMenu = computed(() => route.path)
const username = computed(() => authStore.user?.username || '未登录')
const userAvatar = computed(() => authStore.user?.avatar || '')

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    title: item.meta.title,
    path: item.path
  }))
})

// 事件处理
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const handleSelect = (index: string) => {
  router.push(index)
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗?', '提示', {
          type: 'warning'
        })
        await authStore.logout()
        router.push('/auth/login')
      } catch {
        // 用户取消操作
      }
      break
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  display: flex;
}

.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #1f2d3d;
}

.logo {
  height: 32px;
}

.collapse-icon {
  color: #fff;
  cursor: pointer;
  font-size: 20px;
}

.sidebar-menu {
  border-right: none;
  background-color: transparent;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 20px;
  color: #606266;
  cursor: pointer;
}

.header-badge {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  color: #606266;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu-item) {
  &.is-active {
    background-color: #1f2d3d;
  }
  
  &:hover {
    background-color: #1f2d3d;
  }
}
</style> 