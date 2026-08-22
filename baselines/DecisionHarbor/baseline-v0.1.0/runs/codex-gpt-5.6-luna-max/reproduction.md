# Codex GPT-5.6 Luna Max 复现记录

## 冻结身份核验

- 候选工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-luna-max`。
- 候选分支：`v0.1.0/codex-gpt-5.6-luna-max`。
- baseline：`baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 结果提交：`1dfb4a4d4d441350b6035ea36eacf414cb9e4023`。
- 协调方确认结果提交以 baseline 为祖先，冻结前后工作树洁净，`git diff --check` 无输出。
- 远端分支已推送，远端 SHA 与本地结果提交一致。

以上是冻结身份与 Git 状态核验，不构成产品行为复现。

## Agent 报告的验证结果

开发会话报告最终 `./dev test` 完整通过，包含：

- 固定数据校验通过。
- Python 3.13 API 测试 `25 passed`。
- Vitest `2 passed`。
- Playwright `2 passed`。
- PostgreSQL、API 和 Web 均为 healthy。
- API 与 Web 的 `/health`、`/ready` 均为 HTTP 200。
- 允许查询成功并返回客户数 `100`。
- 对 `platform.query_runs` 的查询被拒绝，错误码为 `object_not_allowed`。
- 审计事件包含 `received -> executing -> succeeded` 和 `received -> rejected`。
- 重复迁移和 seed 报告 `already_loaded`。

这些内容来自 Agent 会话自述，协调方没有在本阶段重新执行，不能作为独立评审的通过证据。

## 协调方复现决定

用户决定跳过冻结阶段的协调方复现，原因是两位独立评审随后都需要对同一冻结提交取得新鲜运行证据。协调方因此没有运行数据集校验、`./dev test`、Compose 启动、HTTP 探针、数据库权限探针、浏览器主链、并行实例或 SQL 安全绕过探针。

上述项目在进入每一份首轮评审时均为待独立验证，评审者不得用本文件中的 Agent 自述替代现场运行。

## 运行资源

开发会话结束时，Compose 项目 `decisionharbor-codex-luna` 仍有 PostgreSQL、API 和 Web 三项 healthy 服务。协调方核对项目归属后执行：

```bash
docker compose -p decisionharbor-codex-luna down --remove-orphans
```

候选容器与默认网络已移除，命名数据卷 `decisionharbor-codex-luna_postgres-data` 保留。未停止或清理 ExamForge 等无关项目。
