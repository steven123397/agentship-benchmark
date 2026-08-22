# Codex GPT-5.6 Luna Max 首轮 Grok 独立评审

## 独立性声明

- 审查者：Grok Build，按 `review-prompts.md` 索引表第 17 行执行。
- 唯一写入文件：本文件 `runs/codex-gpt-5.6-luna-max/grok-review.md`。
- 未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未读取其他候选的 worktree、分支、运行记录或评审材料。
- 未修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 未执行 `git add`、`git commit`、`git push` 或创建 PR。
- 评分只依据本次对冻结 commit `1dfb4a4d4d441350b6035ea36eacf414cb9e4023` 的代码审查与新鲜运行证据；不采用 Agent 自述、协调方未复现记录、模型名称、耗时或既往印象。
- AgentShip 工作区未找到可执行的非公开 harness 副本，因此没有运行官方隐藏用例套件。下列结论来自公开契约、产品代码和本审查者的新鲜探针。

## 评审身份、环境与实际执行命令

### 冻结身份

| 项 | 值 |
| --- | --- |
| 候选 | Codex CLI / `gpt-5.6-luna-max` |
| 工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-luna-max` |
| 分支 | `v0.1.0/codex-gpt-5.6-luna-max` |
| `RESULT_COMMIT` / `HEAD` | `1dfb4a4d4d441350b6035ea36eacf414cb9e4023` |
| `completion.coordinatorFrozen` | `true` |
| 开始时 `git status --short --branch` | `## v0.1.0/codex-gpt-5.6-luna-max...origin/v0.1.0/codex-gpt-5.6-luna-max`，无未提交改动 |
| 开始时 `git diff --check` | 无输出 |

### 评审环境

- 宿主机：WSL2 Linux `6.18.33.2-microsoft-standard-WSL2`，x86_64。
- Docker `29.1.3`，Compose v2。
- 宿主机 Node.js `v24.16.0`，Python `3.10.12`。
- API 测试在候选镜像的 Python 3.13 容器内执行。
- 本机已有 Playwright Chromium 缓存；浏览器主链用产品 Playwright，不用浏览器 MCP 人工点击。
- 评审期间宿主机上另有 ExamForge 容器在跑；本次只创建并停止 `dh-grok-review-luna` 与 `dh-grok-review-luna-b`，未停止无关项目。

### 实际执行命令

主实例（只读复现，不写 `.env`，不改工作树）：

```bash
cd /home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-luna-max
git rev-parse HEAD
git status --short --branch
git diff --check

COMPOSE_PROJECT_NAME=dh-grok-review-luna \
WEB_HOST_PORT=25173 API_HOST_PORT=28080 \
POSTGRES_SUPERUSER_PASSWORD=postgres \
DB_MIGRATOR_PASSWORD=db_migrator \
PLATFORM_WRITER_PASSWORD=platform_writer \
ANALYTICS_READER_PASSWORD=analytics_reader \
PLATFORM_READINESS_PASSWORD=platform_readiness \
ANALYTICS_READINESS_PASSWORD=analytics_readiness \
docker compose up -d --build

docker compose ps -a
docker compose logs migrate
curl -sS http://127.0.0.1:28080/health
curl -sS http://127.0.0.1:28080/ready
curl -sS http://127.0.0.1:25173/health
curl -sS http://127.0.0.1:25173/ready
curl -sS http://127.0.0.1:25173/

# 允许/拒绝/超时/行数/API 边界：对本机 28080 发 POST/GET
# 重复迁移：
docker compose run --rm --no-deps migrate

# 双库与权限：
docker compose exec -T postgres psql ...
docker compose exec -T -e PGPASSWORD=analytics_reader postgres psql -U analytics_reader -d platform ...
docker compose exec -T -e PGPASSWORD=platform_writer postgres psql -U platform_writer -d analytics ...

# 重启与 /ready 失败：
docker compose restart api
docker compose stop postgres
curl /health /ready
docker compose start postgres

python3 datasets/sales-analytics-v1/validate.py
COMPOSE_PROJECT_NAME=dh-grok-review-luna docker compose run --rm --no-deps api pytest
(cd apps/web && npm test)
WEB_BASE_URL=http://127.0.0.1:25173 npx playwright test --reporter=list
```

