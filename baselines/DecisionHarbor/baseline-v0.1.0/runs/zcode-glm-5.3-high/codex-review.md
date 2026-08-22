# Codex 首轮独立评审：DecisionHarbor v0.1.0

## 独立性与评审对象

本报告只依据本次对冻结候选的代码和现场运行证据形成。未读取其他候选的工作树、分支、运行记录或评审材料；未读取本候选的 `grok-review.md`、`review-summary.md` 或 `scorecard.md`。未因 Agent、模型、耗时、token 或既往印象调整评分标准。

- 候选工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.3-high`
- 分支：`v0.1.0/zcode-glm-5.3-high`
- `RESULT_COMMIT`：`a5811b218e42183f9b46aa2a2555194a658c7cf5`
- baseline：`1fb48f499d67677a47fb9b60e1f99346b46e0aee`
- 冻结核验：`metadata.json` 的 `completion.coordinatorFrozen=true`，且 `candidate.resultCommit` 与上述 SHA 一致。

开始和结束时 `git rev-parse HEAD` 都为 `a5811b218e42183f9b46aa2a2555194a658c7cf5`；`git status --short --branch` 仅输出分支行，`git diff --check` 无输出。评审未修改候选源码、候选分支、baseline 或评分规范，未执行 `git add`、`git commit`、`git push` 或创建 PR。本文件是唯一写入的归档文件。

## 环境与实际命令

环境：Docker `29.1.3`、Docker Compose `2.40.3`、宿主 Node.js `v24.16.0`、宿主 Python `3.10.12`、Playwright `1.62.1`。候选 Compose 使用 PostgreSQL 18、Python 3.13 和 Node.js 24 镜像。

在确认没有其他共享 Compose、构建或浏览器评审活动后，以下计分运行证据均以串行项目 `dshreviewzcode53serial`（Web/API：`25322/28322`）及第二个隔离项目 `dshreviewzcode53serialb`（`25323/28323`）重新取得。较早的预检项目 `dshreviewzcode53` 已在任何计分测试前停止，不作为通过证据。

```bash
git rev-parse HEAD
git status --short --branch
git diff --check
COMPOSE_PROJECT_NAME=dshreviewzcode53serial WEB_PORT=25322 API_PORT=28322 BUILDKIT_PROGRESS=quiet make up
curl --fail --silent --show-error http://127.0.0.1:28322/health
curl --fail --silent --show-error http://127.0.0.1:28322/ready
curl --fail --silent --show-error http://127.0.0.1:25322/health
curl --fail --silent --show-error http://127.0.0.1:25322/ready
# HTTP POST/GET /api/v1/query-runs：允许、拒绝、P0 绕过与资源探针
docker compose --project-name dshreviewzcode53serial --env-file .env -f deploy/compose.yaml exec -T api python -
docker compose --project-name dshreviewzcode53serial --env-file .env -f deploy/compose.yaml restart api
COMPOSE_PROJECT_NAME=dshreviewzcode53serial make test
COMPOSE_PROJECT_NAME=dshreviewzcode53serial WEB_PORT=25322 API_PORT=28322 make browser-test
cd web && WEB_URL=http://127.0.0.1:25322 npx playwright test
COMPOSE_PROJECT_NAME=dshreviewzcode53serialb WEB_PORT=25323 API_PORT=28323 BUILDKIT_PROGRESS=quiet make up
docker compose --project-name dshreviewzcode53serialb --env-file .env -f deploy/compose.yaml stop db
docker compose --project-name dshreviewzcode53serialb --env-file .env -f deploy/compose.yaml start db
make dataset-validate
docker compose --project-name dshreviewzcode53serial --env-file .env -f deploy/compose.yaml down --remove-orphans
docker compose --project-name dshreviewzcode53serialb --env-file .env -f deploy/compose.yaml down --remove-orphans
```

候选的 `reproduction.md` 与 `docs/status/` 中的自述未作为通过证据。

## 问题清单（按严重度排序）

1. **[必须修复，P0] 全局 CTE 别名可绕过对象白名单并读取系统目录。** `api/app/policy/engine.py:126-137` 将整棵 AST 的 CTE 名称汇总，之后对任何同名且未限定 schema 的 `Table` 直接放行。非递归 CTE 的定义中不能引用自身，故 `WITH pg_class AS (SELECT relname FROM pg_class WHERE relname = 'pg_class') SELECT relname FROM pg_class` 的第一个 `pg_class` 实际解析为 `pg_catalog.pg_class`，而非 CTE。现场 `POST /api/v1/query-runs` 返回 HTTP `200`、`outcome=succeeded`、`state=succeeded` 与行 `pg_class`。这违反只允许五张 `analytics` 业务表的要求，构成用户 SQL 读取系统对象。应按词法作用域逐层解析 CTE source，或在无法证明引用是当前作用域 CTE 时拒绝；加入该 SQL、嵌套 CTE 与递归 CTE 的回归用例。
2. **[必须修复，P0] 函数黑名单与未受限类型转换允许绕过 AST 对象检查。** `api/app/policy/engine.py:139-142` 仅拒绝有限函数名，且未检查 `Cast` 目标类型。现场 `SELECT 'pg_class'::regclass AS object_id` 返回成功及 `pg_class`；`SELECT query_to_xml('SELECT relname FROM pg_class LIMIT 1', false, false, '')` 同样成功，并返回内嵌系统目录查询的 XML。嵌入函数字符串的内部 SQL 没有 `Table` AST 节点，`query_to_xml` 也未被拒绝。应采用函数白名单或结构化安全分类，拒绝对象标识符转换类型（如 `regclass`），并拒绝会执行嵌入 SQL 的函数；分别添加 API 回归测试。
3. **[重要] 声明的统一测试入口无法完成 Web 和浏览器验证。** `Makefile:27-31` 在生产 Nginx `web` 容器中执行 `npm test`，但 `web/Dockerfile:8-11` 的最终镜像没有 Node/npm。现场 `make test` 先通过 API 的 `51 passed` 和 `8 passed`，随后在 `web-test` 以 `npm: executable file not found`、退出码 `127` 失败。`make browser-test` 还因 `WEB_URL` 是 Make 变量但未导出给 Playwright，固定访问 `localhost:8080`；在隔离端口 `25322` 下两个用例均 `ERR_CONNECTION_REFUSED`。应将 Web 单测放入 Node 测试服务或宿主受控环境，并显式导出 `WEB_URL`；统一入口应在干净环境完整返回结果。
4. **[中等] 常驻 API 容器持有迁移和 seed 的高权限凭据，且 `platform_app` 仍可连接 analytics。** `deploy/compose.yaml:25-29` 向运行时 API 注入 `platform_owner`、`analytics_owner`、`platform_app` 和 `analytics_readonly` 四套凭据，违背设计中服务进程只持有低权限身份的约束。`deploy/initdb/01_roles_databases.sql:22-31` 未撤销 `analytics` 对 `PUBLIC` 的 `CONNECT`。现场 `platform_app` 成功连接 analytics，虽然读取 `analytics.customers` 得到 `InsufficientPrivilege`。应拆分一次性迁移/seed 服务或在 bootstrap 后移除高权限凭据，并撤销 analytics 的 PUBLIC CONNECT 后按角色显式授予。
5. **[中等] 结果行上限不是流式内存边界。** `api/app/execute/executor.py:54-68` 使用普通 psycopg 游标；`cur.execute()` 已取得完整结果集，之后的 `fetchmany(max_rows + 1)` 只限制返回 JSON，不保证限制客户端缓冲。现场 2,000 行查询返回 1,000 行且 `truncated=true`，但大结果仍可能在 API 内存中完整物化；`query_pool_size` 只定义于 `config.py`，未被执行器使用。应使用 server-side cursor/分页流式读取、实际应用受控连接池，并为大结果内存边界增加测试。

## 分项评分

### 功能与外部契约：22.5 / 25

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 查询运行 API 生命周期 | 8 / 8 | 允许聚合查询返回 `succeeded`、运行 ID、列、5 行和耗时；随后 `GET /api/v1/query-runs/{id}` 返回审计事实且不含结果行。 |
| 允许查询结果正确性 | 7 / 7 | `customers` 按区域聚合返回 5 个区域、每个为 20；第二实例 `SELECT count(*)` 返回 100；`make dataset-validate` 通过。 |
| 拒绝与执行失败语义 | 2.5 / 5 | `platform.query_runs` 被审计为 `QY_UNAUTHORIZED_OBJECT`，超时查询为 `failed/QY_TIMEOUT`，浏览器拒绝用例通过；但三条系统对象绕过被伪装为成功，不能完整满足拒绝契约。 |
| 最小查询工作台 | 5 / 5 | 显式 `WEB_URL` 的 Playwright 主流程和拒绝流程均通过，覆盖输入、提交、结果表格和拒绝码展示。 |

未验证：浏览器对极宽列、超大响应及网络中断的呈现。

### SQL 治理与数据正确性：11.5 / 20

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| AST 只读语义与单语句约束 | 3 / 6 | SQLGlot AST 检查拒绝非授权 `platform` 对象，策略单元测试通过 51 项；但作用域错误、类型转换和嵌入 SQL 函数绕过说明策略不能可靠治理全部读取路径。 |
| 授权对象与 schema 范围 | 0 / 4 | 三条独立 API 探针成功读取或解析 `pg_catalog` 对象，详见 P0 问题 1 与 2。 |
| 数据库身份与双库隔离 | 4 / 4 | `analytics_readonly` 读取客户数为 100；删除得到 `ReadOnlySqlTransaction`，连接 `platform` 得到 `OperationalError`。`platform_app` 可连 analytics 但读取业务表为 `InsufficientPrivilege`；该最小权限缺口已列为中等问题。 |
| 执行资源限制 | 1.5 / 3 | `generate_series(1, 2000)` 返回 1,000 行且 `truncated=true`；三重 `order_items` 笛卡尔统计约 10,039 ms 后为 `failed/QY_TIMEOUT`。普通游标未提供真实流式内存限制。 |
| 固定数据契约与业务口径 | 3 / 3 | `make dataset-validate` 通过；API 重启后五张表计数仍为 `100/8/50/1000/3000`，两个实例均可读取固定数据。 |

未验证：锁等待超时、并发连接槽耗尽，以及列宽和响应字节数上限。

### 可运行性与可靠性：20 / 20

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 干净环境启动与就绪 | 6 / 6 | 以独立项目和端口执行 `make up` 后，PostgreSQL、API、Web 均 healthy；API 与 Web 代理的 `/health`、`/ready` 都为 200。 |
| 迁移与固定数据初始化 | 6 / 6 | API bootstrap 执行迁移和 seed；重启 API 后 `/ready` 恢复，五张表仍为契约计数且未重复。 |
| 并行实例隔离 | 5 / 5 | 两个项目使用不同网络、卷和端口同时 ready；第二项目读取第一项目运行 ID `1` 返回 404，首次查询从 `id=1` 开始。 |
| 重启与故障可见性 | 3 / 3 | 停止第二项目 DB 后 `/ready` 返回 503 `platform 数据库未就绪`；重启 DB 后恢复 200。API 重启后也恢复 ready。 |

未验证：迁移失败、seed 标记不一致、审计终态写入失败与数据卷损坏后的恢复。

### 测试与验证证据：8 / 15

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 统一测试入口与可靠断言 | 0 / 3 | `make test` 以 `web-test` 的退出码 127 失败，无法作为完整统一入口。 |
| SQL 策略单元测试 | 2.5 / 5 | 51 个策略单元测试通过，覆盖普通允许、DML/DDL、多语句、写 CTE、显式系统 schema 和部分危险函数；但遗漏 CTE 词法作用域、`regclass` 和 `query_to_xml` 三条已复现 P0 路径。 |
| 双数据库集成测试 | 4 / 4 | 8 个集成测试通过；现场额外验证了只读身份读、写拒绝、平台连接拒绝、固定数据计数及 API 生命周期。 |
| 浏览器主链测试 | 1.5 / 3 | 候选 `make browser-test` 在可配置端口失败；直接以相同 Playwright 配置并明确 `WEB_URL` 后，2 个真实浏览器用例通过。 |

未验证：浏览器失败态和统一入口在未安装宿主 `node_modules`/Playwright 浏览器的干净主机上的行为。

### 代码质量与可维护性：6.5 / 10

| 子项 | 得分 | 证据 |
| --- | ---: | --- |
| 模块边界与职责分离 | 3 / 3 | 策略、执行、审计运行、seed、ready 与路由分层清楚，纯策略函数与服务编排边界明确。 |
| 配置、错误处理与资源清理 | 1.5 / 3 | HTTP 和执行错误映射稳定，Compose 项目可隔离；但高权限凭据常驻、连接权限未完全收紧、行数限制并非流式内存限制。 |
| 类型、命名、重复控制与可测试性 | 1 / 2 | Python 模块有基本类型和可测纯函数；但 Web `QueryRunResponse.rows` 声明为 `string[][]`，实际 API 返回数值行（现场为 `[20]`），且关键作用域边界没有测试。 |
| 依赖、变更范围与维护负担 | 1 / 2 | 改动范围集中，但 Dockerfile 使用浮动 `>=` Python 依赖和 `npm install` 而非锁定安装，测试服务与生产镜像错配，降低可复现维护性。 |

## 技术总分：68.5 / 90

## 产品文档建议：3 / 5

- 治理、索引与阅读入口：1 / 1。README、`docs/index.md`、背景、设计和计划层次清晰。
- 设计完整性与可追溯性：1.5 / 2。双库、SQL 治理、迁移/seed、工作台和测试接缝均有明确设计，但服务只持有低权限身份的设计描述与实际 Compose 环境不符。
- 计划、运行/测试说明与实现一致性：0.5 / 2。`make up` 与运行实现基本一致；`make test` 和可配置端口下的 `make browser-test` 均不能按文档完成。

## 风险标记判断

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | **标记** | 用户 SQL 经 API 成功执行 CTE 系统目录读取、`regclass` 解析和 `query_to_xml` 内嵌系统目录读取，均违反对象白名单与系统对象禁止访问要求。 |
| P1 基座失败 | 不标记 | 串行复现中 `make up`、两级 health/ready、迁移/seed、并行项目及故障恢复均成立。 |
| P2 核心闭环缺失 | 不标记 | API 和真实浏览器均证明允许查询、拒绝查询及最小工作台可用；测试入口失败已在测试分与问题清单中体现。 |

风险标记不改变上述技术分数。

## Compose 资源停止情况与最终 Git 状态

- 预检项目 `dshreviewzcode53` 已在计分前停止；串行计分项目 `dshreviewzcode53serial`、`dshreviewzcode53serialb` 均已执行 `docker compose down --remove-orphans`。最终三个项目均无容器或网络，未停止无关项目。
- 为避免破坏性清理，三个命名 PostgreSQL 数据卷被保留，但不包含运行中资源。
- 最终 HEAD：`a5811b218e42183f9b46aa2a2555194a658c7cf5`；`git status --short --branch` 干净，`git diff --check` 无输出。

## 未验证项汇总

- 锁等待超时、连接池耗尽、列宽与响应字节上限的现场行为。
- 迁移失败、seed 标记不一致、审计终态写入失败和数据卷损坏后的恢复。
- 未安装宿主 Node/npm 依赖和 Playwright 浏览器时，按 README 的干净环境测试体验。
