# DecisionHarbor v0.1.0 Codex 首轮独立评审

评审日期：2026-07-21

## 独立性声明

本报告仅依据本次在冻结候选工作树上的代码阅读和新鲜运行证据形成。我没有读取、引用、比较或延续任何其他候选的工作树、分支、运行记录、评审材料、分数、命令输出或结论；也没有读取本候选的 `grok-review.md`、`review-summary.md` 或 `scorecard.md`。`reproduction.md` 中的 Agent 自述未作为通过证据或加分依据。

本次未修改候选源码、候选分支、baseline、评分规则或其他归档文件；唯一写入为本文件。

## 冻结状态与环境

- 候选分支：`v0.1.0/codex-gpt-5.6-sol-xhigh`
- 评审 HEAD：`6e3964f05b72d44a50f7d2a7657304a83cfa11c1`，与指定冻结 commit 一致。
- baseline commit：`1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 开始和结束时的 `git status --short --branch` 都只显示跟踪分支；`git diff --check` 均为无输出。
- 宿主：Docker `29.1.3`、Docker Compose `2.40.3`、Node.js `v24.16.0`、Python `3.10.12`。实际应用容器使用项目锁定的 Python `3.13`、Node.js `24`、PostgreSQL `18`；浏览器测试使用 Playwright Chromium 容器。
- 候选根目录不存在 `.codegraph/`，因此未使用 CodeGraph。

## 实际执行命令与结果

以下均在候选工作树 `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-sol-xhigh` 中执行，除非另注。

```text
git rev-parse HEAD
git status --short --branch
git diff --check
(datasets/sales-analytics-v1) python3 validate.py
COMPOSE_PROJECT_NAME=dhcodexreviewa WEB_HOST_PORT=19173 API_HOST_PORT=19180 ./dev up
COMPOSE_PROJECT_NAME=dhcodexreviewa WEB_HOST_PORT=19173 API_HOST_PORT=19180 ./dev test
COMPOSE_PROJECT_NAME=dhcodexreviewb WEB_HOST_PORT=19273 API_HOST_PORT=19280 \
  QUERY_MAX_ROWS=2 QUERY_STATEMENT_TIMEOUT_MS=1000 QUERY_MAX_CONCURRENCY=1 \
  QUERY_CAPACITY_WAIT_MS=1 ./dev up
