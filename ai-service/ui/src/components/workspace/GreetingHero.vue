<template>
  <section class="mx-auto max-w-3xl text-center animate-fade-in">
    <div class="inline-flex items-center rounded-full bg-white/70 px-4 py-2 text-sm text-brand-deep">
      {{ greeting }} · {{ userName }}
    </div>
    <h2 class="mt-6 text-4xl font-semibold text-app-text md:text-5xl">
      今天想让 AI 帮您处理什么？
    </h2>
    <p class="mx-auto mt-4 max-w-2xl text-base leading-7 text-app-mute">
      AstraHost 会在同一工作台里处理房源推荐、订单进度、支付问题与客户沟通，并在需要时展开执行轨迹。
    </p>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  greeting: string;
  userName: string;
}>();
</script>
