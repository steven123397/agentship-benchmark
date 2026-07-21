# DecisionHarbor v0.1.0 — Codex 首轮独立评审

## 独立性声明

本报告只依据本次对冻结提交 d14dbba7b2d36f71483853995022b5898f386309 的代码与本次现场运行证据评分。未读取、比较、引用或使用任何其他候选的工作树、分支、运行记录、评审材料、分数、问题或结论；也未读取本候选的 grok-review.md、review-summary.md、scorecard.md。未因 Agent、模型、耗时、token 或既往印象调整评分。

候选源码、候选分支、baseline、评分规范与其他归档文件均未修改；本次唯一写入为本报告。

## 审查对象、环境与最终 Git 状态

- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/kimi-kimi-k3-thinking
- 分支：v0.1.0/kimicode-kimi-k3-thinking
- 审查 commit：d14dbba7b2d36f71483853995022b5898f386309
- baseline：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- Docker：29.1.3
- Docker Compose：v2.40.3

开始前和结束前均执行：

    git rev-parse HEAD
    git status --short --branch
    git diff --check

两次均得到指定 commit；status 仅为：

    ## v0.1.0/kimicode-kimi-k3-thinking...origin/v0.1.0/kimicode-kimi-k3-thinking

工作树 git diff --check 无输出。候选相对 baseline 的 git diff --check 也无输出。

## 实际执行命令与复现结果

| 范围 | 实际命令或方式 | 本次证据 |
| --- | --- | --- |
| 数据集 | PYTHONDONTWRITEBYTECODE=1 python3 datasets/sales-analytics-v1/validate.py | 通过。|
| 原生统一测试入口 | env DH_PROJECT_NAME=dhkimreviewa DH_API_PORT=18180 DH_WEB_PORT=15183 scripts/test.sh | SQL 策略单测 39 passed；之后 Web Docker 构建停在 node:24-alpine 元数据获取，未形成完整通过证据。|
| API、迁移、seed 启动 | docker compose up -d db migrate api，项目 dhkimreviewa | 初始迁移日志显示 platform、analytics 迁移、只读授权和五表 seed 均成功；health=200，ready=200。|
| API 单测 | 统一入口实际执行 | 39 passed in 0.11s。|
| 双库集成 | docker compose run --rm --no-deps --entrypoint python migrate -m pytest tests/integration -q | 15 passed, 1 warning in 5.79s。|
| 前端单元 | 候选 Web 源码复制到临时容器文件系统后 npm run test:run | Vitest 6 passed。候选目录未写入。|
| 浏览器主链 | 候选 e2e Dockerfile 构建后，以候选 Playwright 镜像访问临时只读 Vite/API 网络 | 3 passed in 3.7s：成功结果、执行中状态、拒绝展示。原生 Nginx Web Compose 路径另列未验证。|
| 允许、拒绝、审计 | 对 API 18180 发起 POST 和 GET 请求 | 允许聚合、DELETE 拒绝、直接系统表拒绝、行数截断、超时和审计读取均获得现场响应。|
| 资源限制 | 默认实例与第二实例分别查询大结果集、pg_sleep | 默认 1000 行截断和超时生效；第二实例 MAX_ROWS=2、STATEMENT_TIMEOUT_MS=1000 时返回 2 行 truncated=true，pg_sleep(2) 于约 1018 ms 失败为 QUERY_TIMEOUT。|
| 重启、故障可见性 | docker compose restart api；只停止本评审 db 再恢复 | restart 后第 2 次轮询 ready 成功；db 停止时 health=200、ready=503；恢复 db 后第 2 次轮询 ready。|
| 并行隔离 | 同时运行 dhkimreviewa 与 dhkimreviewb | 两者各自 ready；网络分别为 dhkimreviewa_default、dhkimreviewb_default，卷分别为同名前缀 pgdata；A 的审计数为 22，B 为 2。|

完整 Web Compose 构建未取得新鲜成功证据。候选原生测试入口与单独 Web build 都停在 Docker Hub 的 node:24-alpine 元数据阶段；本机对 registry-1.docker.io 的独立连接检查为连接超时。该外部环境故障不能作为候选 Web 逻辑失败计分，因此完整 Web Compose 冷启动与原样统一测试完成状态均标为未验证。

