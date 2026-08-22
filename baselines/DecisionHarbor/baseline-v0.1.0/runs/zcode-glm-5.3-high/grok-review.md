# ZCode GLM-5.3 High 首轮 Grok 独立评审

## 独立性声明

- 审查者：Grok Build，按 `review-prompts.md` 索引表第 19 行执行。
- 唯一写入文件：本文件 `runs/zcode-glm-5.3-high/grok-review.md`。
- 未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未读取其他候选的 worktree、分支、运行记录或评审材料。
- 未修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 未执行 `git add`、`git commit`、`git push` 或创建 PR。
- 评分只依据本次对冻结 commit `a5811b218e42183f9b46aa2a2555194a658c7cf5` 的代码审查与新鲜运行证据；不采用候选状态文档自述、协调方未复现记录、模型名称、耗时或既往印象。
- AgentShip 工作区未找到可执行的非公开 harness 副本，因此没有运行官方隐藏用例套件。下列结论来自公开契约、产品代码和本审查者的新鲜探针。

## 评审身份、环境与实际执行命令

### 冻结身份

| 项 | 值 |
| --- | --- |
| 候选 | ZCode / `glm-5.3-high` |
| 工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.3-high` |
| 分支 | `v0.1.0/zcode-glm-5.3-high` |
| `RESULT_COMMIT` / `HEAD` | `a5811b218e42183f9b46aa2a2555194a658c7cf5` |
| `completion.coordinatorFrozen` | `true` |
| 开始时 `git status --short --branch` | `## v0.1.0/zcode-glm-5.3-high...origin/v0.1.0/zcode-glm-5.3-high`，无未提交改动 |
| 开始时 `git diff --check` | 无输出 |

`.env` 存在且与 `.env.example` 内容一致，已被 `.gitignore` 忽略，不构成未提交改动。

### 评审环境

- 宿主机：WSL2 Linux `6.18.33.2-microsoft-standard-WSL2`，x86_64。
- Docker `29.1.3`，Compose v2。
- 宿主机 Node.js `v24.16.0`，Python `3.10.12`。
- API 测试在候选镜像的 Python 3.13 容器内执行。
- 本机已有 Playwright Chromium 缓存；浏览器主链用产品 Playwright，不用浏览器 MCP 人工点击。
- 评审期间宿主机上另有 ExamForge 容器在跑；本次只创建并停止 `dh-grok-review-z53` 与 `dh-grok-review-z53b`，未停止无关项目。

### 实际执行命令

主实例（不改工作树，不覆盖 `.env`；用 `-p` 与端口环境变量与默认 `decision-harbor` 项目隔离）：

```bash
cd /home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.3-high
git rev-parse HEAD
git status --short --branch
git diff --check

WEB_PORT=25280 API_PORT=28281 \
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 up --build --wait

docker compose -f deploy/compose.yaml -p dh-grok-review-z53 ps -a
docker logs dh-grok-review-z53-api-1
curl -sS http://127.0.0.1:28281/health
curl -sS http://127.0.0.1:28281/ready
curl -sS http://127.0.0.1:25280/health
curl -sS http://127.0.0.1:25280/ready
curl -sS http://127.0.0.1:25280/

# 允许/拒绝/超时/截断/API 边界：对本机 28281 发 POST/GET
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 restart api
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 stop db
curl /health /ready
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 start db

python3 datasets/sales-analytics-v1/validate.py
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 exec -T api pytest tests/unit -q
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 exec -T api pytest tests/integration -q
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 exec -T web npm test -- --run   # 失败，见下文
(cd web && npx vitest run)
WEB_URL=http://127.0.0.1:25280 npx playwright test --reporter=list
```

并行实例：

```bash
WEB_PORT=25281 API_PORT=28282 \
docker compose -f deploy/compose.yaml -p dh-grok-review-z53b up --build --wait
```

结束时：

