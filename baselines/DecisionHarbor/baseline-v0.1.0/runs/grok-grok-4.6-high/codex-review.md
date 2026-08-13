# DecisionHarbor v0.1.0 Codex 首轮独立评审

## 独立性声明

本报告只依据本次对冻结候选工作树的代码阅读和现场运行证据形成。评审期间未读取、比较或引用任何其他候选的工作树、分支、运行记录、评审材料、分数或结论；未读取本候选的 `grok-review.md`、`review-summary.md`、`scorecard.md`。未修改候选源码、候选分支、baseline、评分规范或其他归档文件，也未执行 `git add`、`commit`、`push` 或创建 PR。本次唯一写入为本文件。

## 冻结、环境与边界核验

| 项目 | 结果 |
| --- | --- |
| 候选工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high` |
| 候选分支 | `v0.1.0/grokbuild-grok-4.6-high` |
| baseline commit | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| `metadata.json` 冻结条件 | `completion.coordinatorFrozen=true`；`candidate.resultCommit=cd8b766fa6242cf1bdb30304af6f453af6331af7` |
| 评审 commit | `cd8b766fa6242cf1bdb30304af6f453af6331af7` |
| 开始时 Git | `git rev-parse HEAD` 等于评审 commit；`git status --short --branch` 仅显示跟踪分支行，无未提交改动 |
| 主机环境 | WSL2 Linux `6.18.33.2-microsoft-standard-WSL2`；Docker Engine `29.1.3`；宿主 Python `3.10.12`；Node `v24.16.0` |

已阅读 AgentShip 规则、评分规范、当前候选 `metadata.json`、`reproduction.md`，以及候选的 `AGENTS.md`、`README.md`、`docs/index.md`、`docs/background/`、`docs/design/`、`docs/plan/`。候选根目录无 `.codegraph/`，因此未使用 CodeGraph。

## 实际执行命令与运行证据

下列命令均在候选工作树执行，除本报告写入外均为只读验证或本次评审的可恢复 Compose 操作。

| 覆盖项 | 实际命令或探针 | 新鲜结果 |
| --- | --- | --- |
| 冻结与清洁度 | `git rev-parse HEAD`；`git status --short --branch` | HEAD 为 `cd8b766...`，开始时无改动。 |
| 静态审查 | `rg`、`sed`、`nl -ba` 读取 API、迁移、Compose、测试、Web 和正式文档 | 确认 AST 策略、三身份、两套 Alembic、seed、资源上限、测试入口与工作台实现。 |
| 数据契约 | `python3 datasets/sales-analytics-v1/validate.py` | 通过：固定夹具、清单哈希、关系、业务边界和确定性重生成均验证成功。 |
| 统一启动 | `./scripts/up.sh` | 成功构建并启动 PostgreSQL、API、Web，脚本输出 `DecisionHarbor is ready on http://127.0.0.1:55173`。 |
| 统一测试入口 | `./scripts/test.sh` | 命令成功；其中 API 测试输出 `25 passed`。 |
| 前端单测 | `docker compose --env-file .env --profile test run --rm --build web-test` | Vitest `3 passed`。 |
| 浏览器主链 | `docker compose --env-file .env --profile test run --rm --build e2e` | Playwright 在真实 `web`、`api`、`postgres` 容器上 `2 passed`：允许 SQL 的执行中与结果表、拒绝 SQL 的错误码。 |
| 初始健康与就绪 | `curl http://127.0.0.1:58000/health`；`curl http://127.0.0.1:58000/ready`；Web 根路径 | 分别为 `200 {"status":"ok"}`、`200 {"status":"ready"}`、HTTP `200`；三服务 Docker healthcheck 均 healthy。 |
| 允许 SQL | API `POST /api/v1/query-runs`：确认订单聚合；含 CTE 的按地区聚合 | 都为 `succeeded`。前者结果为 `720`，后者返回五个地区各 `20` 位客户。 |
| 拒绝 SQL | 同一 API：`DELETE FROM orders`、多语句、`SELECT ... FROM pg_catalog.pg_class` | 依次得到 `POLICY_DENIED`、`QUERY_INVALID`、`POLICY_DENIED`，均未产生查询结果。 |
| 行数限制 | API：`SELECT id FROM order_items ORDER BY id` | `failed`，错误码 `RESULT_LIMIT_EXCEEDED`，未返回截断行集。 |
| 超时限制 | 一次性 API 容器，`QUERY_STATEMENT_TIMEOUT_MS=100`，直接以 `QueryExecutor` 执行 `SELECT pg_sleep(0.3)` | 映射为 `EXECUTION_TIMEOUT`。这是执行器资源上限验证；该函数仍被用户 SQL 策略拒绝。 |
| 三身份与双库 | `psql` 分别以 `platform_app`、`analytics_owner`、`analytics_reader` 连接；尝试跨库连接和 reader `INSERT` | reader 实际身份为 `analytics_reader,on`，客户数为 `100`；平台、所有者、reader 的三项跨库连接均被拒绝；reader 写入被拒绝。 |
| 故障与恢复 | `docker compose ... stop postgres` 后探测 `/ready`；启动 PostgreSQL 后 `restart api` | PostgreSQL 停止时 `/ready` 仍错误返回 `200 {"status":"ready"}`；数据库恢复后 API 在第 2 次轮询恢复就绪。 |
| 并行 Compose | 主项目运行时，以 `-p dhgrok46reviewparallel` 及 API `58001`、Web `55174` 执行 `up --build -d postgres api web` | 两个项目各自的三服务同时 healthy；并行项目返回 `succeeded` 且 seed 后客户数为 `100`。项目名隔离了容器、网络和卷。 |
| 系统目录绕过 | API：`SELECT CAST('pg_catalog.pg_class' AS regclass) AS relation` | 策略返回 `succeeded`，结果为 `[["pg_class"]]`。这是 P0 的可复核现场证据。 |

