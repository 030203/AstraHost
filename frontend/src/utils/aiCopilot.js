export const AI_COPILOT_BASE_PATH = '/assistant'
export const AI_COPILOT_PATH = '/assistant'
const LEGACY_COPILOT_BASE_PATH = '/copilot'

export const isAiCopilotPath = (value) =>
  typeof value === 'string' &&
  (value.startsWith(AI_COPILOT_BASE_PATH) || value.startsWith(LEGACY_COPILOT_BASE_PATH))

export const normalizeAiCopilotPath = (value = AI_COPILOT_PATH) => {
  if (typeof value !== 'string' || !value) {
    return AI_COPILOT_PATH
  }
  if (value.startsWith(LEGACY_COPILOT_BASE_PATH)) {
    return value.replace(LEGACY_COPILOT_BASE_PATH, AI_COPILOT_BASE_PATH)
  }
  return value
}

export const openAiCopilot = ({ replace = false, target = AI_COPILOT_PATH } = {}) => {
  if (typeof window === 'undefined') {
    return
  }
  const nextTarget = normalizeAiCopilotPath(target)
  if (replace) {
    window.location.replace(nextTarget)
    return
  }
  window.location.assign(nextTarget)
}

export const clearAiCopilotState = () => {
  if (typeof window === 'undefined') {
    return
  }
  try {
    localStorage.removeItem('ai-service-copilot-conversations')
  } catch (error) {
    console.warn('clear_ai_copilot_state_failed', error)
  }
}
