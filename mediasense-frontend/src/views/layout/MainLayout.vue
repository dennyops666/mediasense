<template>
  <el-container class="main-layout">
    <el-header height="60px">
      <div class="header-content">
        <div class="logo">
          <router-link to="/">MediaSense</router-link>
        </div>
        <el-menu
          mode="horizontal"
          :router="true"
          :default-active="route.path"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/news">新闻列表</el-menu-item>
          <el-menu-item index="/search">新闻搜索</el-menu-item>
          <el-menu-item v-if="isAdmin" index="/monitor">系统监控</el-menu-item>
        </el-menu>
        <div class="user-actions">
          <template v-if="isAuthenticated">
            <el-dropdown>
              <span class="user-info">
                {{ user?.username }}
                <el-icon><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/auth/login">
              <el-button>登录</el-button>
            </router-link>
            <router-link to="/auth/register">
              <el-button type="primary">注册</el-button>
            </router-link>
          </template>
        </div>
      </div>
    </el-header>

    <el-main>
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>

    <el-footer height="60px">
      <div class="footer-content">
        <p>&copy; 2024 MediaSense. All rights reserved.</p>
      </div>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowDown } from '@element-plus/icons-vue'
import { storeToRefs } from 'pinia'

const route = useRoute()
const authStore = useAuthStore()
const { isAuthenticated, isAdmin, user } = storeToRefs(authStore)

const handleLogout = () => {
  authStore.logout()
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.logo {
  font-size: 24px;
  font-weight: bold;
}

.logo a {
  color: var(--el-color-primary);
  text-decoration: none;
}

.user-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.footer-content {
  text-align: center;
  color: var(--el-text-color-secondary);
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
</style> 