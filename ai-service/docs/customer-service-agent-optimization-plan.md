# 客服 Agent 优化方案

## 1. 背景与目标

当前 `ai-service` 是 FindMyBed 民宿平台的客服 Agent 服务，采用 Flask API、Anthropic Claude、关键词 Skill 路由、工具调用和后端业务 API 的组合方式实现。它已经具备基础客服闭环：用户发问、识别领域、选择工具、调用后端、基于真实数据生成中文回复。

本方案基于当前代码结构和现有问题，目标是把服务从“可演示、可调用”提升到“可上线、可追踪、可控风险、可持续扩展”的客服 Agent。

核心优化目标：

- 提升多轮对话能力，支持真实会话上下文和历史记忆。
- 提升意图识别准确率，减少关键词路由漏判和误判。
- 强化工具调用安全，尤其是取消订单、入住、离店、回复评价、通知已读等写操作。
- 改造真正的模型流式输出，降低首字响应时间。
- 完善用户身份、角色和权限边界，避免只信任前端传入的 `userContext`。
- 增强可观测性、测试覆盖和错误处理，方便定位线上问题。

## 2. 当前架构概览

当前主链路如下：

```text
前端或外部系统
  -> POST /chat 或 /chat/stream
  -> app.py 接收 message、conversationId、userContext
  -> ChatService.chat()
  -> SkillService.resolve()
  -> KeywordSkill 根据关键词匹配客服领域
  -> ToolService 根据技能和角色筛选工具
  -> AnthropicClient 调 Claude Messages API
  -> Claude 发起 tool_use
  -> ToolService.execute()
  -> BackendAPIService 请求 booking-service
  -> ToolAccessPolicy 校验角色和资源权限
  -> Claude 基于工具结果生成中文客服回复
```

主要模块职责：

| 模块 | 当前职责 |
| --- | --- |
| `app.py` | Flask 入口，提供 `/chat`、`/chat/stream`、`/skills`、`/suggestions` 等接口 |
| `services/chat_service.py` | 主问答循环，构建 prompt，处理工具调用回合 |
| `services/skill_service.py` | 匹配技能，决定本轮可用工具集合 |
| `skills/customer_service.py` | 定义房源、订单、支付、评价、通知、优惠券、商家、用户等客服技能 |
| `services/tool_service.py` | 注册工具、生成工具 schema、执行工具 |
| `services/backend_api_service.py` | 封装 booking-service HTTP API |
| `services/tool_access_policy.py` | 角色识别、资源归属校验、数据过滤 |
| `clients/anthropic_client.py` | 调 Anthropic SDK 或 HTTP messages API |

## 3. 主要问题总结

### 3.1 没有真实多轮会话记忆

`conversationId` 当前主要用于前端展示，后端没有根据该 ID 保存和读取历史消息。每次请求只把当前用户消息发给模型，所以用户追问“那第二个多少钱”“帮我取消刚才那个订单”时，Agent 无法可靠理解“那个”指代什么。

影响：

- 多轮推荐体验较弱。
- 订单、支付、评价等强上下文问题容易丢信息。
- 用户必须重复提供订单号、房源 ID、城市、预算等条件。

### 3.2 Skill 路由过度依赖关键词

当前 `KeywordSkill.matches()` 通过字符串包含判断是否命中领域。这种方式实现简单，但对自然语言表达不够稳。

典型风险：

- 用户说“我明天到店之后怎么拿钥匙”，可能是入住问题，但未必命中订单或入住关键词。
- 用户说“这笔钱扣了吗”，实际是支付问题，但如果没有“支付/付款/交易”等关键词可能漏判。
- 跨领域问题会匹配多个技能，工具集合可能变宽。
- 没有命中技能时，会 fallback 到当前角色可用的所有读工具，工具暴露面偏大。

### 3.3 写操作缺少强确认机制

当前写操作通过 prompt 和工具描述约束模型：“只有用户明确要求时调用”。但这仍属于软约束，模型一旦误判就可能调用 action 工具。

