<template>
  <div class="settings">
    <el-tabs v-model="activeTab">
      <!-- 告警设置 -->
      <el-tab-pane label="告警设置" name="alert">
        <el-card class="setting-card">
          <template #header>
            <div class="card-header">
              <span>告警阈值设置</span>
              <el-button type="primary" @click="saveAlertSettings">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="alertFormRef"
            :model="alertSettings"
            :rules="alertRules"
            label-width="120px"
          >
            <el-form-item label="CPU 告警阈值" prop="cpu">
              <el-input-number
                v-model="alertSettings.cpu"
                :min="0"
                :max="100"
                :step="5"
              >
                <template #suffix>%</template>
              </el-input-number>
              <div class="form-tip">
                当 CPU 使用率超过此值时触发告警
              </div>
            </el-form-item>
            
            <el-form-item label="内存告警阈值" prop="memory">
              <el-input-number
                v-model="alertSettings.memory"
                :min="0"
                :max="100"
                :step="5"
              >
                <template #suffix>%</template>
              </el-input-number>
              <div class="form-tip">
                当内存使用率超过此值时触发告警
              </div>
            </el-form-item>
            
            <el-form-item label="磁盘告警阈值" prop="disk">
              <el-input-number
                v-model="alertSettings.disk"
                :min="0"
                :max="100"
                :step="5"
              >
                <template #suffix>%</template>
              </el-input-number>
              <div class="form-tip">
                当磁盘使用率超过此值时触发告警
              </div>
            </el-form-item>
            
            <el-form-item label="告警检查间隔" prop="checkInterval">
              <el-input-number
                v-model="alertSettings.checkInterval"
                :min="1"
                :max="60"
                :step="1"
              >
                <template #suffix>分钟</template>
              </el-input-number>
              <div class="form-tip">
                系统自动检查告警条件的时间间隔
              </div>
            </el-form-item>
            
            <el-form-item label="告警通知方式" prop="notifyMethods">
              <el-checkbox-group v-model="alertSettings.notifyMethods">
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="sms">短信通知</el-checkbox>
                <el-checkbox label="webhook">Webhook</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="setting-card">
          <template #header>
            <div class="card-header">
              <span>通知配置</span>
              <el-button type="primary" @click="saveNotifySettings">
                保存配置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="notifyFormRef"
            :model="notifySettings"
            :rules="notifyRules"
            label-width="120px"
          >
            <!-- 邮件配置 -->
            <div v-show="alertSettings.notifyMethods.includes('email')">
              <div class="setting-section-title">邮件配置</div>
              <el-form-item label="SMTP 服务器" prop="email.host">
                <el-input v-model="notifySettings.email.host" />
              </el-form-item>
              <el-form-item label="SMTP 端口" prop="email.port">
                <el-input-number v-model="notifySettings.email.port" :min="1" :max="65535" />
              </el-form-item>
              <el-form-item label="发件人邮箱" prop="email.from">
                <el-input v-model="notifySettings.email.from" />
              </el-form-item>
              <el-form-item label="邮箱密码" prop="email.password">
                <el-input
                  v-model="notifySettings.email.password"
                  type="password"
                  show-password
                />
              </el-form-item>
              <el-form-item label="收件人列表" prop="email.to">
                <el-select
                  v-model="notifySettings.email.to"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="请输入邮箱地址"
                >
                  <el-option
                    v-for="item in notifySettings.email.to"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
            </div>
            
            <!-- 短信配置 -->
            <div v-show="alertSettings.notifyMethods.includes('sms')">
              <div class="setting-section-title">短信配置</div>
              <el-form-item label="API Key" prop="sms.apiKey">
                <el-input v-model="notifySettings.sms.apiKey" show-password />
              </el-form-item>
              <el-form-item label="API Secret" prop="sms.apiSecret">
                <el-input v-model="notifySettings.sms.apiSecret" show-password />
              </el-form-item>
              <el-form-item label="短信模板ID" prop="sms.templateId">
                <el-input v-model="notifySettings.sms.templateId" />
              </el-form-item>
              <el-form-item label="手机号列表" prop="sms.phones">
                <el-select
                  v-model="notifySettings.sms.phones"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  placeholder="请输入手机号"
                >
                  <el-option
                    v-for="item in notifySettings.sms.phones"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
            </div>
            
            <!-- Webhook配置 -->
            <div v-show="alertSettings.notifyMethods.includes('webhook')">
              <div class="setting-section-title">Webhook配置</div>
              <el-form-item label="Webhook URL" prop="webhook.url">
                <el-input v-model="notifySettings.webhook.url" />
              </el-form-item>
              <el-form-item label="请求方法" prop="webhook.method">
                <el-select v-model="notifySettings.webhook.method">
                  <el-option label="POST" value="POST" />
                  <el-option label="GET" value="GET" />
                </el-select>
              </el-form-item>
              <el-form-item label="请求头" prop="webhook.headers">
                <el-input
                  v-model="notifySettings.webhook.headers"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入JSON格式的请求头"
                />
              </el-form-item>
            </div>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <!-- 系统设置 -->
      <el-tab-pane label="系统设置" name="system">
        <el-card class="setting-card">
          <template #header>
            <div class="card-header">
              <span>基本设置</span>
              <el-button type="primary" @click="saveSystemSettings">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="systemFormRef"
            :model="systemSettings"
            :rules="systemRules"
            label-width="120px"
          >
            <el-form-item label="系统名称" prop="name">
              <el-input v-model="systemSettings.name" />
            </el-form-item>
            
            <el-form-item label="数据保留天数" prop="dataRetention">
              <el-input-number
                v-model="systemSettings.dataRetention"
                :min="1"
                :max="365"
                :step="1"
              >
                <template #suffix>天</template>
              </el-input-number>
              <div class="form-tip">
                系统自动清理超过保留天数的历史数据
              </div>
            </el-form-item>
            
            <el-form-item label="数据备份" prop="backup">
              <el-switch
                v-model="systemSettings.backup.enabled"
                inline-prompt
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item
              label="备份时间"
              prop="backup.time"
              v-show="systemSettings.backup.enabled"
            >
              <el-time-picker
                v-model="systemSettings.backup.time"
                format="HH:mm"
                placeholder="选择时间"
              />
              <div class="form-tip">
                系统将在每天该时间点进行自动备份
              </div>
            </el-form-item>
            
            <el-form-item
              label="备份保留数量"
              prop="backup.keep"
              v-show="systemSettings.backup.enabled"
            >
              <el-input-number
                v-model="systemSettings.backup.keep"
                :min="1"
                :max="30"
                :step="1"
              />
              <div class="form-tip">
                超过保留数量的旧备份将被自动删除
              </div>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="setting-card">
          <template #header>
            <div class="card-header">
              <span>安全设置</span>
              <el-button type="primary" @click="saveSecuritySettings">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form
            ref="securityFormRef"
            :model="securitySettings"
            :rules="securityRules"
            label-width="120px"
          >
            <el-form-item label="密码有效期" prop="passwordExpiry">
              <el-input-number
                v-model="securitySettings.passwordExpiry"
                :min="0"
                :max="365"
                :step="1"
              >
                <template #suffix>天</template>
              </el-input-number>
              <div class="form-tip">
                0表示永不过期，大于0表示密码需要定期更换
              </div>
            </el-form-item>
            
            <el-form-item label="登录失败锁定" prop="loginLock">
              <el-switch
                v-model="securitySettings.loginLock.enabled"
                inline-prompt
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
            
            <el-form-item
              label="失败次数"
              prop="loginLock.attempts"
              v-show="securitySettings.loginLock.enabled"
            >
              <el-input-number
                v-model="securitySettings.loginLock.attempts"
                :min="1"
                :max="10"
                :step="1"
              />
              <div class="form-tip">
                连续登录失败超过该次数将被锁定
              </div>
            </el-form-item>
            
            <el-form-item
              label="锁定时间"
              prop="loginLock.duration"
              v-show="securitySettings.loginLock.enabled"
            >
              <el-input-number
                v-model="securitySettings.loginLock.duration"
                :min="1"
                :max="1440"
                :step="1"
              >
                <template #suffix>分钟</template>
              </el-input-number>
            </el-form-item>
            
            <el-form-item label="会话超时" prop="sessionTimeout">
              <el-input-number
                v-model="securitySettings.sessionTimeout"
                :min="1"
                :max="1440"
                :step="1"
              >
                <template #suffix>分钟</template>
              </el-input-number>
              <div class="form-tip">
                用户无操作超过该时间将自动退出
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 当前激活的标签页
const activeTab = ref('alert')