浏览器行为仍获得了新鲜证据：候选 e2e Dockerfile 成功基于 mcr.microsoft.com/playwright:v1.61.1-noble 构建；候选 Web 源码仅复制到临时容器中由 Vite 提供，候选 Playwright 三条用例真实驱动浏览器访问 API。临时 Vite 不是候选 Nginx Web 服务，故不替代上段未验证项。

## 技术评分：68.0 / 90

评分按规范的未通过 0、部分通过 50%、完全通过满分给出。P0/P1/P2 封顶不改变以下技术原始分。

### 1. 功能与外部契约：25.0 / 25

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 查询运行 API 生命周期 | 8.0 / 8 | 成功、拒绝、超时、行数截断均生成 UUID；GET 可读回相同状态和原始 SQL。例如状态聚合记录 20b900db-591e-4ccf-827c-3eb7775c59a8 的 POST/GET 均为 succeeded。|
| 允许查询结果正确性 | 7.0 / 7 | 客户区域聚合返回五组各 20；订单状态聚合返回 cancelled=100、confirmed=720、pending=100、refunded=80，与固定契约一致。|
| 拒绝与执行失败语义 | 5.0 / 5 | DELETE 为 rejected/POLICY_NON_QUERY_STATEMENT；直接 pg_catalog 为 rejected/POLICY_UNAUTHORIZED_OBJECT；资源超限为 failed/QUERY_TIMEOUT；均有记录标识与可读错误。|
| 最小查询工作台 | 5.0 / 5 | 实际浏览器用例覆盖输入、成功表格、执行中状态和拒绝面板；前端 Vitest 还覆盖成功、截断、拒绝、失败、等待、请求层失败。|

### 2. SQL 治理与数据正确性：11.5 / 20

| 子项 | 分数 | 证据与结论 |
| --- | ---: | --- |
| AST 只读语义与单语句约束 | 3.0 / 6 | 39 个策略单测和现场请求证明 DML、多语句、SELECT INTO、直接目录表被拒绝，且实现使用 SQLGlot；但 CTE 作用域处理与函数型二次 SQL 均可绕过 AST 对象治理，不能完全通过。|
| 授权对象与 schema 范围 | 0.0 / 4 | P0 现场复现两条未授权系统对象读取路径，见问题清单。|
| 数据库身份与双库隔离 | 4.0 / 4 | API 的 SELECT current_user,current_database 返回 analytics_readonly,analytics；analytics_readonly 可读 analytics 五表但 INSERT 被拒绝，连接 platform 被拒绝；platform_app 连接 analytics 亦被拒绝。has_database_privilege 对两条跨库 CONNECT 均为 false。|
| 执行资源限制 | 3.0 / 3 | 执行器设置 statement_timeout 并流式取上限加一行；默认实例 1000 行截断，低阈值实例 2 行截断与约 1 秒超时均现场成立。|
| 固定数据契约与业务口径 | 1.5 / 3 | CSV 校验、五表行数、关系和订单状态分布均正确；但 orders.currency 在迁移中是 varchar(3)，契约是 char(3)，并且迁移未对 CNY、状态集合、discount_rate 0..1、价格关系建立数据库 CHECK 约束。|

### 3. 可运行性与可靠性：14.5 / 20

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 干净环境启动与就绪 | 3.0 / 6 | db/migrate/api 的原生 Compose 链路、health 与 ready 已现场通过。完整受支持命令需要的 Web Docker Hub 基础镜像受本机网络超时阻断，不能按完整三服务成功处理。|
| 迁移与固定数据初始化 | 6.0 / 6 | 初始迁移/授权/seed 日志成功；再次运行 migrate 后五表计数为 100、8、50、1000、3000；集成测试的重复 seed 也通过。固定 fixture 由 seed 独占，截断重载有文档化设计理由。|
| 并行实例隔离 | 2.5 / 5 | 两个 db/migrate/api 实例并行并具有独立容器、网络、卷和审计数据；完整三服务并行因 Web 镜像外部阻断未验证。|
| 重启与故障可见性 | 3.0 / 3 | API restart 后恢复；依赖 db 不可达时 health/ready 正确分离，恢复后 ready 恢复。|

