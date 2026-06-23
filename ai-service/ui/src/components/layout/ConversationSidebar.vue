<template>
  <aside
    class="flex h-full flex-col overflow-hidden rounded-card border border-app-line/70 bg-[#F5F0EA]/88 shadow-soft backdrop-blur-md transition-[width,padding] duration-300"
    :class="collapsed ? 'w-[88px] px-3 py-4' : 'w-[250px] px-4 py-5'"
  >
    <div class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-[18px] bg-brand text-white">
          <Sparkles class="h-5 w-5" />
        </div>
        <div v-if="!collapsed" class="min-w-0">
          <h1 class="truncate text-lg font-semibold text-app-text">AstraHost</h1>
          <p class="truncate text-xs text-app-mute">AI 智能管家工作台</p>
        </div>
      </div>

      <button
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-app-line/80 bg-white/70 text-app-mute transition hover:border-brand/40 hover:text-brand-deep"
        :title="collapsed ? '展开侧栏' : '收起侧栏'"
        type="button"
        @click="$emit('toggle-collapse')"
      >
        <ChevronRight v-if="collapsed" class="h-4 w-4" />
        <ChevronLeft v-else class="h-4 w-4" />
      </button>
    </div>

    <button
      class="mt-5 flex h-12 items-center justify-center rounded-[18px] bg-brand text-sm font-medium text-white transition hover:bg-brand-deep"
      :class="collapsed ? 'w-12 self-center' : 'w-full gap-2'"
      :title="collapsed ? '新建会话' : undefined"
      type="button"
      @click="$emit('new-chat')"
    >
      <Plus class="h-4 w-4" />
      <span v-if="!collapsed">新建会话</span>
    </button>

    <div class="mt-6 flex min-h-0 flex-1 flex-col">
      <div v-if="!collapsed" class="mb-3 flex items-center justify-between px-1">
        <h2 class="text-sm font-medium text-app-text">历史会话</h2>
        <span class="rounded-full bg-white/70 px-2.5 py-1 text-xs text-app-mute">{{ conversations.length }}</span>
      </div>

      <div class="copilot-scrollbar min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <button
          v-for="item in conversations"
          :key="item.id"
          class="group flex w-full items-center gap-3 rounded-[18px] border text-left transition"
          :class="
            collapsed
              ? item.id === activeConversationId
                ? 'justify-center border-brand/30 bg-brand-soft/90 p-2.5'
                : 'justify-center border-transparent bg-white/55 p-2.5 hover:border-app-line hover:bg-white/80'
              : item.id === activeConversationId
                ? 'border-brand/30 bg-brand-soft/90 px-3 py-3'
                : 'border-transparent bg-white/55 px-3 py-3 hover:border-app-line hover:bg-white/80'
          "
          :title="collapsed ? item.title : undefined"
          type="button"
          @click="$emit('select-conversation', item.id)"
        >
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-[16px] bg-white/80 text-sm font-semibold text-app-text">
            {{ conversationGlyph(item.title) }}
          </div>

          <div v-if="!collapsed" class="min-w-0 flex-1">
            <div class="truncate text-sm font-medium text-app-text">{{ item.title }}</div>
            <div class="mt-1 text-xs text-app-mute">{{ formatConversationTime(item.updatedAt) }}</div>
          </div>

          <button
            v-if="!collapsed"
            class="hidden h-8 w-8 shrink-0 items-center justify-center rounded-full text-app-mute transition hover:bg-white hover:text-red-500 group-hover:flex"
            title="删除会话"
            type="button"
            @click.stop="$emit('delete-conversation', item.id)"
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </button>

        <div
          v-if="!conversations.length"
          class="flex items-center justify-center rounded-[18px] border border-dashed border-app-line/80 bg-white/45 text-app-mute"
          :class="collapsed ? 'h-14 text-xs' : 'px-4 py-6 text-sm'"
        >
          {{ collapsed ? '暂无' : '暂无历史会话' }}
        </div>
      </div>
    </div>

    <div v-if="!collapsed" class="mt-4 border-t border-app-line/70 pt-4">
      <button
        class="flex w-full items-center justify-between gap-3 rounded-[18px] bg-white/55 px-3 py-3 text-left transition hover:bg-white/75"
        type="button"
        @click="identityOpen = !identityOpen"
      >
        <div class="flex min-w-0 items-center gap-3">
          <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-semibold text-brand-deep">
            {{ conversationGlyph(userContext.username) }}
          </div>
          <div class="min-w-0">
            <div class="truncate text-sm font-medium text-app-text">{{ userContext.username }}</div>
            <div class="text-xs text-app-mute">{{ userContext.role }}</div>
          </div>
        </div>
        <div class="flex items-center gap-2 text-app-mute">
          <SlidersHorizontal class="h-4 w-4" />
          <ChevronDown class="h-4 w-4 transition-transform" :class="identityOpen ? 'rotate-180' : ''" />
        </div>
      </button>

      <div v-if="identityOpen" class="mt-3 grid gap-3 rounded-[18px] bg-white/50 p-3">
        <label class="grid gap-1.5 text-xs text-app-mute">
          用户 ID
          <input
            :value="userContext.id"
            class="rounded-input border-app-line bg-white/80 px-3 py-2 text-sm text-app-text"
            type="text"
            @input="updateTextField('id', $event)"
          />
        </label>
        <label class="grid gap-1.5 text-xs text-app-mute">
          昵称
          <input
            :value="userContext.username"
            class="rounded-input border-app-line bg-white/80 px-3 py-2 text-sm text-app-text"
            type="text"
            @input="updateTextField('username', $event)"
          />
        </label>
        <label class="grid gap-1.5 text-xs text-app-mute">
          角色
          <select
            :value="userContext.role"
            class="rounded-input border-app-line bg-white/80 px-3 py-2 text-sm text-app-text"
            @change="updateTextField('role', $event)"
          >
            <option value="USER">USER</option>
            <option value="MERCHANT">MERCHANT</option>
            <option value="ADMIN">ADMIN</option>
          </select>
        </label>
        <label class="grid gap-1.5 text-xs text-app-mute">
          商家 ID
          <input
            :value="userContext.merchantId || ''"
            class="rounded-input border-app-line bg-white/80 px-3 py-2 text-sm text-app-text"
            placeholder="可留空"
            type="text"
            @input="updateTextField('merchantId', $event)"
          />
        </label>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ChevronDown, ChevronLeft, ChevronRight, Plus, SlidersHorizontal, Sparkles, Trash2 } from "lucide-vue-next";
import { formatConversationTime } from "../../lib/time";
import type { ConversationSummary, UserContext } from "../../types/copilot";

defineProps<{
  collapsed: boolean;
  conversations: ConversationSummary[];
  activeConversationId: string;
  userContext: UserContext;
}>();

const emit = defineEmits<{
  (event: "toggle-collapse"): void;
  (event: "new-chat"): void;
  (event: "select-conversation", id: string): void;
  (event: "delete-conversation", id: string): void;
  (event: "update-user-context", value: Partial<UserContext>): void;
}>();

const identityOpen = ref(false);

function conversationGlyph(value: string) {
  const normalized = value.trim();
  return normalized ? normalized.charAt(0).toUpperCase() : "A";
}

function updateTextField(key: keyof UserContext, event: Event) {
  const target = event.target as HTMLInputElement | HTMLSelectElement | null;
  const value = target?.value || "";
  emit("update-user-context", {
    [key]: key === "merchantId" ? value || null : value
  });
}
</script>
