# DecisionHarbor v0.1.0 Grok 首轮独立评审

- 审查者：Grok Build
- 候选：Grok Build / grok-4.6-high
- 产品工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high`
- 候选分支：`v0.1.0/grokbuild-grok-4.6-high`
- `RESULT_COMMIT`：`cd8b766fa6242cf1bdb30304af6f453af6331af7`
- baseline commit：`1fb48f499d67677a47fb9b60e1f99346b46e0aee`（该提交是 `HEAD` 祖先）
- 评审日期：2026-08-13

## 独立性声明

本报告只依据本次对冻结 commit 的代码阅读，以及本审查者在该工作树内新执行的命令、HTTP 探针、数据库探针、统一测试入口和独立 Playwright 复现。不读取、不引用、不比较其他候选的工作树、分支、运行记录或评审材料；不读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。不引用开发自述或给予自我信用。不因 Agent、模型、耗时或 token 调整分数。未修改候选源码、分支、baseline 或评分规范；唯一写入的文件是本报告。

冻结前置条件已满足：`metadata.json` 中 `completion.coordinatorFrozen` 为 `true`，`candidate.resultCommit` 为完整 SHA `cd8b766fa6242cf1bdb30304af6f453af6331af7`。开始前 `git rev-parse HEAD` 等于该 SHA，`git status --short --branch` 无未提交改动。

## 评审 commit、环境与实际执行命令

### 工作树状态（开始）

```text
HEAD  cd8b766fa6242cf1bdb30304af6f453af6331af7
branch  v0.1.0/grokbuild-grok-4.6-high...origin/v0.1.0/grokbuild-grok-4.6-high
git status --short --branch  无未提交改动
git diff --check  退出码 0
```

已提交文档 `docs/design/governed-query-path.md` 经 `git show --check` 报告 9 处行尾空格。这是冻结交付本身的问题，不是评审后的工作树改动。

### 环境

| 项 | 值 |
| --- | --- |
| 宿主机 | Linux MAGICBOOK14，WSL2，`6.18.33.2-microsoft-standard-WSL2` |
| Docker | 29.1.3 |
| Docker Compose | 2.40.3 |
| Node.js | v24.16.0 |
| 宿主机 Python | 3.10.12（数据集校验）；API 镜像为 `python:3.13-slim` |
| 候选 `.env` | `COMPOSE_PROJECT_NAME=dh-grok-46-high`，`WEB_HOST_PORT=55173`，`API_HOST_PORT=58000` |
| 评审并行实例 | `COMPOSE_PROJECT_NAME=dh-grok-46-high-rev2`，Web `55174`，API `58001` |

评审开始时宿主机另有 `examforge`、`examforge-v5p3-e2e`、`examforge-v5p4-preview` 在运行。全程未停止这些无关项目。

### 实际执行的命令

1. `git rev-parse HEAD`、`git status --short --branch`、`git log -1`、`git diff --check`、`git merge-base --is-ancestor 1fb48f499d67677a47fb9b60e1f99346b46e0aee HEAD`
2. `python3 datasets/sales-analytics-v1/validate.py`
3. `./scripts/up.sh`
4. `curl`：`/health`、`/ready`、Web 根路径；同源反代下的 Web `/health`、`/ready`
5. Python HTTP 探针：允许查询、拒绝查询、绕过/对象范围、行数上限、超长 SQL、非法请求体、生命周期 `GET`
6. `docker compose --env-file .env exec`：双库、三身份、`CONNECT` 拒绝、只读写入拒绝、五表行数、订单状态计数、表权限
7. 独立 CSV 重算已实现销售额，并与 API 聚合结果对照
8. `docker compose --env-file .env restart api`；停止再启动 `postgres`，观察 `/health`、`/ready` 与 `POST /api/v1/query-runs`
9. `./scripts/test.sh`
10. 并行启动第二 Compose 项目并对其发允许查询
11. 在 `/tmp/dh46-review-e2e` 对实时 Web `http://127.0.0.1:55173` 跑独立 Playwright 主链（未写入候选工作树）
12. `git show --check`
13. 结束：停止本次评审启动的两个 Compose 项目，再次检查 Git

AgentShip 工作区未找到可执行的非公开 harness 副本，因此没有运行官方隐藏用例套件。下列结论全部来自公开契约、产品代码和本审查者的新鲜探针。

## 技术评分

子项按规范三档计分：未通过 `0`，部分通过为该子项 `50%`，完全通过为满分。技术总分可保留 `0.5` 分。

