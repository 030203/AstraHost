import { computed, ref } from 'vue'

const BASE_STEPS = [
  { key: 'understand', label: '理解需求', detail: '解析当前问题的目标、对象与限制' },
  { key: 'search', label: '调用工具', detail: '查询订单、支付、房源或其他业务数据' },
  { key: 'confirm', label: '等待确认', detail: '危险操作需要用户二次确认后才会执行' },
  { key: 'result', label: '生成结果', detail: '整理结论、证据与下一步操作建议' }
]

const cloneSteps = () =>
  BASE_STEPS.map((step, index) => ({
    ...step,
    status: index === 0 ? 'running' : 'pending'
  }))

export const useAssistantTimeline = () => {
  const steps = ref(cloneSteps())
  const liveLabel = ref('分析中...')

  const reset = () => {
    steps.value = cloneSteps()
    liveLabel.value = '分析中...'
  }

  const setRunning = (key, detail) => {
    steps.value = steps.value.map((step) => {
      if (step.key === key) {
        return {
          ...step,
          detail: detail || step.detail,
          status: 'running'
        }
      }
      if (step.status === 'running') {
        return { ...step, status: 'done' }
      }
      return step
    })
  }

  const setFinal = (status, detail) => {
    const lastIndex = steps.value.length - 1
    steps.value = steps.value.map((step, index) => {
      if (index < lastIndex && step.status === 'pending') {
        return { ...step, status: 'done' }
      }
      if (index === lastIndex) {
        return {
          ...step,
          detail: detail || step.detail,
          status
        }
      }
      if (step.status === 'running') {
        return { ...step, status: 'done' }
      }
      return step
    })
  }

  const markConfirmation = (detail) => {
    setRunning('confirm', detail || '等待用户确认危险操作')
  }

  const applyStatus = (label) => {
    liveLabel.value = label
    if (/理解|分析/.test(label)) {
      setRunning('understand', label)
      return
    }
    if (/确认/.test(label)) {
      markConfirmation(label)
      return
    }
    if (/工具|查询|搜索|调用/.test(label)) {
      setRunning('search', label)
      return
    }
    if (/输出|生成|完成|整理/.test(label)) {
      setRunning('result', label)
    }
  }

  return {
    steps: computed(() => steps.value),
    liveLabel: computed(() => liveLabel.value),
    reset,
    setRunning,
    setFinal,
    markConfirmation,
    applyStatus
  }
}
