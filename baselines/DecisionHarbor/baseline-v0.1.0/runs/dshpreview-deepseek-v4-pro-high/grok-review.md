# DecisionHarbor v0.1.0 Grok 首轮独立评审

- 审查者：Grok Build
- 候选：DeepSeek Harness Web / deepseek-v4-pro-high
- 产品工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high`
- 候选分支：`v0.1.0/dshpreview-deepseek-v4-pro-high`
- `RESULT_COMMIT`：`4306278abbfb4a65d6d52a6e701c1e308fe2ed46`
- baseline commit：`1fb48f499d67677a47fb9b60e1f99346b46e0aee`（该提交是 `HEAD` 祖先）
- 评审日期：2026-08-14
- 索引：`review-prompts.md` 第 15 行

## 独立性声明

本报告只依据本次对冻结 commit 的代码阅读，以及本审查者在该工作树内新执行的命令、HTTP 探针、数据库探针、统一测试入口和独立 Playwright 复现。不读取、不引用、不比较其他候选的工作树、分支、运行记录或评审材料；不读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。不引用开发自述或给予自我信用。不因 Agent、模型、耗时或 token 调整分数。未修改候选源码、分支、baseline 或评分规范；唯一写入的文件是本报告。

冻结前置条件已满足：`metadata.json` 中 `completion.coordinatorFrozen` 为 `true`，`candidate.resultCommit` 为完整 SHA `4306278abbfb4a65d6d52a6e701c1e308fe2ed46`。开始前 `git rev-parse HEAD` 等于该 SHA，`git status --short --branch` 无未提交改动。

## 评审 commit、环境与实际执行命令

### 工作树状态（开始）

```text
HEAD  4306278abbfb4a65d6d52a6e701c1e308fe2ed46
branch  v0.1.0/dshpreview-deepseek-v4-pro-high
git status --short --branch  无未提交改动
git diff --check  退出码 0
```

### 环境

| 项 | 值 |
| --- | --- |
| 宿主机 | Linux MAGICBOOK14，WSL2，`6.18.33.2-microsoft-standard-WSL2` |
| Docker | 29.1.3 |
| Docker Compose | 2.40.3 |
| Node.js | v24.16.0 |
| 宿主机 Python | 3.10.12（数据集校验）；API 镜像为 `python:3.13-slim` |
| 候选 `.env` | `API_PORT=8010`，`WEB_PORT=5173`，`VITE_API_BASE_URL=http://localhost:8010`，`CORS_ORIGIN=http://localhost:5173` |
| Compose 项目 | 主实例 `decisionharbor`；并行实例 `dhds-review2`（API `58110`，Web `55174`） |

评审开始时宿主机另有 `examforge`、`examforge-v5p3-e2e`、`examforge-v5p4-preview` 在运行。全程未停止这些无关项目。

### 实际执行的命令

1. `git rev-parse HEAD`、`git status --short --branch`、`git log -1`、`git diff --check`、`git merge-base --is-ancestor 1fb48f499d67677a47fb9b60e1f99346b46e0aee HEAD`
2. `python3 datasets/sales-analytics-v1/validate.py`
3. `make up`
4. `curl`：API `/health`、`/ready`、Web 根路径
5. Python HTTP 探针：允许查询、拒绝查询、系统对象绕过、行数上限、超时、非法请求体、生命周期 `GET`
6. `docker compose exec`：双库、三身份、`CONNECT`、只读写入拒绝、五表行数、订单状态、表权限
7. 独立 CSV 重算已实现销售额，并与 API 聚合结果对照
8. `docker compose restart api`；停止再启动 `db`，观察 `/health` 与 `/ready`
9. `make test`
10. 并行启动 `COMPOSE_PROJECT_NAME=dhds-review2` 并对其发允许查询
11. 在 `/tmp` 对实时 Web 跑独立 Playwright（`127.0.0.1` 与 `localhost` 各一次；未写入候选工作树）
12. 结束：停止本次评审启动的两个 Compose 项目，再次检查 Git

AgentShip 工作区未找到可执行的非公开 harness 副本。下列结论来自公开契约、产品代码和本审查者的新鲜探针。

## 技术评分

子项按规范三档计分：未通过 `0`，部分通过为该子项 `50%`，完全通过为满分。技术总分可保留 `0.5` 分。

