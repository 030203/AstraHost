import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const readStoredUser = () => {
  if (typeof window === 'undefined') {
    return null
  }

  const userStr = localStorage.getItem('user')
  if (!userStr) {
    return null
  }

  try {
    return JSON.parse(userStr)
  } catch (error) {
    return null
  }
}

export const useSession = () => {
  const user = ref(readStoredUser())

  const syncUser = () => {
    user.value = readStoredUser()
  }

  onMounted(() => {
    syncUser()
    window.addEventListener('user-changed', syncUser)
    window.addEventListener('storage', syncUser)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('user-changed', syncUser)
    window.removeEventListener('storage', syncUser)
  })

  return {
    user,
    syncUser,
    isLoggedIn: computed(() => !!user.value)
  }
}

export const getStoredUser = () => readStoredUser()
