# DecisionHarbor v0.1.0 Codex 首轮独立评审

## 独立性与评审身份

本报告对应 `review-prompts.md` 索引表中编号 `16` 的 DeepSeek Harness Web（`deepseek-v4-pro-high`）候选。唯一报告文件为本文件。

本次评分只基于冻结 commit 的本轮代码阅读与现场运行证据。评审期间未读取、比较或引用其他候选的工作树、分支、归档、评审报告、分数或结论；未读取本候选的 `grok-review.md`、`review-summary.md` 或 `scorecard.md`。未修改候选源码、候选分支、baseline、评分规则或其他归档文件，未执行 `git add`、`commit`、`push` 或创建 PR。本文件是本次唯一写入。

## 先列问题

### [必须修复][P0] SQL 策略允许三种路径访问 PostgreSQL 系统对象

- 位置：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high/api/app/policy.py:96-116`。
- 触发与现场结果：
  - `SELECT CAST('pg_catalog.pg_class' AS regclass) AS relation` 经 API 返回 `202`，终态为 `succeeded`，结果为 `pg_class`。
  - `WITH pg_class AS (SELECT 1 AS x) SELECT relname FROM pg_catalog.pg_class LIMIT 1` 经 API 返回 `succeeded`，读取到系统目录中的 `customers_pkey`。
  - `SELECT query_to_xml('SELECT relname FROM pg_class LIMIT 1', true, false, '')` 经 API 返回 `succeeded`，XML 中包含系统目录查询结果 `customers_pkey`。
  - 对照输入 `SELECT relname FROM pg_catalog.pg_class LIMIT 1` 被正确拒绝为 HTTP 422 / `POLICY_UNAUTHORIZED_OBJECT`。
- 根因：策略只遍历 `exp.Table` 节点；cast 目标和函数内 SQL 字符串不形成受检的表节点。同时 `cte_names` 是全局名称集合，`api/app/policy.py:104-111` 仅按表名跳过，错误地将有 `pg_catalog` 限定的物理表当作 CTE。
- 违反依据：`docs/background/product-requirements.md` 的 SQL 治理规则要求拒绝系统目录、未授权对象和对象范围绕过；`docs/design/system-design.md` 的 I4 要求授权对象恒等于五张 `analytics` 表。
- 最小修复方向：实现有词法作用域的 AST visitor，只将无 schema/catalog 限定的 CTE 引用解析为 CTE；所有限定物理表继续经过 allowlist。对函数建立显式安全允许名单，拒绝动态执行 SQL 的函数，并校验 `CAST` / `::` 的目标类型，禁止 `regclass`、`regproc`、`regprocedure`、`regtype` 等对象解析类型。将上述三条输入加入 HTTP 级回归测试。

### [建议修改][P2] 依赖不固定且 Web 构建没有 lockfile，干净环境的可重复性不足

- 位置：`api/requirements.txt:1-9`、`web/package.json:13-26`、`web/Dockerfile:3-4`、`docker-compose.yml:5`。
- 触发场景：Python 依赖大多没有精确版本，Web 使用范围版本且 Dockerfile 执行 `npm install`，仓库没有 `package-lock.json`。当前宿主缓存下构建成功不能冻结下次干净 WSL 拉取到的解析结果。
- 影响：首轮对“干净环境可启动”的长期可复现性依赖上游最新包和镜像 patch，而不是冻结输入；未来上游不兼容更新可能改变构建或测试结果。
- 最小修复方向：提交 lockfile，改用 `npm ci`；固定 Python 依赖及基础镜像到经验证版本或 digest，并在更新时显式维护。

### [建议修改][P2] 阅读入口与目录现状说明仍称产品未实现

- 位置：`README.md:5`、`docs/design/README.md:26-28`、`docs/plan/README.md:22-24`。
- 触发场景：上述文件仍称应用源码、运行命令、专题设计和阶段计划尚未建立，但同一冻结提交已有 `api/`、`web/`、`docker-compose.yml`、`docs/design/system-design.md`、`docs/plan/first-round.md`，且 `docs/status/project_status.md:7-20` 已登记真实命令。
- 影响：从 README 或目录说明进入项目的开发者会得到错误的交付状态与阅读路径，降低文档作为运行入口的可信度。
- 最小修复方向：在实现落地时同步更新根 README 和两个目录 README，使其链接系统设计、首轮计划以及 `make up` / `make test`。

## 冻结、环境与 Git 核验

| 项目 | 结果 |
| --- | --- |
| 索引身份 | `review-prompts.md:27` 的编号 `16`，唯一报告路径与本文件一致 |
| 候选工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high` |
| 候选分支 | `v0.1.0/dshpreview-deepseek-v4-pro-high` |
| baseline commit | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| `RESULT_COMMIT` | `4306278abbfb4a65d6d52a6e701c1e308fe2ed46` |
| 冻结前置 | `metadata.json` 中 `completion.coordinatorFrozen=true`，且 `candidate.resultCommit` 为完整 SHA |
| 开始与结束 HEAD | 两次 `git rev-parse HEAD` 都为 `4306278abbfb4a65d6d52a6e701c1e308fe2ed46` |
| 开始与结束状态 | `git status --short --branch` 仅为分支跟踪行，无未提交改动；`git diff --check` 无输出 |
| 实际环境 | Docker Engine `29.1.3`，Docker Compose `2.40.3`，宿主 Python `3.10.12`，Node `v24.16.0`；候选 Compose 声明 Python 3.13、Node 24、PostgreSQL 18 镜像 |

