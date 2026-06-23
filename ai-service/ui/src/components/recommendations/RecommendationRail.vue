<template>
  <section class="space-y-4 rounded-card border border-app-line/70 bg-white/70 p-4 backdrop-blur-sm">
    <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <h3 class="text-xl font-semibold text-app-text">{{ recommendations.title || "为您推荐的酒店" }}</h3>
        <p v-if="recommendations.subtitle" class="mt-1 text-sm text-app-mute">{{ recommendations.subtitle }}</p>
      </div>
      <div class="text-sm font-medium text-brand">{{ recommendations.count || recommendations.cards.length }} 家可查看</div>
    </div>

    <div class="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(280px,1fr))]">
      <article
        v-for="(card, index) in recommendations.cards"
        :key="card.id"
        class="rounded-card border border-app-line/70 bg-[#FFF9F5] transition hover:border-brand/30 hover:bg-white"
      >
        <div class="relative aspect-[4/3] overflow-hidden rounded-t-card bg-app-soft">
          <img
            :src="safeImage(card.imageUrl)"
            :alt="card.name"
            class="h-full w-full object-cover"
          />
          <div class="absolute inset-x-0 top-0 flex items-start justify-between p-3">
            <span
              class="rounded-full px-3 py-1 text-xs font-medium text-white shadow-soft"
              :class="card.featured || index === 0 ? 'bg-warning' : 'bg-success'"
            >
              {{ card.featured || index === 0 ? "推荐优先" : "可重点看" }}
            </span>
            <button class="rounded-full bg-white/78 p-2 text-app-text backdrop-blur" type="button">
              <Heart class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div class="space-y-4 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <h4 class="truncate text-base font-semibold text-app-text">{{ card.name }}</h4>
              <p class="mt-1 text-sm text-app-mute">{{ card.location || card.address || "位置待补充" }}</p>
            </div>
            <span v-if="card.type" class="rounded-full bg-app-panel px-3 py-1 text-xs text-app-mute">{{ card.type }}</span>
          </div>

          <div class="flex items-center justify-between gap-4">
            <div class="text-2xl font-semibold text-app-text">{{ card.priceLabel || "价格待咨询" }}</div>
            <div class="rounded-2xl bg-app-panel px-3 py-2 text-sm text-app-text">
              <span class="font-semibold">★ {{ card.rating || "-" }}</span>
              <span class="ml-1 text-app-mute">({{ card.reviewCount ?? "客服推荐" }})</span>
            </div>
          </div>

          <div v-if="card.highlights?.length" class="flex flex-wrap gap-2">
            <span
              v-for="tag in card.highlights.slice(0, 6)"
              :key="tag"
              class="rounded-full bg-app-panel px-3 py-1 text-xs text-app-mute"
            >
              {{ tag }}
            </span>
          </div>

          <p class="max-h-[72px] overflow-hidden text-sm leading-6 text-app-mute">
            {{ card.summary || "适合继续查看详情、比价和咨询具体入住条件。" }}
          </p>

          <div class="grid grid-cols-2 gap-3">
            <button
              class="rounded-button border border-app-line/70 bg-white/85 px-4 py-3 text-sm font-medium text-app-text transition hover:border-brand/30 hover:bg-white"
              type="button"
              @click="handleSecondary(card)"
            >
              查看详情
            </button>
            <button
              class="rounded-button bg-brand px-4 py-3 text-sm font-medium text-white transition hover:bg-brand-deep"
              type="button"
              @click="handlePrimary(card)"
            >
              立即前往
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Heart } from "lucide-vue-next";
import { FALLBACK_CARD_IMAGE } from "../../lib/fallbacks";
import type { RecommendationCard, RecommendationsPayload } from "../../types/copilot";

defineProps<{
  recommendations: RecommendationsPayload;
}>();

const emit = defineEmits<{
  (event: "follow-up", prompt: string): void;
}>();

const PROPERTY_DETAIL_BASE_URL = "http://localhost:5400";
const PROPERTY_DETAIL_PATH_RE = /^\/property\/[^?#]+(?:[?#].*)?$/i;
const LOCALHOST_PROPERTY_URL_RE = /^https?:\/\/localhost(?::\d+)?(\/property\/[^?#]+(?:[?#].*)?)$/i;

function normalize(url?: string): string {
  if (!url) return "";
  const trimmed = url.trim();
  if (!trimmed) return "";
  const localhostPropertyMatch = trimmed.match(LOCALHOST_PROPERTY_URL_RE);
  if (localhostPropertyMatch) {
    return `${PROPERTY_DETAIL_BASE_URL}${localhostPropertyMatch[1]}`;
  }
  if (PROPERTY_DETAIL_PATH_RE.test(trimmed)) {
    return `${PROPERTY_DETAIL_BASE_URL}${trimmed}`;
  }
  return /^https?:\/\//i.test(trimmed) ? trimmed : "";
}

function safeImage(url?: string) {
  return normalize(url) || FALLBACK_CARD_IMAGE;
}

function openLink(url?: string) {
  const normalized = normalize(url);
  if (normalized) {
    window.open(normalized, "_blank", "noopener,noreferrer");
    return true;
  }
  return false;
}

function fallbackPrompt(card: RecommendationCard) {
  emit("follow-up", card.followUpPrompt || `请详细介绍一下 ${card.name} 的房型、入住规则和预订建议`);
}

function handleSecondary(card: RecommendationCard) {
  if (!openLink(card.detailUrl || card.mapUrl)) {
    fallbackPrompt(card);
  }
}

function handlePrimary(card: RecommendationCard) {
  if (!openLink(card.bookingUrl || card.detailUrl || card.mapUrl)) {
    fallbackPrompt(card);
  }
}
</script>
