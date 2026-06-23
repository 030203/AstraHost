<template>
  <div class="auth-page">
    <div class="auth-shell">
      <AuthShowcase
        eyebrow="Create Account"
        title="把住客、商户和管理员都接进同一套工作空间。"
        description="注册流程也统一切换到暖色设计语言。用户可以预订，商户可以管理房源，管理员可以查看平台全局。"
        :items="showcaseItems"
      />

      <section class="auth-panel app-section-card fade-rise">
        <div class="auth-panel__header">
          <p class="app-kicker">Register</p>
          <h1>创建账号</h1>
          <p>根据角色显示必要字段，避免一次性暴露过多输入项。</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="mergedRules" label-position="top" class="auth-form">
          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" placeholder="请选择角色" size="large">
              <el-option label="普通用户" value="USER" />
              <el-option label="商户" value="MERCHANT" />
              <el-option label="管理员" value="ADMIN" />
            </el-select>
            <div class="helper">普通用户用于预订，商户可管理房源，管理员用于全局管理。</div>
          </el-form-item>

          <div class="form-grid">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" size="large" placeholder="3-20 位，字母/数字/下划线" :prefix-icon="User" />
            </el-form-item>

            <el-form-item label="邮箱（可选）" prop="email">
              <el-input v-model="form.email" size="large" placeholder="name@example.com" :prefix-icon="Message" />
            </el-form-item>
          </div>

          <div class="form-grid">
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" size="large" type="password" placeholder="至少 6 位" :prefix-icon="Lock" show-password />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="form.confirmPassword" size="large" type="password" placeholder="再次输入密码" :prefix-icon="Lock" show-password />
            </el-form-item>
          </div>

          <el-form-item label="手机（可选）" prop="phone">
            <el-input v-model="form.phone" size="large" placeholder="11 位手机号" :prefix-icon="Phone" />
          </el-form-item>

          <section v-if="form.role === 'MERCHANT'" class="merchant-block">
            <div class="merchant-block__head">
              <strong>商户信息</strong>
              <span>这些字段用于后续房源创建和审核。</span>
            </div>

            <div class="form-grid">
              <el-form-item label="商户名称" prop="merchantName">
                <el-input v-model="form.merchantName" size="large" placeholder="公司或店铺名称" />
              </el-form-item>

              <el-form-item label="联系人姓名" prop="merchantContactName">
                <el-input v-model="form.merchantContactName" size="large" placeholder="联系人姓名" />
              </el-form-item>
            </div>

            <div class="form-grid">
              <el-form-item label="联系人电话" prop="merchantContactPhone">
                <el-input v-model="form.merchantContactPhone" size="large" placeholder="联系人电话" />
              </el-form-item>

              <el-form-item label="联系人邮箱" prop="merchantContactEmail">
                <el-input v-model="form.merchantContactEmail" size="large" placeholder="联系人邮箱（可选）" />
              </el-form-item>
            </div>

            <div class="form-grid">
              <el-form-item label="省份" prop="merchantProvince">
                <el-input v-model="form.merchantProvince" size="large" placeholder="省份" />
              </el-form-item>

              <el-form-item label="城市" prop="merchantCity">
                <el-input v-model="form.merchantCity" size="large" placeholder="城市" />
              </el-form-item>
            </div>

            <div class="form-grid">
              <el-form-item label="区县" prop="merchantDistrict">
                <el-input v-model="form.merchantDistrict" size="large" placeholder="区县（可选）" />
              </el-form-item>

              <el-form-item label="营业执照号" prop="businessLicense">
                <el-input v-model="form.businessLicense" size="large" placeholder="营业执照号（可选）" />
              </el-form-item>
            </div>

            <el-form-item label="详细地址" prop="merchantAddress">
              <el-input v-model="form.merchantAddress" size="large" placeholder="详细地址（可选）" />
            </el-form-item>
          </section>

          <el-button type="primary" size="large" :loading="loading" class="submit-btn" @click="onSubmit">
            创建账号
          </el-button>

          <el-alert v-if="error" type="error" :title="error" show-icon :closable="false" class="auth-alert" />
        </el-form>

        <div class="auth-footer">
          <span>已有账号？</span>
          <router-link class="auth-link" to="/login">立即登录</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, User, Lock, Message, Phone, House } from '@element-plus/icons-vue'