### 1. 功能与外部契约 — 25 / 25

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**查询运行 API 生命周期。** `POST /api/v1/query-runs` 对合法 `{ "sql": string }` 一律建档并返回终态。成功记录 `c1b90a30-b988-4146-808a-7604a9b9b93f` 的 `GET` 返回同一 `id`、`status=succeeded`、原始 SQL、`row_count=1`、`duration_ms`、`created_at`，且 `result` 为 `null`。非法体 `{"statement":"SELECT 1"}` 返回 `400` / `REQUEST_INVALID`；非 UUID 与不存在 UUID 均返回 `404` / `QUERY_RUN_NOT_FOUND`。拒绝与失败同样带记录标识。

**允许查询结果正确性。** `SELECT id, region FROM customers ORDER BY id LIMIT 2` 返回 `[[1, "West"], [2, "East"]]`，与权威 CSV 前两行一致。`GROUP BY region` 得到 5 个区域。CTE、连接、窗口、集合运算均可执行。已实现销售额

```sql
SELECT SUM(i.quantity * i.unit_price * (1 - i.discount_rate))
FROM order_items i
JOIN orders o ON o.id = i.order_id
WHERE o.status = 'confirmed'
```

返回字符串 `"11058789.642500"`。审查者用同一 CSV 独立重算，得到 `sales_amount=11058789.642500`、`cost_amount=7977580.36`、`gross_margin=3081209.282500`，与 API 一致。`list_price` 以字符串返回，符合定点数量序列化。

**拒绝与执行失败语义。** `DELETE FROM orders` → `rejected` / `POLICY_DENIED`；多语句 → `rejected` / `QUERY_INVALID`；无 `LIMIT` 的 `order_items` → `failed` / `RESULT_LIMIT_EXCEEDED` 且不返回截断行集；笛卡尔积 → `failed` / `EXECUTION_TIMEOUT`（约 5007 ms）；超长 SQL → `rejected` / `QUERY_TOO_LARGE`。拒绝与失败均带稳定错误码、可读说明和记录 `id`，HTTP 为 200 领域终态。

**最小查询工作台。** Web 根路径 200，标题为「DecisionHarbor 查询工作台」。`./scripts/test.sh` 中 Playwright 2 passed；审查者另用独立 Playwright 对 `http://127.0.0.1:55173` 复现：允许查询先见「执行中」再见表头 `id`/`region` 与单元格 `1`/`West`；`DELETE FROM orders` 见 `POLICY_DENIED`。Vitest 另覆盖 `failed` / `EXECUTION_TIMEOUT` 展示。

**未验证：** 无浏览器 MCP 人工点击；主链以独立 Playwright 代替。未运行非公开 harness 中可能存在的额外 API 边界用例。

### 2. SQL 治理与数据正确性 — 18 / 20

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| AST 只读语义与单语句约束 | 6 | 6 | 完全通过 |
| 授权对象与 schema 范围 | 4 | 2 | 部分通过 |
| 数据库身份与双库隔离 | 4 | 4 | 完全通过 |
| 执行资源限制 | 3 | 3 | 完全通过 |
| 固定数据契约与业务口径 | 3 | 3 | 完全通过 |

**AST 只读语义与单语句约束。** `api/app/policy.py` 使用 `sqlglot.parse(..., read="postgres")`，要求恰好一棵树，根节点为 `Select` / `Union` / `Intersect` / `Except`，再遍历 AST。实测拒绝多语句、`INSERT`/`UPDATE`/`DELETE`/`CREATE`、修改型 CTE、`SELECT INTO`、`COPY`、`EXPLAIN`、`FOR UPDATE`、空输入与纯注释。注释和字符串中的写关键字不误拒。策略基于 AST，不是字符串黑名单。

**授权对象与 schema 范围。** 直接引用 `pg_catalog.pg_class`、`information_schema.tables`、`public.customers`、`query_runs`、`pg_stat_activity`、CTE 同名遮蔽后的 `pg_catalog.pg_class`、`FROM CAST(... AS regclass)` 均 `POLICY_DENIED`。未加引号的契约表与 `analytics.products` 放行；`"Customers"` / `"CUSTOMERS"` 按 PostgreSQL 折叠规则拒绝。

扣分证据：类型转换被策略显式放行后，下列语句以 `succeeded` 返回系统对象名，而不是拒绝：