```bash
docker compose -f deploy/compose.yaml -p dh-grok-review-z53b down --volumes --remove-orphans
docker compose -f deploy/compose.yaml -p dh-grok-review-z53 down --volumes --remove-orphans
git rev-parse HEAD
git status --short --branch
git diff --check
```

未把 `make test` 作为单条命令整包重跑；其组成步骤已分别取得新鲜证据。`make web-test` 等价命令在运行中的 Web 容器上失败。

## 技术评分

评分规则：每个子项三档。未通过 `0`，部分通过为该子项 `50%`，完全通过为满分。没有新鲜证据的项目标为未验证，不按通过计分。

### 1. 功能与外部契约 22.5 / 25

#### 查询运行 API 生命周期 8 / 8

**证据**

- `POST /api/v1/query-runs` 对允许 SQL 返回 `200`，含 `outcome=succeeded`、`run.id`（自增整数）、`run.state`、`run.sql`、`row_count`、`duration_ms`、`created_at`/`finished_at`，以及 `result.columns/rows`。
- 同一 `id` 的 `GET /api/v1/query-runs/{id}` 返回 `200` 与相同终态审计字段，响应只有 `run`、没有 `result`，与设计「结果行不入库」一致。
- 拒绝与失败同样先建记录再返回稳定 `id`；`GET` 能读回 `state` 与拒绝/错误码。
- 未知整数 ID：`GET /api/v1/query-runs/999999` → `404`，`detail.code=QY_RUN_NOT_FOUND`。

**未验证**

- 未观察到真实的短暂 `running` HTTP 响应（实现是请求内同步执行；`running` 只作为落库中间态）。

#### 允许查询结果正确性 7 / 7

**证据**

| 查询 | 结果 |
| --- | --- |
| `COUNT(*)` on `analytics.customers` / 未限定 `customers` | `100` |
| 按 `region` 聚合客户数 | 5 行，Central/East/North/South/West 各 `20` |
| 订单状态分布 | confirmed `720`，pending `100`，cancelled `100`，refunded `80` |
| 已确认订单销售额 / 成本 / 毛利 / 明细行 | `11058789.642500` / `7977580.36` / `3081209.282500` / `2139` |
| `WITH ... SELECT` 连接聚合 | `order_lines=2139` |
| `DATE_TRUNC('month', ordered_at)` | `succeeded`，返回 timestamptz |

定点数以字符串返回；耗时字段存在。

#### 拒绝与执行失败语义 2.5 / 5

**通过的新鲜证据**

- 策略拒绝均为 HTTP `200` + `outcome=rejected` + 稳定码 + 可读中文说明 + 记录 ID：`QY_UNAUTHORIZED_OBJECT`、`QY_FORBIDDEN_STATEMENT`、`QY_MULTIPLE_STATEMENTS`、`QY_WRITE_CTE`、`QY_SELECT_INTO`、`QY_FORBIDDEN_FUNCTION`、`QY_INVALID_SYNTAX`。
- 执行失败：三表交叉计数 → `failed/QY_TIMEOUT`。
- 空 SQL / 仅空白：`rejected/QY_INVALID_SYNTAX`，并创建审计记录。

**缺陷（故本子项部分通过）**

1. 非法请求体未遵守设计的 `400 QY_INVALID_REQUEST`。`{"sql":7}` 与缺少 `sql` 返回 FastAPI 默认 `422`，正文为 Pydantic `detail` 数组，没有稳定产品错误码，也没有运行记录标识。
2. 非整数路径 `GET /api/v1/query-runs/does-not-exist` 返回 `422` 校验错误，而不是设计中的 `404 QY_RUN_NOT_FOUND`。

#### 最小查询工作台 5 / 5

**证据**