涉及写操作：

- `cancel_booking`
- `check_in_booking`
- `check_out_booking`
- `reply_review`
- `mark_notification_read`
- `mark_all_notifications_read`

风险：

- 用户只是咨询“能不能取消”，Agent 误调用取消工具。
- 用户表达含糊，例如“帮我处理一下这个订单”，Agent 可能错误执行动作。
- 缺少二次确认和幂等防护。

### 3.4 `/chat/stream` 不是真流式

当前 `stream_chat()` 先调用完整的 `chat()`，等模型和工具链路全部完成后，再把完整答案按固定长度切片返回。

影响：

- 首字延迟没有改善。
- 工具调用耗时长时，前端一直等待。
- 无法展示模型正在调用哪些工具，也无法做更自然的“查询中”状态。

### 3.5 用户身份和权限主要依赖前端传参

前端通过 `userContext` 传入 `id`、`username`、`role`、`merchantId`。后端本地会做权限过滤，但身份本身缺少可信认证来源。

风险：

- 用户可以伪造 `role=ADMIN`。
- 用户可以伪造 `merchantId`。
- 后端请求 booking-service 时只传 request id，没有透传用户 token 或服务间鉴权。

另外，前端默认用户 ID 是 `guest_10001`，但工具层很多地方会把 userId 转成整数。真实调用订单、支付、通知等工具时，可能出现“缺少 userId”或类型转换失败。

### 3.6 错误处理面向开发，不够面向客服体验

当前工具错误会包装成：

```json
{
  "ok": false,
  "tool": "...",
  "error": "..."
}
```

模型会看到错误并生成回答，但没有统一的错误类型、用户可读文案和重试建议。比如后端超时、无权限、资源不存在、参数缺失、外部工具缺 API key，最终体验可能不稳定。

### 3.7 可观测性不足

已有 `X-Request-ID` 和日志基础，但缺少 Agent 维度的结构化事件。

建议追踪但当前不足的内容：

- 命中的 skills。
- 暴露给模型的 tools。
- 模型是否触发 tool_use。
- 每个工具调用耗时、成功/失败、错误类型。
- 完整链路耗时。
- 模型 stop reason。
- token 使用量。

### 3.8 测试覆盖不足

当前缺少系统化单元测试和集成测试。`test.py`、`te.py` 更像手动验证脚本，不是稳定测试套件。

高风险区域包括：

- Skill 路由准确性。
- 角色权限过滤。
- 工具执行参数转换。
- 写操作保护。
- 后端 API 错误处理。
- 多轮上下文。

### 3.9 前端展示与后端能力不一致

前端页面文案写着“涉及实时订单、库存、支付结果时会明确说明无法直接查询”，但后端已经支持订单、支付、通知等工具查询。这个信息会误导演示和验收。

## 4. 优化方案

### 4.1 增加真实会话状态

目标：让 `conversationId` 成为后端真实会话 ID，支持多轮追问。

建议实现：

1. 新增 `ConversationStore`。
   - 初期可用内存实现，适合本地开发和演示。
   - 上线建议接 Redis，支持 TTL 和多实例共享。

2. 每次请求按 `conversationId` 读取历史。
   - 存储最近 N 轮消息，例如 10 到 20 轮。
   - 对工具结果只保存摘要，避免上下文过大。

3. 在 `ChatService.chat()` 中构造 messages：

```text
历史 user/assistant 消息
+ 当前 user 消息
+ 必要工具调用结果
```

4. 增加会话摘要机制。
   - 当历史超长时，把旧消息压缩成 `conversation_summary`。
   - 摘要保留关键业务字段：订单号、房源 ID、城市、预算、入住日期、用户偏好等。

建议新增文件：

- `services/conversation_store.py`
- `services/conversation_memory.py`

优先级：P0。

### 4.2 升级 Skill 路由

目标：让领域识别从纯关键词升级为“规则优先 + 模型分类兜底 + 低风险 fallback”。

建议分三层：