并行实例：

```bash
COMPOSE_PROJECT_NAME=dh-grok-review-luna-b \
WEB_HOST_PORT=25273 API_HOST_PORT=28081 \
... docker compose up -d --build
```

结束时：

```bash
COMPOSE_PROJECT_NAME=dh-grok-review-luna-b docker compose down --volumes --remove-orphans
COMPOSE_PROJECT_NAME=dh-grok-review-luna docker compose down --volumes --remove-orphans
git rev-parse HEAD
git status --short --branch
git diff --check
```

未把 `./dev test` 作为单条命令整包重跑；其组成步骤（`validate.py`、容器内 pytest、Vitest、Playwright）已分别取得新鲜证据。

## 技术评分

评分规则：每个子项三档。未通过 `0`，部分通过为该子项 `50%`，完全通过为满分。没有新鲜证据的项目标为未验证，不按通过计分。

### 1. 功能与外部契约 22.5 / 25

#### 查询运行 API 生命周期 8 / 8

**证据**

- `POST /api/v1/query-runs` 对允许 SQL 返回 `200`，含 `id`、`raw_sql`、`state=succeeded`、`outcome`、`created_at`、`policy`、`result.columns/rows/row_count/duration_ms`。
- 同一 `id` 的 `GET /api/v1/query-runs/{id}` 返回 `200`、相同终态与审计字段，且 `result` 为 `null`，与设计「结果行不入库」一致。
- 拒绝与失败路径同样先建记录再返回稳定 `id`；`GET` 能读回 `state`、`error.code`、`error.message`。
- 合法但未知 UUID：`GET /api/v1/query-runs/00000000-0000-0000-0000-000000000099` → `404 query_run_not_found`。

**未验证**

- 未观察到真实的短暂 `received`/`executing` HTTP 响应（实现是请求内同步执行；`executing` 只在审计事件中出现）。

#### 允许查询结果正确性 7 / 7

**证据**

| 查询 | 结果 |
| --- | --- |
| `COUNT(*)` on `analytics.customers` | `100` |
| 按 `region` 聚合客户数 | 5 行，Central/East/North/South/West 各 `20` |
| 订单状态分布 | confirmed `720`，pending `100`，cancelled `100`，refunded `80` |
| 已确认订单销售额 / 成本 / 毛利 / 明细行 | `11058789.642500` / `7977580.36` / `3081209.282500` / `2139`；与库内同一口径直查一致 |
| `WITH ... SELECT` 连接聚合 | `order_lines=2139` |
| `DATE_TRUNC('month', ordered_at)` | `succeeded`，返回 timestamptz |

金额以定数字符串返回，`bigint` 计数以字符串返回，耗时字段存在。

#### 拒绝与执行失败语义 2.5 / 5

**通过的新鲜证据**

- 策略拒绝均为 HTTP `200` + `state=rejected` + 稳定码 + 可读说明 + 记录 ID，不伪装成功：`object_not_allowed`、`non_read_query`、`multiple_statements`、`write_cte`、`select_into`、`function_not_allowed`、`sql_parse_error`、`sql_empty`、`sql_too_large`、`result_limit_exceeded`（字面量 `LIMIT 10001`）。
- 执行失败：超时查询 → `failed/query_timeout`；超大结果交叉连接 → `failed/result_limit_exceeded`；均保留 `policy.decision=allowed`。
- 非法 JSON：`{"sql":7}`、缺少 `sql` → `400 invalid_request`。
- 带 `Content-Length` 的超大请求体 → `413 request_too_large`。

**缺陷（故本子项部分通过）**

