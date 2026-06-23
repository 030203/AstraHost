<template>
  <div class="not-found">
    <div class="nf-card">
      <div class="nf-code">404</div>
      <h1>页面未找到</h1>
      <p>你访问的页面不存在或已被移除。</p>
      <div class="nf-actions">
        <el-button type="primary" size="large" @click="$router.push('/')">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button size="large" @click="$router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
      <div class="nf-links">
        <span>试试这些：</span>
        <router-link to="/simple-booking">快速预订</router-link>
        <router-link to="/login">登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { HomeFilled, ArrowLeft } from '@element-plus/icons-vue'
</script>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 220px);
  padding: 40px 20px;
}

.nf-card {
  text-align: center;
  max-width: 480px;
}

.nf-code {
  font-size: 120px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 55%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.nf-card h1 {
  margin: 0 0 12px;
  font-size: 28px;
  color: var(--ink, #0f172a);
}

.nf-card p {
  color: var(--muted, #64748b);
  font-size: 15px;
  line-height: 1.6;
  margin: 0 0 28px;
}

.nf-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.nf-actions .el-button span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.nf-links {
  font-size: 14px;
  color: var(--muted, #64748b);
}

.nf-links a {
  color: var(--primary, #2563eb);
  margin-left: 12px;
  text-decoration: none;
  font-weight: 600;
}

.nf-links a:hover {
  text-decoration: underline;
}
</style>
