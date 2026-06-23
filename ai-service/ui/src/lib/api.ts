import type { PendingActionPayload, UserContext } from "../types/copilot";
import { buildAuthHeaders } from "./auth";

export async function getSuggestions(): Promise<string[]> {
  const response = await fetch("/suggestions");
  if (!response.ok) {
    throw new Error("快捷问题加载失败");
  }
  return response.json();
}

export async function getConversationIds(): Promise<string[]> {
  const response = await fetch("/conversations", {
    headers: buildAuthHeaders()
  });
  if (!response.ok) {
    throw new Error("历史会话加载失败");
  }
  const payload = await response.json();
  return Array.isArray(payload.conversationIds) ? payload.conversationIds : [];
}

export async function streamChat(payload: {
  message: string;
  conversationId: string;
  userContext: UserContext;
  pendingAction?: PendingActionPayload | null;
  signal: AbortSignal;
  onEvent: (event: Record<string, unknown>) => void;
}): Promise<void> {
  const response = await fetch("/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...buildAuthHeaders()
    },
    body: JSON.stringify({
      message: payload.message,
      conversationId: payload.conversationId,
      userContext: payload.userContext,
      pendingAction: payload.pendingAction || null
    }),
    signal: payload.signal
  });

  if (!response.ok || !response.body) {
    throw new Error("连接 AI 服务失败");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || "";

    for (const chunk of chunks) {
      const line = chunk.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      payload.onEvent(JSON.parse(line.slice(6)));
    }
  }
}
