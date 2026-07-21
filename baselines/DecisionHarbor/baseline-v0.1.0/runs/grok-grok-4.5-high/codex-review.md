# DecisionHarbor v0.1.0 — Codex 首轮独立评审

## 独立性与范围

本报告仅依据本次对冻结候选 8bbe8de2875d32804067d8418fb5bc6fc8cb431c 的代码审查和现场运行证据形成。未读取或使用任何其他候选的工作树、分支、运行记录、评审报告、分数、问题清单或结论；也未读取本候选的 grok-review.md、review-summary.md、scorecard.md。未因 Agent、模型、耗时、token 或既往印象调整评分。

候选源码、分支、baseline、评分规范和其他归档文件均未修改；本次唯一写入为本报告。

## 审查对象、环境与 Git 状态

- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.5-high
- 审查 commit：8bbe8de2875d32804067d8418fb5bc6fc8cb431c
- baseline：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- Docker：29.1.3；Docker Compose：v2.40.3

开始前执行：

    git rev-parse HEAD
    # 8bbe8de2875d32804067d8418fb5bc6fc8cb431c
    git status --short --branch
    # ## v0.1.0/grokbuild-grok-4.5-high...origin/v0.1.0/grokbuild-grok-4.5-high

结束前再次执行同一组命令及 git diff --check；HEAD 未变、status 仍只显示上述分支头、工作树 git diff --check 无输出。候选相对 baseline 的 git diff --check 发现 10 处文档尾随空白（docs/design/README.md、docs/plan/README.md、docs/status/README.md），不属于本次评审产生的工作树改动。

## 实际执行与复现结果

| 检查 | 实际命令或方式 | 新鲜证据 |
| --- | --- | --- |
| 数据集 | PYTHONDONTWRITEBYTECODE=1 python3 datasets/sales-analytics-v1/validate.py | 通过。|
| 启动、迁移与 seed | docker compose --project-name dhg45reviewa up -d db api；API 映射 18080 | 成功；health 为 200，ready 为 200，返回 platform_query_runs=true 与 sales-analytics@1.0.0。|
| API 单测 | docker compose ... exec -T api pytest tests/unit -q | 18 passed in 0.06s。|
| 双库集成 | docker compose ... exec -T api pytest tests/integration -q，并显式注入 db DSN | 8 passed in 0.67s。|
| 允许与拒绝 SQL | 对 POST /api/v1/query-runs 现场请求 | 聚合成功；DELETE、pg_catalog.pg_tables、analytics_seed_meta 的直接引用和双语句均拒绝并生成审计记录。|
| 资源限制 | API 执行 SELECT id FROM order_items ORDER BY id；SELECT pg_sleep(6) | 分别为 EXECUTION_ROW_LIMIT 与约 5015 ms 后的 EXECUTION_TIMEOUT。|
| 重启与就绪 | docker compose ... restart api；随后只停止本评审的 db | API 重启后第 2 次轮询 ready 成功；数据库停止时 health=200、ready=503，恢复后第 2 次轮询重新 ready。|
| 并行 Compose | 同时启动 dhg45reviewa（API 18080）和 dhg45reviewb（API 18081） | 两者各自 ready；网络和 pgdata 卷均按项目名前缀隔离；A 的 platform.query_runs=16，B 为 0。|
| 浏览器主链 | 临时只读源码挂载的 Vite 容器提供 127.0.0.1:15173，再运行 Playwright，产物定向 /dev/shm | 两条用例通过：允许聚合显示成功、写 SQL 显示拒绝，2 passed in 1.3s。|

完整 docker compose up -d --build 的 Web 镜像路径本次没有完成：拉取 node:24-bookworm 元数据时返回 failed to fetch anonymous token，auth.docker.io 连接 i/o timeout；独立检查 registry-1.docker.io 也超时。这是本机 Registry 连通性证据，不能作为候选 Web 逻辑失败计分。API/DB 已用候选镜像完成复现，浏览器测试验证了前端源码到真实 API 的链路；但候选 Nginx Web Compose 镜像的完整冷启动仍为未验证。