- Web `http://127.0.0.1:25280/` 返回工作台 HTML，标题为「DecisionHarbor 查询工作台」。
- 产品 Playwright（`WEB_URL=http://127.0.0.1:25280`）2 passed：允许查询可见 5 行结果表与「共 5 行 · 耗时 … ms」；`DELETE FROM customers` 可见 `QY_FORBIDDEN_STATEMENT`。
- 独立 Playwright 脚本确认提交后 `data-testid="running"`（「执行中…」）可见，随后结果表与拒绝文案均成立。

**未验证**

- 产品 e2e 未覆盖 `failed` 面板；失败 UI 代码存在，API 超时语义已验证。
- 无浏览器 MCP 人工点击。

### 2. SQL 治理与数据正确性 20 / 20

#### AST 只读语义与单语句约束 6 / 6

**证据**

- `evaluate()` 使用 `sqlglot.parse(..., read="postgres")`，按 AST 节点判定，不是字符串黑名单。
- 现场拒绝：多语句、`UPDATE`/`INSERT`/`DELETE`/`CREATE`/`COPY`/`CALL`/`DO`/`SET`/`EXPLAIN`、写 CTE、`SELECT INTO`。
- 注释后的第二条语句被判 `QY_MULTIPLE_STATEMENTS`。
- `SELECT 1`、CTE、未限定白名单表、显式 `analytics.` 限定均允许。

#### 授权对象与 schema 范围 4 / 4

**证据**

- API 拒绝：`platform.query_runs`、`pg_catalog.pg_class`、`information_schema.tables`、`generate_series`、未限定 `pg_tables`。
- 未限定名必须落在契约五表或本次 CTE 名中。

直连 `analytics_readonly` 仍能读 `pg_catalog`（PostgreSQL 固有行为）；用户 SQL 经 API 访问系统表会被策略拒绝。

**残留缺口（不降本子项档）**

- 函数策略是黑名单。`SELECT current_user`、`session_user`、`version()`、`inet_server_addr()` 均 `succeeded`，分别返回 `analytics_readonly`、服务端版本与容器内网地址。这不是表对象越权，但是会话/系统信息泄漏。

#### 数据库身份与双库隔离 4 / 4

**证据**

- 用户 SQL 以 `analytics_readonly` 执行（`SELECT current_user` 返回该角色；角色级 `default_transaction_read_only=on`）。
- `analytics_readonly` 连接 `platform`：`FATAL: permission denied ... CONNECT privilege`。
- `analytics_readonly` 对 `analytics.customers` 插入：`cannot execute INSERT in a read-only transaction`。
- API 运行时使用 `platform_app@platform` 写审计、`analytics_readonly@analytics` 执行用户 SQL；引导身份只在启动脚本中使用。

**残留缺口（不降本子项档）**

- `analytics` 未撤销 `PUBLIC CONNECT`。`platform_app` 与 `platform_owner` 都能连上 `analytics`。`platform_app` 对 `analytics` schema 无 USAGE，不能读五张业务表，但仍能读 `pg_catalog`。用户 SQL 路径本身未改用平台身份。

#### 执行资源限制 3 / 3

**证据**

- 语句超时：交叉计数返回 `failed/QY_TIMEOUT`。
- 行数上限：`order_items × customers` 返回 `succeeded`、`row_count=1000`、`truncated=true`，与设计「截断并标记」一致；上限真实生效。
- 角色级 `statement_timeout=10s` 与应用层 `SET statement_timeout` 双重设置。

**未验证**

- 未现场触发 SQL 长度上限（单测覆盖 `QY_SQL_TOO_LONG`）。
- 未验证设计中的只读连接池上限 `query_pool_size`（配置项存在，执行器每次新建连接，未见使用）。

#### 固定数据契约与业务口径 3 / 3

**证据**