首次 API 探针使用了本机不存在的 `jq`，在请求写出前即失败；随后已使用 Node 完成 JSON 编码和字段归纳，并完整重跑所有 API 探针。表中的 API 结果均来自后一次成功执行。

## 技术评分：73.5 / 90

评分仅包含指定的五个技术维度。每个子项按评分规范的 0 / 半分 / 满分档位给分。

### 功能与外部契约：22.5 / 25

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 查询运行生命周期与审计 | 8 / 8 | `QueryRunService` 先记录 `running`，再落终态；通过的集成测试验证成功查询在 `platform.query_runs` 留下审计事实。 |
| 允许查询与结果表示 | 7 / 7 | 允许聚合与 CTE 均返回正确列、行和行数；数值序列化由 API 测试覆盖。 |
| 拒绝与执行失败 | 2.5 / 5 | 写入、多语句、直接系统目录和超行数均按稳定码处理，但 P0 显示系统目录对象可经 `regclass` cast 绕过策略并成功执行。 |
| 查询工作台 | 5 / 5 | 真实浏览器用例通过：输入、执行中、结果表以及拒绝错误码均可用。 |

### SQL 治理与数据正确性：13 / 20

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| AST 只读与多语句控制 | 3 / 6 | `sqlglot` 单语句 AST 检查、写语句和锁定语句拒绝均有效；但 `api/app/policy.py:222-224` 无条件放行 `exp.Cast`，造成可执行的对象访问绕过。 |
| 对象、schema 与系统目录范围 | 0 / 4 | 直接 `pg_catalog.pg_class` 被拒绝，但 cast 到 `regclass` 成功解析系统目录对象，违反「系统目录或未授权对象必须拒绝」的契约。 |
| 双库身份隔离 | 4 / 4 | 现场验证平台、所有者、reader 的跨库连接均失败；reader 处于只读事务且写入失败；用户 SQL 执行器绑定 reader engine。 |
| 资源限制 | 3 / 3 | `max_rows + 1` 实测触发 `RESULT_LIMIT_EXCEEDED`；100 ms `pg_sleep` 执行器探针返回 `EXECUTION_TIMEOUT`。 |
| 数据契约与业务正确性 | 3 / 3 | 数据集校验通过；迁移包含五表、主键、唯一键、外键和定点金额列；启动及并行实例均装入固定数据。 |