未原样运行 scripts/test.sh：其会向候选工作树写入或刷新 apps/web/node_modules、Playwright 浏览器和测试产物（scripts/test.sh:36-41），违反本次“只可写评审报告”的边界。其数据集、API 单测、集成测和浏览器组成部分已以上述隔离方式分别复现，不等同于统一入口已完整通过。

## 技术评分：61.0 / 90

评分按规范的未通过 0、部分通过 50%、完全通过满分规则给出。P0/P1/P2 封顶不改变下列技术原始分。

### 1. 功能与外部契约：25.0 / 25

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 查询运行 API 生命周期 | 8.0 / 8 | 成功、拒绝、行数限制和超时请求均获得 UUID；后续 GET 返回相符的 sql_text、状态、行数与错误。允许查询 ID 为 75bbc232-803e-4289-a37e-4e2f83541cae，拒绝 ID 为 964dfe17-4d75-41a5-9358-f4322720bcdf。|
| 允许查询结果正确性 | 7.0 / 7 | 聚合连接查询返回五区域订单数：Central 198、East 214、North 203、South 197、West 188；同时返回列、行、row_count=5 与耗时。|
| 拒绝与执行失败语义 | 5.0 / 5 | DELETE 为 rejected/POLICY_FORBIDDEN_STATEMENT；目录表、未授权表、双语句均有稳定错误码；行数与超时为 failed 且带可读错误和记录 ID。|
| 最小查询工作台 | 5.0 / 5 | 真实浏览器用例验证输入、提交、成功结果和拒绝展示；执行中状态实现位于 apps/web/src/App.tsx:60-64。|

### 2. SQL 治理与数据正确性：8.0 / 20

| 子项 | 分数 | 证据与未通过原因 |
| --- | ---: | --- |
| AST 只读语义与单语句约束 | 0.0 / 6 | 常规 DML、多语句、SELECT INTO 和直接目录表被拒绝，且单测通过；但 P0 复现表明函数参数内的二次 SQL 完全不受 AST 治理。SqlPolicy._check_objects 仅遍历 exp.Table，见 apps/api/app/policy.py:172-213。|
| 授权对象与 schema 范围 | 0.0 / 4 | 直接 SELECT analytics_seed_meta 被拒绝；用户却可调用 query_to_xml 读取该非白名单表，也可读取 pg_user 系统角色信息，均 HTTP 200/succeeded。|
| 数据库身份与双库隔离 | 2.0 / 4 | API 现场 SELECT current_user,current_database 返回 analytics_readonly,analytics；只读身份直接 DELETE customers 被数据库拒绝。可是 platform_app 可连接 analytics，analytics_readonly 可连接 platform；两条 psql 连接均成功，has_database_privilege 均为 true。直接跨库业务表读取仍被表权限拒绝，故部分通过。|
| 执行资源限制 | 3.0 / 3 | 执行器设置只读事务和本地超时，见 apps/api/app/executor.py:49-55；现场行数与超时上限均真实生效。|
| 固定数据契约与业务口径 | 3.0 / 3 | 数据集校验通过；迁移具备五张业务表及外键；seed/restart 后计数为 100、8、50、1000、3000。|

### 3. 可运行性与可靠性：11.5 / 20

| 子项 | 分数 | 证据与未验证项 |
| --- | ---: | --- |
| 干净环境启动与就绪 | 3.0 / 6 | API/DB Compose 启动、健康与就绪通过；完整支持命令的三服务冷构建被本机 Docker Registry 超时阻断，Web Compose 镜像无新鲜成功证据。|
| 迁移与固定数据初始化 | 3.0 / 6 | 两逻辑库、迁移、seed 和重启后的契约行数均成立；但 seed_analytics.py:34-37 每次 seed 无条件 TRUNCATE 五张表和 seed 元数据，未证明非破坏性重复。|
| 并行实例隔离 | 2.5 / 5 | 两个 API/DB Compose 项目确实并行，网络、卷、审计数据隔离；Web 服务因 Registry 故障未作为两个完整三服务实例验证。README 所称“设置”环境变量也不能直接覆盖已有 .env：scripts/up.sh:7-17 先 source .env。|
| 重启与故障可见性 | 3.0 / 3 | API restart 后恢复 ready；停止评审数据库时 health=200、ready=503，恢复数据库后 ready 恢复。|