- 行数：customers 100、product_categories 8、products 50、orders 1000、order_items 3000。
- 订单状态、日期范围（2024-01-01 至 2025-12-31）与销售额/成本/毛利口径与契约一致。
- `python3 datasets/sales-analytics-v1/validate.py` 通过。
- seed 标记 `sales-analytics/1.0.0/20260720` 写入 `platform.dataset_markers`。
- DDL 由契约派生：主键、唯一、外键、`NOT NULL` 成立。契约中的 `allowed_values` / 价格与折扣检查未生成 `CHECK` 约束；固定 CSV 本身符合口径。

### 3. 可运行性与可靠性 17.5 / 20

#### 干净环境启动与就绪 6 / 6

**证据**

- `docker compose -f deploy/compose.yaml -p dh-grok-review-z53 up --build --wait` 一次拉起 db / api / web。
- API 引导执行 Alembic `0001_platform_baseline`；`/health` 与 `/ready` 在 API 与 Web 代理上均为 HTTP 200。
- 产品入口是 `make up`（`docker compose --env-file .env -f deploy/compose.yaml up --build --wait`）。本次为避免占用默认项目名/端口，使用等价的 `-p` 与端口覆盖。

#### 迁移与固定数据初始化 6 / 6

**证据**

- 新卷首次启动后五表行数正确，seed 标记已写。
- `restart api` 后 `/ready` 恢复 200，行数不变，标记仍在；Alembic 第二次启动不再执行 `upgrade -> 0001`。

**未验证**

- 未手工制造部分/冲突 fixture 后再跑 seed，以观察 `SeedError` 停机（代码路径存在）。

#### 并行实例隔离 2.5 / 5

**通过**

- 无 `container_name`。用 `-p dh-grok-review-z53` / `dh-grok-review-z53b` 可同时存在。
- 端口 `25280/28281` 与 `25281/28282` 同时 healthy；两边允许查询均 `succeeded` 且 `COUNT=100`。
- 审计行数：主实例 41，并行实例 1。数据卷与网络按项目名隔离。数据库不发布宿主端口。

**缺陷（故本子项部分通过）**

1. `deploy/compose.yaml` 写死 `name: decision-harbor-api`。未传 `-p` 时，`docker compose config` 的项目名为 `decision-harbor-api`，与 `.env.example` 的 `COMPOSE_PROJECT_NAME=decision-harbor` 不一致。`make up` 依赖 `.env` 的项目名覆盖，文档与文件默认值互相打架。
2. 技术约束禁止共享绑定目录；架构文档写「源码构建进镜像、不使用绑定挂载」。实际 `api` 绑定 `../datasets`，`db` 绑定 `../deploy/initdb`。两个并行实例共享同一宿主数据集目录。

#### 重启与故障可见性 3 / 3

**证据**

- `restart api` 后 `/ready` 恢复 200。
- `stop db` 后 `/health` 仍 200，`/ready` 为 `503`，`reason=platform 数据库未就绪`。
- 重新 `start db` 后 `/ready` 恢复 200，允许查询再次返回 100。

### 4. 测试与验证证据 12 / 15

#### 统一测试入口与可靠断言 1.5 / 3

**证据**

- `Makefile` 提供 `make test`：单元 → 集成 → Web → 浏览器；失败会非零退出。
- 本次：`validate.py` 通过；容器内单元 `51 passed`；集成 `8 passed`；宿主机 Vitest `4 passed`；Playwright `2 passed`。

**缺陷**

- `make web-test` / `make test` 的 Web 步是 `docker compose exec -T web npm test`。运行中的 Web 镜像是 `nginx:1.27-alpine`，没有 `npm`：`exec: "npm": executable file not found`，退出码 127。统一入口按文档不能完整跑通。

**未验证**

- 未把 `make test` 作为单条命令从空栈再跑一遍（已知会在 Web 步失败）。

#### SQL 策略单元测试 5 / 5

**证据**

- `api/tests/unit/test_policy.py` 覆盖允许查询（连接、子查询、窗口、CTE、集合操作、schema 限定、注释/大小写、尾部分号）、全部列出的写语句与命令、写 CTE、`SELECT INTO`、多语句、空/超长、占位符、系统目录、未授权对象、危险函数。
- 本次容器内 `51 passed`。

