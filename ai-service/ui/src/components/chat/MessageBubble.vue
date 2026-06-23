<template>
  <div class="animate-slide-up">
    <div class="flex gap-3" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
      <div
        v-if="message.role === 'assistant'"
        class="mt-1 flex h-10 w-10 flex-none items-center justify-center rounded-full bg-brand text-white"
      >
        <Sparkles class="h-4 w-4" />
      </div>
      <div class="max-w-[min(100%,780px)]">
        <div
          class="rounded-bubble border px-4 py-3"
          :class="
            message.role === 'assistant'
              ? message.error
                ? 'border-red-200 bg-red-50/80'
                : 'border-app-line/70 bg-white/82'
              : 'border-transparent bg-brand-soft/85'
          "
        >
          <div
            v-if="message.role === 'assistant'"
            class="markdown-body"
            v-html="renderMarkdown(message.content || '正在整理信息...')"
          />
          <div v-else class="whitespace-pre-wrap text-sm leading-7 text-app-text">
            {{ message.content }}
          </div>
        </div>

        <div class="mt-2 px-1 text-xs text-app-mute">{{ formatMessageTime(message.createdAt) }}</div>

        <div
          v-if="message.role === 'assistant' && message.pendingAction"
          class="mt-3 rounded-card border border-[#E9C89A] bg-[#FBF3E5] px-4 py-3 text-sm text-[#815C34]"
        >
          <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div class="space-y-2">
              <p class="font-medium">
                待确认操作
                <span v-if="message.pendingAction.summary?.target_label">· {{ message.pendingAction.summary.target_label }}</span>
              </p>
              <p v-if="message.pendingAction.summary?.current_status" class="text-[#8B6A46]">
                当前状态：{{ message.pendingAction.summary.current_status }}
              </p>
              <p v-if="message.pendingAction.summary?.impact" class="text-[#8B6A46]">
                影响：{{ message.pendingAction.summary.impact }}
              </p>
              <p v-if="message.pendingAction.summary?.reason" class="text-[#8B6A46]">
                原因：{{ message.pendingAction.summary.reason }}
              </p>
              <p class="text-xs text-[#8B6A46]">
                将在 {{ formatExpiresAt(message.pendingAction.expires_at) }} 前有效
              </p>
            </div>

            <button
              class="rounded-button bg-[#D29A5A] px-4 py-2 text-sm font-medium text-white transition hover:bg-[#BF8746]"
              type="button"
              @click="$emit('confirm-action', message.pendingAction.confirmation_text)"
            >
              确认执行
            </button>
          </div>
        </div>
      </div>
      <div
        v-if="message.role === 'user'"
        class="mt-1 flex h-10 w-10 flex-none items-center justify-center rounded-full bg-white/75 text-app-text"
      >
        <User class="h-4 w-4" />
      </div>
    </div>

    <div
      v-if="message.role === 'assistant' && message.recommendations && message.recommendations.cards.length"
      class="result-rail-shell mt-4"
    >
      <RecommendationRail
        :recommendations="message.recommendations"
        @follow-up="$emit('follow-up', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Sparkles, User } from "lucide-vue-next";
import { renderMarkdown } from "../../lib/markdown";
import { formatMessageTime } from "../../lib/time";
import type { ChatMessage } from "../../types/copilot";
import RecommendationRail from "../recommendations/RecommendationRail.vue";

defineProps<{
  message: ChatMessage;
}>();

defineEmits<{
  (event: "follow-up", prompt: string): void;
  (event: "confirm-action", confirmationText: string): void;
}>();

function formatExpiresAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}
</script>