1. 规则层。
   - 保留当前关键词匹配，速度快，可解释。
   - 对高置信关键词直接命中，例如订单号格式、支付单号格式、明确“取消订单”。

2. 轻量分类层。
   - 当关键词没有命中或命中多个领域时，调用模型做一次结构化分类。
   - 输出固定 JSON：

```json
{
  "intent": "booking_status",
  "skills": ["booking_support"],
  "confidence": 0.87,
  "requires_action": false,
  "required_slots": ["booking_number"]
}
```

3. 安全 fallback。
   - 没有明确领域时，不直接暴露当前角色所有读工具。
   - 只暴露低风险工具，例如 `search_properties`、`get_top_properties`、`tavily_search`、`get_weather`。
   - 如果问题明显需要身份数据但参数不足，先追问。

建议改造点：

- `SkillService.resolve()` 返回 `confidence`、`intent`、`required_slots`。
- `SkillRoute` 增加 `intent`、`confidence`、`needs_clarification`。
- 增加 `services/intent_classifier.py`。

优先级：P0/P1。

### 4.3 强化写操作安全

目标：所有会修改后端状态的工具必须经过显式确认和服务端硬校验。

建议引入两阶段动作模型：

```text
用户提出动作请求
  -> Agent 查询目标资源详情
  -> Agent 返回确认信息
  -> 用户明确确认
  -> 服务端执行 action 工具
```

确认信息应该包含：

- 动作名称。
- 资源 ID 和业务编号。
- 当前状态。
- 动作后状态或影响。
- 风险提示。

示例：

```text
我查到订单 BOOK20250401001 当前状态为待入住。
如果继续取消，订单状态会变为已取消，可能触发平台取消规则。
请回复“确认取消订单 BOOK20250401001”，我再帮你执行。
```

服务端硬校验建议：

1. `ToolService` 对 `mode="action"` 工具增加确认 token。
2. 第一次请求只生成 `pending_action`，不执行工具。
3. 用户确认后，必须匹配动作类型、资源 ID、业务编号和当前用户。
4. pending action 设置短 TTL，例如 5 分钟。
5. action 工具执行前重新读取资源状态，避免状态已变化。

建议新增：

- `services/action_confirmation_service.py`
- `PendingAction` 数据结构
- `POST /actions/confirm` 或继续复用 `/chat` 但由 `ChatService` 识别确认语义

优先级：P0。

### 4.4 实现真正的模型流式

目标：让 `/chat/stream` 能边生成边返回，降低用户等待感。

建议：

1. 在 `AnthropicClient` 增加 streaming 方法。
2. `ChatService.stream_chat()` 使用 Anthropic Messages Stream API。
3. SSE 事件拆成更细类型：

```text
meta: 会话、路由、requestId
thinking: 正在理解问题
tool_start: 开始调用工具
tool_result: 工具调用完成
chunk: 模型文本片段
done: 完成
error: 错误
```

4. 如果模型先触发工具调用：
   - 先返回 `tool_start`。
   - 执行工具。
   - 把结果继续喂给模型。
   - 再开始流式输出最终答案。

优先级：P1。

### 4.5 可信用户身份与服务间鉴权

目标：不再信任前端传入的角色和身份。

建议：

1. 从请求 Header 或 Cookie 中读取用户 token。
2. 调认证服务解析真实用户身份、角色和 merchantId。
3. `userContext` 只作为展示或调试字段，不作为权限来源。
4. 请求 booking-service 时透传认证信息或使用服务间 token。
5. 对开发环境保留 mock userContext，但必须通过配置开关启用。

建议配置：

```env
AUTH_MODE=mock|jwt|session
ALLOW_MOCK_USER_CONTEXT=false
SERVICE_AUTH_TOKEN=...
```

优先级：P0。

### 4.6 统一错误分类和客服话术

目标：工具错误不直接暴露技术细节，统一转成用户可理解的客服回复。

建议定义错误类型：

