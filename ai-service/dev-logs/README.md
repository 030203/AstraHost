# 开发日志使用说明

本目录用于按日期记录 `ai-service` 的开发事项、验证结果、风险和待办。每个自然日一份日志，文件名格式为：

```text
YYYY-MM-DD.md
```

## 日志更新规则

- 每次开始开发前，先确认当天日志存在。
- 每次完成一个小步骤后，记录到“已完成”。
- 每次留下后续工作，记录到“待办”。
- 每次遇到阻塞、设计决策或验证结果，都要写入对应栏目。
- 不把大段调试输出、密钥、用户隐私数据写入日志。

## 推荐命令

```bash
python tools/dev_log.py
python tools/dev_log.py done --done "完成会话存储设计草案"
python tools/dev_log.py todo --todo "补充 Skill 路由单元测试"
python tools/dev_log.py verify --verify "运行 pytest tests/test_skill_service.py"
```

如果系统日期不可靠，可以显式指定日期：

```bash
python tools/dev_log.py --date 2026-06-01 done --done "初始化开发日志体系"
```

