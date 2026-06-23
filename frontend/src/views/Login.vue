<template>
  <div class="auth-page">
    <div class="auth-shell">
      <AuthShowcase
        eyebrow="Account Access"
        title="欢迎回来，继续你的入住与运营流程。"
        description="登录后可直接查看订单、支付、房源状态与 AI 客服上下文，所有角色都在同一套入口体系里工作。"
        :items="showcaseItems"
      />

      <section class="auth-panel app-section-card fade-rise">
        <div class="auth-panel__header">
          <p class="app-kicker">Sign in</p>
          <h1>登录账号</h1>
          <p>演示环境提供示例账号，点击下方标签即可快速填充。</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="auth-form">
          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" placeholder="请选择角色" size="large">
              <el-option label="普通用户" value="USER" />
              <el-option label="商户" value="MERCHANT" />
              <el-option label="管理员" value="ADMIN" />
            </el-select>
            <div class="helper">住客用于预订，商户用于管理房源，管理员拥有全局权限。</div>
          </el-form-item>

          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" size="large" placeholder="请输入用户名" :prefix-icon="User" />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              @keyup.enter="onSubmit"
            />
          </el-form-item>

          <el-button type="primary" size="large" :loading="loading" class="submit-btn" @click="onSubmit">
            登录并继续
          </el-button>

          <el-alert
            v-if="error"
            type="error"
            :title="error"
            show-icon
            :closable="false"
            class="auth-alert"
          />
        </el-form>

        <section class="demo-panel">
          <div class="demo-panel__head">
            <strong>示例账号</strong>
            <span>点击即可填入表单</span>
          </div>
          <div class="demo-tags">
            <button
              v-for="acc in demoAccounts"
              :key="acc.username + acc.role"
              type="button"
              class="demo-tag"
              @click="fillAccount(acc)"
            >
              {{ roleText(acc.role) }} · {{ acc.username }} / {{ acc.password }}
            </button>
          </div>
        </section>

        <div class="auth-footer">
          <span>还没有账号？</span>
          <router-link class="auth-link" to="/register">立即注册</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, User, Lock, Calendar, Tickets } from '@element-plus/icons-vue'
import AuthShowcase from '../components/auth/AuthShowcase.vue'
import { authApi } from '../api/auth'
import { isAiCopilotPath, normalizeAiCopilotPath } from '../utils/aiCopilot'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const error = ref('')

const form = reactive({
  role: 'USER',
  username: '',
  password: ''
})

const rules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const showcaseItems = [
  { icon: Check, title: '统一身份进入', description: '登录后会自动恢复导航、订单和 AI 客服上下文。' },
  { icon: Calendar, title: '预订流程不断裂', description: '用户可继续快速预订，商户可直接回到待处理事务。' },
  { icon: Tickets, title: '多角色同入口', description: '住客、商户、管理员共用同一套温暖且清晰的界面语言。' }
]

const demoAccounts = [
  { role: 'USER', username: 'user1', password: 'password' },
  { role: 'MERCHANT', username: 'merchant1', password: 'password' },
  { role: 'ADMIN', username: 'admin', password: 'admin123' }
]

const roleText = (role) => {
  const map = { USER: '用户', MERCHANT: '商户', ADMIN: '管理员' }
  return map[role] || role
}

const fillAccount = (acc) => {
  form.role = acc.role
  form.username = acc.username
  form.password = acc.password
}

const onSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    error.value = ''
    const { data } = await authApi.login({
      username: form.username,
      password: form.password,
      role: form.role
    })
    localStorage.setItem('user', JSON.stringify(data))
    window.dispatchEvent(new Event('user-changed'))
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    if (typeof redirect === 'string' && isAiCopilotPath(redirect)) {
      router.push(normalizeAiCopilotPath(redirect))
    } else if (redirect) {
      router.push(redirect)
    } else if (data?.role === 'ADMIN') {
      router.push('/admin')
    } else if (data?.role === 'USER') {
      router.push('/simple-booking')
    } else {
      router.push('/booking')
    }
  } catch (err) {
    if (err !== false) {
      error.value = err?.response?.data?.error || '登录失败，请检查账号、密码和角色。'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 140px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-shell {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(360px, 0.8fr);
  border-radius: 30px;
  overflow: hidden;
  box-shadow: var(--app-shadow-lg);
}

.auth-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 22px;
  padding: 36px 34px;
  border-radius: 0;
  background: rgba(255, 253, 249, 0.96);
}

.auth-panel__header h1 {
  margin: 10px 0 12px;
  color: var(--app-text);
  font-size: 32px;
}

.auth-panel__header p:last-child {
  margin: 0;
  color: var(--app-text-soft);
  line-height: 1.7;
}

.auth-form {
  display: grid;
  gap: 6px;
}

.helper {
  margin-top: 8px;
  color: var(--app-text-faint);
  font-size: 12px;
  line-height: 1.6;
}

.submit-btn {
  width: 100%;
  margin-top: 6px;
}

.auth-alert {
  margin-top: 12px;
}

.demo-panel {
  padding: 18px;
  border-radius: 18px;
  background: rgba(246, 237, 229, 0.76);
  border: 1px solid rgba(128, 93, 72, 0.12);
}

.demo-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.demo-panel__head strong {
  color: var(--app-text);
}

.demo-panel__head span,
.auth-footer span {
  color: var(--app-text-soft);
  font-size: 13px;
}

.demo-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.demo-tag {
  padding: 10px 12px;
  border: 1px solid rgba(128, 93, 72, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--app-text);
  cursor: pointer;
  transition: border-color var(--app-transition), transform var(--app-transition), color var(--app-transition);
}

.demo-tag:hover {
  color: var(--app-primary-strong);
  border-color: rgba(201, 134, 106, 0.36);
  transform: translateY(-1px);
}

.auth-footer {
  text-align: center;
}

.auth-link {
  margin-left: 6px;
  color: var(--app-primary-strong);
  font-weight: 700;
  text-decoration: none;
}

.auth-link:hover {
  text-decoration: underline;
}

@media (max-width: 980px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .auth-panel {
    padding: 24px 20px;
  }
}
</style>
