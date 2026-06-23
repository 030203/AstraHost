<template>
  <div class="h-screen overflow-hidden bg-app-bg text-app-text">
    <div class="flex h-full gap-3 p-3">
      <ConversationSidebar
        :collapsed="sidebarCollapsed"
        :conversations="conversations"
        :active-conversation-id="conversationId"
        :user-context="userContext"
        @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
        @new-chat="resetConversation"
        @select-conversation="selectConversation"
        @delete-conversation="deleteConversation"
        @update-user-context="mergeUserContext"
      />

      <main class="min-w-0 flex-1">
        <ChatWorkspace
          :messages="messages"
          :draft="draft"
          :suggestions="suggestions"
          :streaming="streaming"
          :status-label="statusLabel"
          :active-conversation-label="conversationId ? conversationId.slice(0, 8) : '新的会话'"
          :greeting="greetingText"
          :user-name="userContext.username"
          :quick-actions="quickActions"
          :is-empty-state="isEmptyState"
          :trace-visible="isTraceVisible"
          @update:draft="draft = $event"
          @send="sendMessage"
          @pick-suggestion="applySuggestion"
          @follow-up="applySuggestion"
          @confirm-action="applySuggestionAndSend"
          @preview="renderPreview"
          @toggle-trace="toggleTraceVisibility"
        />
      </main>

      <AgentPanel
        :visible="isTraceVisible"
        :steps="agentSteps"
        :live-label="agentLiveLabel"
        :tool-logs="toolLogs"
        @close="hideTrace"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import AgentPanel from "./components/agent/AgentPanel.vue";
import ChatWorkspace from "./components/chat/ChatWorkspace.vue";
import ConversationSidebar from "./components/layout/ConversationSidebar.vue";
import { useAgentTimeline } from "./composables/useAgentTimeline";
import { useLocalConversations } from "./composables/useLocalConversations";
import { buildUserContextFromStorage } from "./lib/auth";
import { getConversationIds, getSuggestions, streamChat } from "./lib/api";
import { DEFAULT_GREETING, DEFAULT_SUGGESTIONS, FALLBACK_CARD_IMAGE, QUICK_ACTIONS } from "./lib/fallbacks";
import { formatGreeting } from "./lib/time";
import type {
  ChatMessage,
  PendingActionPayload,
  RecommendationsPayload,
  ToolLogItem,
  UserContext
} from "./types/copilot";

const greetingText = computed(() => formatGreeting());
const quickActions = QUICK_ACTIONS;
const draft = ref("");
const suggestions = ref<string[]>(DEFAULT_SUGGESTIONS);
const messages = ref<ChatMessage[]>([]);
const conversationId = ref("");
const statusLabel = ref("等待输入");
const streaming = ref(false);
const toolLogs = ref<ToolLogItem[]>([]);
const abortController = ref<AbortController | null>(null);
const pendingAction = ref<PendingActionPayload | null>(null);
const sidebarCollapsed = ref(false);
const traceManuallyOpen = ref(false);
const traceManuallyHidden = ref(false);

const guestUserContext: UserContext = {
  id: "guest_10001",
  username: "demo_guest",
  role: "USER",
  merchantId: null
};

const userContext = ref<UserContext>({ ...guestUserContext });

const { items: conversations, save, remove, syncRemote } = useLocalConversations();
const {
  steps: agentSteps,
  liveLabel: agentLiveLabel,
  reset: resetAgent,
  applyStatus,
  setRunning,
  setFinal
} = useAgentTimeline();

const isEmptyState = computed(
  () =>
    !streaming.value &&
    messages.value.length === 1 &&
    messages.value[0]?.role === "assistant" &&
    messages.value[0]?.content === DEFAULT_GREETING
);

const hasTraceActivity = computed(() => toolLogs.value.length > 0 || Boolean(pendingAction.value));
const isTraceVisible = computed(
  () => (traceManuallyOpen.value || hasTraceActivity.value) && !traceManuallyHidden.value
);

