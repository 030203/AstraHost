import { computed, ref } from "vue";
import { AGENT_BASE_STEPS } from "../lib/fallbacks";
import type { AgentStep, AgentStepStatus } from "../types/copilot";

function cloneSteps(): AgentStep[] {
  return AGENT_BASE_STEPS.map((step, index) => ({
    ...step,
    status: index === 0 ? "running" : "pending"
  }));
}

export function useAgentTimeline() {
  const steps = ref<AgentStep[]>(cloneSteps());
  const liveLabel = ref("分析中...");

  function reset() {
    steps.value = cloneSteps();
    liveLabel.value = "分析中...";
  }

  function setRunning(key: string, detail?: string) {
    steps.value = steps.value.map((step) => {
      if (step.key === key) {
        return {
          ...step,
          detail: detail || step.detail,
          status: "running"
        };
      }
      if (step.status === "running") {
        return { ...step, status: "done" };
      }
      return step;
    });
  }

  function setFinal(status: AgentStepStatus, detail?: string) {
    const lastIndex = steps.value.length - 1;
    steps.value = steps.value.map((step, index) => {
      if (index < lastIndex && step.status === "pending") {
        return { ...step, status: "done" };
      }
      if (index === lastIndex) {
        return {
          ...step,
          detail: detail || step.detail,
          status
        };
      }
      if (step.status === "running") {
        return { ...step, status: "done" };
      }
      return step;
    });
  }

  function applyStatus(label: string) {
    liveLabel.value = label;
    if (/理解|分析/.test(label)) {
      setRunning("understand", label);
      return;
    }
    if (/偏好|条件/.test(label)) {
      setRunning("preference", label);
      return;
    }
    if (/工具|搜索|查询/.test(label)) {
      setRunning("search", label);
      return;
    }
    if (/整理|排序/.test(label)) {
      setRunning("sort", label);
      return;
    }
    if (/输出|生成|完成/.test(label)) {
      setRunning("result", label);
      return;
    }
  }

  return {
    steps: computed(() => steps.value),
    liveLabel: computed(() => liveLabel.value),
    reset,
    setRunning,
    setFinal,
    applyStatus
  };
}