### 1. 功能与外部契约 — 25 / 25

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**查询运行 API 生命周期。** `POST /api/v1/query-runs` 对允许的 SQL 返回 `202` 且 `status=running`，随后 `GET /api/v1/query-runs/{id}` 进入终态。成功记录 `d7d0f7ba-e93e-4cf1-b1e9-71c8d7b9d3af` 的 `GET` 给出列、行、`row_count`、`duration_ms` 与原始 SQL。非法体返回 `400` / `INVALID_REQUEST`；不存在标识返回 `404` / `NOT_FOUND`。拒绝同样建档。设计将结果放在内存缓存，`GET` 在缓存命中时附带结果网格；审计事实仍在 `platform.query_runs`。

**允许查询结果正确性。** `SELECT id, region FROM customers ORDER BY id LIMIT 2` 返回 `[[1, "West"], [2, "East"]]`。`count(*)` 为 `100`。已实现销售额查询返回 `"11058789.642500"`，与权威 CSV 独立重算一致。CTE、连接、`UNION ALL` 均可执行。`numeric` 以字符串返回。

**拒绝与执行失败语义。** `DELETE` / `DROP` → `422` / `rejected` / `POLICY_FORBIDDEN_STATEMENT`；多语句 → `POLICY_MULTIPLE_STATEMENTS`；修改型 CTE → `POLICY_DATA_MODIFYING_CTE`；`SELECT INTO` → `POLICY_SELECT_INTO`。`generate_series(1, 10001)` → `failed` / `EXEC_ROW_LIMIT_EXCEEDED`。三表笛卡尔积 → `failed` / `EXEC_TIMEOUT`（约 30016 ms）。拒绝与失败均带稳定错误码、可读说明和记录 `id`，不伪装为成功。

**最小查询工作台。** Web 根路径 200，标题为「DecisionHarbor 工作台」。`make test` 中 Playwright 2 passed。审查者对 `http://localhost:5173` 独立复现：允许查询先见「执行中」再见表格与 `West`；`DROP TABLE customers` 见 `POLICY_FORBIDDEN_STATEMENT` 与「已拒绝」。对 `http://127.0.0.1:5173` 的同套脚本因 CORS 源不匹配得到 `Failed to fetch`；产品默认源是 `localhost`，不否定工作台在约定入口上可用。

**未验证：** 无浏览器 MCP 人工点击。未运行非公开 harness 的额外 API 边界用例。

### 2. SQL 治理与数据正确性 — 16 / 20

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| AST 只读语义与单语句约束 | 6 | 6 | 完全通过 |
| 授权对象与 schema 范围 | 4 | 0 | 未通过 |
| 数据库身份与双库隔离 | 4 | 4 | 完全通过 |
| 执行资源限制 | 3 | 3 | 完全通过 |
| 固定数据契约与业务口径 | 3 | 3 | 完全通过 |

**AST 只读语义与单语句约束。** `api/app/policy.py` 使用 `sqlglot.parse(..., read="postgres")`，要求恰好一条语句，根节点为 `Select` / `Union` / `Intersect` / `Except`，再遍历 AST 分类写操作。实测拒绝多语句、`INSERT`/`UPDATE`/`DELETE`/`DROP`/`COPY`、修改型 CTE、`SELECT INTO`、`EXPLAIN`、`SET`、空输入。注释和字符串中的写关键字不误拒。不是字符串黑名单。

**授权对象与 schema 范围。** 直接 `SELECT * FROM pg_catalog.pg_class`、`information_schema.tables`、`query_runs`、`pg_stat_activity` 均 `POLICY_UNAUTHORIZED_OBJECT`。但策略把 CTE 别名从物理表检查中整名剔除，且不校验函数与嵌套查询字符串。下列用户 SQL 均策略放行并成功读出系统对象：