1. 非 UUID 的 `GET /api/v1/query-runs/does-not-exist` 触发平台 SQL 错误，被映射为 `503 service_not_ready` / `Query audit storage is unavailable`，而不是 `404 query_run_not_found`。合法未知 UUID 才是 404。这会把客户端输入错误报成服务不可用。
2. `Transfer-Encoding: chunked` 且不带 `Content-Length` 时，中间件不读正文，200 KiB 请求进入应用层。最终因 `sql_too_large` 拒绝，没有变成成功，但绕过了文档承诺的 128 KiB HTTP 上限。

#### 最小查询工作台 5 / 5

**证据**

- Web `http://127.0.0.1:25173/` 返回工作台 HTML，标题为 `DecisionHarbor / Query Console`。
- 产品 Playwright（`WEB_BASE_URL=http://127.0.0.1:25173`）2 passed：默认 SQL 提交后可见 `SUCCEEDED` 与结果表；`SELECT * FROM platform.query_runs` 可见 `object_not_allowed`。
- 独立 Playwright 脚本再次确认结果表、`Central` 区域行、拒绝文案 `Query references an unauthorized object`；提交期间按钮文案变为 `Executing query`。

**未验证**

- 未在浏览器中单独提交一条会 `failed` 的超时查询以目视失败面板（失败 UI 代码存在，API 失败语义已验证）。
- 产品 e2e 未断言「EXECUTING」标签；独立脚本因请求过快也未稳定捕获该标签，只捕获到执行中按钮文案。

### 2. SQL 治理与数据正确性 20 / 20

#### AST 只读语义与单语句约束 6 / 6

**证据**

- `evaluate_sql` 使用 SQLGlot `parse(..., read="postgres")`，按 AST 节点而不是字符串黑名单判定。
- 现场拒绝：多语句、`UPDATE`/`INSERT`/`CREATE`/`COPY`/`CALL`/`DO`/`SET`/`EXPLAIN`、写 CTE、`SELECT INTO`。
- 注释后的第二条语句（`SELECT ...; -- DROP TABLE ...`）被判 `multiple_statements`。
- `SELECT 1`、CTE、`UNION`、窗口函数、安全 `CAST` 被允许。

#### 授权对象与 schema 范围 4 / 4

**证据**

- 白名单仅五张 `analytics` 业务表。
- API 拒绝：`platform.query_runs`、`pg_catalog.pg_class`、`information_schema.tables`、`other.customers`、`generate_series`。
- 未限定表名按 `analytics` 规范化后比对。

直连 `analytics_reader` 仍能读 `pg_catalog`（数据库默认），但用户 SQL 不能经 API 到达该路径。这是第二道权限边界的已知范围，不构成 API 治理失败。

#### 数据库身份与双库隔离 4 / 4

**证据**

- 单容器两个逻辑库 `platform`、`analytics`；角色 `db_migrator` / `platform_writer` / `analytics_reader` / `platform_readiness` / `analytics_readiness` 均非超级用户。
- `analytics_reader` 连接 `platform`：`FATAL: permission denied ... CONNECT privilege`。
- `platform_writer` 连接 `analytics`：同样无 `CONNECT`。
- `analytics_reader` 对 `analytics.customers` 插入：`permission denied for table customers`。
- 就绪身份不能读业务/审计表。
- API 运行时 URL 分别为 `platform_writer@platform` 与 `analytics_reader@analytics`；审计事件只写在 `platform`。
- 成功路径事件为 `received -> executing -> succeeded`，拒绝路径为 `received -> rejected`，失败路径为 `received -> executing -> failed`。

#### 执行资源限制 3 / 3

**证据**

- 语句超时：三表交叉计数在约 5 秒后 `failed/query_timeout`。
- 行数上限：`order_items × customers × product_categories` 在 718 ms 内 `failed/result_limit_exceeded`，不返回部分结果。
- 字面量 `LIMIT 10001` 在策略层拒绝。
- SQL 原文超过 64 KiB：`rejected/sql_too_large`。
- 带 `Content-Length` 的超大 HTTP 体：`413`。

**未验证**