### 可运行性与可靠性：17 / 20

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 启动、健康与就绪 | 3 / 6 | `up.sh`、初始 `/health`、`/ready` 和服务 healthcheck 均成功；但停止 PostgreSQL 后 `/ready` 仍报 200，不能表示当前依赖可用性。 |
| 迁移与幂等 seed | 6 / 6 | 启动路径依次执行两库迁移、seed、验证；集成测试重复 seed 通过；并行新卷也 seed 为 100 位客户。 |
| 并行 Compose 隔离 | 5 / 5 | 两个不同项目名和宿主端口的三服务实例同时 healthy，使用独立网络和命名卷。 |
| 重启与故障恢复 | 3 / 3 | PostgreSQL 恢复后重启 API，API 在第 2 次轮询恢复 ready。该分数不抵消上述 readiness 误报。 |

### 测试与验证证据：12.5 / 15

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 统一测试入口 | 3 / 3 | `./scripts/test.sh` 成功运行，API 部分为 25 项通过；前端和浏览器测试又以各自 Compose test 服务独立复现。 |
| SQL 策略测试 | 2.5 / 5 | 覆盖允许 SQL、CTE、集合运算、写操作、多语句、系统目录、未允许函数等，但没有阻止或回归 `CAST(... AS regclass)` 绕过。 |
| 双库集成测试 | 4 / 4 | 代码用例和本次 `psql` 探针都验证三身份隔离、reader 无写权限、成功查询审计及幂等 seed。 |
| 浏览器主链 | 3 / 3 | 真实容器中的 Playwright 2 / 2 通过。 |

### 代码质量与可维护性：8.5 / 10

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 模块边界 | 3 / 3 | 策略、执行器、运行服务、启动 bootstrap、迁移和 Web 展示职责分离明确。 |
| 配置、错误与清理 | 1.5 / 3 | 环境化端口/项目名、稳定错误码、执行器异常映射和 Compose healthcheck 清晰；但 readiness 只有启动后的进程内布尔值，不能反映依赖状态。 |
| 类型、事务与数据处理 | 2 / 2 | Pydantic 响应模型、SQLAlchemy 模型和事务化 seed/审计实现清晰；数值和时间 JSON 转换有明确规则。 |
| 依赖与维护性 | 2 / 2 | Python 依赖精确固定，Web 使用 lockfile 与 `npm ci`，统一脚本覆盖启动和测试。 |

## 产品文档建议：5 / 5

README 提供最小启动和测试入口，`docs/index.md` 给出文档职责与阅读顺序；背景、设计、计划和数据集契约之间链接完整。设计文档明确外部 HTTP 契约、SQL 边界、两库身份、seed、并行 Compose、错误码和测试接缝，并与本次可验证的主要实现对应。`“两库可连且迁移、seed 已完成”` 的 readiness 文档契约是清楚的；其与运行时 P1 的不一致属于实现缺陷，不扣减文档建议分。

## P0 / P1 / P2 风险标记

