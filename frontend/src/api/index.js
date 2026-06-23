import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const assistantClient = axios.create({
  baseURL: '/ai-api',
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  config => {
    const user = localStorage.getItem('user')
    if (user) {
      const userData = JSON.parse(user)
      if (userData.token) {
        config.headers.Authorization = `Bearer ${userData.token}`
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

assistantClient.interceptors.request.use(
  config => {
    const user = localStorage.getItem('user')
    if (user) {
      const userData = JSON.parse(user)
      if (userData.token) {
        config.headers.Authorization = `Bearer ${userData.token}`
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 用户相关API
export const userApi = {
  getProfile: (id) => api.get(`/users/${id}`),
  updateProfile: (id, data) => api.put(`/users/${id}`, data),
  list: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  remove: (id) => api.delete(`/users/${id}`)
}

// 商户相关API
export const merchantApi = {
  getList: (params) => api.get('/merchants', { params }),
  getById: (id) => api.get(`/merchants/${id}`),
  getByUserId: (userId) => api.get(`/merchants/user/${userId}`),
  create: (data) => api.post('/merchants', data),
  update: (id, data) => api.put(`/merchants/${id}`, data),
  approve: (id, auditBy, remark) => api.post(`/merchants/${id}/approve`, null, { params: { auditBy, remark } }),
  reject: (id, auditBy, remark) => api.post(`/merchants/${id}/reject`, null, { params: { auditBy, remark } })
}

// 民宿相关API
export const propertyApi = {
  getList: (params) => api.get('/properties', { params }),
  search: (params) => api.get('/properties/search', { params }),
  reindexSearch: () => api.post('/properties/search/reindex'),
  getById: (id) => api.get(`/properties/${id}`),
  getDetail: (id) => api.get(`/properties/${id}/detail`),
  getTop: (limit = 5) => api.get('/properties/top', { params: { limit } }),
  create: (data) => api.post('/properties', data),
  update: (id, data) => api.put(`/properties/${id}`, data),
  delete: (id) => api.delete(`/properties/${id}`),
  approve: (id) => api.post(`/properties/${id}/approve`),
  reject: (id) => api.post(`/properties/${id}/reject`),
  getByCity: (city) => api.get('/properties', { params: { city } }),
  getFeatured: () => api.get('/properties', { params: { featured: true } })
}

// 预定相关API
export const bookingApi = {
  getList: (params) => api.get('/bookings', { params }),
  getById: (id) => api.get(`/bookings/${id}`),
  getByNumber: (number) => api.get(`/bookings/number/${number}`),
  create: (data) => api.post('/bookings', data),
  update: (id, data) => api.put(`/bookings/${id}`, data),
  delete: (id) => api.delete(`/bookings/${id}`),
  cancel: (id, reason) => api.post(`/bookings/${id}/cancel`, reason),
  checkIn: (id) => api.post(`/bookings/${id}/check-in`),
  checkOut: (id) => api.post(`/bookings/${id}/check-out`)
}

// 房型相关API
export const roomTypeApi = {
  getList: (params) => api.get('/room-types', { params }),
  getById: (id) => api.get(`/room-types/${id}`),
  getByPropertyId: (propertyId) => api.get('/room-types', { params: { propertyId } }),
  getActiveByPropertyId: (propertyId) => api.get(`/room-types/property/${propertyId}/active`),
  create: (data) => api.post('/room-types', data),
  update: (id, data) => api.put(`/room-types/${id}`, data),
  delete: (id) => api.delete(`/room-types/${id}`)
}

// 支付相关API
export const paymentApi = {
  getList: (params) => api.get('/payments', { params }),
  getById: (id) => api.get(`/payments/${id}`),
  getByNumber: (number) => api.get(`/payments/number/${number}`),
  getByBookingId: (bookingId) => api.get('/payments', { params: { bookingId } }),
  create: (data) => api.post('/payments', data),
  update: (id, data) => api.put(`/payments/${id}`, data),
  process: (id, transactionId) => api.post(`/payments/${id}/process`, null, { params: { transactionId } }),
  delete: (id) => api.delete(`/payments/${id}`)
}

// 评价相关API
export const reviewApi = {
  getList: (params) => api.get('/reviews', { params }),
  getById: (id) => api.get(`/reviews/${id}`),
  getByBookingId: (bookingId) => api.get(`/reviews/booking/${bookingId}`),
  getByPropertyId: (propertyId) => api.get('/reviews', { params: { propertyId } }),
  getByUserId: (userId) => api.get('/reviews', { params: { userId } }),
  create: (data) => api.post('/reviews', data),
  update: (id, data) => api.put(`/reviews/${id}`, data),
  approve: (id) => api.post(`/reviews/${id}/approve`),
  reply: (id, replyContent) => api.post(`/reviews/${id}/reply`, replyContent),
  delete: (id) => api.delete(`/reviews/${id}`)
}

// 优惠券相关API（简单 CRUD）
export const couponApi = {
  getList: (params) => api.get('/coupons', { params }),
  getById: (id) => api.get(`/coupons/${id}`),
  create: (data) => api.post('/coupons', data),
  update: (id, data) => api.put(`/coupons/${id}`, data),
  delete: (id) => api.delete(`/coupons/${id}`)
}

export const assistantApi = {
  getConversations: () => assistantClient.get('/conversations'),
  getConversationMessages: (conversationId) =>
    assistantClient.get(`/conversations/${encodeURIComponent(conversationId)}/messages`),
  getSuggestions: () => assistantClient.get('/suggestions'),
  chat: (data) => assistantClient.post('/chat', data)
}

export default api