- 未构造刚好压过 128 列或 4 MiB JSON 的现场溢出。
- 未现场触发 `lock_timeout` 与 `executor_busy`。
- chunked 请求可绕过 HTTP 413，见上一节；SQL 64 KiB 上限仍生效。

#### 固定数据契约与业务口径 3 / 3

**证据**

- 行数：customers 100、product_categories 8、products 50、orders 1000、order_items 3000。
- 订单状态与契约一致；`ordered_at` 为 2024-01-01 至 2025-12-31；货币仅 `CNY`。
- 已确认订单销售额/成本/毛利与契约公式及库内直查一致。
- 分析迁移使用 `numeric`、状态/折扣/外键检查，未把订单总额做成冗余列。
- `python3 datasets/sales-analytics-v1/validate.py` 通过。

### 3. 可运行性与可靠性 20 / 20

#### 干净环境启动与就绪 6 / 6

**证据**

- 独立项目名 `dh-grok-review-luna` 一次 `docker compose up -d --build` 构建并拉起 postgres / migrate / api / web。
- migrate 退出码 0，日志 `analytics seed: loaded`。
- postgres、api、web 均为 healthy；API 与 Web 代理的 `/health`、`/ready` 均为 HTTP 200。
- 首次构建因 pip 下载较慢（约 15 分钟），属评测环境带宽，不是启动契约失败。

#### 迁移与固定数据初始化 6 / 6

**证据**

- 首次 seed：`loaded`；立即再跑 migrate：`already_loaded`，行数不变。
- 两库、四类运行身份、两套 Alembic head（`platform_0001` / `analytics_0001`）均已建立。

**未验证**

- 未手工制造部分/冲突 fixture 后再跑 seed，以观察 `seed_conflict` 停机（代码路径存在，集成测试未覆盖）。

#### 并行实例隔离 5 / 5

**证据**

- 无 `container_name`；网络 `dh-grok-review-luna_default`，卷 `dh-grok-review-luna_postgres-data`。
- 第二实例 `dh-grok-review-luna-b` 使用 `25273` / `28081`，同时 healthy。
- 两边各自 `POST` 允许查询均 `succeeded` 且 `COUNT=100`，run id 不同。
- 审计行数：主实例 42，并行实例 2。证明平台库未共享。
- 数据库不暴露固定宿主端口。

#### 重启与故障可见性 3 / 3

**证据**

- `docker compose restart api` 后 `/ready` 恢复 200。
- `docker compose stop postgres` 后 `/health` 仍 200，`/ready` 为 `503 service_not_ready`。
- 重新 `start postgres` 后 `/ready` 恢复 200，允许查询再次返回 100。

### 4. 测试与验证证据 9 / 15

#### 统一测试入口与可靠断言 3 / 3

**证据**

- `./dev test` 串行执行数据集校验、Compose 拉起、容器内 `pytest`、`npm test`、`npm run test:browser`；失败会非零退出。
- 本次分别复跑：`validate.py` 通过；容器内 pytest `25 passed`；Vitest `2 passed`；Playwright `2 passed`。

**未验证**

- 未把 `./dev test` 作为单条命令从空栈再跑一遍（组成步骤已有新鲜证据）。

#### SQL 策略单元测试 2.5 / 5

**证据**

- `apps/api/tests/test_policy.py` 覆盖允许 CTE/连接/聚合、未限定名、`UNION`、窗口、`CAST`，以及空 SQL、多语句、`UPDATE`、写 CTE、`platform`、`pg_catalog`、`pg_sleep`、`regclass`、`SELECT INTO`、过大 `LIMIT`、其他 schema。
- 测试失败会非零退出（本次 25 项中策略用例均过）。

**缺口**

- 设计声称覆盖全部背景列出的写操作与边界语法；仓库单测没有独立的 `INSERT`/`DELETE`/`MERGE`/`CREATE`/`ALTER`/`DROP`/`TRUNCATE`/`COPY`/`CALL`/`DO`/`SET`/`EXPLAIN`、注释/大小写/引号用例。这些路径本次用现场 API 补证，但不属于产品测试资产。

