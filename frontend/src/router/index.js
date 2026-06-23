import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Booking from '../views/Booking.vue'
import Property from '../views/Property.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import SimpleBooking from '../views/SimpleBooking.vue'
import Stats from '../views/Stats.vue'
import Settings from '../views/Settings.vue'
import Payment from '../views/Payment.vue'
import Coupon from '../views/Coupon.vue'
import PropertyDetail from '../views/PropertyDetail.vue'
import RoomType from '../views/RoomType.vue'
import Admin from '../views/Admin.vue'
import UserProfile from '../views/UserProfile.vue'
import MerchantOrders from '../views/MerchantOrders.vue'
import PendingPayment from '../views/PendingPayment.vue'
import Assistant from '../views/Assistant.vue'
import HotelCardTest from '../views/HotelCardTest.vue'
import NotFound from '../views/NotFound.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/booking',
    name: 'Booking',
    component: Booking,
    meta: { requiresAuth: true }
  },
  {
    path: '/simple-booking',
    name: 'SimpleBooking',
    component: SimpleBooking
  },
  {
    path: '/stats',
    name: 'Stats',
    component: Stats,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/property',
    name: 'Property',
    component: Property
  },
  {
    path: '/property/:id',
    name: 'PropertyDetail',
    component: PropertyDetail
  },
  {
    path: '/room-type',
    name: 'RoomType',
    component: RoomType,
    meta: { requiresAuth: true }
  },
  {
    path: '/payments',
    name: 'Payment',
    component: Payment,
    meta: { requiresAuth: true }
  },
  {
    path: '/pending-payment',
    name: 'PendingPayment',
    component: PendingPayment,
    meta: { requiresAuth: true }
  },
  {
    path: '/merchant-orders',
    name: 'MerchantOrders',
    component: MerchantOrders,
    meta: { requiresAuth: true }
  },
  {
    path: '/coupons',
    name: 'Coupon',
    component: Coupon
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guestOnly: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { guestOnly: true }
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: Assistant,
    meta: { requiresAuth: true }
  },
  {
    path: '/assistant-preview',
    name: 'AssistantPreview',
    component: Assistant
  },
  {
    path: '/hotel-card-test',
    name: 'HotelCardTest',
    component: HotelCardTest
  },
  {
    path: '/copilot/:pathMatch(.*)*',
    redirect: '/assistant'
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Auth guard
router.beforeEach((to, from, next) => {
  const userStr = localStorage.getItem('user')
  let user = null
  try { user = userStr ? JSON.parse(userStr) : null } catch (e) { /* ignore */ }

  if (to.meta.requiresAuth && !user) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  if (to.meta.requiresAdmin && user?.role !== 'ADMIN') {
    return next({ name: 'Home' })
  }

  if (to.meta.guestOnly && user) {
    return next({ name: 'Home' })
  }

  next()
})

export default router
