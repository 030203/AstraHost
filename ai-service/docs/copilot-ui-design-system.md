# AI Native Homestay Copilot UI 设计系统

## 目标

本次 UI 重构目标不是传统后台改版，而是把 `ai-service` 首页升级为：

- Conversation First
- Agent Visible
- Result Actionable

用户进入页面后应先感知到 AI Copilot，再看到数据，再看到配置。

## 页面结构

采用三栏布局：

1. 左栏 `280px`
   - Logo
   - 新建会话
   - 历史会话
   - 轻量身份调试卡

2. 中栏 `Main Copilot Workspace`
   - Greeting Hero
   - Quick Actions
   - Chat Workspace
   - Prompt Input

3. 右栏 `320px`
   - Agent Timeline
   - Tool Logs

## Vue 组件拆分

`ui/src/App.vue`

- `components/layout/ConversationSidebar.vue`
- `components/workspace/GreetingHero.vue`
- `components/workspace/QuickActionGrid.vue`
- `components/chat/ChatWorkspace.vue`
- `components/chat/MessageBubble.vue`
- `components/recommendations/RecommendationRail.vue`
- `components/agent/AgentPanel.vue`

状态逻辑：

- `composables/useLocalConversations.ts`
- `composables/useAgentTimeline.ts`

基础能力：

- `lib/api.ts`
- `lib/markdown.ts`
- `lib/time.ts`
- `lib/fallbacks.ts`

## Tailwind 设计 Token

定义位置：`ui/tailwind.config.ts`

核心 Token：

- 主色 `brand.DEFAULT = #14B8A6`
- 辅助底色 `app.panel = #F8FAFC`
- 页面背景 `app.bg = #FFFFFF`
- 分割线 `app.line = #E2E8F0`
- 正文 `app.text = #0F172A`
- 次级文字 `app.mute = #64748B`
- 成功 `#22C55E`
- 警告 `#F59E0B`

圆角：

- 卡片 `20px`
- 按钮 `12px`
- 输入框 `14px`
- 消息气泡 `16px`

阴影：

- `shadow-soft = 0 2px 12px rgba(0, 0, 0, 0.04)`
- `shadow-lift = 0 18px 40px rgba(15, 23, 42, 0.08)`

动画：

- `animate-fade-in`
- `animate-slide-up`
- `animate-pulse`

## Element Plus 使用建议

当前实现中保留 Element Plus 作为基础交互层，建议使用边界如下：

适合保留：

- `ElButton`
- `ElDrawer`
- `ElDialog`
- `ElTooltip`
- `ElDropdown`
- `ElEmpty`
- `ElSkeleton`
- `ElScrollbar`

不建议直接使用默认视觉的大型表单容器：

- `ElCard`
- `ElDescriptions`
- 默认表单页式 `ElForm`

原因：

这些组件默认视觉更接近后台系统，不符合本次 Copilot 产品气质。对于 Hero、消息流、推荐卡片、Agent 面板，应使用自定义布局与 Tailwind token。

## 与旧模板的关系

- 旧的 `templates/index.html` 作为回退页面保留
- Flask 根路由优先返回 `static/copilot/index.html`
- 当 Vue 构建产物不存在时，自动回退到旧模板

## 构建与托管

前端源码位置：

- `ui/`

构建产物位置：

- `static/copilot/`

Flask 托管方式：

- `GET /` 优先返回 `static/copilot/index.html`

## 后续建议

1. 把历史会话从本地存储升级为后端可回放摘要
2. 为 `Agent Timeline` 增加更细粒度阶段映射
3. 为推荐卡片增加地图、筛选和排序微交互
4. 将图片上传、文件上传、语音输入接入真实能力