#### 双数据库集成测试 2 / 4

**证据**

- `test_integration.py` 在真实 Compose 库上断言五行数、reader 不能写、跨库无 `CONNECT`、就绪身份权限。

**缺口**

- 没有经 `QueryRunService.submit` 或 HTTP 的真实查询执行。
- 没有 seed 幂等 / 冲突、`/ready` 真库、执行身份 `current_user`、超时或审计事件顺序的集成断言。
- 缺环境变量时该文件 `skip`，而不是失败；本次因容器内已注入 URL 才真正跑到。

#### 浏览器主链测试 1.5 / 3

**证据**

- `apps/web/tests/query-workbench.spec.ts` 覆盖提交允许 SQL、成功表、对象越权拒绝。
- 本次对评审栈复跑 2 passed。

**缺口**

- 产品 e2e 不断言执行中状态。
- 产品 e2e 不覆盖失败（timeout / result limit）展示。
- Vitest 只 mock 成功与拒绝，不覆盖失败或执行中。

### 5. 代码质量与可维护性 8.5 / 10

#### 模块边界与职责分离 3 / 3

策略、执行器、审计、Query Run Service、HTTP、seed/bootstrap、就绪检查边界清楚。Service 可注入 `AuditStore` / `AnalyticsExecutor` / policy，测试接缝可用。用户 SQL 只走 `analytics_reader` 连接。

#### 配置、错误处理与资源清理 1.5 / 3

**成立**

- 资源限制与连接串来自服务端 `Settings`，用户 SQL 不能改超时。
- 对调用方隐藏驱动堆栈；意外执行异常固定为 `analytics_execution_error`。
- 审计状态机用 `FOR UPDATE` 与期望状态转移。

**问题**

- `app.state.owned_resources` 收集了 `dispose()`，但没有 lifespan / shutdown 调用。
- 非法 run id 的 SQL 异常被统一折成 `503 service_not_ready`。
- HTTP 体限制只看 `Content-Length`。
- 设计 6.2 写的 `executing` 启动恢复 / `audit_recovery` 未实现；`status` 把它标成首轮边界，但设计正文仍像已采纳。

#### 类型、命名、重复控制与可测试性 2 / 2

领域对象与 Protocol 清楚，API / Service / Policy 测试分层合理。个人风格不扣分。

#### 依赖、变更范围与维护负担 2 / 2

依赖与约束栈一致（FastAPI、SQLAlchemy 2、SQLGlot、Alembic、psycopg 3、React 19、Vite、Playwright）。`pydantic-settings` 写在依赖里但 `Settings` 手读环境变量，维护负担很小，不单独降档。未看到范围扩张到 LLM / RBAC / 异步队列。

## 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 22.5 / 25 |
| SQL 治理与数据正确性 | 20 / 20 |
| 可运行性与可靠性 | 20 / 20 |
| 测试与验证证据 | 9 / 15 |
| 代码质量与可维护性 | 8.5 / 10 |
| **技术总分** | **80 / 90** |

本报告不计算最终 100 分，也不给视觉分。

## 产品文档建议分 4 / 5

只评价产品内生文档，供人工裁定参考。

| 子项 | 建议 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1 / 1 | 根 `AGENTS.md`、`docs/AGENTS.md`、`docs/index.md` 给出阅读顺序与目录职责；`README.md` 指向文档入口。 |
| 设计完整性与可追溯性 | 1.5 / 2 | `docs/design/first-round-governed-query-design.md` 覆盖状态机、双库身份、AST、API、seed、Compose、测试接缝，并回链背景与契约。扣分点：设计 6.2 的启动恢复、设计 11.2 的冲突 seed 测试、设计 5.3 的 `DATE_TRUNC` 名称与实现 allowlist `TIMESTAMP_TRUNC` 不完全同文（运行时因 SQLGlot 映射仍通过）。 |
| 计划、运行/测试说明与实现一致性 | 1.5 / 2 | `README.md` 与 `./dev` 的 `up`/`down`/`destroy`/`test` 一致，可并行配置有说明。`docs/plan` 与 `docs/status` 大体反映实现。扣分点：状态/设计仍写 Playwright 覆盖执行中，产品 e2e 未断言；集成测试实际范围小于设计宣称。 |

