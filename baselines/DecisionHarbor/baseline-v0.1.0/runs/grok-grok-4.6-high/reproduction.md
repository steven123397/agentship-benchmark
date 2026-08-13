# Grok Build 4.6 复现记录

## 状态

- 候选已冻结于 `cd8b766fa6242cf1bdb30304af6f453af6331af7`（`feat(首轮): 交付受治理 SQL 查询平台`），并已推送 `v0.1.0/grokbuild-grok-4.6-high`。
- 基线为 `baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`；工作树位于 `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high`。
- 冻结后 `HEAD`、本地分支和远端分支均为该结果 SHA，工作树无未提交改动。`git show --check` 对已提交的 `docs/design/governed-query-path.md` 报告 9 处行尾空格；这不是冻结后的工作树改动，且为保留 Agent 原始交付而未由协调方修正。
- 候选 Compose 容器和网络已停止并移除；命名数据卷 `dh-grok-46-high_postgres_data` 保留。

## 协调方独立复现

以下命令均在候选工作树运行，使用候选未跟踪的 `.env` 所定义的隔离 Compose 项目和端口：

```bash
python3 datasets/sales-analytics-v1/validate.py
./scripts/test.sh
docker compose --env-file .env --profile test run --rm api-test
docker compose --env-file .env --profile test run --rm web-test
docker compose --env-file .env --profile test run --rm e2e
```

- 固定数据集校验成功。
- `./scripts/test.sh` 成功退出；单独复验取得 API 测试 `25 passed, 1 warning in 1.93s`、Vitest `3 passed` 和 Playwright `2 passed (2.6s)`。
- API `GET /health` 返回 `200 {"status":"ok"}`，`GET /ready` 返回 `200 {"status":"ready"}`；Web 根路径返回 `200`。
- 允许查询 `SELECT id, region FROM customers ORDER BY id LIMIT 2` 返回 `succeeded`、2 行结果；`DELETE FROM orders` 返回 `rejected/POLICY_DENIED`；多语句返回 `rejected/QUERY_INVALID`；无 `LIMIT` 的 `order_items` 查询返回 `failed/RESULT_LIMIT_EXCEEDED`。
- 直接 `pg_catalog.pg_class` 查询与 CTE 同名遮蔽的系统目录查询均返回 `rejected/POLICY_DENIED`。额外探针 `SELECT CAST('pg_catalog.pg_class' AS regclass)` 返回 `succeeded`，结果为 `pg_class`；该事实只供后续首轮独立评审核验，不构成协调方的风险判断或评分。

## 运行资源

复现完成后，协调方执行：

```bash
docker compose --env-file .env down --remove-orphans
```

`dh-grok-46-high` 的 Web、API、PostgreSQL 容器和默认网络均已移除，命名 PostgreSQL 数据卷保留。未触碰其他项目资源。