- `SELECT CAST('pg_catalog.pg_class' AS regclass)` → `[["pg_class"]]`
- `SELECT 'pg_catalog.pg_class'::regclass` → `[["pg_class"]]`
- `SELECT CAST('pg_catalog.pg_tables' AS regclass)` → `[["pg_tables"]]`
- `SELECT CAST('pg_roles' AS regclass)` → `[["pg_roles"]]`
- `SELECT CAST('information_schema.tables' AS regclass)` → `[["information_schema.tables"]]`

这不是读目录行，也不能经 `FROM CAST(...)` 取出 `pg_class` 元组，但已经让用户 SQL 解析并返回系统/未授权对象的 `regclass` 名。按「拒绝系统目录、未授权对象与绕过限定的引用」记为部分通过。`SELECT tableoid` / `ctid` 来自已授权表的系统列，不单独降档。

**数据库身份与双库隔离。** `postgres/init.sh` 创建 `platform` / `analytics` 与三身份，并 `REVOKE CONNECT ... FROM PUBLIC`。实测：

- `platform_app` 连 `analytics`：`FATAL: permission denied for database "analytics"`
- `analytics_owner` / `analytics_reader` 连 `platform`：同样 `CONNECT` 失败
- `analytics_reader` 的 `search_path=analytics`，`default_transaction_read_only=on`
- 只读身份 `INSERT`/`UPDATE`/`DELETE` 均为 `cannot execute ... in a read-only transaction`
- 五表权限为 `analytics_reader=r/...`
- API 使用三套独立 Engine；执行器只绑定 `analytics_reader`

**执行资源限制。** 无 `LIMIT` 的 `SELECT id FROM order_items` → `RESULT_LIMIT_EXCEEDED` / 「Query returned more than 1000 rows.」。`order_items a CROSS JOIN b CROSS JOIN c` → `EXECUTION_TIMEOUT`，墙钟约 5.02 s、`duration_ms=5007`。超过 20_000 字符 → `QUERY_TOO_LARGE`。递归 CTE 计数 5_000_000 在约 1.44 s 内完成，未否定超时，只说明该语句未触顶。

**固定数据契约与业务口径。** `validate.py` 成功。只读身份计数：`customers=100`、`product_categories=8`、`products=50`、`orders=1000`、`order_items=3000`。订单状态：`confirmed=720`、`pending=100`、`cancelled=100`、`refunded=80`。迁移金额列为 `numeric`，`order_items` 有 `(order_id, product_id)` 唯一约束，无订单总额冗余列。销售额口径见上节独立重算。

**未验证：** 未运行非公开 harness 的额外绕过集。未在手工改写分析表后再跑 seed 恢复（幂等由集成测试 `test_seed_is_idempotent` 与重启后行数证明）。

### 3. 可运行性与可靠性 — 18.5 / 20

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | 部分通过 |

**干净环境启动与就绪。** `./scripts/up.sh` 构建并启动 `postgres` / `api` / `web`。等待环中出现一次 `curl: (56) Recv failure: Connection reset by peer`，随后打印 `DecisionHarbor is ready on http://127.0.0.1:55173`。API `/health` → `200 {"status":"ok"}`；`/ready` → `200 {"status":"ready"}`。Web 根路径 200；Web 同源反代的 `/health`、`/ready` 同样 200。PostgreSQL 不发布宿主端口。

**迁移与固定数据初始化。** 启动后两库、三身份、Alembic 与 CSV seed 均成立。`test.sh` 内 `test_seed_is_idempotent` 通过。API 重启后分析表行数仍为 100 / 1000 / 3000，`platform.query_runs` 仍在（当时 120 行），符合「seed 不清空审计表」。

**并行实例隔离。** `compose.yaml` 无 `container_name`，无写死网络名或卷名。第二实例 `dh-grok-46-high-rev2`（55174 / 58001）与第一实例同时 `running(3)`。独立网络 `dh-grok-46-high_default` 与 `dh-grok-46-high-rev2_default`，独立卷 `*_postgres_data`。rev2 `/ready` 200，允许查询成功；rev1 `/ready` 与 Web 仍 200。

**重启与故障可见性。** `restart api` 后约 2 次探测即 `/ready`。停止 `postgres` 后：

| 探针 | 实际 |
| --- | --- |
| `GET /health` | `200 {"status":"ok"}`（进程仍在，符合存活语义） |
| `GET /ready` | `200 {"status":"ready"}` |
| `POST /api/v1/query-runs` | `HTTP 500`，体为 `Internal Server Error` |

