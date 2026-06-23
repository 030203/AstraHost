# 技术规范

## 1. 技术栈

- Web 框架：Flask。
- 模型接口：Anthropic Messages API。
- HTTP 客户端：`requests`。
- 配置：`.env` + `AppConfig`。
- 后端业务服务：`BOOKING_SERVICE_BASE_URL` 指向的 booking-service。

## 2. 模块边界

| 模块 | 允许职责 | 不应承担 |
| --- | --- | --- |
| `app.py` | HTTP 路由、请求参数读取、响应包装 | 业务规则、权限判断、复杂 prompt 逻辑 |
| `ChatService` | 问答主流程、模型调用、工具回合编排 | 具体后端 API 拼接、资源归属判断 |
| `SkillService` | 意图/技能路由、工具集合候选 | 执行工具、调用后端 |
| `ToolService` | 工具注册、schema 暴露、执行分发 | 直接信任模型参数 |
| `BackendAPIService` | booking-service HTTP 封装 | Agent 决策、客服话术 |
| `ToolAccessPolicy` | 角色和资源权限 | HTTP 调用、prompt 拼接 |

## 3. 工具注册规范

新增工具必须包含：

- 唯一工具名。
- 中文或清晰业务描述。
- 参数 schema。
- 必填参数。
- `mode="read"` 或 `mode="action"`。
- 允许角色。
- handler 中的权限校验。
- 至少一条测试。

action 工具必须额外满足：

- 必须通过二次确认。
- 执行前重新读取资源状态。
- 执行结果必须记录到日志。

## 4. 权限规范

- 任何身份绑定数据都必须通过 `ToolAccessPolicy` 校验。
- USER 只能访问自己的订单、支付、通知、用户资料。
- MERCHANT 只能访问当前 merchantId 关联资源。
- ADMIN 可以访问管理数据，但身份来源必须可信。
- 匿名用户只能访问公开数据和非身份绑定工具。

## 5. 错误处理规范

后续应将工具错误统一为结构化错误：

```json
{
  "ok": false,
  "tool": "get_booking_detail",
  "error": {
    "type": "FORBIDDEN",
    "message": "当前用户无权访问该订单。",
    "retryable": false
  }
}
```

禁止把完整堆栈、密钥、后端敏感响应直接返回给用户。

## 6. 日志规范

每个请求至少应记录：

- `request_id`
- `conversation_id`
- 用户角色
- 命中 skills
- 暴露 tools
- 工具调用列表
- 工具耗时和结果
- 模型名称
- 总耗时

日志中禁止记录密钥、token 和用户隐私原文。

## 7. 测试规范

推荐新增 `tests` 目录：

```text
tests/
  test_skill_service.py
  test_tool_access_policy.py
  test_tool_service.py
  test_chat_service.py
```

最小覆盖要求：

- Skill 路由。
- fallback 工具收敛。
- USER/MERCHANT/ADMIN 权限。
- action 工具确认流程。
- 后端 API 错误处理。

## 8. 配置规范

所有环境差异必须通过 `AppConfig` 读取，不在业务代码中硬编码。

建议新增配置：

```env
AUTH_MODE=mock
ALLOW_MOCK_USER_CONTEXT=true
CONVERSATION_STORE=memory
CONVERSATION_TTL_SECONDS=86400
ENABLE_ACTION_CONFIRMATION=true
```

