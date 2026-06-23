# 详细任务清单

本文档基于当前 `ai-service`、上一级 `backend`、`frontend` 的真实实现整理，不重复描述已完成的最小功能，重点记录仍需推进的落地任务。

## 1. 当前已完成基础

- 已完成低风险 `fallback` 工具收敛。
- 已完成 action 工具二次确认最小骨架。
- 已完成 `/chat/stream` 流式 MVP。
- 已完成酒店推荐卡片和部分前端状态展示。
- 已接入前端登录 token 到 `ai-service`，并优先基于 token 解析真实用户身份。

## 2. P0 任务

### 2.1 可信身份来源收口

目标：后端默认不信任前端直接传入的 `userContext`。

涉及文件：

- `app.py`
- `config.py`
- `services/auth_identity_service.py`
- `services/backend_api_service.py`
- `services/tool_access_policy.py`
- `../frontend/src/api/index.js`

任务拆分：

1. 前端 `assistantApi` 始终透传登录态 `Authorization`。
2. `ai-service` 统一从 Header 解析 token，优先回查真实用户信息。
3. `MERCHANT` 角色自动回查 `merchantId`，避免继续信任前端透传。
4. `ALLOW_MOCK_USER_CONTEXT` 仅用于开发兜底。
5. 后续补 `AUTH_MODE=mock|header-dev|jwt|session` 分层策略。

验收：

- 前端伪造 `role=ADMIN` 不能直接获得管理员能力。
- 登录用户即使不传 `userContext`，也能拿到自己的真实身份。
- 商户用户能自动获得真实 `merchantId`。

### 2.2 真实会话状态最小版本

目标：让 `conversationId` 真正驱动多轮对话上下文。

涉及文件：

- `app.py`
- `services/chat_service.py`

建议新增：

- `services/conversation_store.py`
- `services/conversation_memory.py`

任务拆分：

1. 新增内存版 `ConversationStore`。
2. 在 `/chat`、`/chat/stream` 入口按 `conversationId` 读写会话。
3. 保存最近 N 轮 `user/assistant` 消息。
4. 工具结果只存摘要，不存完整原始对象。
5. 支持 TTL 和过期清理。

验收：

- 用户可追问“刚才那个订单”“第二家酒店”。
- 会话过期后不会继续带旧上下文。
- 日志中能稳定关联 `conversationId`。

### 2.3 写操作确认流补全

目标：把当前 `pending_action` 骨架补成完整安全闭环。

涉及文件：

- `services/action_confirmation_service.py`
- `services/tool_service.py`
- `services/domain_tool_handlers.py`
- `services/chat_service.py`

可选新增：

- `app.py` 中 `/actions/confirm`

任务拆分：

1. 将确认提示从通用 token 提示升级为业务可读文案。
2. `pending_action` 保存资源编号、动作说明、影响说明、过期时间。
3. 执行前再次读取资源状态并重新校验归属。
4. 对已变更状态或不再可执行的动作明确拒绝。
5. 增加 action 审计日志。

验收：

- “能不能取消订单”不会直接取消。
- 只有明确确认后才执行。
- 旧 token 在资源状态变化后不能误执行。

### 2.4 权限与安全回归测试补齐

目标：为身份、权限、确认流和会话补自动化回归。

涉及文件：

- `tests/test_tool_access_policy.py`
- `tests/test_tool_service.py`
- `tests/test_chat_service.py`
- `tests/test_app_chat_api.py`

建议新增：

- `tests/test_auth_identity_service.py`
- `tests/test_conversation_store.py`

任务拆分：

1. 补 token 解析和真实身份回查测试。
2. 补 mock userContext 降级测试。
3. 补 action 确认前后行为测试。
4. 补多轮会话状态测试。

验收：

- 核心越权路径都有自动化覆盖。
- 关键改动可通过测试阻止回归。

## 3. P1 任务

### 3.1 结构化错误体系

目标：不要继续使用 `str(exc)` 贯穿整个链路。

涉及文件：