| 语句 | 结果 |
| --- | --- |
| `CAST('pg_catalog.pg_class' AS regclass)` / `'pg_catalog.pg_class'::regclass` / `to_regclass(...)` | 返回 `pg_class` |
| `WITH pg_class AS (...) SELECT relname FROM pg_catalog.pg_class LIMIT 3` | 返回 `_pg_foreign_data_wrappers` 等系统关系名 |
| `WITH tables AS (...) SELECT table_schema, table_name FROM information_schema.tables` | 返回 `analytics.customers` 等 |
| `WITH pg_tables AS (...) SELECT schemaname, tablename FROM pg_catalog.pg_tables` | 返回目录行 |
| `SELECT query_to_xml('SELECT relname FROM pg_class LIMIT 5', ...)` | XML 中含 `customers` 及系统关系 |
| `SELECT query_to_xml('SELECT rolname FROM pg_roles', ...)` | XML 中含 `postgres`、`dh_admin`、`platform_writer`、`analytics_reader` |
| `SELECT query_to_xml('SELECT datname FROM pg_database LIMIT 3', ...)` | XML 中含 `postgres`、`platform`、`template1` |

这是用户 SQL 访问系统目录与未授权对象，并绕过 AST 对象范围。本子项未通过。

**数据库身份与双库隔离。** 用户 SQL 的 `current_user` / `session_user` 均为 `analytics_reader`。只读身份 `INSERT`/`UPDATE`/`DELETE` 为 `cannot execute ... in a read-only transaction`。`platform_writer` 对 `analytics` schema 为 `permission denied`。`analytics_reader` 对 `platform.public.query_runs` 为 `permission denied for table query_runs`。执行器只使用 `analytics_reader` DSN。`PUBLIC` 仍默认可 `CONNECT` 两库，因此身份可以连上对方数据库，但表级授权挡住了读写；用户 SQL 路径本身不切换到 `platform`。按「用户 SQL 由独立只读身份执行且不能读写 platform」给满分，CONNECT 缺口记入问题清单。

**执行资源限制。** `QUERY_ROW_LIMIT` 默认 10000。`generate_series(1, 10001)` → `EXEC_ROW_LIMIT_EXCEEDED`。`order_items` 全表 3000 行低于上限，返回 `succeeded` / 3000，符合该配置。笛卡尔积在约 31 s 后 `EXEC_TIMEOUT` / 「Statement timed out after 30000 ms」。集成测试另用 500 ms 超时证明 `pg_sleep(5)` → `EXEC_TIMEOUT`。

**固定数据契约与业务口径。** `validate.py` 成功。只读身份计数：100 / 8 / 50 / 1000 / 3000。订单状态：`confirmed=720`、`pending=100`、`cancelled=100`、`refunded=80`。销售额与 CSV 重算一致。`schema_catalog` 按契约生成 DDL，金额为定点类型。

**未验证：** 未运行非公开 harness 的其余绕过集。未在手工改写分析表后再跑 seed 恢复（幂等由 `test_seed_is_idempotent` 覆盖）。

### 3. 可运行性与可靠性 — 20 / 20

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 3 | 完全通过 |

**干净环境启动与就绪。** `make up` 构建并启动 `db` / `api` / `web`，`scripts/wait-ready.sh` 打印 `ready`。API `/health` → `200 {"status":"ok"}`；`/ready` → `200 {"status":"ready"}`。Web 根路径 200。PostgreSQL 不发布宿主端口。

**迁移与固定数据初始化。** 启动后两库、三身份、Alembic `query_runs`/`dataset_seed` 与 CSV seed 均成立。`test_seed_is_idempotent` 通过。`/ready` 会核对 `dataset_seed.version` 并用只读身份 `count(*)` 五张表。

**并行实例隔离。** `docker-compose.yml` 无 `container_name`，卷为项目作用域 `pgdata`。第二实例 `dhds-review2`（55174 / 58110）与主实例同时 `running(3)`，独立网络与卷。rev2 `/ready` 200，`SELECT count(*) FROM customers` 返回 100；rev1 `/ready` 与 Web 仍 200。API 对数据集使用只读绑定 `./datasets/sales-analytics-v1`，两实例共享同一份权威夹具目录，不共享数据库卷。

**重启与故障可见性。** `restart api` 后约 2 次探测即 `/ready`。停止 `db` 后 `/health` 仍 200，`/ready` 为 `503 {"status":"not_ready", ...}`。重新 `start db` 后约 2 次探测恢复 200。`/ready` 在请求时探测两库，不是粘性布尔。

**未验证：** 未在完全空白的新数据卷上对主实例再走一遍 init（并行新卷 `dhds-review2_pgdata` 已成功初始化）。