#### 双数据库集成测试 4 / 4

**证据**

- `test_dual_db.py` 在真实 Compose 库上证明：只读身份不能写/不能 DDL、不能连 `platform`、五表行数、`platform_app` 可读审计、HTTP 允许查询 + `DROP` 拒绝 + `GET` 回读。
- 本次 `8 passed`。

**未验证**

- 集成测试没有单独断言冲突 seed 失败，也没有断言 `platform_app` 不得 `CONNECT analytics`。

#### 浏览器主链测试 1.5 / 3

**证据**

- `web/e2e/workbench.spec.ts` 覆盖提交允许 SQL、成功表格/元信息、拒绝码。
- 本次对评审栈复跑 2 passed。

**缺口**

- 产品 e2e 不断言执行中状态（`testing.md` 写了要覆盖）。独立脚本补证了 `running`，但不属于产品测试资产。
- 产品 e2e 不覆盖失败展示。

### 5. 代码质量与可维护性 7.5 / 10

#### 模块边界与职责分离 3 / 3

`policy` 纯函数不碰库；`execute` 只走只读 DSN；`runs` 编排审计与终态；`seed`/`bootstrap` 使用 owner 身份；HTTP 路由薄。依赖方向与设计一致。

#### 配置、错误处理与资源清理 1.5 / 3

**成立**

- 超时与行数来自服务端 `Settings`。
- 执行异常映射为稳定摘要，不把 PostgreSQL 原文返回给调用方。
- FastAPI lifespan 在关闭时 `platform_engine.dispose()`。
- 只读事务结束 `rollback()`。

**问题**

- 传输层错误未统一成设计中的 `QY_INVALID_REQUEST`，直接暴露 FastAPI/Pydantic `422`。
- `query_pool_size` 写入配置但执行器每次 `psycopg.connect`，连接池未实现。
- `_finalize` 在 `session.get` 为 `None` 时会属性赋值失败（当前同步路径不易触发）。

#### 类型、命名、重复控制与可测试性 2 / 2

领域对象、拒绝码常量和表驱动单测清楚。个人风格不扣分。

#### 依赖、变更范围与维护负担 1 / 2

依赖与约束栈一致（FastAPI、SQLAlchemy 2、SQLGlot、Alembic、psycopg 3、React 19、Vite、Playwright）。扣分点：Dockerfile 用宽范围 `pip install` 而不是锁文件；Compose/Makefile 与设计文档关于绑定挂载、项目名、`make test` Web 步互相矛盾，增加后续维护成本。未见范围扩张到 LLM / RBAC / 异步队列。

## 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 22.5 / 25 |
| SQL 治理与数据正确性 | 20 / 20 |
| 可运行性与可靠性 | 17.5 / 20 |
| 测试与验证证据 | 12 / 15 |
| 代码质量与可维护性 | 7.5 / 10 |
| **技术总分** | **79.5 / 90** |

本报告不计算最终 100 分，也不给视觉分。

## 产品文档建议分 4 / 5

只评价产品内生文档，供人工裁定参考。

| 子项 | 建议 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1 / 1 | 根 `AGENTS.md`、`docs/AGENTS.md`、`docs/index.md` 给出阅读顺序与目录职责；`README.md` 指向文档入口。 |
| 设计完整性与可追溯性 | 2 / 2 | `docs/design/` 六份专题覆盖架构、治理、双库/seed、API、工作台、测试接缝，并回链背景与契约。 |
| 计划、运行/测试说明与实现一致性 | 1 / 2 | `README.md` / `Makefile` 说明 `make up` 与 `make test`。不一致：架构写「不使用绑定挂载」，Compose 绑定了 `datasets` 与 `initdb`；`testing.md` 要求浏览器断言执行中，产品 e2e 未断言；`make test` 的 Web 步在 Nginx 镜像中不可执行；Compose `name:` 与 `.env.example` 项目名不一致。 |