```

- 数据集校验成功。
- 实例 A 从空命名卷启动，Web、API、PostgreSQL 健康；`/health` 和 `/ready` 均为 `200`。实例 A 重复初始化日志为 `bootstrap complete: dataset unchanged`，实例 B 首次日志为 `bootstrap complete: dataset seeded`。
- `./dev test` 成功：pytest `62 passed, 1 warning`、Vitest `6 passed`、Playwright Chromium `4 passed`。Playwright 是连到 Compose 中实际 Web/API 的主链，覆盖允许查询、策略拒绝、语义失败、截断与就绪恢复。
- 允许查询 `SELECT status, count(*) AS order_count FROM orders GROUP BY status ORDER BY status` 返回 `cancelled=100`、`confirmed=720`、`pending=100`、`refunded=80`，查询运行终态为 `succeeded`；后续 `GET /api/v1/query-runs/{id}` 返回审计事实且不含结果单元格。
- `DELETE FROM customers`、`SELECT * FROM pg_catalog.pg_class` 和 `SELECT 1; SELECT 2` 分别稳定返回 `422`，错误码为 `sql_statement_not_allowed`、`sql_object_not_allowed`、`multiple_statements`，并都有 `rejected` 审计记录。
- 数据库身份实测：`analytics_reader` 的 `default_transaction_read_only=on`，可读 `analytics.customers` 的 100 行；其 `UPDATE` 被 PostgreSQL 拒绝。`analytics_reader -> platform` 与 `platform_app -> analytics` 连接均被 `CONNECT` 权限拒绝。
- 实例 B 的 `QUERY_MAX_ROWS=2` 返回两行并标记 `truncated=true`；受控三重 `order_items` 笛卡尔积在 1 秒限制下返回 `504/query_timeout`；同一时间第二请求返回 `429/query_capacity_exceeded`。
- 实例 A 与 B 同时 `/ready=200`，A 的 `query_runs` 为 14 行、B 在任何请求前为 0 行，证明两个 Compose 项目未共用平台库卷。两个实例均使用独立网络、卷和端口。
- 停止实例 B 的 PostgreSQL 后，`/health=200` 而 `/ready=503/service_not_ready`；重新启动数据库后 `/ready=200`。向 B 插入一个临时 `received` 审计记录并重启 API 后，该记录变为 `failed/execution_interrupted`。

## 技术评分（封顶前）

| 维度 | 子项 | 分数 | 新鲜证据与判断 |
| --- | --- | ---: | --- |
| 功能与外部契约 | 查询运行 API 生命周期 | 8 / 8 | POST 成功后可 GET 到同一审计记录，状态和结果分离符合契约。 |
|  | 允许查询结果正确性 | 7 / 7 | 实测五表固定数据的订单状态聚合与 contract 一致。 |
|  | 拒绝与执行失败语义 | 5 / 5 | 实测 DML、系统对象、多语句拒绝；集成/浏览器主链实际验证语义失败与超时。 |
|  | 最小查询工作台 | 5 / 5 | Playwright 4 个真实 Compose 浏览器用例全部通过。 |
|  | **功能与外部契约小计** | **25 / 25** |  |
| SQL 治理与数据正确性 | AST 只读语义与单语句约束 | 3 / 6 | 普通 DML、多语句、修改型结构均拒绝，但存在下述 `reg*` 类型转换的 AST 对象治理绕过。 |
|  | 授权对象与 schema 范围 | 2 / 4 | 直接访问未授权对象会拒绝；但内部维护 relation、系统 relation 和角色名可被未建模的对象标识类型转换解析并返回。 |
|  | 数据库身份与双库隔离 | 4 / 4 | 两个运行时身份、只读事务、写入拒绝与跨库 `CONNECT` 拒绝均在 PostgreSQL 18 实测。 |
|  | 执行资源限制 | 3 / 3 | 行数、1 秒语句超时和容量拒绝均经真实 API 观察。 |
|  | 固定数据契约与业务口径 | 3 / 3 | 数据集 validator、迁移/seed 集成测试和订单状态实测一致。 |
|  | **SQL 治理与数据正确性小计** | **15 / 20** |  |
| 可运行性与可靠性 | 干净环境启动与就绪 | 6 / 6 | `./dev up` 构建、等待并启动三个运行服务；health/ready 实测。 |
|  | 迁移与固定数据初始化 | 6 / 6 | 空卷 `seeded`，重复启动 `unchanged`，pytest 集成测试覆盖重复 seed 与冲突。 |
|  | 并行实例隔离 | 5 / 5 | 两个显式项目名和两组端口同时运行，网络、卷和审计数据隔离。 |
|  | 重启与故障可见性 | 3 / 3 | DB 失联时 health/ready 分离，恢复后就绪；API 重启收敛遗留审计记录。 |
|  | **可运行性与可靠性小计** | **20 / 20** |  |
| 测试与验证证据 | 统一测试入口与可靠断言 | 3 / 3 | `./dev test` 非零失败语义由 shell 严格模式保证，本次全量入口成功。 |
|  | SQL 策略单元测试 | 2.5 / 5 | 覆盖常见允许、DML、修改型 CTE、多语句、系统表、函数和边界语法；未覆盖导致 P0 的 PostgreSQL `reg*` 对象标识类型转换。 |
|  | 双数据库集成测试 | 4 / 4 | pytest 中的真实 PostgreSQL contract、identity、seed 与 query chain 用例连同本次手工身份验证均通过。 |
|  | 浏览器主链测试 | 3 / 3 | Playwright 真实 Compose 主链 4/4 通过。 |
|  | **测试与验证证据小计** | **12.5 / 15** |  |
| 代码质量与可维护性 | 模块边界与职责分离 | 3 / 3 | API、policy、service、repository、executor、bootstrap 和 Web 客户端边界清楚。 |
|  | 配置、错误处理与资源清理 | 3 / 3 | 配置有界校验；执行器有事务、超时、连接池和安全错误映射；Compose 可定向关闭。 |
|  | 类型、命名、重复控制与可测试性 | 2 / 2 | 纯策略模块、协议接口、领域数据类和单元/集成接缝可测试。 |
|  | 依赖、变更范围与维护负担 | 1 / 2 | 依赖版本固定、变更范围集中；但本次 `./dev test` 仍产生 `StarletteDeprecationWarning`，上游 `TestClient`/httpx 迁移应在升级前处理。 |
|  | **代码质量与可维护性小计** | **9 / 10** |  |

**技术总分（封顶前）：81.5 / 90**

## 产品文档建议分（不含视觉）

**建议：4 / 5**

- 治理、索引与阅读入口：`1 / 1`。`README.md`、`docs/index.md`、目录规则和背景/设计/计划/status 的职责清晰。
- 设计完整性与可追溯性：`2 / 2`。`docs/design/first-release-system-design.md` 对数据合同、双库、状态流、资源限制和测试接缝有可追溯说明。
- 计划、运行/测试说明与实现一致性：`1 / 2`。启动、seed、测试和浏览器路径均可复现，但设计与状态文档宣称对象范围由完整 AST 策略约束，未覆盖实际允许的 `reg*` 对象标识转换，因此安全边界的实现一致性不足。

未评视觉项，也未计算最终 100 分、技术平均分或任何候选间平均分。

## 封顶判断

| 级别 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | **命中** | `POST /api/v1/query-runs` 发送 `SELECT 'maintenance.dataset_seeds'::regclass::text AS resolved_object` 返回 `200`、`succeeded`、`policy_decision=allowed`、`referenced_objects=[]`，且结果为 `maintenance.dataset_seeds`。`SELECT 'pg_catalog.pg_class'::regclass::text` 返回 `pg_class`，`SELECT 'harbor_admin'::regrole::text` 返回 `harbor_admin`。对照地，直接 `SELECT * FROM maintenance.dataset_seeds` 返回 `422/sql_object_not_allowed`。用户 SQL 已通过 AST 对象范围治理绕过解析并返回未授权内部对象、系统对象和角色对象。 |
| P1 基座失败 | 不命中 | 独立启动、迁移、seed、health、ready、恢复、完整测试入口均有成功证据。 |
| P2 核心闭环缺失 | 不命中 | 允许查询、拒绝查询和浏览器工作台均在本次实例上实测成立。 |

根据评分规范，P0 证据成立时，汇总阶段适用质量原始分 `39` 的上限。本报告只给出技术 90 分和文档建议分，不计算最终 100 分或任何平均分。

## 问题清单

### P0 - 必须修复：`reg*` PostgreSQL 对象标识类型转换绕过对象授权

- **位置：** `apps/api/src/decisionharbor/policy.py:62-123,162-188`；`apps/api/migrations/analytics/versions/0001_sales_analytics.py:67-71`。
- **根因：** 策略将所有 `exp.DataType` 视为支持节点，并只通过 `scope.tables` 检查 `FROM`/JOIN 表来源。`regclass`、`regrole` 等 PostgreSQL 对象标识伪类型在 CAST 表达式中不产生受检查的 table source，函数白名单也不会覆盖它们；数据库又为 readiness 向 `analytics_reader` 授予了内部维护 relation 的读取权限。
- **复现：**

```text
POST /api/v1/query-runs
{"sql":"SELECT 'maintenance.dataset_seeds'::regclass::text AS resolved_object"}

