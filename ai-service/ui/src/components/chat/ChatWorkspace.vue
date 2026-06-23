<template>
  <section class="relative flex h-full min-h-0 flex-col overflow-hidden rounded-[28px] border border-app-line/70 bg-white/60 shadow-soft backdrop-blur-md">
    <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(201,133,107,0.12),transparent_30%),radial-gradient(circle_at_right,rgba(151,167,137,0.08),transparent_26%)]"></div>

    <header class="relative z-10 flex flex-wrap items-start justify-between gap-4 border-b border-app-line/70 px-6 py-5">
      <div class="min-w-0">
        <div class="text-sm font-medium text-brand-deep">AstraHost AI 工作台</div>
        <div class="mt-2 flex flex-wrap items-center gap-2 text-sm text-app-mute">
          <span class="rounded-full bg-white/80 px-3 py-1.5">会话 {{ activeConversationLabel }}</span>
          <span class="rounded-full bg-white/80 px-3 py-1.5">{{ statusLabel || "等待输入" }}</span>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <button
          class="inline-flex items-center gap-2 rounded-full border border-app-line/80 bg-white/80 px-4 py-2 text-sm text-app-mute transition hover:border-brand/40 hover:text-brand-deep"
          type="button"
          @click="$emit('preview')"
        >
          <Hotel class="h-4 w-4" />
          <span>预览房源</span>
        </button>
        <button
          class="inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm transition"
          :class="
            traceVisible
              ? 'border-brand/40 bg-brand-soft text-brand-deep'
              : 'border-app-line/80 bg-white/80 text-app-mute hover:border-brand/40 hover:text-brand-deep'
          "
          type="button"
          @click="$emit('toggle-trace')"
        >
          <Sparkles class="h-4 w-4" />
          <span>{{ traceVisible ? "隐藏轨迹" : "查看轨迹" }}</span>
        </button>
      </div>
    </header>

    <div
      ref="scrollRef"
      class="copilot-scrollbar relative z-10 min-h-0 flex-1 overflow-y-auto px-6"
      :class="isEmptyState ? 'pb-[220px]' : 'pb-[360px]'"
    >
      <div v-if="isEmptyState" class="flex min-h-full items-center justify-center py-12">
        <div class="w-full max-w-[980px] space-y-8">
          <GreetingHero :greeting="greeting" :user-name="userName" />
          <QuickActionGrid :actions="quickActions" @select="$emit('pick-suggestion', $event)" />
        </div>
      </div>

      <div v-else class="space-y-5 pb-8 pt-6">
        <MessageBubble
          v-for="item in messages"
          :key="item.id"
          :message="item"
          @follow-up="$emit('follow-up', $event)"
          @confirm-action="$emit('confirm-action', $event)"
        />
        <div
          v-if="streaming"
          class="inline-flex items-center gap-2 rounded-full border border-app-line/80 bg-white/85 px-4 py-2 text-sm text-app-mute"
        >
          <span class="h-2 w-2 rounded-full bg-brand animate-pulse"></span>
          AI 正在整理回复
        </div>
      </div>
    </div>

    <div class="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-28 bg-gradient-to-t from-[#FCFAF8] via-[#FCFAF8]/88 to-transparent"></div>

    <div class="absolute inset-x-0 bottom-0 z-20 px-5 pb-5">
      <div v-if="showSuggestions" class="copilot-scrollbar mb-3 overflow-x-auto px-1 pb-1">
        <div class="flex w-max min-w-full gap-2 px-1">
          <button
            v-for="item in suggestions"
            :key="item"
            class="shrink-0 rounded-full border border-app-line/70 bg-white/80 px-3 py-1.5 text-sm text-app-mute transition hover:border-brand/30 hover:bg-brand-soft/70 hover:text-brand-deep"
            type="button"
            @click="$emit('pick-suggestion', item)"
          >
            {{ item }}
          </button>
        </div>
      </div>

      <div class="rounded-[28px] border border-white/70 bg-[rgba(255,250,245,0.78)] shadow-lift backdrop-blur-xl">
        <div class="flex items-end gap-3 px-4 pt-4">
          <button
            class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-app-line/70 bg-white/70 text-app-mute transition hover:border-brand/30 hover:text-brand-deep"
            title="上传资料"
            type="button"
          >
            <Paperclip class="h-4 w-4" />
          </button>

          <div class="min-w-0 flex-1">
            <textarea
              :value="draft"
              class="h-[96px] w-full resize-none border-0 bg-transparent px-2 py-2 text-sm leading-7 text-app-text placeholder:text-app-mute/80 focus:ring-0"
              maxlength="2000"
              placeholder="例如：帮我处理今晚延迟入住的订单，并同步推荐可替代房源"
              @input="$emit('update:draft', ($event.target as HTMLTextAreaElement).value)"
              @keydown.enter.exact.prevent="$emit('send')"
            />
          </div>

          <div class="flex items-end gap-2 pb-1">
            <button
              class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-app-line/70 bg-white/70 text-app-mute transition hover:border-brand/30 hover:text-brand-deep"
              title="语音输入"
              type="button"
            >
              <Mic class="h-4 w-4" />
            </button>
            <button
              class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-brand text-white transition hover:bg-brand-deep disabled:cursor-not-allowed disabled:opacity-55"
              :disabled="streaming || !draft.trim()"
              type="button"
              @click="$emit('send')"
            >
              <SendHorizonal class="h-5 w-5" />
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between gap-4 px-5 pb-4 pt-2 text-xs text-app-mute">
          <span>支持房源推荐、订单处理、支付协助与客户沟通</span>
          <span>{{ draft.length }} / 2000</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { Hotel, Mic, Paperclip, SendHorizontal as SendHorizonal, Sparkles } from "lucide-vue-next";
import type { ChatMessage } from "../../types/copilot";
import MessageBubble from "./MessageBubble.vue";
import GreetingHero from "../workspace/GreetingHero.vue";
import QuickActionGrid from "../workspace/QuickActionGrid.vue";

interface QuickActionItem {
  key: string;
  title: string;
  subtitle: string;
  prompt: string;
}

const props = defineProps<{
  messages: ChatMessage[];
  draft: string;
  suggestions: string[];
  streaming: boolean;
  statusLabel: string;
  activeConversationLabel: string;
  greeting: string;
  userName: string;
  quickActions: QuickActionItem[];
  isEmptyState: boolean;
  traceVisible: boolean;
}>();

defineEmits<{
  (event: "update:draft", value: string): void;
  (event: "send"): void;
  (event: "pick-suggestion", value: string): void;
  (event: "follow-up", value: string): void;
  (event: "confirm-action", value: string): void;
  (event: "preview"): void;
  (event: "toggle-trace"): void;
}>();

const scrollRef = ref<HTMLElement | null>(null);
const showSuggestions = computed(
  () =>
    !props.isEmptyState &&
    props.suggestions.length > 0 &&
    !props.messages.some((message) => Boolean(message.recommendations?.cards?.length))
);

watch(
  () => [props.messages.length, props.streaming],
  async () => {
    await nextTick();
    if (scrollRef.value) {
      scrollRef.value.scrollTop = props.isEmptyState ? 0 : scrollRef.value.scrollHeight;
    }
  }
);
</script>