**文档建议分：4 / 5。**

## 风险标记

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | **不触发** | 用户 SQL 不能写入分析表；API 拒绝系统目录、`platform`、未授权对象、DML/DDL/写 CTE；执行身份是 `analytics_reader`，该身份无 `platform` `CONNECT`、无分析表写权限。未发现绕过 AST 后仍能写数据或读平台库的路径。chunked 413 绕过仍停在 `sql_too_large`，不是治理绕过。 |
| P1 基座失败 | **不触发** | 独立 Compose 启动成功；`/health`、`/ready`、迁移、固定 seed 均成立；重复 seed 为 `already_loaded`。 |
| P2 核心闭环缺失 | **不触发** | API 与浏览器均同时证明一条允许查询和一条拒绝查询；工作台可输入、提交、展示成功表与拒绝码。 |

## 按严重度排序的问题清单

1. **GET 非 UUID run id 报成服务不可用。** `GET /api/v1/query-runs/does-not-exist` → `503 service_not_ready`。合法未知 UUID 才是 `404`。根因是 `platform.query_runs.id` 为 UUID，非法文本使审计查询抛 `SQLAlchemyError`，再被收成 `AuditPersistenceError`。
2. **HTTP 128 KiB 上限可被 chunked 请求绕过。** 中间件只检查 `Content-Length`。200 KiB chunked 正文进入应用层；本次被 `sql_too_large` 兜住，但仍违反设计的传输层拒绝。
3. **集成测试没有证明「实际查询执行」。** `test_integration.py` 只查权限与行数，不调用 `submit()` / HTTP，也不覆盖 seed 冲突或审计事件。
4. **策略单测窄于设计和背景清单。** 缺少多类 DML/DDL 与边界语法的产品测试；这些路径靠本次现场探针，而不是仓库回归网。
5. **浏览器主链不断言执行中，也不覆盖失败展示。** 工作台代码有执行中按钮与失败面板，但产品 e2e 只有成功表 + 对象拒绝。
6. **连接资源没有关闭钩子。** `dispose()` 存在但从不在应用生命周期中调用。
7. **设计与实现有几处不同文。** 启动恢复 / `audit_recovery`、冲突 seed 测试、`DATE_TRUNC` 函数名。运行时 `DATE_TRUNC` 因 SQLGlot 映射到 `TIMESTAMP_TRUNC` 仍被允许。

## Compose 资源停止情况

本次评审启动并随后销毁：

- `dh-grok-review-luna`：容器、默认网络、数据卷 `dh-grok-review-luna_postgres-data`。
- `dh-grok-review-luna-b`：容器、默认网络、数据卷 `dh-grok-review-luna-b_postgres-data`。

结束时 `docker ps/volume/network --filter name=dh-grok-review-luna` 无残留。ExamForge 等无关项目保持原状，未停止。

## 最终 Git 状态

候选工作树结束时：

```text
1dfb4a4d4d441350b6035ea36eacf414cb9e4023
## v0.1.0/codex-gpt-5.6-luna-max...origin/v0.1.0/codex-gpt-5.6-luna-max
```

`git status --porcelain` 为空，`git diff --check` 无输出。评审未改候选文件。

## 未验证项汇总

- 官方非公开 harness 套件（工作区无副本）。
- `./dev test` 单条整包命令。
- 手工制造部分/冲突 fixture 后的 `seed_conflict`。
- 结果 128 列 / 4 MiB JSON、锁等待、执行槽耗尽的现场溢出。
- 浏览器失败面板与稳定的 `EXECUTING` 标签截图。
- 浏览器 MCP 人工点击。