### 4. 测试与验证证据 — 15 / 15

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 3 | 完全通过 |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**统一测试入口。** `make test` 退出码 0。本次输出：Pytest `50 passed, 4 warnings in 2.92s`；Vitest `1 passed`；Playwright `2 passed (2.2s)`。失败会非零退出。

**SQL 策略单元测试。** `api/tests/unit/test_policy.py` 覆盖允许的 `SELECT` / `WITH` / 连接 / 子查询 / 聚合 / 窗口 / 集合运算；拒绝多语句、写操作、DDL、`COPY`/`CALL`、修改型 CTE、`SELECT INTO`、系统目录、未授权表、跨库限定名；注释或字符串中的写关键字不误拒。未覆盖 CTE 同名遮蔽与 `query_to_xml`，这是覆盖缺口，但公开基线要求的类别已具备。

**双数据库集成测试。** 证明 seed 幂等、平台身份可写审计、只读身份可读且 `INSERT` 被拒、行上限与超时、允许查询生命周期、拒绝落库、启动收敛 `EXEC_INTERRUPTED`。

**浏览器主链测试。** 产品 Playwright 覆盖允许结果表与拒绝码。审查者在 `localhost` 源下独立复跑允许（含「执行中」）与拒绝，2 passed。

**未验证：** 产品 e2e 未断言「执行中」文案（独立脚本已补证）。未运行非公开 harness。

### 5. 代码质量与可维护性 — 7.5 / 10

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | 部分通过 |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 1 | 部分通过 |

**模块边界。** `web/`、`api/`、Compose `db` 三分。策略、执行器、审计存储、编排服务、健康路由职责清楚。策略不执行用户 SQL；执行器只用只读 DSN；工作台只走 HTTP。

**配置、错误处理与资源清理。** 端口与项目名可配置；`/ready` 实时探测依赖。扣分：`CORS_ORIGIN` 默认钉死 `http://localhost:5173`，用 `127.0.0.1` 打开同一端口会 `Failed to fetch`；执行失败把 SQLAlchemy/psycopg 原文（含 SQL）送进 `error.message`；`execute()` 每次查询新建并销毁 Engine；`PUBLIC` 的数据库 `CONNECT` 未收回。

**类型、命名与可测试性。** API 有类型标注；策略可单测；契约驱动目录减少表清单双写。

**依赖与维护负担。** `api/requirements.txt` 未钉发行版本；Web 镜像 `npm install` 且仓库无 lockfile。`README.md` 仍写「应用源码尚未建立」；`docs/design/README.md` 与 `docs/plan/README.md` 声称目录为空，但已有 `system-design.md` 与 `first-round.md`。这些会提高后续维护成本。

## 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 / 25 |
| SQL 治理与数据正确性 | 16 / 20 |
| 可运行性与可靠性 | 20 / 20 |
| 测试与验证证据 | 15 / 15 |
| 代码质量与可维护性 | 7.5 / 10 |
| **技术总分** | **83.5 / 90** |

本报告不计算质量分、平均分或 100 分制总分，不给视觉分。

## 产品文档建议分 — 3 / 5

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | ---: | --- |
| 治理、索引与阅读入口 | 1 | 0.5 | `docs/index.md` 与根 `AGENTS.md` 给出阅读顺序；人入口 `README.md` 仍声称应用尚未建立，与仓库事实冲突。 |
| 设计完整性与可追溯性 | 2 | 2 | `docs/design/system-design.md` 覆盖模块、状态机、双库、策略、API、seed、Compose 与测试接缝；`CONTEXT.md` 固定术语；决策写了理由。 |
| 计划、运行/测试说明与实现一致性 | 2 | 0.5 | `docs/status/project_status.md` 与 `make up` / `make test` 一致；`docs/plan/first-round.md` 存在，但 `plan/README.md`、`design/README.md` 仍写「暂无」。 |

建议分 **3 / 5**。最终文档分由人工裁定。

## P0 / P1 / P2 风险标记

