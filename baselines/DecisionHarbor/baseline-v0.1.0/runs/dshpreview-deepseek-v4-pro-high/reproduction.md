# DeepSeek Harness Web 复现记录

## 状态

- 候选冻结于 `4306278abbfb4a65d6d52a6e701c1e308fe2ed46`，基线为 `baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 候选工作树和分支分别为 `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high` 与 `v0.1.0/dshpreview-deepseek-v4-pro-high`。复现前后 `HEAD` 一致，工作树干净，`git diff --check` 通过。
- 结果分支尚未推送；本地冻结提交可直接用于当前工作树中的首轮评审。

## 固定输入与环境

- 开发委托 SHA-256：`fd72d609fffcf0dee4fe2760c8a112468fddce647ad57ec2e68b375d3cf2aa23`。
- 数据契约 SHA-256：`b790ae12efe3393529829008c794e56df469a96b3861130443bbf200ca34b757`；manifest SHA-256：`dad00a2fb52b7ffe6d5abdd68290dd5ad1e233d7f17e4cb083ffeb52e559ce9d`。
- 共用外部 Skill 清单 SHA-256：`6e54ce93d8b1ad32cf4c0798f97f70d0e9efbbdd189ef3c8eadd02cb3a8c0760`。
- Docker `29.1.3`，Docker Compose `2.40.3`，宿主 Node.js `24.16.0`，宿主 Python `3.10.12`，容器 PostgreSQL `18.4`、Python `3.13.14`、Node.js `24.18.0`，Playwright `1.61.1`。

## 独立复现

- `python3 datasets/sales-analytics-v1/validate.py`：通过。
- `make test`：通过；Pytest `50 passed`、Vitest `1 passed`、Playwright `2 passed`。Pytest 仅报告 4 条依赖弃用警告。
- 主实例在 Web `5173`、API `8010` 启动；`/health` 返回 200 / `{"status":"ok"}`，`/ready` 返回 200 / `{"status":"ready"}`，Web 返回 200。
- API 允许查询与 CTE 查询成功，客户总数为 100；DROP、多语句和直接读取 `pg_catalog.pg_class` 分别以稳定策略错误拒绝。`generate_series(1, 10001)` 触发行数上限，最终状态为 `failed`、错误码为 `EXEC_ROW_LIMIT_EXCEEDED`。
- 分析只读身份可以读取 `analytics`，写入因只读事务失败；读取 `platform.public.query_runs` 因权限不足失败，写入同样失败。重复 bootstrap 与 seed 幂等性由独立运行的集成测试覆盖。
- 数据库停止后 `/ready` 在约 8.01 秒返回 503；数据库恢复后约 0.026 秒返回 200。
- 使用 `COMPOSE_PROJECT_NAME=dhdeepverify2`、API `58110`、Web `55174` 启动第二套实例时，两套 `/ready` 与 Web 均返回 200，网络、端口和数据卷隔离；第二套允许查询返回客户总数 100。

## 安全边界观察

以下查询均通过 API 策略并成功执行，能够解析或读取系统对象：

- `CAST('pg_catalog.pg_class' AS regclass)`；
- `'pg_catalog.pg_class'::regclass`；
- `to_regclass('pg_catalog.pg_class')`；
- `query_to_xml('SELECT relname FROM pg_class LIMIT 1', true, false, '')`，返回系统表名 `pg_statistic`；
- `WITH pg_class AS (...) SELECT relname FROM pg_catalog.pg_class LIMIT 1`，返回系统表名 `pg_statistic`。

这些是可复核的首轮评审输入，不在协调归档阶段预先计算分数。它们满足评分规范中“用户 SQL 能访问系统对象”的 P0 判定条件，最终风险标记在两份互盲报告完成后汇总确认。

## 资源与未验证项

- `dhdeepverify2` 的容器、网络和专用卷已删除。主候选容器与网络已停止并移除，保留 `decisionharbor_pgdata`；未触碰 19 个无关 ExamForge 容器。
- 未独立测量 30 秒 API 查询超时，只确认集成测试中的 500 ms 执行器超时用例通过。
- 未进行人工视觉评分；该项在两份首轮报告完成后由用户处理。