AgentShip 工作树在开始时已有无关未提交改动，全部保留且未读入评分证据。候选工作树没有 `.codegraph/`，因此按规则使用 `rg` 定位代码与文件。

## 实际命令与新鲜运行证据

| 覆盖项 | 实际命令或探针 | 结果 |
| --- | --- | --- |
| 固定数据 | `make validate-dataset` | 通过，`datasets/sales-analytics-v1/validate.py` 验证固定夹具、关系和可重复生成。 |
| 统一启动与测试 | `make test` | 成功启动 `db`、`api`、`web`，`/ready` 成功；pytest `50 passed`（4 条弃用警告）、Vitest `1 passed`、Playwright `2 passed`。 |
| 健康与就绪 | HTTP `GET /health`、`GET /ready` | 分别为 `200 {"status":"ok"}`、`200 {"status":"ready"}`。 |
| 允许 SQL | `POST /api/v1/query-runs` 后轮询 `GET`：客户计数与 CTE 分组 | POST 为 `202 running`，均到达 `succeeded`；客户数为 `100`，五个地区各 `20` 位客户。 |
| 拒绝 SQL | `DROP TABLE customers`、`SELECT 1; SELECT 2`、直接读取 `pg_catalog.pg_class` | 都为 HTTP 422 / `rejected`；错误码分别为 `POLICY_FORBIDDEN_STATEMENT`、`POLICY_MULTIPLE_STATEMENTS`、`POLICY_UNAUTHORIZED_OBJECT`。 |
| 行数上限 | `SELECT * FROM generate_series(1, 10001) AS x(n)` | POST 为 202，终态为 `failed` / `EXEC_ROW_LIMIT_EXCEEDED`，没有返回截断结果。 |
| 超时上限 | `docker compose run --rm --no-deps -T -e QUERY_TIMEOUT_MS=100 api python -`，以执行器运行 `SELECT pg_sleep(0.3)` | 输出 `timeout=EXEC_TIMEOUT`。 |
| 双库与身份 | `psql` 分别使用 `analytics_reader`、`platform_writer`；尝试 reader 写 analytics、reader 读写 platform、writer 读 analytics | reader 实际为 `analytics_reader,analytics,on,100`；四项越权操作均被拒绝；writer 身份为 `platform_writer,platform`。 |
| 故障可见性 | `docker compose stop db` 后探测 `/ready`，再 `docker compose start db` | DB 停止时 `/ready` 为 `503 {"status":"not_ready",...}`、`/health` 仍为 200；DB 恢复后第 2 次轮询 `/ready` 回到 200。 |
| 并行 Compose | 主实例运行时，以 `COMPOSE_PROJECT_NAME=dhdeepreview`、API `58111`、Web `55175`、匹配的 CORS/API build 参数执行 `docker compose up -d --build db api web` | 两个项目的三项服务同时运行；两个 `/ready` 与 Web 均为 200，并行实例允许查询返回客户数 `100`；容器、网络和卷命名空间均不同。 |
| P0 安全探针 | 表首三条系统对象输入，经真实 API 提交并轮询 | 三条均获策略允许且执行成功，详见首个问题。 |

## 技术评分：73.5 / 90

评分按规范的 0 / 半分 / 满分档位。风险标记不作为额外扣分项，根因已在相关技术子项中体现。

### 功能与外部契约：22.5 / 25

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 查询运行 API 生命周期 | 8 / 8 | 实测 `202 running → GET terminal`；统一测试还覆盖审计与启动收敛。 |
| 允许查询结果正确性 | 7 / 7 | 实测聚合与 CTE 的列、行、行数正确；固定数据校验通过。 |
| 拒绝与执行失败语义 | 2.5 / 5 | 常规 DDL、多语句、直接目录和行上限都有稳定状态及错误码；但未授权系统对象可绕过策略而成功。 |
| 最小查询工作台 | 5 / 5 | 真实 Playwright 覆盖输入、提交、成功结果和拒绝信息。 |

### SQL 治理与数据正确性：13 / 20

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| AST 只读语义与单语句约束 | 3 / 6 | SQLGlot 解析、多语句、DML/DDL、修改型 CTE、`SELECT INTO` 的常规路径均有效；函数 SQL、对象解析 cast 和限定 CTE 作用域可绕过 AST 对象约束。 |
| 授权对象与 schema 范围 | 0 / 4 | 三条 P0 输入成功访问系统对象，不能满足仅限五张 `analytics` 表的核心约束。 |
| 数据库身份与双库隔离 | 4 / 4 | 现场角色探针验证 reader 的只读与平台库数据访问拒绝，writer 不能读 analytics；执行器使用 reader DSN。 |
| 执行资源限制 | 3 / 3 | API 行上限与独立 100 ms 执行器超时均实际生效。 |
| 固定数据契约与业务口径 | 3 / 3 | 数据集校验、启动 seed、第二实例 seed 和行计数均通过。 |