### 4. 测试与验证证据：9.0 / 15

| 子项 | 分数 | 证据与未通过原因 |
| --- | ---: | --- |
| 统一测试入口与可靠断言 | 1.5 / 3 | scripts/test.sh 使用 set -euo pipefail 和测试断言，但受唯一写入边界未原样执行；它还要求宿主 python3、npm install 与 npx playwright install --with-deps，和“仅 Git、Docker、Docker Compose”的前置不一致。|
| SQL 策略单元测试 | 2.5 / 5 | 18 项单测实跑通过，覆盖允许 SELECT、DML/DDL、目录表、多语句、修改型 CTE、超长输入和 SELECT INTO；没有覆盖函数、类型转换或字符串内 SQL，遗漏已复现的 P0 绕过。|
| 双数据库集成测试 | 2.0 / 4 | 8 项实跑通过，覆盖迁移、seed、只读写入拒绝和实际 API；未断言身份不能跨库 CONNECT，也未覆盖函数型非白名单读取。|
| 浏览器主链测试 | 3.0 / 3 | 真实 Playwright 两条主链都通过。|

### 5. 代码质量与可维护性：7.5 / 10

| 子项 | 分数 | 证据与原因 |
| --- | ---: | --- |
| 模块边界与职责分离 | 3.0 / 3 | 策略、执行器、仓储、服务、API、迁移和 Web 分层清楚，依赖可注入。|
| 配置、错误处理与资源清理 | 1.5 / 3 | 连接上下文、超时与 Compose healthcheck 合理；但 executor.py:118-123 将原始数据库错误返回。现场未知列查询向用户泄露列名、表名和 SQL 位置；跨库 CONNECT 与 .env 覆盖也降低配置安全性。|
| 类型、命名、重复控制与可测试性 | 2.0 / 2 | dataclass/Pydantic、明确结果类型及可替换 Settings/Database 便于测试。|
| 依赖、变更范围与维护负担 | 1.0 / 2 | apps/web/package-lock.json 存在，但 Web Dockerfile 只复制 package.json 并运行 npm install，未锁定镜像构建依赖；另有 10 处提交文档尾随空白。|

## 产品文档建议：3.0 / 5

不含视觉评分。

| 子项 | 建议 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1.0 / 1 | README、docs/index.md 与 background/design/plan/status 入口完整且角色清楚。|
| 设计完整性与可追溯性 | 1.0 / 2 | docs/design/first-round-system.md 对双库、策略、seed 和测试设计完整；但其中“只读身份无平台库连接”“撤销非业务对象访问”与实际 ACL、analytics_seed_meta 授权和 P0 绕过不一致。|
| 计划、运行/测试说明与实现一致性 | 1.0 / 2 | README 给出启动、停止、测试路径；但测试脚本实际依赖宿主 Node/npm/Playwright，.env source 行为也使按环境变量设置并行项目不直接成立。|

未评价视觉质量，也未计算最终 100 分或任何技术平均分。

## P0/P1/P2 封顶判断

| 级别 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | 命中 | 用户 SQL 通过 query_to_xml 读取系统 pg_user 的角色名，也读取策略白名单外的 analytics_seed_meta；两条请求均 HTTP 200/succeeded，并可由 GET 审计读取。此为访问系统或未授权对象且绕过 AST 治理，命中规则 P0。汇总时适用 P0 总质量分上限 39；本报告不计算最终质量分。|
| P1 基座失败 | 未单独命中 | API/DB 启动、health/ready、迁移与固定 seed 在本次运行中成立。三服务冷构建受已验证的 Docker Registry 网络故障阻断，因此 Web Compose 冷启动为未验证，而非据此判定候选 P1。|
| P2 核心闭环缺失 | 未命中 | 允许查询、拒绝查询和最小工作台均有新鲜 HTTP、审计和浏览器证据。|

## 问题清单（按严重度）

### P0：函数型动态 SQL 绕过 AST 白名单，泄露系统与未授权对象

