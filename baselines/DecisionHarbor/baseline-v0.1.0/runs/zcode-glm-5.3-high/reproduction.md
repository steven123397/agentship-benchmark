# ZCode GLM-5.3 High 复现记录

## 冻结身份核验

- 候选工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.3-high`。
- 候选分支：`v0.1.0/zcode-glm-5.3-high`。
- baseline：`baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 结果提交：`a5811b218e42183f9b46aa2a2555194a658c7cf5`。
- 候选自行创建了 3 个结果提交；协调方确认最终提交以 baseline 为祖先，冻结时工作树洁净，`git diff --check` 无输出。
- 远端分支已推送，远端 SHA 与本地结果提交一致。

以上是冻结身份与 Git 状态核验，不构成产品行为复现。

## 候选报告的验证结果

候选的 `docs/status/project_status.md` 报告首轮目标已实现，并记录：

- `pytest tests` 为 `59 passed`，其中 51 个单元测试、8 个集成测试。
- Vitest 为 `4 passed`。
- Playwright 为 `2 passed`。
- `make up` 可重复收敛，`/ready` 为 HTTP 200。
- 重复启动后五张固定数据表的行数保持为 100、8、50、1000、3000，seed 标记不变，审计记录持久。

这些内容来自候选自身的状态文档，协调方没有在本阶段重新执行，不能作为独立评审的通过证据。

## 协调方复现决定

沿用用户对本轮候选的决定，冻结阶段不重复执行协调方复现，将新鲜运行证据留给两位独立评审。协调方没有运行数据集校验、`make test`、Compose 启动、HTTP 探针、数据库权限探针、浏览器主链、并行实例或 SQL 安全绕过探针。

上述项目在进入每一份首轮评审时均为待独立验证，评审者不得用本文件中的候选自述替代现场运行。

## 运行资源

候选结束时，Compose 项目 `decision-harbor` 的 PostgreSQL、API 和 Web 服务仍在运行。协调方按工作目录和 Compose 标签核对归属后执行：

```bash
docker compose -f deploy/compose.yaml -p decision-harbor down --remove-orphans
```

候选容器与默认网络已移除，命名数据卷 `decision-harbor_pgdata` 保留。未停止或清理 ExamForge 等无关项目。