**文档建议分：4 / 5。**

## 风险标记

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | **不触发** | 用户 SQL 不能写入分析表；API 拒绝系统目录表、`platform`、未授权对象、DML/DDL/写 CTE；执行身份是 `analytics_readonly`，该身份无 `platform` `CONNECT`，写操作被只读事务拒绝。未发现绕过 AST 后仍能写数据或读平台业务表的路径。`current_user` 等会话函数可执行，但不构成写或未授权表访问。 |
| P1 基座失败 | **不触发** | 独立 Compose 启动成功；`/health`、`/ready`、迁移、固定 seed 均成立；重启后行数与标记保持。 |
| P2 核心闭环缺失 | **不触发** | API 与浏览器均同时证明一条允许查询和一条拒绝查询；工作台可输入、提交、展示执行中、成功表与拒绝码。 |

## 按严重度排序的问题清单

1. **`make test` 的 Web 步不可执行。** 运行中的 `web` 容器是 Nginx 静态镜像，没有 `npm`；`make web-test` 退出 127。统一测试入口不能按文档跑完。
2. **并行隔离使用共享绑定目录。** `../datasets` 与 `../deploy/initdb` 挂到每个实例；违反技术约束，也与架构文档「不使用绑定挂载」矛盾。
3. **Compose 项目名默认值自相矛盾。** 文件写死 `name: decision-harbor-api`，`.env.example` 写 `COMPOSE_PROJECT_NAME=decision-harbor`。不传 `-p` 时实际项目名取决于 Compose 对 `name` 与环境变量的覆盖顺序。
4. **传输层错误不是产品契约。** 非法 JSON/类型与非整数 run id 返回 FastAPI `422` 校验体，而不是 `400 QY_INVALID_REQUEST` / `404 QY_RUN_NOT_FOUND`。
5. **`platform_app` 能连接 `analytics`。** `analytics` 未收紧 `CONNECT`；不能读业务表，但仍扩大了身份边界。
6. **函数策略是黑名单。** `current_user` / `session_user` / `version()` / `inet_server_addr()` 经 API 成功返回身份与服务器信息。
7. **契约 `allowed_values` 与金额约束未进入生成 DDL。** 数据来自固定 CSV 所以当前正确，但库层不强制状态、区域、折扣和价格不变量。
8. **产品 Playwright 不断言执行中，也不覆盖失败。** 工作台代码与独立脚本能证明执行中；仓库 e2e 资产不完整。
9. **`query_pool_size` 未接入执行器。** 每次查询新建连接。

## Compose 资源停止情况

本次评审启动并随后销毁：

- `dh-grok-review-z53`：容器、默认网络、数据卷 `dh-grok-review-z53_pgdata`。
- `dh-grok-review-z53b`：容器、默认网络、数据卷 `dh-grok-review-z53b_pgdata`。

结束时 `docker ps/volume/network --filter name=dh-grok-review-z53` 无残留。ExamForge 等无关项目保持原状，未停止。

## 最终 Git 状态

候选工作树结束时：

```text
a5811b218e42183f9b46aa2a2555194a658c7cf5
## v0.1.0/zcode-glm-5.3-high...origin/v0.1.0/zcode-glm-5.3-high
```

`git status --porcelain` 为空，`git diff --check` 无输出。评审未改候选文件。

## 未验证项汇总

- 官方非公开 harness 套件（工作区无副本）。
- 整包 `make test` / `make up`（未使用默认项目名与 8080/8081，以免与文档默认实例冲突）。
- 手工冲突 fixture 的 `SeedError`。
- SQL 长度上限的现场 HTTP 探针（单测已覆盖）。
- 浏览器失败面板与浏览器 MCP 人工点击。
