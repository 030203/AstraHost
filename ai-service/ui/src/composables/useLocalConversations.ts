import { computed, ref } from "vue";
import type { ConversationSummary } from "../types/copilot";

const STORAGE_KEY = "ai-service-copilot-conversations";

function readStorage(): ConversationSummary[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function useLocalConversations() {
  const items = ref<ConversationSummary[]>(readStorage());

  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value.slice(0, 50)));
  }

  function save(entry: ConversationSummary) {
    const next = items.value.filter((item) => item.id !== entry.id);
    items.value = [entry, ...next];
    persist();
  }

  function remove(id: string) {
    items.value = items.value.filter((item) => item.id !== id);
    persist();
  }

  function syncRemote(ids: string[]) {
    if (!ids.length) return;
    const map = new Map(items.value.map((item) => [item.id, item]));
    ids.forEach((id) => {
      if (!map.has(id)) {
        map.set(id, {
          id,
          title: "历史会话",
          updatedAt: Date.now()
        });
      }
    });
    items.value = Array.from(map.values()).sort((a, b) => b.updatedAt - a.updatedAt);
    persist();
  }

  return {
    items: computed(() => items.value),
    save,
    remove,
    syncRemote
  };
}

