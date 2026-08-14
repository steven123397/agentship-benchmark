# DecisionHarbor v0.1.0 Codex 首轮独立评审

评审日期：2026-07-22  
候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/qoder-qwen3.8-max-preview-thinking  
候选分支：v0.1.0/qoder-qwen3.8-max-preview-thinking  
评审提交：fffe1f6bbe15872479d3579ea99d57deba7445f3  
baseline 提交：1fb48f499d67677a47fb9b60e1f99346b46e0aee

## 独立性声明

本报告仅依据上述冻结提交的代码、文档和本次实际运行证据形成。未读取或引用其他候选的工作树、分支、运行记录、评审材料、评分或结论；未读取本候选的 grok-review.md、review-summary.md 或 scorecard.md。评分不考虑 Agent、模型、耗时、token 或开发阶段自述。

评审期间未修改候选源码、候选分支、baseline 或评分规范；唯一写入目标为本文件。

## 冻结与环境

- metadata.json 显示 completion.coordinatorFrozen 为 true，candidate.resultCommit 为 fffe1f6bbe15872479d3579ea99d57deba7445f3。
- 评审开始和结束时，git rev-parse HEAD 均为 fffe1f6bbe15872479d3579ea99d57deba7445f3。
- 评审开始和结束时，git status --short --branch 仅显示分支跟踪行，无未提交改动；git diff --check 均以 0 退出。
- 环境：Docker 29.1.3、Docker Compose 2.40.3、宿主 Node.js v24.16.0、宿主 Python 3.10.12。
- Docker Hub、PyPI、Playwright 浏览器下载可达。首次未显式传入代理参数的 API 镜像依赖下载停滞；在用户授权后，以 Docker build 的 http_proxy/https_proxy 参数重试并成功。报告不记录代理地址或凭据。

## 实际执行与结果

以下为本次评审实际执行的关键命令或等价的受限临时容器命令，命令均在候选工作树执行，除本报告外未写入候选：

    PYTHONDONTWRITEBYTECODE=1 python3 datasets/sales-analytics-v1/validate.py
    COMPOSE_PROJECT_NAME=dhqoder0722a API_HOST_PORT=18200 WEB_HOST_PORT=18273 docker compose up -d --build
    COMPOSE_PROJECT_NAME=dhqoder0722a API_HOST_PORT=18200 WEB_HOST_PORT=18273 docker compose build --build-arg http_proxy=... --build-arg https_proxy=... api
    COMPOSE_PROJECT_NAME=dhqoder0722a API_HOST_PORT=18200 WEB_HOST_PORT=18273 docker compose up -d
    curl --fail --silent --show-error http://127.0.0.1:18200/health
    curl --fail --silent --show-error http://127.0.0.1:18200/ready
    docker compose restart api
    docker compose run --rm --no-deps -e QUERY_STATEMENT_TIMEOUT_MS=100 api python -c ...
    docker run --rm ... node:24-alpine ... npm ci --ignore-scripts --silent && npm test
    docker run --rm ... dhqoder0722a-api:latest ... pytest -q tests/unit tests/integration
    docker run --rm ... mcr.microsoft.com/playwright:v1.52.0-jammy ... npm ci --ignore-scripts --silent && npx playwright install chromium && npx playwright test
    COMPOSE_PROJECT_NAME=dhqoder0722b API_HOST_PORT=18201 WEB_HOST_PORT=18274 docker compose up -d

得到的新鲜运行证据：