### 可运行性与可靠性：20 / 20

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 干净环境启动与就绪 | 6 / 6 | 受支持的 `make test` 构建、启动并等待 ready；健康端点与 Web 可达。未在完全没有镜像和依赖缓存的新机器上重拉所有依赖。 |
| 迁移与固定数据初始化 | 6 / 6 | bootstrap、两次集成 seed、固定数据验证和新项目 seed 均成功。 |
| 并行实例隔离 | 5 / 5 | 两套实例以不同项目名和端口同时运行，独立网络和卷。 |
| 重启与故障可见性 | 3 / 3 | DB 停止时 readiness 正确失败，恢复后无需清理数据即可恢复。 |

### 测试与验证证据：12.5 / 15

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 统一测试入口与可靠断言 | 3 / 3 | `make test` 以非零失败语义串联构建、pytest、Vitest 和 Playwright；本次运行完整通过。 |
| SQL 策略单元测试 | 2.5 / 5 | 覆盖允许、DML/DDL、多语句、修改型 CTE、直接系统目录及常规 schema 边界，但缺少函数、cast 和限定 CTE 的绕过回归，因此绿灯未发现 P0。 |
| 双数据库集成测试 | 4 / 4 | 真实 PostgreSQL 角色探针及集成套件均验证 seed、审计、reader 只读、资源上限与启动收敛。 |
| 浏览器主链测试 | 3 / 3 | Playwright 2 / 2 通过，覆盖允许与拒绝两条用户主链。 |

### 代码质量与可维护性：5.5 / 10

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 模块边界与职责分离 | 3 / 3 | 策略、目录、执行器、存储、服务、bootstrap、路由和 Web API 客户端职责清楚。 |
| 配置、错误处理与资源清理 | 1.5 / 3 | Compose、健康检查、超时、seed 和资源销毁路径明确；但 P0 表明治理边界并未封闭，且策略测试没有覆盖关键安全路径。 |
| 类型、命名、重复控制与可测试性 | 1 / 2 | Python 模块与测试接缝可读，但 API 使用无验证的 `dict` 封套、执行/缓存采用无界后台线程而没有并发控制或负载证据。 |
| 依赖、变更范围与维护负担 | 0 / 2 | 依赖与镜像版本未冻结，Web 缺 lockfile 且 Dockerfile 使用 `npm install`。 |

## 产品文档建议：4 / 5

| 子项 | 建议 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1 / 1 | `docs/index.md`、根和 docs 规则清楚区分背景、设计、计划、状态。 |
| 设计完整性与可追溯性 | 2 / 2 | `docs/design/system-design.md` 明确状态机、三身份、对象边界、错误码、seed、Compose 和测试接缝。 |
| 计划、运行/测试说明与实现一致性 | 1 / 2 | `docs/status/project_status.md` 的命令与本次复现一致，但根 README、design README、plan README 仍报告“未建立”或“暂无”，与实现矛盾。 |

未给视觉分，也未计算最终 100 分或任何平均分。

## P0 / P1 / P2 风险判断

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | 有 | 用户 SQL 经 API 实际访问了 `pg_catalog` 系统对象，满足评分规范的「访问系统或未授权对象、绕过 AST 治理」条件。 |
| P1 基座失败 | 无 | 统一启动、迁移、seed、health、ready、故障时 readiness 和恢复均在本次复现中成立。 |
| P2 核心闭环缺失 | 无 | 允许查询、拒绝查询、结果行上限失败和浏览器工作台均有新鲜运行证据。 |

## 未验证项与残余风险

- 未在一个没有现有 Docker / npm / pip 缓存的全新宿主机重新拉取全部依赖；由于依赖未锁定，这不能按通过处理。
- 未进行并发负载、长时间缓存过期或人工视觉评分；它们不计入本报告已给分的通过证据。
- 系统对象绕过的三条独立路径已证实，但没有声称已枚举所有可能的 PostgreSQL 函数、cast 或 AST 绕过变体。

## Compose 清理与最终 Git 状态

- 本次评审通过 `make test` 启动主项目 `decisionharbor`，通过显式 `COMPOSE_PROJECT_NAME=dhdeepreview` 启动并行项目 `dhdeepreview`。
- 已执行并行项目的 `docker compose down --volumes --remove-orphans`，删除本次创建的容器、网络与 `dhdeepreview_pgdata`。
- 已执行主项目的 `docker compose down --remove-orphans`，停止并删除本次主项目的容器和网络，保留既有主项目命名卷；未停止其他项目。
- 两个项目在清理后的 `docker compose ps --all` 均为空。
- 最终候选 HEAD 仍为 `4306278abbfb4a65d6d52a6e701c1e308fe2ed46`；`git status --short --branch` 无未提交改动，`git diff --check` 无输出。