`/ready` 实现是进程内粘性布尔：`bootstrap()` 成功后 `ready = True`，之后不再探测两库是否可连。这与设计「两库可连且迁移、seed 已完成」以及评分「依赖未就绪时 `/ready` 准确失败」不符。重新 `start postgres` 后堆栈可恢复。故本子项部分通过。

**未验证：** 未在从未执行过 init 的全新数据卷上从零演示第二次全新初始化（本候选卷 `dh-grok-46-high_postgres_data` 为既有卷；并行实例使用新卷并成功就绪，可部分替代）。

### 4. 测试与验证证据 — 15 / 15

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 3 | 完全通过 |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**统一测试入口。** `./scripts/test.sh` 退出码 0。本次输出：API `25 passed, 1 warning in 1.90s`；Vitest `3 passed`；Playwright `2 passed (3.0s)`。脚本 `set -euo pipefail`，失败会非零退出。

**SQL 策略单元测试。** `api/tests/test_policy.py` 覆盖允许的 `SELECT` / `WITH` / 连接 / 子查询 / 聚合 / 窗口 / 集合运算；拒绝多语句、写操作、DDL、`COPY`/`CALL`/`DO`、修改型 CTE、`SELECT INTO`、`EXPLAIN`/`SET`/`FOR UPDATE`、系统目录、未授权表、未允许函数；CTE 名不误判为物理表；注释或字符串中的写关键字不误拒。

**双数据库集成测试。** `api/tests/test_integration.py` 证明平台身份不能连 `analytics`、分析所有者与只读身份不能连 `platform`、只读身份不能写分析表、允许查询留下 `platform.query_runs` 审计、seed 重复后 `customers=100`。HTTP 单测覆盖 bootstrap 前 `/ready=503`。审查者的直连探针与之一致。

**浏览器主链测试。** 产品 Playwright 覆盖允许路径的「执行中 → 结果表」和拒绝路径的 `POLICY_DENIED`。审查者独立复跑 2 passed。Vitest 另覆盖 `failed` 展示。

**未验证：** 产品测试未用 `SELECT current_user` 钉死执行身份（代码路径与直连权限可证明）。未运行非公开 harness。

### 5. 代码质量与可维护性 — 8.5 / 10

| 子项 | 分值 | 得分 | 判定 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | 部分通过 |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**模块边界。** `web/`、`api/`、`postgres/` 三分。策略、执行器、查询运行服务、三套 Engine 职责清楚：策略不执行用户 SQL，执行器不写 `platform`，`GET` 不访问 `analytics`。工作台只走同源反代。

**配置、错误处理与资源清理。** 端口与项目名可配置；关闭时 `engines.dispose()`。扣分：`/ready` 不在请求时探测依赖；数据库不可用时 `POST` 变成无结构 HTTP 500，而不是设计留给基础设施故障的稳定 JSON。`create_query_run` 在未就绪时返回 `JSONResponse` 却标注 `QueryRunResponse`（`# type: ignore`）。这些会提高运行期误判和排障成本。

**类型、命名与可测试性。** API 有类型标注和 Pydantic 模型；策略可单测。SQLGlot 会把部分函数显示为内部名（例如 `generate_series` → `exploding_generate_series`），拒绝仍然成立，不构成缺陷。

**依赖与维护负担。** Python 依赖钉版本；`.env` 被忽略；数据集未被改写。`test.sh` 每个 profile 都会再 `up --build`，偏慢但可重复。已提交设计文档有行尾空格，不影响运行。

## 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 / 25 |
| SQL 治理与数据正确性 | 18 / 20 |
| 可运行性与可靠性 | 18.5 / 20 |
| 测试与验证证据 | 15 / 15 |
| 代码质量与可维护性 | 8.5 / 10 |
| **技术总分** | **85 / 90** |

本报告不计算质量分、平均分或 100 分制总分，不给视觉分。

## 产品文档建议分 — 4 / 5

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | ---: | --- |
| 治理、索引与阅读入口 | 1 | 1 | 根 `AGENTS.md`、`README.md`、`docs/index.md`、`docs/AGENTS.md` 与各目录 README 给出阅读顺序和职责，不复制正文。 |
| 设计完整性与可追溯性 | 2 | 2 | `docs/design/governed-query-path.md` 覆盖模块、状态、双库、策略、API、seed、Compose 与测试接缝；`CONTEXT.md` 固定术语；关键决策写了理由和被拒绝方案。 |
| 计划、运行/测试说明与实现一致性 | 2 | 1 | `README.md` / `scripts/up.sh` / `scripts/test.sh` 与计划一致，状态页与实现大体吻合。设计写明 `/ready` 仅在两库可连且迁移、seed 完成后成功，实现却是启动成功后的粘性标志，与正文不一致。`governed-query-path.md` 第 279–303 行有 9 处行尾空格。 |

