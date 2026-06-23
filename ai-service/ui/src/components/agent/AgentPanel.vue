<template>
  <aside
    class="hidden h-full shrink-0 overflow-hidden transition-[width,opacity,transform] duration-300 xl:block"
    :class="visible ? 'w-[300px] opacity-100 translate-x-0' : 'pointer-events-none w-0 translate-x-6 opacity-0'"
  >
    <div class="flex h-full w-[300px] flex-col rounded-card border border-app-line/70 bg-[#F7F2ED]/92 p-4 shadow-soft backdrop-blur-md">
      <div class="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 class="text-lg font-semibold text-app-text">AI Workspace Trace</h3>
          <p class="mt-1 text-sm text-app-mute">仅在复杂任务执行时展开。</p>
        </div>
        <div class="flex items-center gap-2">
          <div class="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-2 text-xs text-app-mute">
            <span class="h-2 w-2 rounded-full bg-brand animate-pulse"></span>
            {{ liveLabel }}
          </div>
          <button
            class="flex h-9 w-9 items-center justify-center rounded-full border border-app-line/80 bg-white/80 text-app-mute transition hover:border-brand/30 hover:text-brand-deep"
            title="关闭轨迹"
            type="button"
            @click="$emit('close')"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <div class="copilot-scrollbar min-h-0 flex-1 overflow-y-auto pr-1">
        <ol class="space-y-3">
          <li v-for="(step, index) in steps" :key="step.key" class="relative pl-8">
            <span
              v-if="index < steps.length - 1"
              class="absolute left-[11px] top-7 h-[calc(100%+10px)] w-px bg-app-line/80"
            ></span>
            <span
              class="absolute left-0 top-1 flex h-[22px] w-[22px] items-center justify-center rounded-full border text-xs"
              :class="indicatorClass(step.status)"
            >
              <Check v-if="step.status === 'done'" class="h-3.5 w-3.5" />
              <AlertCircle v-else-if="step.status === 'error'" class="h-3.5 w-3.5" />
              <span
                v-else
                class="h-2.5 w-2.5 rounded-full bg-current"
                :class="step.status === 'running' ? 'animate-pulse' : ''"
              ></span>
            </span>
            <div class="rounded-[20px] border border-app-line/60 bg-white/65 p-4">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <div class="text-sm font-medium text-app-text">{{ step.label }}</div>
                  <div class="mt-1 text-sm leading-6 text-app-mute">{{ step.detail }}</div>
                </div>
                <span class="rounded-full px-2.5 py-1 text-xs" :class="badgeClass(step.status)">
                  {{ statusText(step.status) }}
                </span>
              </div>
            </div>
          </li>
        </ol>
      </div>

      <div class="mt-4 space-y-3 rounded-[20px] border border-app-line/60 bg-white/58 p-4">
        <div class="text-sm font-medium text-app-text">工具轨迹</div>
        <div v-if="!toolLogs.length" class="text-sm text-app-mute">当前还没有工具调用记录。</div>
        <div
          v-for="item in toolLogs"
          :key="`${item.tool}-${item.summary}`"
          class="rounded-[18px] border border-app-line/60 bg-white/75 px-3 py-3 text-sm"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="font-medium text-app-text">{{ item.label }}</span>
            <span :class="badgeClass(item.status)" class="rounded-full px-2.5 py-1 text-xs">
              {{ statusText(item.status) }}
            </span>
          </div>
          <p v-if="item.summary" class="mt-2 leading-6 text-app-mute">{{ item.summary }}</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { AlertCircle, Check, X } from "lucide-vue-next";
import type { AgentStep, AgentStepStatus, ToolLogItem } from "../../types/copilot";

defineProps<{
  visible: boolean;
  steps: AgentStep[];
  liveLabel: string;
  toolLogs: ToolLogItem[];
}>();

defineEmits<{
  (event: "close"): void;
}>();

function indicatorClass(status: AgentStepStatus) {
  if (status === "done") return "border-success/40 bg-success/10 text-success";
  if (status === "error") return "border-red-200 bg-red-50 text-red-500";
  if (status === "running") return "border-brand/40 bg-brand-soft text-brand-deep";
  return "border-app-line/80 bg-white text-app-mute";
}

function badgeClass(status: AgentStepStatus | ToolLogItem["status"]) {
  if (status === "done") return "bg-green-50 text-success";
  if (status === "error") return "bg-red-50 text-red-500";
  if (status === "running") return "bg-brand-soft text-brand-deep";
  return "bg-white text-app-mute";
}

function statusText(status: AgentStepStatus | ToolLogItem["status"]) {
  if (status === "done") return "完成";
  if (status === "error") return "异常";
  if (status === "running") return "执行中";
  return "等待";
}
</script>