- 根因：策略仅检查 SQLGlot Table 节点，未限制函数、类型转换或字符串内二次 SQL（apps/api/app/policy.py:133-137,172-213）；通过后执行器直接执行 SQL（apps/api/app/executor.py:47-55）。
- 最小复现一：

      SELECT query_to_xml(
        'SELECT usename FROM pg_user ORDER BY usename', false, false, ''
      )::text AS leaked

  API 返回 succeeded，XML 含 analytics_migrator、analytics_readonly、platform_app、postgres。

- 最小复现二：

      SELECT query_to_xml(
        'SELECT dataset, version FROM analytics_seed_meta', false, false, ''
      )::text AS leaked

  API 返回白名单外的 analytics_seed_meta 数据。作为对照，直接 SELECT analytics_seed_meta 被 POLICY_FORBIDDEN_OBJECT 拒绝。

- 影响：只读事务和表权限仍可限制普通 DML，但产品承诺的 AST/对象治理边界已被绕过；系统目录和非五张业务表不再受应用层约束。

### P1：双库身份可跨数据库 CONNECT，违反隔离契约

- bootstrap_db.py:57-59 显式给 platform_app 授予 analytics CONNECT，且没有撤销 platform 的 PUBLIC CONNECT。
- 现场 psql 证明 platform_app@analytics 与 analytics_readonly@platform 均可连接；has_database_privilege 对两条连接以及只读角色访问 analytics 均返回 true。业务表权限仍令直接读取 customers/query_runs 失败，但“无平台库连接”和逻辑库身份隔离未成立。
- analytics_seed_meta 还被授予只读身份 SELECT（bootstrap_db.py:76-94、migrate_and_seed.py:26-43），直接为 P0 动态 SQL 路径提供非白名单可读对象。

### P2：seed 在每次启动破坏性 TRUNCATE 固定表

- seed_analytics.py:34-37 在每次 API entrypoint 执行的 seed 中无条件 TRUNCATE 全部分析表和 seed 元数据。
- 本次重启后 fixture 行数恢复正确，故不是 P1 基座链路失败；但未来写入或增量扩展会在 API restart 时被清除，不符合非破坏性重复目标。

### P2：审计提交晚于实际 SQL 执行，且错误信息泄露数据库细节

- QueryRunRepository 的 create_running/finalize 仅 flush（repository.py:17-40）；main.py:167-177 在 service.submit 返回之后才 commit，而 service.py:39-53 已执行 analytics SQL。平台库提交失败时，执行过的查询可能没有持久审计。
- executor.py:118-123 原样截断后返回数据库异常；现场 SELECT missing_column FROM customers 向用户泄露列名、表名和 SQL 位置。

### P2：统一运行/测试契约不够可复现

- scripts/test.sh:36-41 依赖宿主 npm、Playwright 浏览器安装并写入工作树产物，与 README/背景的“仅 Git、Docker、Docker Compose”前置不一致。
- scripts/up.sh:7-17 与 scripts/down.sh:5-11 先 source .env，使已有 .env 覆盖调用时的项目名和端口；文档需明确只能编辑各工作树 .env，或代码改为显式环境变量优先。

## 未验证项

1. 候选原生 Web Compose 镜像（Node build + Nginx）在可访问 Docker Hub 的干净环境中的完整冷启动；本机 auth.docker.io 超时阻断，不能按通过处理。
2. 原样 scripts/test.sh 的端到端通过状态；受唯一写入边界限制未执行，已分别复现 API 和浏览器组成部分。
3. 只安装 Git、Docker、Docker Compose 的全新 WSL 上统一测试命令可用性；脚本静态上还要求宿主 Python/Node/npm/Playwright，未取得相反的新鲜运行证据。

## Compose 资源清理

本次仅创建并随后清理：

- dhg45reviewa：API 18080、其 db/api 容器、默认网络及 dhg45reviewa_pgdata；
- dhg45reviewb：API 18081、其 db/api 容器、默认网络及 dhg45reviewb_pgdata；
- 临时前端容器 dhg45reviewa-vite。

已执行精确的 docker compose --project-name <name> down --volumes --remove-orphans 和临时容器停止/删除；最终按项目名检查无上述容器、网络或卷残留，未停止或修改无关 Docker 项目。
