<template>
  <div id="app-shell">
    <el-container class="app-layout">
      <!-- ═══════════════════════════════════════════════ -->
      <!-- NAVIGATION — dark on Home/AI, light elsewhere   -->
      <!-- ═══════════════════════════════════════════════ -->
      <el-header
        class="app-header"
        :class="{
          'app-header--floating': isFloatingNav,
          'app-header--light': !isFloatingNav
        }"
      >
        <div class="header-content">
          <router-link to="/" class="brand" aria-label="返回首页">
            <div class="brand-mark">
              <el-icon><House /></el-icon>
            </div>
            <div class="brand-copy">
              <strong>AstraHost</strong>
            </div>
          </router-link>

          <button
            class="hamburger" type="button"
            @click="mobileNavOpen = !mobileNavOpen"
            :aria-expanded="String(mobileNavOpen)"
            aria-label="切换导航菜单"
          >
            <el-icon><component :is="mobileNavOpen ? Close : MenuIcon" /></el-icon>
          </button>

          <nav class="nav" :class="{ 'nav--open': mobileNavOpen }">
            <router-link
              v-for="item in visibleNavItems"
              :key="item.key"
              :to="item.to"
              class="nav-link"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </router-link>

            <router-link :to="aiCopilotPath" class="nav-link">
              <el-icon><ChatLineRound /></el-icon>
              <span>AI 客服</span>
            </router-link>

            <router-link v-if="!isLoggedIn" to="/login" class="nav-link nav-link--accent">
              <el-icon><User /></el-icon>
              <span>登录</span>
            </router-link>

            <div v-else class="session-pill">
              <span class="session-role">{{ roleText(user?.role) }}</span>
              <el-dropdown @command="handleCommand">
                <button class="session-trigger" type="button">
                  <el-avatar :size="30" :src="user?.avatar" icon="Avatar" />
                  <span>{{ user?.username }}</span>
                  <el-icon><ArrowDown /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                    <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </nav>
        </div>
      </el-header>

      <!-- ═══════════════════════════════════════════════ -->
      <!-- MAIN CONTENT                                   -->
      <!-- ═══════════════════════════════════════════════ -->
      <el-main class="app-main" :class="{ 'app-main--full': isFloatingNav }">
        <div class="main-frame" :class="{ 'main-frame--plain': isFloatingNav }">
          <router-view v-slot="{ Component, route }">
            <transition :name="route.path === '/' ? 'app-page-fast' : 'app-page'">
              <component :is="Component" :key="route.fullPath" />
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  House, HomeFilled, Calendar, User, Avatar, ArrowDown,
  Tickets, Collection, Menu as MenuIcon, Close, ChatLineRound,
  Setting, DataAnalysis
} from '@element-plus/icons-vue'
import { AI_COPILOT_PATH, clearAiCopilotState } from './utils/aiCopilot'
import { useSession } from './composables/useSession'

const router = useRouter()
const route = useRoute()
const mobileNavOpen = ref(false)
const aiCopilotPath = AI_COPILOT_PATH

// Floating nav (absolute over hero) only on Home
const isFloatingNav = computed(() => route.path === '/')

const { user, isLoggedIn, syncUser } = useSession()

const roleText = (role) => {
  const roleMap = { USER: '住客', MERCHANT: '商户', ADMIN: '管理员' }
  return roleMap[role] || '访客'
}

const navItems = computed(() => [
  { key: 'home', label: '首页', to: '/', icon: HomeFilled, show: true },
  { key: 'quick-booking', label: '快速预订', to: '/simple-booking', icon: Calendar, show: true },
  { key: 'booking', label: user.value?.role === 'USER' ? '购物车 / 订单' : '预订管理', to: '/booking', icon: Tickets, show: isLoggedIn.value },
  { key: 'payments', label: '支付管理', to: '/payments', icon: Collection, show: isLoggedIn.value },
  { key: 'merchant-orders', label: '订单', to: '/merchant-orders', icon: Tickets, show: isLoggedIn.value && ['MERCHANT', 'ADMIN'].includes(user.value?.role) },
  { key: 'property', label: '民宿管理', to: '/property', icon: House, show: isLoggedIn.value && ['MERCHANT', 'ADMIN'].includes(user.value?.role) },
  { key: 'stats', label: '数据看板', to: '/stats', icon: DataAnalysis, show: isLoggedIn.value && user.value?.role === 'ADMIN' },
  { key: 'settings', label: '设置', to: '/settings', icon: Setting, show: isLoggedIn.value },
  { key: 'profile', label: '个人中心', to: '/profile', icon: Avatar, show: isLoggedIn.value },
  { key: 'admin', label: '后台管理', to: '/admin', icon: Tickets, show: isLoggedIn.value && user.value?.role === 'ADMIN' }
])

const visibleNavItems = computed(() => navItems.value.filter(item => item.show))

watch(() => route.fullPath, () => {
  syncUser()
  mobileNavOpen.value = false
  // instantly switch body background — no flash during transition
  document.body.style.background = route.path === '/' ? '#1a100c' : '#fff8f1'
}, { immediate: true })

const handleCommand = (command) => {
  if (command === 'profile') { router.push('/profile'); return }
  if (command === 'logout') {
    localStorage.removeItem('user')
    clearAiCopilotState()
    window.dispatchEvent(new Event('user-changed'))
    router.push('/login')
  }
}
</script>

<style scoped>
/* ═══════════════════════════════════════════════ */
/* SHELL                                          */
/* ═══════════════════════════════════════════════ */
#app-shell { min-height: 100vh; }
.app-layout { min-height: 100vh; }