评分规范将风险标记与技术分数分开，本报告不计算最终 100 分、平均分或额外自动封顶。

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 | 有 | API 允许并成功执行 `SELECT CAST('pg_catalog.pg_class' AS regclass) AS relation`，返回 `pg_class`。代码中 `api/app/policy.py:222-224` 对所有 `exp.Cast` 直接返回，没有验证目标类型。该行为违反 `docs/background/product-requirements.md:63-71` 对系统目录和未授权对象访问的禁止。 |
| P1 | 有 | 停止本项目 PostgreSQL 后，`GET /ready` 仍为 `200 {"status":"ready"}`。`api/app/main.py:21,49,74-78` 仅维护启动后布尔值，未重新检查平台库或 analytics reader；这违反 `docs/background/product-requirements.md:79-80` 和 `docs/design/governed-query-path.md:223-225` 的就绪契约。 |
| P2 | 无单独触发 | 允许 SQL、拒绝 SQL、执行失败和工作台浏览器主链均有本次新鲜运行证据。P0 和 P1 仍应在合入或发布前修复。 |

## 问题清单（按严重度）

### P0：`CAST` 白名单绕过对象范围，用户 SQL 可访问系统目录对象

- 位置：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high/api/app/policy.py:222-224`。
- 触发：向 `POST /api/v1/query-runs` 提交 `SELECT CAST('pg_catalog.pg_class' AS regclass) AS relation`。
- 现场结果：响应为 `succeeded`，结果列 `relation` 的值为 `pg_class`；对照的 `SELECT relname FROM pg_catalog.pg_class LIMIT 1` 被 `POLICY_DENIED`。
- 影响：解析器 AST 中的表节点检查无法覆盖通过 PostgreSQL reg* 类型转换进行的对象解析，导致「仅 analytics 五张业务表」和「拒绝系统目录」两个核心 SQL 治理承诺失效。只读数据库身份不能替代对象范围策略。
- 最小修复方向：不要无条件允许 `exp.Cast`。显式允许有限、安全的 cast 目标类型，并拒绝会解析对象标识符的 `regclass`、`regproc`、`regprocedure`、`regtype` 等类型及等价语法；为 `CAST` 和 `::` 两种语法增加 API 级回归测试。

### P1：依赖失效后 `/ready` 持续返回成功

- 位置：`/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.6-high/api/app/main.py:21,49,74-78`，与启动期一次性检查 `api/app/bootstrap.py:107-120` 的组合。
- 触发：`docker compose --env-file .env stop postgres`，等待 2 秒后请求 `GET http://127.0.0.1:58000/ready`。
- 现场结果：PostgreSQL 已停止，而响应仍为 HTTP 200 和 `{"status":"ready"}`；恢复数据库并重启 API 后才重新完成启动期检查。
- 影响：反向代理或编排器会把无法访问平台库和 analytics 的实例继续作为可接收流量的实例，违反 `/ready` 的外部定义。
- 最小修复方向：`/ready` 使用有界、低开销的实际平台库和 analytics reader 探针，探针失败时返回 503；补充「数据库在启动后中断」的集成回归测试，并确保查询端点对该基础设施错误有受控响应。

## 未验证项

本任务规定的启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链和可行的并行 Compose 隔离均已取得本次新鲜证据，没有将未验证项目按通过处理。

未扩展到评分范围外的事项包括生产部署、认证、多租户、外部网络暴露和视觉回归；这些不是本次的未验证通过项，也未计入分数。

## Compose 资源停止与最终 Git 状态

本次评审启动了两个 Compose 项目：主项目 `dh-grok-46-high` 与临时并行项目 `dhgrok46reviewparallel`。

- 已执行 `docker compose --env-file .env -p dhgrok46reviewparallel down --volumes --remove-orphans`，删除本次创建的临时容器、网络和卷。
- 已执行 `docker compose --env-file .env down --remove-orphans`，仅停止并删除本次主项目的容器和网络，未使用 `--volumes`，因此不删除主项目既有命名卷。
- 两个项目执行 `ps --all` 后均为空；未操作无关 Compose 项目。
- 结束时 `git status --short --branch` 仅为分支跟踪行：`## v0.1.0/grokbuild-grok-4.6-high...origin/v0.1.0/grokbuild-grok-4.6-high`；`git diff --check` 无输出。