### 4. 测试与验证证据：9.5 / 15

| 子项 | 分数 | 证据与未通过原因 |
| --- | ---: | --- |
| 统一测试入口与可靠断言 | 1.5 / 3 | scripts/test.sh 存在并使用 set -euo pipefail；本次实际完成其第一阶段 39 项策略测试，但前端镜像外部构建超时，统一入口未完成。|
| SQL 策略单元测试 | 2.5 / 5 | 39 项通过，覆盖允许查询、DML/DDL、多语句、修改型 CTE、对象范围与普通 CTE 遮蔽；没有测试显式 schema 下同名 CTE 或函数参数中的二次 SQL，遗漏 P0。|
| 双数据库集成测试 | 4.0 / 4 | 15 项真实 PostgreSQL 集成测试通过，覆盖双身份跨库拒绝、只读写入/DDL 拒绝、API、超时、截断、ready、seed 幂等。|
| 浏览器主链测试 | 1.5 / 3 | 候选 Playwright 三条用例在真实浏览器、候选 API 和候选前端源码上通过；生产 Nginx Web Compose 服务因 Docker Hub 超时未取得新鲜证据。|

### 5. 代码质量与可维护性：7.5 / 10

| 子项 | 分数 | 证据与原因 |
| --- | ---: | --- |
| 模块边界与职责分离 | 3.0 / 3 | policy、executor、audit、router、迁移、seed、Web 与 e2e 分层明确；策略为纯函数，数据库会话和执行身份分离。|
| 配置、错误处理与资源清理 | 1.5 / 3 | Compose 配置、事务、超时和资源清理整体清楚；但 executor.py:91-94 将数据库 primary error 直接返回，现场未知列查询泄露列名。安全关键策略也缺函数与正确 CTE 作用域防护。|
| 类型、命名、重复控制与可测试性 | 2.0 / 2 | Pydantic、dataclass、SQLAlchemy 模型、依赖配置和测试接缝清楚，前后端测试可独立运行。|
| 依赖、变更范围与维护负担 | 1.0 / 2 | Web 有 package-lock 且 Dockerfile 使用 npm ci；但 API requirements 仅是范围约束，且 analytics_readonly 的默认权限被扩展为未来 analytics 表全部 SELECT，维护时容易偏离“五表”边界。|

## 产品文档建议：3.0 / 5

不含视觉评分。

| 子项 | 建议 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1.0 / 1 | README、docs/index.md、background/design/plan/status 分层及 AGENTS 规则完整。|
| 设计完整性与可追溯性 | 1.0 / 2 | 设计对双库、状态机、迁移、资源限制与测试接缝表述清楚；但 query-governance 的 CTE 白名单说明与实现的作用域漏洞不一致，且将函数限制延后与产品要求的系统对象拒绝存在风险。|
| 计划、运行/测试说明与实现一致性 | 1.0 / 2 | scripts/run.sh、scripts/test.sh 与文档有明确入口；但原生全栈冷启动本次未能验证，且数据类型/业务约束与 contract 的严格对齐主张不完全一致。|

未评价视觉质量，也未计算最终 100 分或任何技术平均分。

## P0/P1/P2 封顶判断

| 级别 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | 命中 | 用户 SQL 能读取 pg_catalog 系统对象和 pg_user 系统角色信息，绕过 AST 对象白名单。符合“访问系统或未授权对象”以及“绕过 AST 治理”；汇总时适用 P0 总质量分上限 39。本报告不计算最终质量分。|
| P1 基座失败 | 未单独命中 | db/migrate/api、health、ready、迁移、固定 seed 在本次实例均成立。Web 完整冷启动被已验证的 Docker Registry 外部网络故障阻断，故标未验证而不据此判为 P1。|
| P2 核心闭环缺失 | 未命中 | 允许查询、拒绝查询、审计读取和浏览器工作台均有本次运行证据；生产 Web Compose 路径仍单列未验证。|