- 数据集校验成功。
- 主栈的 db、api 均为 healthy，web 可访问；/health 和 /ready 均返回 HTTP 200。API 重启后 /ready 再次返回 HTTP 200，日志显示迁移和 seed 完成。
- 允许查询 SELECT COUNT(*) AS total FROM customers 返回 HTTP 201、succeeded 和 total=100；SELECT id FROM order_items 返回 1,000 行。查询审计读取成功，未知审计 ID 返回 HTTP 404。
- DELETE、两条 SELECT 语句、直接访问 pg_catalog.pg_class 分别返回 HTTP 201 且 status=rejected，错误码为 FORBIDDEN_STATEMENT、MULTI_STATEMENT、FORBIDDEN_OBJECT。
- 以 QUERY_STATEMENT_TIMEOUT_MS=100 运行的超时探针返回 ExecutionError / TIMEOUT。
- API 单元与集成测试为 39 passed；Web Vitest 为 6 passed；Playwright 浏览器主链为 3 passed（允许查询、拒绝查询、空 SQL）。
- 两个完整 Compose 项目 dhqoder0722a（API 18200、Web 18273）与 dhqoder0722b（API 18201、Web 18274）同时健康。两边各自执行 SELECT COUNT(*) AS customers FROM customers 均返回 HTTP 201、succeeded、100，且使用独立容器、网络、卷和宿主端口。

以下负向复现也在运行栈上完成：

    SELECT query_to_xml(
      'SELECT relname FROM pg_catalog.pg_class LIMIT 1',
      false, true, ''
    )::text AS catalog_xml

该请求返回 HTTP 201、succeeded，并把 pg_catalog 的 relname 作为 XML 返回给用户。另有：

    SELECT id FROM order_items LIMIT (SELECT 3000)

该请求返回 HTTP 201、succeeded、row_count=3000，越过 QUERY_MAX_ROWS=1000。

在 db 容器中分别以 analytics_reader 和 platform_app 验证数据库连接与表操作，结果为：

- analytics_reader 可连接 analytics、不能 INSERT；
- analytics_reader 可连接 platform、不能 SELECT query_runs；
- platform_app 可连接 analytics、不能 SELECT customers。

这证明表权限阻断了已测表访问，但未阻断跨数据库连接。

## 技术评分：65.5 / 90

### 功能与外部契约：22.5 / 25

| 子项 | 分数 | 证据 | 未验证项或限制 |
| --- | ---: | --- | --- |
| API 生命周期与契约 | 8 / 8 | /health、/ready、创建查询审计、读取审计和不存在 ID 的 HTTP 契约均实际验证。 | 未做完整 OpenAPI 差异扫描。 |
| 允许 SQL 的正确结果 | 7 / 7 | customers 聚合返回 100；order_items 正常上限返回 1,000 行；双栈各自 seed 后均可查询。 | 未逐项重算所有业务口径。 |
| 拒绝 SQL 与执行语义 | 2.5 / 5 | DELETE、多语句、直接系统目录访问均被拒绝。 | query_to_xml 中的 SQL 字符串可读取 pg_catalog，故对象拒绝语义不完整。 |
| 查询工作台 | 5 / 5 | 真实 Chromium Playwright 3 项均通过，覆盖允许、拒绝和空 SQL 主链。 | 未进行人工长时交互和极端错误恢复探索。 |

### SQL 治理与数据正确性：9.5 / 20

| 子项 | 分数 | 证据 | 未验证项或限制 |
| --- | ---: | --- | --- |
| AST 只读与单语句治理 | 3 / 6 | sqlglot 解析、DML、数据修改 CTE、SELECT INTO、多语句和普通系统表路径有控制；标准负例已通过 API 复现。 | 用户可借 query_to_xml 的字符串参数执行未被 AST 表遍历看到的 SQL，已实际读到系统目录。 |
| 表、schema 与对象范围 | 0 / 4 | 直接表名白名单存在。 | 上述 query_to_xml 已实际访问 pg_catalog；api/app/policy.py:74-118 只检查 exp.Table，不能作为完整对象边界。 |
| 双库身份与隔离 | 2 / 4 | 用户查询的 current_user 为 analytics_reader；reader 写入和跨库表读取被 PostgreSQL 拒绝。 | reader 与 platform_app 均可连接对方数据库。db/init/01-init-databases.sh:27-45 未撤销 PUBLIC 的 CONNECT，因此不是严格双库连接隔离。 |
| 资源限制 | 1.5 / 3 | 100 ms 超时探针返回 TIMEOUT；无 LIMIT 时实际限制为 1,000 行。 | api/app/policy.py:121-131 仅钳制整数文本 LIMIT；LIMIT (SELECT 3000) 实测返回 3,000 行。未压测内存、并发或超大响应。 |
| 数据契约与 seed | 3 / 3 | 固定数据集校验成功，迁移和 seed 日志成功，两个独立栈均得到 customers=100。 | 未独立重新推导每一个 CSV 的业务口径。 |

