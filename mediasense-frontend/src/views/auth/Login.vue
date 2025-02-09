<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <img src="@/assets/logo.png" alt="Logo" class="logo">
          <h2>MediaSense 监控平台</h2>
        </div>
      </template>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            data-test="username-input"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            data-test="password-input"
          />
        </el-form-item>

        <div class="form-actions">
          <el-button
            type="primary"
            native-type="submit"
            :loading="authStore.loading"
            class="submit-btn"
            data-test="login-button"
          >
            登录
          </el-button>
          <div class="action-links">
            <el-link type="primary" @click="router.push('/auth/register')">
              注册账号
            </el-link>
            <el-divider direction="vertical" />
            <el-link type="primary" @click="router.push('/auth/forgot-password')">
              忘记密码
            </el-link>
          </div>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, var(--el-color-primary-light-8) 0%, var(--el-color-primary-light-9) 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  margin: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  padding: 20px 0;
}

.logo {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
}

.login-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 24px;
}

.form-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
}

.submit-btn {
  width: 100%;
  height: 40px;
  font-size: 16px;
}

.action-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-input__wrapper) {
  padding: 8px 12px;
}

:deep(.el-input__inner) {
  height: 40px;
}

:deep(.el-form-item__label) {
  font-size: 14px;
  padding-bottom: 8px;
}
</style>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    await authStore.login(form.username, form.password)
    const redirect = router.currentRoute.value.query.redirect as string
    await router.push(redirect || '/dashboard')
    ElMessage.success('登录成功')
  } catch (error) {
    if (error instanceof Error) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('登录失败,请检查用户名和密码')
    }
  }
}
</script> 