import AuthShowcase from '../components/auth/AuthShowcase.vue'
import { authApi } from '../api/auth'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const error = ref('')

const form = reactive({
  role: 'USER',
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: '',
  merchantName: '',
  merchantContactName: '',
  merchantContactPhone: '',
  merchantContactEmail: '',
  merchantAddress: '',
  merchantProvince: '',
  merchantCity: '',
  merchantDistrict: '',
  businessLicense: ''
})

const showcaseItems = [
  { icon: Check, title: '角色分层清楚', description: '先选角色，再按需展示字段，减少一次性输入负担。' },
  { icon: House, title: '商户信息独立分组', description: '商户注册时额外信息收束在单独区块里，更好扫描。' },
  { icon: User, title: '注册后直接进入流程', description: '账号建立完成后可以立刻回到登录并进入对应业务页面。' }
]

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const validateEmail = (rule, value, callback) => {
  if (!value) return callback()
  const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
  callback(ok ? undefined : new Error('邮箱格式不正确'))
}

const validatePhone = (rule, value, callback) => {
  if (!value) return callback()
  const ok = /^1[3-9]\d{9}$/.test(value)
  callback(ok ? undefined : new Error('手机号格式不正确'))
}

const baseRules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度 3-20 位', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '仅支持字母数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '长度 6-50 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  phone: [{ validator: validatePhone, trigger: 'blur' }]
}

const merchantRequired = [{ required: true, message: '商户信息为必填', trigger: 'blur' }]

const mergedRules = computed(() => {
  if (form.role === 'MERCHANT') {
    return {
      ...baseRules,
      merchantName: merchantRequired,
      merchantContactName: merchantRequired,
      merchantContactPhone: merchantRequired
    }
  }
  return baseRules
})

const onSubmit = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    error.value = ''
    await authApi.register({
      username: form.username,
      password: form.password,
      email: form.email || null,
      phone: form.phone || null,
      role: form.role,
      merchantName: form.merchantName,
      merchantContactName: form.merchantContactName,
      merchantContactPhone: form.merchantContactPhone,
      merchantContactEmail: form.merchantContactEmail || null,
      merchantAddress: form.merchantAddress || null,
      merchantProvince: form.merchantProvince || null,
      merchantCity: form.merchantCity || null,
      merchantDistrict: form.merchantDistrict || null,
      businessLicense: form.businessLicense || null
    })
    ElMessage.success('注册成功，正在跳转登录')
    setTimeout(() => router.push('/login'), 800)
  } catch (err) {
    if (err !== false) {
      error.value = err?.response?.data?.error || '注册失败，请检查输入。'
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
  grid-template-columns: minmax(0, 0.95fr) minmax(420px, 0.95fr);
  border-radius: 30px;
  overflow: hidden;
  box-shadow: var(--app-shadow-lg);
}

.auth-panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 32px 34px;
  border-radius: 0;
  background: rgba(255, 253, 249, 0.96);
}

.auth-panel__header h1 {
  margin: 10px 0 12px;
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.helper {
  margin-top: 8px;
  color: var(--app-text-faint);
  font-size: 12px;
  line-height: 1.6;
}

.merchant-block {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(246, 237, 229, 0.76);
  border: 1px solid rgba(128, 93, 72, 0.12);
}

.merchant-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.merchant-block__head strong {
  color: var(--app-text);
}

.merchant-block__head span,
.auth-footer span {
  color: var(--app-text-soft);
  font-size: 13px;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}

.auth-alert {
  margin-top: 12px;
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

@media (max-width: 1100px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .auth-panel {
    padding: 24px 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .merchant-block__head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
