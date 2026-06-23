<template>
  <section class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
    <button
      v-for="action in actions"
      :key="action.key"
      class="group flex min-h-[156px] flex-col justify-between rounded-[20px] border border-app-line/70 bg-white/72 p-5 text-left backdrop-blur-sm transition hover:border-brand/30 hover:bg-white/88"
      type="button"
      @click="$emit('select', action.prompt)"
    >
      <div class="flex h-11 w-11 items-center justify-center rounded-[16px] bg-brand-soft text-brand-deep">
        <component :is="resolveIcon(action.key)" class="h-5 w-5" />
      </div>
      <div>
        <h3 class="text-base font-semibold text-app-text">{{ action.title }}</h3>
        <p class="mt-2 text-sm leading-6 text-app-mute">{{ action.subtitle }}</p>
      </div>
    </button>
  </section>
</template>

<script setup lang="ts">
import { CreditCard, FileText, Hotel, MessagesSquare } from "lucide-vue-next";

interface QuickActionItem {
  key: string;
  title: string;
  subtitle: string;
  prompt: string;
}

defineProps<{
  actions: QuickActionItem[];
}>();

defineEmits<{
  (event: "select", prompt: string): void;
}>();

function resolveIcon(key: string) {
  if (key === "property" || key === "hotel") return Hotel;
  if (key === "order") return FileText;
  if (key === "payment") return CreditCard;
  if (key === "reply") return MessagesSquare;
  return FileText;
}
</script>
