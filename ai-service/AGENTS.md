# ai-service 项目工作指引

本文件是 `ai-service` 的项目级开发指引。所有参与本项目的 Agent 或开发者，在修改代码前都应先阅读本文件和 `docs` 下的标准文档。

## 工作原则

- 小步推进：每次只处理一个明确目标，避免一次性改动过多模块。
- 稳定优先：客服 Agent 涉及订单、支付、评价、通知等敏感业务，任何修改都必须考虑权限、审计和回滚。
- 安全优先：写操作必须具备明确用户意图、二次确认、资源归属校验和执行结果记录。
- 先验证后交付：能写测试就写测试，能跑测试就跑测试；不能验证时必须在开发日志记录原因。
- 不编造业务数据：涉及平台真实数据时必须使用后端工具或明确说明无法查询。

## 标准文件路径

| 文件 | 用途 |
| --- | --- |
| `docs/README.md` | 开发文档索引 |
| `docs/development-requirements.md` | 开发需求和优先级 |
| `docs/technical-standards.md` | 技术规范和模块边界 |
| `docs/design-standards.md` | Agent 设计规范和客服体验标准 |
| `docs/execution-steps.md` | 分阶段执行步骤 |
| `docs/customer-service-agent-optimization-plan.md` | 客服 Agent 优化总方案 |
| `dev-logs/README.md` | 每日开发日志规则 |
| `dev-logs/YYYY-MM-DD.md` | 每日开发事项、待办、风险和验证记录 |
| `tools/dev_log.py` | 自动创建和更新每日开发日志 |

## 开发前检查

1. 阅读本文件。
2. 阅读本次任务相关的 `docs` 标准文件。
3. 确认当天日志存在：

```bash
python tools/dev_log.py
```

4. 在日志中记录本次任务目标：

```bash
python tools/dev_log.py todo --todo "本次准备完成的开发事项"
```

## 开发中约束

- 修改业务链路前，先定位涉及模块：`app.py`、`ChatService`、`SkillService`、`ToolService`、`BackendAPIService`、`ToolAccessPolicy`。
- 新增工具时必须同时补充工具说明、权限规则、错误处理和测试。
- 新增 action 工具时必须接入二次确认流程。
- 涉及用户身份时，不应直接信任前端传入的 `userContext`，除非处于明确的 mock 开发模式。
- 修改 prompt 时必须同步更新行为预期和回归测试。
- 不在日志、文档或代码中写入 API key、token、真实用户隐私数据。

## 开发后记录

每完成一个可验证步骤，更新当天日志：

```bash
python tools/dev_log.py done --done "完成事项"
python tools/dev_log.py verify --verify "验证方式和结果"
python tools/dev_log.py todo --todo "遗留待办"
```

如果遇到阻塞：

```bash
python tools/dev_log.py block --block "阻塞原因和下一步需要的信息"
```

## 推荐推进顺序

优先处理 P0：

1. 写操作二次确认。
2. 可信身份来源。
3. 真实会话状态。
4. fallback 工具收敛。
5. 权限和路由测试。

然后处理 P1：

1. 真流式输出。
2. 结构化错误。
3. 结构化日志和指标。
4. 模型意图分类兜底。

最后处理 P2：

1. prompt 文件化。
2. 前端工具状态展示。
3. FAQ/RAG 知识库。