| 错误类型 | 场景 | 用户话术方向 |
| --- | --- | --- |
| `AUTH_REQUIRED` | 未登录或缺少用户 ID | 引导登录 |
| `FORBIDDEN` | 无权访问资源 | 说明无法查看该记录 |
| `NOT_FOUND` | 订单/支付/房源不存在 | 提醒核对编号 |
| `VALIDATION_ERROR` | 参数缺失或格式错误 | 追问必要信息 |
| `UPSTREAM_TIMEOUT` | 后端超时 | 建议稍后重试 |
| `UPSTREAM_ERROR` | 后端异常 | 告知系统暂不可用 |
| `EXTERNAL_TOOL_MISSING_KEY` | 天气/搜索未配置 key | 降级回答 |

实现方式：

- `BackendAPIService` 抛出结构化异常，而不是普通 `ValueError`。
- `ToolService.execute()` 返回标准错误对象。
- prompt 中要求模型根据错误类型生成客服话术。

优先级：P1。

### 4.7 加强可观测性

目标：线上问题可以通过 requestId 快速还原。

建议记录结构化日志：

```json
{
  "request_id": "...",
  "conversation_id": "...",
  "user_id": 12,
  "role": "USER",
  "message_length": 32,
  "skills": ["booking_support"],
  "tools_exposed": ["get_booking_by_number"],
  "tool_calls": [
    {
      "name": "get_booking_by_number",
      "duration_ms": 128,
      "ok": true
    }
  ],
  "model": "claude-3-5-sonnet-latest",
  "stop_reason": "end_turn",
  "total_duration_ms": 1430
}
```

建议增加指标：

- 请求总数、成功率、失败率。
- 工具调用成功率。
- 各工具 P95 延迟。
- action 工具触发次数和确认转化率。
- 无权限错误次数。
- 模型调用耗时和 token 使用量。

优先级：P1。

### 4.8 完善测试体系

目标：把核心 Agent 行为变成可回归测试。

建议测试分层：

1. 单元测试。
   - `KeywordSkill.matches()`
   - `SkillService.resolve()`
   - `ToolAccessPolicy`
   - `ToolService.get_tool_definitions()`
   - 各 domain handler 的角色过滤

2. 集成测试。
   - mock `BackendAPIService`
   - 模拟用户查订单、商家查订单、管理员查用户
   - 模拟无权限访问
   - 模拟后端 404、500、timeout

3. Agent 行为测试。
   - 用户问“我的订单状态怎么样”时，应该调用订单工具或追问订单号。
   - 用户问“能不能取消订单”时，不应该直接调用 `cancel_booking`。
   - 用户明确“确认取消订单 BOOKxxx”时，才允许进入 action flow。

4. 契约测试。
   - 验证 `BackendAPIService` 封装路径、参数名和 booking-service API 一致。

建议新增目录：

```text
tests/
  test_skill_service.py
  test_tool_access_policy.py
  test_tool_service.py
  test_chat_service.py
  fixtures/
```

优先级：P0/P1。

### 4.9 Prompt 与工具描述治理

目标：减少 prompt 分散和重复，便于版本管理。

建议：

1. 将全局 system prompt 从 `app.py` 移到独立文件。
2. 将各 skill prompt 改成可配置模板。
3. 每次 prompt 改动配套行为测试。
4. 对工具描述增加统一规范：
   - 何时调用。
   - 不该何时调用。
   - 必填参数。
   - 是否写操作。
   - 失败时如何处理。

建议路径：

```text
prompts/
  system.md
  skills/
    booking_support.md
    payment_support.md
    property_support.md
```

优先级：P2。

### 4.10 前端体验修正

目标：让控制台正确展示当前后端能力。

建议：

- 修改前端说明文案，明确“需要业务数据时会调用后端工具查询”。
- 默认用户 ID 改成数字，例如 `12`。
- 角色切换时，如果选择 `MERCHANT`，提示填写 `merchantId`。
- 展示本次路由结果：命中 skill、调用工具、requestId。
- 对 SSE `tool_start`、`tool_result` 做可视化状态展示。