// 告警设置
const alertSettings = ref({
  cpu: 80,
  memory: 80,
  disk: 85,
  checkInterval: 5,
  notifyMethods: ['email']
})

// 通知设置
const notifySettings = ref({
  email: {
    host: '',
    port: 465,
    from: '',
    password: '',
    to: []
  },
  sms: {
    apiKey: '',
    apiSecret: '',
    templateId: '',
    phones: []
  },
  webhook: {
    url: '',
    method: 'POST',
    headers: ''
  }
})

// 系统设置
const systemSettings = ref({
  name: 'MediaSense监控平台',
  dataRetention: 30,
  backup: {
    enabled: false,
    time: new Date(2000, 0, 1, 2, 0),
    keep: 7
  }
})

// 安全设置
const securitySettings = ref({
  passwordExpiry: 90,
  loginLock: {
    enabled: true,
    attempts: 5,
    duration: 30
  },
  sessionTimeout: 30
})

// 表单校验规则
const alertRules = {
  cpu: [
    { required: true, message: '请设置CPU告警阈值', trigger: 'blur' }
  ],
  memory: [
    { required: true, message: '请设置内存告警阈值', trigger: 'blur' }
  ],
  disk: [
    { required: true, message: '请设置磁盘告警阈值', trigger: 'blur' }
  ],
  checkInterval: [
    { required: true, message: '请设置告警检查间隔', trigger: 'blur' }
  ]
}

