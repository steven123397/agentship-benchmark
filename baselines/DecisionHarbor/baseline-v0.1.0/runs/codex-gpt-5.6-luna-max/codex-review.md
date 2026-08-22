# Codex 首轮独立评审：DecisionHarbor v0.1.0（更正）

## 独立性与审查对象

本报告只依据本次对冻结候选的代码与现场运行证据形成。未读取其他候选的工作树、分支、运行归档或评审材料；未读取本候选的 `grok-review.md`、`review-summary.md` 或 `scorecard.md`。未因 Agent、模型、耗时、token 或既往印象调整标准。补充复核发现了一条此前遗漏的、可稳定复现的 P0 SQL 策略绕过，因此替换原先报告的评分与风险判断。

- 候选工作树：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-luna-max`
- 分支：`v0.1.0/codex-gpt-5.6-luna-max`
- `RESULT_COMMIT`：`1dfb4a4d4d441350b6035ea36eacf414cb9e4023`
- baseline：`1fb48f499d67677a47fb9b60e1f99346b46e0aee`
- 冻结核验：`completion.coordinatorFrozen=true`；开始和结束时 `git rev-parse HEAD` 均为上述 `RESULT_COMMIT`，`git status --short --branch` 除分支行外无输出，`git diff --check` 无输出。

评审未修改候选源码、候选分支、baseline 或评分规范，未执行 `git add`、`git commit`、`git push` 或创建 PR。本文件是唯一写入的归档文件。

## 环境与实际命令

环境：Docker `29.1.3`、Docker Compose `2.40.3`、宿主 Node.js `v24.16.0`、宿主 Python `3.10.12`。API Compose 镜像为 Python `3.13-slim`；API 测试实际在该容器中运行。Playwright 使用仓库配置的 Desktop Chrome 项目。

主要实际命令如下（SQL、端口和 Compose 项目均仅针对本次评审）：

```bash
git rev-parse HEAD
git status --short --branch
git diff --check
python3 datasets/sales-analytics-v1/validate.py
COMPOSE_PROJECT_NAME=dshreviewluna20260814 WEB_HOST_PORT=25179 API_HOST_PORT=28086 ./dev up
curl --fail-with-body http://127.0.0.1:28086/health
curl --fail-with-body http://127.0.0.1:28086/ready
curl --fail-with-body http://127.0.0.1:25179/health
curl --fail-with-body http://127.0.0.1:25179/ready
COMPOSE_PROJECT_NAME=dshreviewluna20260814 WEB_HOST_PORT=25179 API_HOST_PORT=28086 docker compose run --rm --no-deps migrate
COMPOSE_PROJECT_NAME=dshreviewluna20260814 WEB_HOST_PORT=25179 API_HOST_PORT=28086 WEB_BASE_URL=http://127.0.0.1:25179 ./dev test
COMPOSE_PROJECT_NAME=dshreviewluna20260814b WEB_HOST_PORT=25180 API_HOST_PORT=28087 ./dev up
COMPOSE_PROJECT_NAME=dshcompareluna20260814c WEB_HOST_PORT=25182 API_HOST_PORT=28089 ./dev up
# Node fetch: POST /api/v1/query-runs，SQL 为下文 P0 探针
# Node net.Socket: 无 Content-Length、Transfer-Encoding: chunked 的 130 KiB JSON 请求
COMPOSE_PROJECT_NAME=dshreviewluna20260814 WEB_HOST_PORT=25179 API_HOST_PORT=28086 docker compose down --remove-orphans
COMPOSE_PROJECT_NAME=dshreviewluna20260814b WEB_HOST_PORT=25180 API_HOST_PORT=28087 docker compose down --remove-orphans
COMPOSE_PROJECT_NAME=dshcompareluna20260814c WEB_HOST_PORT=25182 API_HOST_PORT=28089 docker compose down --remove-orphans
```

另执行了 API `POST /api/v1/query-runs` 与 `GET /api/v1/query-runs/{id}`、真实 PostgreSQL 角色权限探针、原始 HTTP 分块传输探针、第二实例的数据库停机和 API 重启探针。`reproduction.md` 中的 Agent 自述未作为通过证据。

## 分项评分

### 功能与外部契约：22.5 / 25

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 查询运行 API 生命周期 | 8 / 8 | 允许聚合返回 `succeeded`、运行 ID、列、5 行结果和耗时；随后 `GET` 同一 ID 返回已审计状态且不返回结果行。常规对象越权运行的 `GET` 返回 `rejected` 与 `object_not_allowed`。 |
| 允许查询结果正确性 | 7 / 7 | `analytics.customers` 的按区域聚合及普通 CTE 路径均返回 5 个区域、每个客户数为 20；固定数据校验通过。 |
| 拒绝与执行失败语义 | 2.5 / 5 | `platform.query_runs`、多语句、写 CTE、`query_to_xml`、`regclass`、`current_user`、`version()` 和 `FOR UPDATE` 都以稳定错误码记录为 `rejected`；行数和超时运行均记录为 `failed`。但存在可执行的未授权系统对象读取，且分块请求可绕过 HTTP 大小拒绝契约。 |
| 最小查询工作台 | 5 / 5 | Playwright 浏览器主链通过：默认允许 SQL 显示 `SUCCEEDED` 与结果表；输入 `SELECT * FROM platform.query_runs` 后显示 `object_not_allowed`。 |

未验证：没有手工检验极端宽列或 4 MiB 负载在浏览器中的呈现。

### SQL 治理与数据正确性：13 / 20

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| AST 只读语义与单语句约束 | 3 / 6 | 使用 SQLGlot `parse`、根节点和全 AST 遍历，普通多语句、写 CTE、锁和函数路径会被拒绝；但其全局 CTE 名称例外不符合 SQL 词法作用域，见 P0。 |
| 授权对象与 schema 范围 | 0 / 4 | `WITH pg_class AS (SELECT relname FROM pg_class) SELECT relname FROM pg_class LIMIT 3` 由 API 返回 HTTP `200`、`state=succeeded`，并返回 `alembic_version_pkc`、`customers_id_seq`、`customers_pkey` 等 `pg_catalog.pg_class` 元数据行。该对象不在 `analytics` 白名单内。 |
| 数据库身份与双库隔离 | 4 / 4 | `analytics_reader` 可读取 100 个客户，但 `INSERT analytics.customers` 得到 `permission denied`；同一身份连接 `platform`、`platform_writer` 连接 `analytics` 均因 `CONNECT privilege` 失败。初始化脚本及两套迁移只授予对应身份所需权限。 |
| 执行资源限制 | 3 / 3 | 100 万行笛卡尔结果运行后返回 `result_limit_exceeded`；五重客户笛卡尔聚合约 5,020 ms 后返回 `query_timeout`。执行器在只读事务中设置 `statement_timeout`、`lock_timeout` 并读取至多 10,001 行。HTTP 入口上限缺陷在功能与代码质量项扣分。 |
| 固定数据契约与业务口径 | 3 / 3 | 数据集校验通过；迁移建立契约五表、约束和关联；真实数据库计数与 `100/8/50/1000/3000` 一致。 |

未验证：未以 5 个并发长查询动态触发 `BoundedSemaphore` 的第 5 个槽位，也未现场触发 128 列和 4 MiB 响应上限。

### 可运行性与可靠性：20 / 20

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 干净启动与就绪 | 6 / 6 | 独立项目 `dshreviewluna20260814` 从零构建并启动 PostgreSQL、迁移、API、Web；三个常驻服务均为 healthy，API 与 Web 代理的 `/health`、`/ready` 都返回 200。 |
| 迁移与固定数据初始化 | 6 / 6 | 首次迁移日志为 `analytics seed: loaded`；同一项目再次运行迁移命令得到 `analytics seed: already_loaded`。 |
| 并行实例隔离 | 5 / 5 | 第二项目 `dshreviewluna20260814b` 使用 `25180/28087`，第一项目使用 `25179/28086`，同时均 healthy；存在两个不同命名的数据卷，第二 API 读取第一项目运行 ID 返回 404。 |
| 重启与故障可见性 | 3 / 3 | 停止第二项目 PostgreSQL 后，API `/health` 仍为 200，而 `/ready` 返回 503 `service_not_ready`；重启 PostgreSQL 后恢复 ready。随后重启 API，ready 再次恢复 200。 |

未验证：未模拟迁移本身失败、平台审计终态写入失败或长期磁盘空间耗尽。

### 测试与验证证据：11 / 15

| 子项 | 得分 | 新鲜证据 |
| --- | ---: | --- |
| 统一测试入口与可靠断言 | 1.5 / 3 | 带隔离项目环境的 `./dev test` 通过数据校验、API、Vitest 和 Playwright，失败会由 `set -euo pipefail` 产生非零退出。但干净副本中未安装被忽略的 `node_modules` 时，同一入口在 `npm test` 以 127 失败，不能作为干净检出的自包含入口。 |
| SQL 策略单元测试 | 2.5 / 5 | 现有 25 项测试覆盖 AST 允许、写操作、多语句、写 CTE、系统对象、函数、`regclass`、`SELECT INTO` 与过大 `LIMIT`；却未覆盖 CTE 定义内同名系统对象这一作用域边界，遗漏了已复现的 P0。 |
| 双数据库集成测试 | 4 / 4 | API 测试在 Python 3.13 Compose 容器中通过，且现场以真实角色重做了跨库连接、读和写拒绝探针。 |
| 浏览器主链测试 | 3 / 3 | Playwright 2 项通过，覆盖提交允许 SQL 后的结果表和对象越权拒绝展示。 |

未验证：在干净主机先按可文档化步骤安装 npm 依赖和 Playwright 浏览器后的完整 `./dev test`；当前脚本没有提供该准备步骤。

### 代码质量与可维护性：8.5 / 10

| 子项 | 得分 | 证据 |
| --- | ---: | --- |
| 模块边界与职责分离 | 3 / 3 | `policy.py`、`executor.py`、`audit.py`、`service.py`、`readiness.py` 与 API 路由职责清晰；Query Run Service 的协作接口可替换并有针对性测试。 |
| 配置、错误处理与资源清理 | 1.5 / 3 | Compose 项目、端口和资源命名可配置，数据库引擎与执行槽实现合理；但 `api.py:57-62` 仅信任 `Content-Length`，且 `policy.py:121-159` 以全局别名代替词法作用域，未能落实核心治理边界。 |
| 类型、命名、重复控制与可测试性 | 2 / 2 | Python dataclass/Protocol、稳定错误码、TypeScript API 类型和前后端测试接缝明确，未见无依据的重复实现。 |
| 依赖、变更范围与维护负担 | 2 / 2 | 依赖有锁定范围，改动聚焦首轮所需的 Web/API/数据库/文档，没有越界功能。 |

## 技术总分：75 / 90

## 产品文档建议：4 / 5

- 治理、索引与阅读入口：1 / 1。`README.md` 与 `docs/index.md` 提供清晰导航；背景、设计、计划和状态职责分明。
- 设计完整性与可追溯性：2 / 2。设计文档覆盖状态机、双库身份、AST 策略、资源边界、迁移/seed、Compose 和测试接缝，并可追溯至数据契约。
- 计划、运行/测试说明与实现一致性：1 / 2。计划和 README 的启动路径与实际 Compose 实现相符，但运行 `./dev test` 所需的宿主 npm 依赖和 Playwright 浏览器准备未说明，也没有被该入口自行完成。

## 风险标记判断

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | **标记** | `apps/api/src/decisionharbor_api/policy.py:121-122` 收集全查询树的 CTE 名称，`policy.py:150-159` 对任意同名、未限定 schema 的 `Table` 直接跳过对象白名单。非递归 CTE 的定义内不能引用自身，故其中 `pg_class` 实际解析为 `pg_catalog.pg_class`，却被策略当作 CTE。现场 API 成功执行上述 SQL 并返回系统目录元数据，构成用户 SQL 读取未授权系统对象。 |
| P1 基座失败 | 不标记 | 从零启动、两级健康检查、迁移、首次与重复 seed、恢复和第二 Compose 实例均有成功现场证据。 |
| P2 核心闭环缺失 | 不标记 | 浏览器和 API 均证明允许查询与常规拒绝查询两条路径，最小查询工作台可用。 |

风险标记不改变上述技术分数。

## 问题清单（按严重度排序）

1. **[P0，必须修复] 全局 CTE 别名白名单允许读取未授权系统对象。** `apps/api/src/decisionharbor_api/policy.py:121-122` 将所有 CTE 别名汇总，`policy.py:155` 对任一同名且未限定 schema 的表节点跳过白名单。SQL `WITH pg_class AS (SELECT relname FROM pg_class) SELECT relname FROM pg_class LIMIT 3` 中，第一个 `pg_class` 位于非递归 CTE 定义内，解析为 `pg_catalog.pg_class`，不属于 CTE 引用；API 却返回 HTTP `200`、`succeeded` 和系统目录结果。应以 SQLGlot 作用域遍历逐层解析 table source，或在没有完整作用域证明时拒绝该引用；新增该精确回归测试及嵌套、递归 CTE 覆盖。
2. **[P2，必须修复] 分块传输可绕过 128 KiB 的 HTTP 请求上限。** `apps/api/src/decisionharbor_api/api.py:57-62` 只读取 `Content-Length`，未在接收请求主体时累计字节数。现场向 `:28089` 发送无 `Content-Length`、`Transfer-Encoding: chunked` 的约 130 KiB JSON `{"sql":"SELECT 1 AS ok","padding":"..."}`，返回 HTTP `200`、`succeeded`，表明请求被完整解析且额外字段被忽略。应在 ASGI 接收层累计每个 `http.request` body 分块并在超过阈值时终止为 `413`，或在受控反向代理设置等价硬限制；不要仅依赖可缺失的请求头。
3. **[P2，建议修改] 统一测试入口依赖未说明的宿主机状态。** `dev:28-32` 在宿主机直接执行 `npm test` 与 `npm run test:browser`，而 Docker 构建安装的依赖不会写回宿主目录。对只读挂载、排除 `node_modules` 的临时 Node 24 副本执行同一 `npm test`，以 127 退出并输出 `sh: vitest: not found`。Playwright 浏览器安装也未由入口或 README 处理。应将 Web 测试纳入可复现的 Compose/测试镜像，或在正式前置步骤中明确并检查 `npm ci` 与 Playwright 浏览器安装。

## 资源停止情况与最终 Git 状态

- 本次创建并使用了 `dshreviewluna20260814`、`dshreviewluna20260814b` 和补充复核项目 `dshcompareluna20260814c`，以及自动删除的临时 Node 容器。
- 已对这三个命名 Compose 项目分别执行 `docker compose down --remove-orphans`；最终均无运行容器或网络。未停止无关项目。
- 为避免破坏性清理，本次创建的命名数据卷被保留；它们不包含运行中的资源。
- 最终候选 HEAD 为 `1dfb4a4d4d441350b6035ea36eacf414cb9e4023`，`git status --short --branch` 干净，`git diff --check` 无输出。

## 未验证项汇总

- 5 个并发长查询下第 5 个执行槽的 `executor_busy` 行为。
- 128 列上限、4 MiB 响应上限、锁等待超时以及审计终态写入失败的现场行为。
- 迁移失败、数据卷损坏和长期资源耗尽后的恢复行为。
- 在全新主机按文档完成 npm/浏览器安装后的统一测试体验；当前已证实入口本身不负责该准备。