| 标记 | 是否命中 | 判断 |
| --- | --- | --- |
| P0 安全失败 | **是** | 用户 SQL 可通过 CTE 同名遮蔽执行 `SELECT ... FROM pg_catalog.pg_class` / `information_schema.tables` / `pg_catalog.pg_tables`，并可通过 `query_to_xml('SELECT ... FROM pg_class|pg_roles|pg_database')` 读出系统关系、角色和库名。这满足「访问系统或未授权对象」以及「绕过 AST 治理」。未证明用户 SQL 能写入业务表或经平台身份执行。 |
| P1 基座失败 | 否 | `make up` 可启动；`/health`、`/ready`、迁移与 seed 成立。 |
| P2 核心闭环缺失 | 否 | API 与浏览器均同时证明一条允许查询和一条拒绝查询；工作台在 `localhost` 源可用。 |

**风险标记：P0。**

## 按严重度排序的问题清单

1. **P0 / 对象范围绕过。** `policy.py` 对 `exp.Table` 只比较未限定表名，并在名称属于任一 CTE 别名时跳过检查。`WITH pg_class AS (...) SELECT relname FROM pg_catalog.pg_class` 因此放行，实际读出系统目录行。`information_schema.tables`、`pg_catalog.pg_tables` 可用同一手法。

2. **P0 / 函数未纳入对象范围。** 策略不检查函数。`query_to_xml` 以字符串执行任意只读 SQL，返回 `pg_class`、`pg_roles`、`pg_database` 等内容。`to_regclass` / `CAST(... AS regclass)` 解析系统对象名。`pg_sleep` 可被策略放行（超时由执行器兜底）。

3. **中 / 第二道 CONNECT 边界不完整。** `platform` 与 `analytics` 的 `datacl` 为空，默认 `PUBLIC` 可连接。`analytics_reader` 能连上 `platform`，`platform_writer` 能连上 `analytics`。表级授权目前挡住读写，但与设计「运行时身份不得跨库连接」不符。

4. **中 / CORS 源过窄。** `CORS_ORIGIN=http://localhost:5173` 时，用 `http://127.0.0.1:5173` 打开工作台会 `Failed to fetch`。产品 e2e 走 `localhost`，故测试仍绿。

5. **低 / 错误摘要泄漏内部细节。** `EXEC_DB_ERROR` 的 `message` 含 `psycopg.errors...`、`[SQL: ...]` 与 SQLAlchemy 链接。

6. **低 / 文档入口过期。** `README.md` 写应用尚未建立；`docs/design/README.md`、`docs/plan/README.md` 写目录为空。

7. **低 / 维护负担。** Python 依赖未钉版本；Web 无 lockfile，镜像内 `npm install`。

8. **观察。** 分析只读身份在数据库层仍能 `SELECT` `pg_catalog.pg_class`（430 行）。这是 PostgreSQL 默认目录可读性；本候选的问题是应用层策略未能挡住到达执行器的目录查询。

## Compose 资源停止情况

本次评审启动了：

- `decisionharbor`（候选 `.env`，端口 5173 / 8010）
- `dhds-review2`（仅用于并行隔离，端口 55174 / 58110）

结束时执行：

```bash
COMPOSE_PROJECT_NAME=dhds-review2 docker compose down --volumes --remove-orphans
docker compose down --remove-orphans
```

结果：两个项目的容器和默认网络已移除；rev2 数据卷 `dhds-review2_pgdata` 已删除（本审查者创建）；候选命名卷 `decisionharbor_pgdata` 保留。未停止 ExamForge 项目，也未删除宿主机上既有的其他 `decisionharbor*` 卷。结束后 `docker compose ls` 中不再出现本次评审项目。

## 最终 Git 状态

工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high`

```text
HEAD  4306278abbfb4a65d6d52a6e701c1e308fe2ed46
## v0.1.0/dshpreview-deepseek-v4-pro-high
git status --short --branch  无未提交改动
git diff --check  退出码 0
git status --porcelain=v1 -uall  空
```

候选工作树在评审全程保持干净，无需清理。

## 未验证项汇总

- AgentShip 工作区没有可执行的非公开 harness，未跑官方隐藏用例套件。
- 无浏览器 MCP，未做人工点击；主链以独立 Playwright 对 `localhost` 复现。
- 未在手工污染分析表后再验证 seed 回夹具。
- 未在主实例既有卷上从空白 init 再走一遍（并行新卷已成功初始化）。