const notifyRules = {
  'email.host': [
    { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
  ],
  'email.port': [
    { required: true, message: '请输入SMTP端口', trigger: 'blur' }
  ],
  'email.from': [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  'email.password': [
    { required: true, message: '请输入邮箱密码', trigger: 'blur' }
  ],
  'sms.apiKey': [
    { required: true, message: '请输入API Key', trigger: 'blur' }
  ],
  'sms.apiSecret': [
    { required: true, message: '请输入API Secret', trigger: 'blur' }
  ],
  'webhook.url': [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ]
}

const systemRules = {
  name: [
    { required: true, message: '请输入系统名称', trigger: 'blur' }
  ],
  dataRetention: [
    { required: true, message: '请设置数据保留天数', trigger: 'blur' }
  ]
}

const securityRules = {
  passwordExpiry: [
    { required: true, message: '请设置密码有效期', trigger: 'blur' }
  ],
  sessionTimeout: [
    { required: true, message: '请设置会话超时时间', trigger: 'blur' }
  ]
}

// 保存设置
const saveAlertSettings = () => {
  // TODO: 实现保存告警设置的逻辑
  ElMessage.success('告警设置已保存')
}

const saveNotifySettings = () => {
  // TODO: 实现保存通知配置的逻辑
  ElMessage.success('通知配置已保存')
}

const saveSystemSettings = () => {
  // TODO: 实现保存系统设置的逻辑
  ElMessage.success('系统设置已保存')
}

const saveSecuritySettings = () => {
  // TODO: 实现保存安全设置的逻辑
  ElMessage.success('安全设置已保存')
}
</script>

<style scoped>
.settings {
  padding: 20px;
}

.setting-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-section-title {
  font-size: 16px;
  font-weight: bold;
  margin: 20px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-card__header) {
  padding: 15px 20px;
}
</style> 