## 问题清单（按严重度）

### P0：CTE 同名遮蔽可读取显式系统 schema

- 根因：api/app/policy.py:94-106 将所有 CTE alias 收集为全局名称集合，并在检查 catalog/schema 之前仅按表名跳过引用。显式 pg_catalog.pg_class 在 SQL 语义上不受 CTE pg_class 遮蔽，但实现仍把它当作 CTE。
- 最小复现：

      WITH pg_class AS (SELECT 1)
      SELECT relname FROM pg_catalog.pg_class LIMIT 3

- 现场结果：直接 SELECT pg_catalog.pg_class 被 rejected/POLICY_UNAUTHORIZED_OBJECT；上述查询却返回 succeeded，行中含 alembic_version、alembic_version_pkc、customers_id_seq。
- 影响：用户可访问系统目录，直接命中 P0 安全失败。

### P0：未限制函数使字符串内二次 SQL 绕过对象白名单

- 根因：policy.py:99-124 仅检查 SQLGlot Table 节点；函数调用及其字符串参数没有治理。设计文档中把函数级限制延后，但产品要求禁止系统目录和绕过对象范围。
- 最小复现：

      SELECT query_to_xml(
        'SELECT usename FROM pg_user ORDER BY usename', false, false, ''
      )::text AS leaked

- 现场结果：HTTP 200/succeeded，返回 analytics_owner、analytics_readonly、platform_app、postgres 四个角色。
- 影响：即使数据库身份正确隔离，应用层白名单仍可被用于系统信息枚举。

### P2：固定数据 schema 未严格兑现契约类型与业务约束

- a0001_sales_tables.py:57-65 将 orders.currency 建为 String(3)，实际 information_schema 为 character varying(3)，而 contract.json 指定 char(3)。
- 迁移只建立非空、主外键、唯一约束；未建立货币 CNY、订单状态集合、discount_rate 范围、成本不高于标价等契约业务约束。
- 当前 fixture 经校验正确，且只读身份无写入权；问题主要影响未来迁移/seed 之外的数据正确性和“严格对齐”可维护性。

### P2：数据库错误摘要泄露内部对象细节

- executor.py:91-94 将 psycopg 的 primary message 拼进对外错误。
- 现场提交 SELECT missing_column FROM customers 返回 EXECUTION_ERROR 及 column "missing_column" does not exist，暴露数据库列名。建议对外保留稳定错误码与通用摘要，将详细信息仅记录服务端日志。

### P2：分析只读角色默认获所有未来 analytics 表 SELECT

- migrate.py:19-25 同时执行 GRANT SELECT ON ALL TABLES IN SCHEMA analytics 和 ALTER DEFAULT PRIVILEGES ... GRANT SELECT ON TABLES。
- 当前 schema 只有五张契约业务表，故本次直接角色隔离测试通过；但未来在 analytics 新增非业务表会自动授予查询身份，和“五张表”最小权限边界不一致。

## 未验证项

1. 候选原生 Web Compose 镜像在可访问 Docker Hub 的干净环境中的完整冷启动，包括 nginx 静态生产构建和反向代理。
2. 原样 scripts/test.sh 全流程的最终通过状态；本次确实运行但 Web Docker Hub 基础镜像获取超时，只有策略阶段可确认通过。
3. 完整三服务的并行 Compose 隔离；本次已验证 db/migrate/api 双实例隔离，Web 服务因同一外部镜像阻断未验证。

## Compose 资源停止情况

本次仅创建并清理：

- dhkimreviewa：API 18180、db/migrate/api 容器、默认网络及 dhkimreviewa_pgdata；
- dhkimreviewb：API 18181、db/migrate/api 容器、默认网络及 dhkimreviewb_pgdata；
- 临时前端容器 dhkimreviewa-vite；
- 临时 e2e 调试容器。

已精确执行 docker compose down --volumes --remove-orphans，并停止删除临时容器。最终按项目名检查，没有上述容器、网络或卷残留；未停止或修改无关 Docker 项目。