优先级：P1/P2。

## 5. 推荐实施路线

### 阶段一：安全与可用性补强

目标：先把高风险点补住，减少误操作和权限风险。

任务：

- 增加真实会话存储的最小版本。
- 修改 fallback 策略，未命中 skill 时不要暴露全部读工具。
- 为 action 工具增加二次确认机制。
- 修正前端默认 userId 类型。
- 增加权限和路由单元测试。
- 明确 mock userContext 只用于开发环境。

建议周期：1 到 2 周。

### 阶段二：体验与稳定性提升

目标：提升问答质量、响应速度和可观测性。

任务：

- 实现真正模型流式。
- 增加工具调用 SSE 状态事件。
- 引入结构化错误类型。
- 增加结构化日志和基础指标。
- 增加模型意图分类兜底。
- 修正前端展示文案和路由信息展示。

建议周期：2 到 3 周。

### 阶段三：生产化与规模化

目标：让 Agent 能稳定承接真实客服流量。

任务：

- 接入正式认证体系。
- 会话存储切 Redis。
- 增加 prompt 版本管理。
- 增加 Agent 行为回归测试集。
- 引入灰度开关和工具调用审计。
- 对高频问题沉淀 FAQ/RAG 知识库。

建议周期：3 到 5 周。

## 6. 建议优先级清单

| 优先级 | 优化项 | 原因 |
| --- | --- | --- |
| P0 | action 工具二次确认 | 防止误取消订单、误修改状态 |
| P0 | 可信身份来源 | 防止伪造角色和越权访问 |
| P0 | 会话状态最小版本 | 支持真实多轮客服 |
| P0 | fallback 工具收敛 | 减少模型误调用敏感工具 |
| P0 | 权限单元测试 | 当前最核心的安全边界 |
| P1 | 真流式输出 | 明显改善等待体验 |
| P1 | 结构化错误 | 提升客服回复稳定性 |
| P1 | 结构化日志和指标 | 方便线上排查 |
| P1 | 模型意图分类兜底 | 提升复杂问法识别能力 |
| P2 | prompt 文件化 | 便于长期维护 |
| P2 | 前端路由和工具状态展示 | 提升演示和调试体验 |

## 7. 一个推荐的目标架构

```text
Client
  -> Flask API
    -> AuthService 解析可信用户身份
    -> ConversationStore 读取历史
    -> IntentRouter 规则 + 模型分类
    -> ToolPolicy 生成安全工具集合
    -> ChatService 调模型
      -> ToolExecutor
        -> ActionConfirmationService
        -> BackendAPIService
        -> ExternalTools
    -> ConversationStore 写入消息和摘要
    -> SSE/JSON 返回
```

这个目标架构保留当前代码的轻量优势，同时把安全、记忆、路由、确认和观测能力拆成独立模块，后续扩展新的客服领域会更稳。

## 8. 验收标准

建议按以下标准验收优化结果：

- 用户可以连续追问同一个订单或房源，不需要重复输入完整信息。
- 用户问“能不能取消订单”时，Agent 只解释规则或查询订单，不直接取消。
- 用户明确确认后，action 工具才会执行，并且执行前重新校验订单归属和状态。
- 普通用户无法通过伪造 `role=ADMIN` 查询其他用户信息。
- 未命中 skill 时，Agent 不会暴露所有读工具。
- `/chat/stream` 首字响应明显快于非流式接口。
- 每次请求能通过 requestId 查到命中 skill、工具调用、耗时和错误原因。
- 权限、路由、写操作保护都有自动化测试覆盖。

## 9. 结论

当前 `ai-service` 的基础设计方向是正确的：模型负责理解和表达，工具负责真实数据，权限层负责安全边界。下一步最重要的不是堆更多工具，而是把会话状态、动作确认、可信身份和测试观测补齐。

建议先做 P0 项，尤其是 action 二次确认、身份可信化、会话存储和 fallback 收敛。这些改完以后，Agent 才更适合从演示环境进入真实客服场景。