watch(hasTraceActivity, (active, previous) => {
  if (active && !previous) {
    traceManuallyHidden.value = false;
  }
  if (!active) {
    traceManuallyOpen.value = false;
    traceManuallyHidden.value = false;
  }
});

function uid(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function resetTracePanelState() {
  traceManuallyOpen.value = false;
  traceManuallyHidden.value = false;
}

function showTrace() {
  traceManuallyHidden.value = false;
  traceManuallyOpen.value = true;
}

function hideTrace() {
  traceManuallyOpen.value = false;
  traceManuallyHidden.value = true;
}

function toggleTraceVisibility() {
  if (isTraceVisible.value) {
    hideTrace();
    return;
  }
  showTrace();
}

function ensureConversationId() {
  if (!conversationId.value) {
    conversationId.value = crypto?.randomUUID?.() || uid("conv");
  }
}

function pushMessage(payload: Omit<ChatMessage, "id" | "createdAt">) {
  messages.value.push({
    id: uid(payload.role),
    createdAt: Date.now(),
    ...payload
  });
}

function resetConversation() {
  if (abortController.value) {
    abortController.value.abort();
    abortController.value = null;
  }
  draft.value = "";
  conversationId.value = "";
  messages.value = [
    {
      id: uid("assistant"),
      role: "assistant",
      content: DEFAULT_GREETING,
      createdAt: Date.now()
    }
  ];
  toolLogs.value = [];
  pendingAction.value = null;
  statusLabel.value = "等待输入";
  streaming.value = false;
  resetAgent();
  resetTracePanelState();
}

function selectConversation(id: string) {
  conversationId.value = id;
  messages.value = [
    {
      id: uid("assistant"),
      role: "assistant",
      content: `已切换到会话 ${id.slice(0, 8)}。当前后端只保存上下文，不回放旧消息，你可以继续追问。`,
      createdAt: Date.now()
    }
  ];
  toolLogs.value = [];
  pendingAction.value = null;
  statusLabel.value = "已切换会话";
  resetAgent();
  resetTracePanelState();
}

function deleteConversation(id: string) {
  remove(id);
  if (conversationId.value === id) {
    resetConversation();
  }
}

function mergeUserContext(value: Partial<UserContext>) {
  userContext.value = {
    ...userContext.value,
    ...value
  };
}

function syncUserContextFromStorage() {
  userContext.value = buildUserContextFromStorage() || { ...guestUserContext };
}

function applySuggestion(value: string) {
  draft.value = value;
}

function applySuggestionAndSend(value: string) {
  draft.value = value;
  void sendMessage();
}

function upsertToolLog(next: ToolLogItem) {
  const found = toolLogs.value.findIndex((item) => item.tool === next.tool);
  if (found >= 0) {
    toolLogs.value[found] = next;
    toolLogs.value = [...toolLogs.value];
    return;
  }
  toolLogs.value.push(next);
}

function attachRecommendations(messageId: string, recommendations: RecommendationsPayload | null | undefined) {
  if (!recommendations?.cards?.length) return;
  const index = messages.value.findIndex((item) => item.id === messageId);
  if (index >= 0) {
    messages.value[index] = {
      ...messages.value[index],
      recommendations: {
        ...recommendations,
        cards: recommendations.cards.map((card) => ({
          ...card,
          imageUrl: card.imageUrl || FALLBACK_CARD_IMAGE
        }))
      }
    };
    messages.value = [...messages.value];
  }
}

async function sendMessage() {
  const message = draft.value.trim();
  if (!message || streaming.value) return;
  const currentPendingAction = pendingAction.value;

  ensureConversationId();
  save({
    id: conversationId.value,
    title: message.slice(0, 30) || "新对话",
    updatedAt: Date.now()
  });

  pushMessage({ role: "user", content: message });
  const assistantId = uid("assistant");
  messages.value.push({
    id: assistantId,
    role: "assistant",
    content: "",
    createdAt: Date.now()
  });

  draft.value = "";
  streaming.value = true;
  statusLabel.value = "分析中...";
  toolLogs.value = [];
  resetAgent();
  resetTracePanelState();
  applyStatus("分析中...");

  const controller = new AbortController();
  abortController.value = controller;

  try {
    await streamChat({
      message,
      conversationId: conversationId.value,
      userContext: userContext.value,
      pendingAction: currentPendingAction,
      signal: controller.signal,
      onEvent(event) {
        if (event.type === "meta") {
          if (typeof event.conversationId === "string" && event.conversationId) {
            conversationId.value = event.conversationId;
          }
          statusLabel.value = "已连接";
          return;
        }

        if (event.type === "status") {
          const label = String(event.label || "处理中");
          statusLabel.value = label;
          applyStatus(label);
          return;
        }

        if (event.type === "tool_start") {
          const label = String(event.label || event.tool || "工具调用");
          upsertToolLog({
            tool: String(event.tool || label),
            label,
            status: "running"
          });
          showTrace();
          setRunning("search", label);
          statusLabel.value = label;
          return;
        }

        if (event.type === "tool_end") {
          const isError = event.status === "error";
          const label = String(event.label || event.tool || "工具调用");
          upsertToolLog({
            tool: String(event.tool || label),
            label,
            status: isError ? "error" : "done",
            summary: String(event.summary || "")
          });
          statusLabel.value = isError ? "工具返回异常" : "工具调用完成";
          applyStatus(isError ? "工具返回异常" : "正在整理结果");
          return;
        }

        if (event.type === "chunk") {
          const index = messages.value.findIndex((item) => item.id === assistantId);
          if (index >= 0) {
            messages.value[index] = {
              ...messages.value[index],
              content: messages.value[index].content + String(event.content || "")
            };
            messages.value = [...messages.value];
          }
          statusLabel.value = "正在输出回答";
          setRunning("result", "正在生成回复内容");
          return;
        }

        if (event.type === "done") {
          attachRecommendations(assistantId, (event.recommendations as RecommendationsPayload | null) || null);
          const nextPendingAction = (event.pendingAction as PendingActionPayload | null) || null;
          pendingAction.value = nextPendingAction;
          if (nextPendingAction) {
            showTrace();
          }
          if (nextPendingAction) {
            const index = messages.value.findIndex((item) => item.id === assistantId);
            if (index >= 0) {
              messages.value[index] = {
                ...messages.value[index],
                pendingAction: nextPendingAction
              };
              messages.value = [...messages.value];
            }
          }
          statusLabel.value = "回答完成";
          setFinal("done", "已生成最终回复和推荐结果");
          save({
            id: conversationId.value,
            title: message.slice(0, 30) || "新对话",
            updatedAt: Date.now()
          });
          return;
        }

        if (event.type === "error") {
          throw new Error(String(event.error || "请求失败"));
        }
      }
    });
  } catch (error) {
    const index = messages.value.findIndex((item) => item.id === assistantId);
    if (index >= 0) {
      messages.value[index] = {
        ...messages.value[index],
        content: `请求失败：${error instanceof Error ? error.message : "未知错误"}`,
        error: true
      };
      messages.value = [...messages.value];
    }
    statusLabel.value = "请求失败";
    setFinal("error", "生成过程中出现异常");
  } finally {
    streaming.value = false;
    abortController.value = null;
  }
}

function renderPreview() {
  resetConversation();
  pushMessage({
    role: "user",
    content: "推荐东京新宿区，适合 4 人家庭入住的酒店，预算每晚 1000-1500 元，带厨房和洗衣机"
  });
  messages.value.push({
    id: uid("assistant"),
    role: "assistant",
    content: "好的，我已经根据位置、人数、预算和设施偏好整理出一组更适合家庭入住的房源，先看卡片，再决定是否继续问我细节。",
    createdAt: Date.now(),
    recommendations: {
      title: "为您推荐的酒店",
      subtitle: "东京 · 新宿区 · 4 人家庭 · 1000-1500 元/晚",
      count: 4,
      cards: [
        {
          id: "1",
          name: "新宿家庭公寓",
          location: "新宿区 · 距离新宿站 450m",
          priceLabel: "¥1,280 / 晚",
          rating: "4.8",
          reviewCount: 156,
          type: "整套公寓",
          highlights: ["厨房", "洗衣机", "Wi-Fi", "亲子友好"],
          summary: "空间完整，适合一家四口入住，离地铁站近，生活便利。",
          imageUrl: FALLBACK_CARD_IMAGE
        },
        {
          id: "2",
          name: "新宿中心家庭套房",
          location: "新宿区 · 距离新宿站 600m",
          priceLabel: "¥1,150 / 晚",
          rating: "4.7",
          reviewCount: 89,
          type: "家庭套房",
          highlights: ["早餐", "双床房", "洗衣服务", "近商圈"],
          summary: "预算友好，适合家庭短住，交通和餐饮都方便。",
          imageUrl: FALLBACK_CARD_IMAGE
        },
        {
          id: "3",
          name: "新宿阳光家庭公寓",
          location: "新宿区 · 距离新宿站 800m",
          priceLabel: "¥1,380 / 晚",
          rating: "4.6",
          reviewCount: 72,
          type: "整套公寓",
          highlights: ["厨房", "客厅", "洗衣机", "采光好"],
          summary: "适合希望住得更宽敞的家庭，设备齐全，适合多日停留。",
          imageUrl: FALLBACK_CARD_IMAGE
        },
        {
          id: "4",
          name: "新宿和风家庭房",
          location: "新宿区 · 距离新宿站 550m",
          priceLabel: "¥1,450 / 晚",
          rating: "4.9",
          reviewCount: 112,
          type: "家庭房",
          highlights: ["和风风格", "厨房", "洗衣机", "高评分"],
          summary: "风格更有在地感，适合重视体验感的家庭客人。",
          imageUrl: FALLBACK_CARD_IMAGE
        }
      ]
    },
    pendingAction: {
      token: "preview-confirm-token",
      tool: "cancel_booking",
      arguments: {
        booking_id: 5108,
        reason: "行程变更"
      },
      expires_at: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
      confirmation_text: "确认取消订单 BK177383620199277AB4AAA",
      summary: {
        action: "cancel_booking",
        target_type: "booking",
        target_id: "5108",
        target_label: "订单 BK177383620199277AB4AAA",
        current_status: "CONFIRMED",
        impact: "订单状态将变为已取消，可能触发平台取消规则。",
        reason: "行程变更"
      }
    }
  });
  toolLogs.value = [
    { tool: "analyze", label: "理解需求", status: "done", summary: "已识别位置、人数、预算和设施偏好" },
    { tool: "search_properties", label: "搜索酒店", status: "done", summary: "已检索到 12 个匹配房源" }
  ];
  pendingAction.value = messages.value[messages.value.length - 1].pendingAction || null;
  resetTracePanelState();
  setRunning("result", "生成推荐结果");
  setFinal("done", "预览数据已完成渲染");
  statusLabel.value = "预览模式";
}

onMounted(async () => {
  syncUserContextFromStorage();
  window.addEventListener("user-changed", syncUserContextFromStorage);
  window.addEventListener("storage", syncUserContextFromStorage);
  resetConversation();
  try {
    suggestions.value = await getSuggestions();
  } catch {
    suggestions.value = DEFAULT_SUGGESTIONS;
  }

  try {
    const ids = await getConversationIds();
    syncRemote(ids);
  } catch {
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("user-changed", syncUserContextFromStorage);
  window.removeEventListener("storage", syncUserContextFromStorage);
});
</script>