### 可运行性与可靠性：18.5 / 20

| 子项 | 分数 | 证据 | 未验证项或限制 |
| --- | ---: | --- | --- |
| 干净启动与就绪 | 6 / 6 | 两套全栈均完成 build、启动、健康检查和 HTTP /ready。 | 本环境首次无显式代理的 PyPI 下载停滞；代理构建路径可用。未验证离线构建。 |
| 迁移与 seed | 6 / 6 | API 启动日志显示 Migrations complete 与 Seed complete；运行查询验证了种子数据。 | 未演练迁移回滚或部分失败恢复。 |
| 并行 Compose 隔离 | 5 / 5 | 两个 project name、网络、卷和端口同时存在且独立健康；各自查询得到 100。 | 仅在同一 Docker 主机上验证两栈。 |
| 重启与故障边界 | 1.5 / 3 | API restart 后重新迁移、seed 并恢复 /ready。 | 未动态断开 analytics 数据库；api/app/main.py:24-29 的 /ready 只检查 platform，不能证明分析库或 seed 失效时会失就绪。 |

### 测试与验证证据：7.5 / 15

| 子项 | 分数 | 证据 | 未验证项或限制 |
| --- | ---: | --- | --- |
| 统一、可复现测试入口 | 0 / 3 | 可分别运行 pytest、Vitest 和 Playwright。 | 根 package.json:1-7 没有 scripts，仓库无统一测试入口；本次需用只读临时容器拼接各命令。 |
| 策略单元测试 | 2.5 / 5 | api/tests 的单元和集成入口实际为 39 passed，普通拒绝规则覆盖存在。 | 缺少 query_to_xml 动态 SQL 与非字面 LIMIT 的回归测试，未捕获 P0 和资源绕过。 |
| 集成测试 | 2 / 4 | 实际 Compose、真实 PostgreSQL、seed、超时和双库行为均已复现。 | 现有自动集成测试未断言跨库 CONNECT 必须拒绝，且没有把上述负例固化。 |
| 浏览器验证 | 3 / 3 | Playwright 真实 Chromium 运行 3 passed。 | 未覆盖查询历史列表或不存在的长尾界面。 |

### 代码质量与可维护性：7.5 / 10

| 子项 | 分数 | 证据 | 未验证项或限制 |
| --- | ---: | --- | --- |
| 模块边界 | 3 / 3 | policy、executor、router、migrate、seed、Web 组件与 E2E 分层清晰，实际测试可独立运行。 | 未做长期演进下的架构负载验证。 |
| 配置、错误处理与资源清理 | 1.5 / 3 | 有明确错误码、健康检查、超时和 Compose 健康依赖。 | /ready 只依赖 platform；docker-compose.yml:21-25 将 analytics_admin 连接串注入常驻 API 进程，权限暴露面过大。 |
| 类型与可测试性 | 2 / 2 | Python 数据模型和前后端测试可运行，测试执行稳定。 | 未执行静态类型检查或 lint。 |
| 依赖与维护性 | 1 / 2 | Web 和根目录存在锁文件，容器构建可复现到本次已拉取依赖。 | api/pyproject.toml:12-27 只有下界、无锁文件；api/Dockerfile:12 使用在线 pip install，Web Dockerfile 使用 npm install，依赖漂移与网络可用性风险仍在。 |

## 产品文档建议分：3 / 5

- 文档治理与索引：1 / 1。docs/index.md、background、design、plan、status 的目录职责可辨。
- 架构设计：2 / 2。docs/design/first-round-architecture.md 对首轮边界、数据库角色和查询流程有足够细节。
- 计划、运行与测试文档一致性：0 / 2。README.md:5 仍称应用源码、依赖、Compose、迁移、测试和运行命令“尚未建立”；docs/plan/first-round-implementation.md:11-16 的所有任务仍为“待开始”，而 docs/status/project_status.md:5、13 称实现完成且全部测试通过。用户无法据这些文档得到可执行的运行和统一测试入口。