/* ═══════════════════════════════════════════════ */
/* DARK GLASS PILL — default for ALL routes       */
/* ═══════════════════════════════════════════════ */
.app-header {
  z-index: 40;
  background: transparent;
  position: sticky;
  top: 0;
  height: 72px !important;
  padding: 10px 18px 0;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  max-width: var(--app-max-width);
  margin: 0 auto;
  padding: 8px 24px;
  border-radius: 999px;
  flex-wrap: nowrap;
  white-space: nowrap;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

/* ── Brand ── */
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  color: #fff8f1;
  font-size: 17px;
  background: linear-gradient(145deg, #d0845a, #c97a50);
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.20);
  flex-shrink: 0;
}

.brand-copy { display: grid; gap: 2px; }
.brand-copy strong { color: #fff; font-size: 16px; line-height: 1; }

/* ── Nav links ── */
.nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 1;
  gap: 2px;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.78);
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.nav-link:hover { color: #fff; background: rgba(255, 255, 255, 0.12); }
.nav-link.router-link-active { color: #fff; background: rgba(255, 255, 255, 0.15); font-weight: 600; }

.nav-link--accent {
  color: #fff;
  background: rgba(201, 134, 106, 0.65);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.nav-link--accent:hover { background: rgba(201, 134, 106, 0.85); }

/* ── Session ── */
.session-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 4px;
  padding: 5px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.12);
  flex-shrink: 0;
}

.session-role { padding: 0 6px; font-size: 11px; font-weight: 500; color: rgba(255, 255, 255, 0.55); }

.session-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 8px 0 2px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
.session-trigger:hover { background: rgba(255, 255, 255, 0.08); }

/* ── Hamburger ── */
.hamburger {
  display: none;
  width: 38px;
  height: 38px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.10);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
}

/* ═══════════════════════════════════════════════ */
/* LIGHT VARIANT — all pages EXCEPT Home/AI       */
/* ═══════════════════════════════════════════════ */
.app-header--light .header-content {
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow:
    0 2px 16px rgba(0, 0, 0, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.app-header--light .brand-mark {
  color: #fff;
  background: linear-gradient(145deg, #d0845a, #c97a50);
  box-shadow: 0 4px 10px rgba(200, 120, 70, 0.25);
}

.app-header--light .brand-copy strong {
  color: #2c2416;
}

.app-header--light .nav-link {
  color: rgba(60, 45, 30, 0.72);
}

.app-header--light .nav-link:hover {
  color: #2c2416;
  background: rgba(0, 0, 0, 0.04);
}

.app-header--light .nav-link.router-link-active {
  color: #2c2416;
  background: rgba(0, 0, 0, 0.06);
  font-weight: 600;
}

.app-header--light .nav-link--accent {
  color: #fff;
  background: rgba(201, 134, 106, 0.78);
  box-shadow: 0 3px 10px rgba(200, 120, 70, 0.18);
}

.app-header--light .nav-link--accent:hover {
  background: rgba(201, 134, 106, 0.92);
}

.app-header--light .session-pill {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.app-header--light .session-role {
  color: rgba(60, 45, 30, 0.48);
}

.app-header--light .session-trigger {
  color: #2c2416;
}

.app-header--light .session-trigger:hover {
  background: rgba(0, 0, 0, 0.04);
}

.app-header--light .hamburger {
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: rgba(0, 0, 0, 0.04);
  color: #2c2416;
}

/* ═══════════════════════════════════════════════ */
/* FLOATING VARIANT — Home page only              */
/* ═══════════════════════════════════════════════ */
.app-header--floating {
  position: absolute;
  top: 28px;
  left: 50%;
  transform: translateX(-50%);
  width: auto;
  height: auto !important;
  padding: 0;
}

.app-header--floating .header-content {
  width: auto;
  max-width: none;
}

/* ═══════════════════════════════════════════════ */
/* MAIN CONTENT                                   */
/* ═══════════════════════════════════════════════ */
.app-main { width: 100%; padding: 10px 0 0; }

.app-main--full {
  padding: 0;
  overflow: hidden;
  background: transparent;
}

.main-frame {
  position: relative;
  width: 100%;
  padding: 18px;
  border-radius: 0;
  border: none;
  border-bottom: 1px solid rgba(128, 93, 72, 0.06);
  background:
    radial-gradient(circle at top right, rgba(255, 235, 220, 0.5), transparent 26%),
    linear-gradient(180deg, rgba(255, 253, 249, 0.6), rgba(255, 250, 245, 0.7));
  box-shadow: none;
}

.main-frame--plain {
  padding: 0;
  border: none;
  background: transparent;
  box-shadow: none;
}

/* ═══════════════════════════════════════════════ */
/* RESPONSIVE                                     */
/* ═══════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .nav-link { padding: 8px 10px; }
}

@media (max-width: 992px) {
  .app-header { height: auto !important; }

  .app-header--floating {
    left: 16px;
    right: 16px;
    transform: none;
    top: 16px;
  }

  .header-content { flex-wrap: wrap; border-radius: 22px; padding: 12px 16px; }

  .hamburger {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-left: auto;
  }

  .nav { display: none; width: 100%; flex-direction: column; align-items: stretch; padding-top: 8px; }
  .nav--open { display: flex; }
  .nav-link, .session-pill { width: 100%; }
  .session-pill { justify-content: space-between; }
  .session-trigger { width: 100%; justify-content: flex-start; }
}

@media (max-width: 768px) {
  .app-header { padding: 8px 12px 0; }
  .header-content { padding: 10px 14px; border-radius: 20px; }
  .main-frame { padding: 14px; }
  .app-main { padding: 8px 0 0; }
  .brand-copy strong { font-size: 15px; }
}
</style>