建议分 **4 / 5**。最终文档分由人工裁定。

## P0 / P1 / P2 风险标记

| 标记 | 是否命中 | 判断 |
| --- | --- | --- |
| P0 安全失败 | 否 | 用户 SQL 不能写入分析表；平台身份不能连 `analytics`；写语句、修改型 CTE、直接系统表引用均被策略拒绝。`CAST(... AS regclass)` 只解析对象名，不能 `FROM` 出目录行，也不构成绕过 AST 后的数据访问或写入。 |
| P1 基座失败 | 否 | `./scripts/up.sh` 可启动；健康路径上 `/health`、`/ready`、迁移与 seed 成立。`/ready` 在依赖事后断开时仍报 ready，属于可靠性缺陷，不是「核心启动/就绪链路不成立」。 |
| P2 核心闭环缺失 | 否 | API 与浏览器均同时证明一条允许查询和一条拒绝查询；工作台可用。 |

**风险标记：无。**

## 按严重度排序的问题清单

1. **高 / 可靠性。** `/ready` 在 bootstrap 后不再探测数据库。停止 PostgreSQL 后仍返回 `200 {"status":"ready"}`，同时 `POST /api/v1/query-runs` 变为无结构 `HTTP 500 Internal Server Error`。代码：`api/app/main.py` 的模块级 `ready` 布尔。设计：`docs/design/governed-query-path.md`「两库可连且迁移、seed 已完成」。

2. **中 / 对象范围。** 允许的 `CAST` / `::` 可使 `pg_catalog.pg_class`、`pg_roles`、`information_schema.tables` 等以 `regclass` 名称返回。`FROM CAST(... AS regclass)` 已被拒绝，因此不能读目录行，但仍违反「拒绝系统目录与未授权对象引用」的字面范围。

3. **低 / 错误处理。** 基础设施故障未收敛到稳定 JSON 错误体；调用方只能看到框架默认 500 文本。

4. **低 / 文档一致性。** `/ready` 的设计语义与实现不符；`governed-query-path.md` 有 9 处已提交行尾空格。

5. **低 / 测试缝。** 集成测试未断言执行期 `current_user` 为 `analytics_reader`。三 Engine 与直连权限可补证，但测试未钉死。

6. **观察，不单独扣分。** 分析只读身份在数据库层仍能 `SELECT` `pg_catalog.pg_class`（437 行）。这是 PostgreSQL 默认目录可读性；应用层 AST 已拒绝同类语句。设计已要求策略不能因只读身份而省略对象检查。

## Compose 资源停止情况

本次评审启动了：

- `dh-grok-46-high`（候选 `.env` 项目，端口 55173 / 58000）
- `dh-grok-46-high-rev2`（仅用于并行隔离，端口 55174 / 58001）

结束时执行：

```bash
COMPOSE_PROJECT_NAME=dh-grok-46-high-rev2 docker compose down --remove-orphans -v
docker compose --env-file .env down --remove-orphans
```

结果：两个项目的容器和默认网络已移除；rev2 数据卷已删除（本审查者创建）；候选命名卷 `dh-grok-46-high_postgres_data` 保留。未停止 `examforge`、`examforge-v5p3-e2e`、`examforge-v5p4-preview`。结束后 `docker compose ls` 中不再出现 `dh-grok-46-high*`。

## 最终 Git 状态

工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high`

```text
HEAD  cd8b766fa6242cf1bdb30304af6f453af6331af7
## v0.1.0/grokbuild-grok-4.6-high...origin/v0.1.0/grokbuild-grok-4.6-high
git status --short --branch  无未提交改动
git diff --check  退出码 0
git status --porcelain=v1 -uall  空
```

候选工作树在评审全程保持干净，无需清理。

## 未验证项汇总

- AgentShip 工作区没有可执行的非公开 harness，未跑官方隐藏用例套件。
- 无浏览器 MCP，未做人工点击；主链以独立 Playwright 对实时 Web 复现。
- 未在手工污染分析表后再验证 seed 回夹具。
- 未在候选既有卷上从完全空白 init 再走一遍（并行新卷已成功初始化）。