HTTP 200
status=succeeded
policy_decision=allowed
referenced_objects=[]
rows=[["maintenance.dataset_seeds"]]
```

- **影响：** 违反“只允许 analytics 五张业务表、拒绝系统目录和未授权对象”的外部契约，且审计没有记录实际解析的对象。属于评分规则中“访问系统或未授权对象 / 绕过 AST 治理”的 P0 条件。
- **建议：** 为 CAST/DataType 增加正向类型允许集，至少拒绝所有 `reg*` 对象标识类型及任何能解析 relation、role、function、namespace 或 type catalog 的转换；用真实 API 回归测试覆盖 `regclass`、`regrole`、`regproc`、`regnamespace` 等，并断言拒绝记录的稳定错误码和零执行路径。

### P2 - 建议修改：统一测试入口仍有上游弃用警告

- **证据：** 本次 `./dev test` 的 pytest 输出包含 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
- **影响：** 当前不影响可运行性或测试结果，但依赖升级时可能破坏测试入口。
- **建议：** 在升级 FastAPI/Starlette/httpx 前安排兼容性迁移，并让全量测试恢复为无该弃用警告。

## 未验证项

以下项未按通过处理：

- 未提供或运行非公开 harness；本报告没有为其隐含用例给分。
- 启动在已有 Docker 镜像缓存的宿主上完成；未通过破坏性清理 Docker 缓存来模拟全新主机。这不影响已观察到的构建/启动路径，但“零缓存全新 WSL”没有单独验证。
- 两个 Compose 项目是在同一候选工作树中同时启动，已证明项目名、端口、网络和卷隔离；未另起一个物理工作树做同一验证。
- `npm audit` 没有在本次独立评审中执行；状态文档中的该项自述未被采信。
- 未进行前端视觉评分或手工视觉截图审美判断，依题意不计视觉项。

## Compose 清理与最终 Git 状态

- 本次只创建了 `dhcodexreviewa`（`19173/19180`）和 `dhcodexreviewb`（`19273/19280`）两个 Compose 项目。
- 已对两者分别执行 `./dev down`；项目专属容器和网络均已移除，项目专属命名卷按项目 `down` 的非破坏性语义保留，未触碰任何无关项目。
- 清理后项目专属 `docker compose ps --all --format json` 均为空。
- 最终候选 HEAD 仍为 `6e3964f05b72d44a50f7d2a7657304a83cfa11c1`；`git status --short --branch` 无未提交改动，`git diff --check` 无输出。