- `services/backend_api_service.py`
- `services/tool_service.py`
- `services/chat_service.py`
- `app.py`

建议新增：

- `services/errors.py`

任务拆分：

1. 定义统一错误类型：`AUTH_REQUIRED`、`FORBIDDEN`、`NOT_FOUND`、`VALIDATION_ERROR`、`UPSTREAM_TIMEOUT`、`UPSTREAM_ERROR`。
2. 后端 API 层抛结构化异常。
3. 工具层返回标准错误对象。
4. ChatService 根据错误类型组织客服话术。

验收：

- 403、404、timeout 返回不同错误类别。
- 用户侧回复不暴露内部堆栈。

### 3.2 结构化日志和指标

目标：支持按 `requestId` 还原整条请求链路。

涉及文件：

- `app.py`
- `services/chat_service.py`
- `clients/anthropic_client.py`
- `services/backend_api_service.py`

任务拆分：

1. 记录 `request_id`、`conversation_id`、`skills`、`tools_exposed`。
2. 记录每次 `tool_call` 的耗时、结果、错误类型。
3. 记录模型 `stop_reason`、总耗时。
4. 预留 metrics 埋点结构。

验收：

- 一次请求可以从入口追踪到模型、工具和后端调用。
- 工具失败原因可统计。

### 3.3 Skill 路由升级

目标：从纯关键词升级为“规则优先 + 分类兜底”。

涉及文件：

- `services/skill_service.py`
- `skills/`

建议新增：

- `services/intent_classifier.py`

任务拆分：

1. 保留高置信规则匹配。
2. 增加业务编号格式识别。
3. 对低置信场景调用轻量分类。
4. 输出 `intent`、`confidence`、`required_slots`、`needs_clarification`。

验收：

- “这笔钱扣了吗”能稳定路由到支付。
- “明天到店怎么拿钥匙”不会因为关键词不足而漏判。

### 3.4 流式协议收尾

目标：把现有流式 MVP 收口成稳定事件协议。

涉及文件：

- `clients/anthropic_client.py`
- `services/chat_service.py`
- `templates/index.html`
- `../frontend/src/components/AiAssistant.vue`

任务拆分：

1. 统一事件类型：`meta / thinking / tool_start / tool_result / chunk / done / error`。
2. 工具事件摘要标准化。
3. 前端准确展示工具开始、完成、失败状态。
4. 完善 SSE 错误处理。

验收：

- 首字响应明显快于同步接口。
- 工具执行时前端有稳定反馈。

### 3.5 前端调试和能力对齐

目标：让演示界面展示真实后端能力和当前身份状态。

涉及文件：

- `templates/index.html`
- `../frontend/src/components/AiAssistant.vue`

任务拆分：

1. 展示命中 skill、当前可用工具。
2. 展示当前身份来源：token / mock / anonymous。
3. 展示 action 待确认状态。
4. 对齐真实后端能力说明。

验收：

- 前端不再误导“后端不能查”。
- 调试时能看清当前链路。

## 4. P2 任务

### 4.1 Prompt 文件化

目标：减少 prompt 分散在代码中的情况。

涉及文件：

- `app.py`
- `services/chat_service.py`
- `skills/`

任务拆分：

1. 抽离系统 prompt。
2. 抽离领域 prompt。
3. 抽离 action 安全提示。
4. 建立 prompt 版本管理方式。

### 4.2 FAQ / RAG 预研

目标：为高频客服问答做知识沉淀。

任务拆分：

1. 盘点高频 FAQ 场景。
2. 明确可接入的数据源。
3. 设计召回边界和兜底策略。
4. 输出方案评估文档。

## 5. 推荐执行顺序

1. 可信身份来源收口
2. 真实会话状态最小版本
3. 写操作确认流补全
4. 权限与安全回归测试补齐
5. 结构化错误体系
6. 结构化日志和指标
7. Skill 路由升级
8. 流式协议收尾
9. 前端调试和能力对齐
10. Prompt 文件化与 FAQ/RAG