这是文档建议分，不含视觉分，也未与技术分相加或计算任何总分。

## P0 / P1 / P2 风险标记

评分规范中的风险标记不对技术分做封顶。本次判断如下：

| 标记 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 | 命中 | 用户提交的 query_to_xml 包含 pg_catalog.pg_class 的 SQL 字符串，API 返回 HTTP 201、succeeded，并返回 catalog XML。该路径绕过 api/app/policy.py:74-118 的 exp.Table 对象治理，属于用户 SQL 访问系统目录及绕过 AST 治理。首轮不具备安全上线资格。 |
| P1 | 未命中 | 两个干净项目均完成启动、/health、/ready、迁移和 seed；API 重启后恢复。 |
| P2 | 未命中 | 允许与拒绝 SQL 均有实际证据，且浏览器主链 Playwright 3 passed。 |

## 问题清单（按严重度）

1. **P0：函数字符串中的动态 SQL 绕过对象治理并读取系统目录。**  
   api/app/policy.py:74-118 只查找语法树中的 exp.Table。query_to_xml('SELECT relname FROM pg_catalog.pg_class LIMIT 1', ...) 的内部 SQL 位于字符串字面量，不会形成外层 AST 表节点；实际 API 已返回 pg_catalog 内容。应禁止能够执行或解释 SQL 字符串的 PostgreSQL 函数，或采用能对其参数进行安全证明的更窄 SQL 子集；在修复前不能将 AST 白名单视为安全边界。

2. **高：QUERY_MAX_ROWS 可被非字面 LIMIT 绕过。**  
   api/app/policy.py:121-131 仅处理 exp.Literal 整数。LIMIT (SELECT 3000) 实际返回 3,000 行，超过配置的 1,000。应拒绝非字面 LIMIT 或在执行层施加独立、不可绕过的行数上限，并增加回归测试。

3. **高：双库隔离没有收紧默认 CONNECT 权限。**  
   db/init/01-init-databases.sh:27-45 只授予目标角色权限，未先 REVOKE CONNECT ON DATABASE ... FROM PUBLIC。实测 analytics_reader 可连接 platform，platform_app 可连接 analytics，虽无相应表权限。应撤销 PUBLIC CONNECT，再仅授予必要角色，并把连接级隔离加入集成测试。

4. **中：就绪检查与常驻高权限配置的边界不完整。**  
   api/app/main.py:24-29 只验证 platform；分析库不可用或 seed 不完整仍可能报告 ready。docker-compose.yml:21-25 又把 analytics_admin 连接串交给常驻 API。应让 readiness 覆盖用户查询依赖，并把迁移 / seed 高权限工作拆到短生命周期任务或独立凭据。

5. **中：测试入口、负例覆盖与依赖锁定不足。**  
   根 package.json 没有测试 scripts；本次只能手工运行不同栈的命令。API 无锁文件且容器在线安装浮动版本。应提供一个统一入口，固定 API 依赖，并将 P0、非字面 LIMIT、跨库 CONNECT 加入自动化回归。

6. **中：README、实现计划与状态文档互相矛盾。**  
   README 仍描述尚未建立应用，计划仍显示全部待开始，状态却称全部完成。应同步运行、测试、Compose 和完成状态，避免使用者按错误入口操作。

## Compose 资源与最终 Git 状态

- 本次评审创建的 dhqoder0722a 和 dhqoder0722b 均已执行 docker compose down --volumes --remove-orphans；两次后续 docker compose ps --all 均为空，仅有表头。
- 临时 API、Web、Playwright 测试容器均使用 --rm，未保留。
- 未停止或查询无关项目资源。
- 最终候选 Git 状态：HEAD 为 fffe1f6bbe15872479d3579ea99d57deba7445f3；git status --short --branch 无未提交改动；git diff --check 通过。
