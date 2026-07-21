# DecisionHarbor v0.1.0：Codex 首轮独立评审

## 独立性声明与范围

- 本报告只依据冻结提交 e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde 的代码、配置和本次实际运行证据评分。
- 先核验本运行的 metadata.json：completion.coordinatorFrozen 为 true，candidate.resultCommit 为上述完整 SHA；候选工作树的 HEAD 与其一致。
- 未读取、比较、引用或使用其他候选的工作树、分支、运行记录、评审材料、分数或结论；也未读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 候选源码和基线均保持只读；本次唯一写入为本文件。未执行 git add、commit、push、PR、checkout、reset 或清理候选工作树。
- reproduction.md 只用于识别候选声称支持的命令，不作为任何通过证据。

## 冻结提交、环境与 Git 状态

| 项目 | 证据 |
| --- | --- |
| 候选分支 | v0.1.0/zcode-glm-5.2-high |
| 评审提交 | e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde |
| baseline 提交 | 1fb48f499d67677a47fb9b60e1f99346b46e0aee |
| Docker / Compose | Docker Server 29.1.3；Docker Compose 2.40.3+ds1-0ubuntu1~22.04.1 |
| 宿主 Node / Python | Node v24.16.0；Python 3.10.12。应用镜像声明 Python 3.13、Node 24。 |
| 开始前 Git | HEAD 为评审提交；git status --short --branch 仅显示分支跟踪行，无未提交改动。 |
| 结束前 Git | HEAD 仍为评审提交；git status --short --branch 仍洁净；git diff --check 退出 0。 |

## 实际执行命令与运行证据

以下命令均在候选工作树执行，除报告外不写入工作树。

1. 冻结与环境核验：

       git rev-parse HEAD
       git status --short --branch
       git diff --check
       docker version --format '{{.Server.Version}}'
       docker compose version
       node --version
       python3 --version
       PYTHONDONTWRITEBYTECODE=1 make validate-dataset
       DH_PROJECT_NAME=dhzcode0721 DH_WEB_PORT=18173 DH_API_PORT=18000 docker compose config

   数据集校验成功。Compose 配置显示项目名、API 端口和 Web 端口可配置，网络与卷名称均受项目名作用域化。

2. 原生三服务启动尝试：

       DH_PROJECT_NAME=dhzcode0721 DH_WEB_PORT=18173 DH_API_PORT=18000 make up

   未完成。构建 Web 时 Docker 无法从 auth.docker.io 获取 node:24-slim 的匿名令牌，错误为 DeadlineExceeded 与 TCP 443 超时。随后独立检查：

       curl --connect-timeout 5 --max-time 20 ... https://auth.docker.io/token?...
       docker image inspect node:24-slim

   curl 返回 000 / exit 28，本机无 node:24-slim。故这是一项外部镜像仓库连通性阻塞；完整 Web 构建、完整三服务启动与浏览器验证均标为“未验证”，不当作候选通过或候选启动失败的证据。

3. 后端、迁移与种子：

       DH_PROJECT_NAME=dhzcode0721 DH_WEB_PORT=18173 DH_API_PORT=18000 docker compose up -d db api
       DH_API_PORT=18000 bash scripts/wait-ready.sh
       DH_PROJECT_NAME=dhzcode0721 DH_WEB_PORT=18173 DH_API_PORT=18000 make test-integration
       DH_PROJECT_NAME=dhzcode0721 DH_WEB_PORT=18173 DH_API_PORT=18000 make test-unit

   DB 健康、API 就绪；wait-ready 输出 ready。集成测试实际输出 14 passed in 0.88s，策略单元测试实际输出 36 passed in 0.07s。集成命令通过 Alembic 和 seed，覆盖第二次 seed 收敛。

4. API 实测：

   - GET /health 返回 200 和 status=ok；GET /ready 返回 200 和 status=ready。
   - 允许查询 SELECT id, customer_code FROM analytics.customers ORDER BY id LIMIT 3 返回 200、succeeded、3 行，首行是 [1, "CUST-0001"]；随后 GET 该 id 返回 succeeded 且 rows 为 null。
   - DELETE FROM analytics.customers 返回 422、rejected、FORBIDDEN_STATEMENT；SELECT 1; SELECT 2; 返回 422、rejected、MULTI_STATEMENT；直接访问 pg_catalog.pg_class 返回 422、FORBIDDEN_OBJECT。
   - SELECT id FROM analytics.order_items 返回 200、failed、ROW_LIMIT_EXCEEDED，证明默认 1000 行上限真实生效。
   - confirmed 订单计数查询返回 720；按契约的 sales_amount / cost_amount SQL 返回 11058789.64 / 7977580.36。

5. 身份与资源限制实测：

   - 在 DB 容器中以 analytics reader 身份验证：analytics SELECT 允许；analytics INSERT 被拒；连接 platform 被拒。
   - platform writer 身份连接 analytics 被拒。
   - 使用同一执行器、DH_STATEMENT_TIMEOUT_MS=100 运行 SELECT pg_sleep(1)，输出 succeeded=False、error_code=STATEMENT_TIMEOUT、duration_ms=117。

6. 后端重启与并行隔离：

       DH_PROJECT_NAME=dhzcode0721 ... docker compose restart api
       DH_API_PORT=18000 bash scripts/wait-ready.sh
       DH_PROJECT_NAME=dhzcode0721b DH_WEB_PORT=18174 DH_API_PORT=18001 docker compose build api
       DH_PROJECT_NAME=dhzcode0721b DH_WEB_PORT=18174 DH_API_PORT=18001 docker compose up -d db api
       DH_API_PORT=18001 bash scripts/wait-ready.sh

   API 重启后再次 ready。两个后端实例同时就绪，资源分别使用 dhzcode0721 与 dhzcode0721b 的网络和卷，端口为 18000 / 18001；两边的 customers 计数均为 100，审计 id 分别为 16 与 1，证明后端数据卷和审计库没有共享。完整含 Web 的并行实例未验证。

7. 本次 Compose 清理：

       DH_PROJECT_NAME=dhzcode0721 ... docker compose down --volumes --remove-orphans
       DH_PROJECT_NAME=dhzcode0721b ... docker compose down --volumes --remove-orphans

   两组容器、网络和 db-data 卷均已停止并移除。结束后分别执行 docker compose ps --all，均无本次项目的容器。

## 技术评分（封顶前，90 分）

| 维度与子项 | 分数 | 本次证据与未验证项 |
| --- | ---: | --- |
| 功能与外部契约：查询运行 API 生命周期 | 8 / 8 | POST 创建审计记录、GET 读取审计事实、health / ready 均有实时 HTTP 证据。 |
| 功能与外部契约：允许查询结果正确性 | 7 / 7 | 五表数据、confirmed=720、聚合口径与返回列/行均已实测。 |
| 功能与外部契约：拒绝与执行失败语义 | 2.5 / 5 | DML、多语句、直接系统目录、行数超限语义正确；但下述 P0 绕过可把系统目录查询伪装为 allowed 并成功执行。 |
| 功能与外部契约：最小查询工作台 | 0 / 5 | 未验证：Web 镜像无法因外部 Docker Hub 连通性构建，未取得新鲜浏览器证据。静态 React 源码不计为通过。 |
| 功能与外部契约小计 | 17.5 / 25 |  |
| SQL 治理与数据正确性：AST 只读语义与单语句约束 | 6 / 6 | SQLGlot AST 实现位于 api/app/policy.py；本次 DML、多语句、直接目录查询均被拒，单元测试 36 项通过。对象范围绕过单列计分。 |
| SQL 治理与数据正确性：授权对象与 schema 范围 | 0 / 4 | P0：构造 CTE 别名可执行 pg_catalog.pg_class，详见封顶与问题清单。 |
| SQL 治理与数据正确性：数据库身份与双库隔离 | 4 / 4 | reader 的写入及 platform 连接均被拒；writer 连接 analytics 被拒。 |
| SQL 治理与数据正确性：执行资源限制 | 3 / 3 | HTTP 行数上限和同一执行器上的 100 ms statement timeout 均实际生效。 |
| SQL 治理与数据正确性：固定数据契约与业务口径 | 3 / 3 | validate.py、集成测试、五表计数与 confirmed 销售口径均有新鲜证据。 |
| SQL 治理与数据正确性小计 | 16 / 20 |  |
| 可运行性与可靠性：干净环境启动与就绪 | 3 / 6 | DB + API 从候选 Compose 启动并 ready；完整 Web/API/DB 启动未验证，原因是外部 Node 基础镜像不可拉取。 |
| 可运行性与可靠性：迁移与固定数据初始化 | 6 / 6 | entrypoint 的 Alembic + seed 与 integration 测试均成功；重复 seed 收敛由 14 项集成测试实际覆盖。 |
| 可运行性与可靠性：并行实例隔离 | 2.5 / 5 | Compose 静态命名和两组后端实例均证明隔离；含 Web 的完整双实例未验证。 |
| 可运行性与可靠性：重启与故障可见性 | 1.5 / 3 | API 重启后 ready；完整三服务重启及依赖故障下的 Web 行为未验证。 |
| 可运行性与可靠性小计 | 13 / 20 |  |
| 测试与验证证据：统一测试入口与可靠断言 | 1.5 / 3 | Makefile 的 test 入口存在，test-unit 与 test-integration 均实际通过；完整 make test 因浏览器前置条件未验证。 |
| 测试与验证证据：SQL 策略单元测试 | 2.5 / 5 | 36 项实际通过，覆盖直接目录、DML、DDL、多语句等；未覆盖本次实际复现的 CTE 同名绕过。 |
| 测试与验证证据：双数据库集成测试 | 4 / 4 | make test-integration 实际 14 passed，且独立身份命令复核读写与跨库拒绝。 |
| 测试与验证证据：浏览器主链测试 | 0 / 3 | 未验证：Playwright 未实际运行，不能将静态 e2e 源码按通过计。 |
| 测试与验证证据小计 | 8 / 15 |  |
| 代码质量与可维护性：模块边界与职责分离 | 3 / 3 | policy、executor、audit、db、seed、FastAPI 入口职责清楚，迁移与固定数据 seed 分离。 |
| 代码质量与可维护性：配置、错误处理与资源清理 | 1.5 / 3 | 环境变量、Engine dispose 与 Compose 清理路径清晰；但 policy 的 CTE 对象跳过逻辑造成严重安全边界失效，且完整 Web 运行链未获验证。 |
| 代码质量与可维护性：类型、命名、重复控制与可测试性 | 2 / 2 | Python 类型标注、纯策略函数与分层测试接缝明确。 |
| 代码质量与可维护性：依赖、变更范围与维护负担 | 1 / 2 | 变更范围集中且有 package-lock.json；但 Python 依赖仅使用 >= 下限、无锁定文件，Web Dockerfile 使用 npm install 而非锁文件严格安装，长期复现性较弱。 |
| 代码质量与可维护性小计 | 7.5 / 10 |  |

技术原始总分：62 / 90。

这是 P0 封顶前的技术分。按照评分规范，P0 作用于汇总阶段的质量原始分上限；本报告不计算最终 100 分、技术平均分或视觉分。

## 产品文档建议分（不含视觉）

建议分：4 / 5。

| 子项 | 分数 | 证据 |
| --- | ---: | --- |
| 治理、索引与阅读入口 | 1 / 1 | 根 AGENTS.md、docs/AGENTS.md、docs/index.md 及 background / design / plan / status 职责清楚。 |
| 设计完整性与可追溯性 | 2 / 2 | docs/design/first-round.md 对 API、状态机、双库、策略、资源限制、Compose 与测试接缝有完整可追溯设计。 |
| 计划、运行/测试说明与实现一致性 | 1 / 2 | first-round 计划与主要实现一致；但 README.md 仍称应用源码、依赖、容器、迁移、测试和运行命令“尚未建立”，与本提交实际内容冲突，也未提供可直接执行的当前运行/测试说明。 |

## P0 / P1 / P2 封顶判断

| 级别 | 判断 | 可复核证据 |
| --- | --- | --- |
| P0 安全失败 | 命中。汇总阶段质量原始分上限为 39。 | api/app/policy.py 的 _cte_names 在第 37–42 行收集 CTE 名称；第 79–82 行仅按表名跳过，未限制为无 schema 的 CTE 引用。实际 POST SQL：WITH pg_class AS (SELECT 1) SELECT relname FROM pg_catalog.pg_class LIMIT 1。响应为 HTTP 200、status=succeeded、row_count=1，结果为 product_categories_pkey。用户 SQL 因而实际读取了 pg_catalog 系统目录，并绕过了 AST 对象范围治理。 |
| P1 基座失败 | 不判定命中。 | 后端 Compose 的 DB + API 已实际 ready；Alembic、固定 seed、14 项集成测试均通过。三服务启动未验证的直接根因是评测环境无法连接 auth.docker.io 且无本地 node:24-slim，不把该外部阻塞归因于候选。 |
| P2 核心闭环缺失 | 不判定命中。 | 已同时证明一条允许查询与多条拒绝查询。浏览器工作台未验证，但没有证据证明其不可用；因此不能把“缺少浏览器证据”写成“工作台不可用”。 |

## 问题清单（按严重度）

1. P0／必须修复：CTE 同名可绕过系统对象拦截。

   api/app/policy.py 先收集所有 CTE alias，随后遇到任意同名 exp.Table 即直接跳过，不区分 pg_catalog.pg_class 这样的限定引用。上述 HTTP 复现返回系统对象的 relname，已满足 P0 的“用户 SQL 访问系统对象 / 绕过 AST 治理”条件。现有测试只覆盖直接 pg_catalog 查询，未覆盖同名 CTE 遮蔽。

2. P1／高优先级功能问题（不等同于 P1 封顶）：默认 schema 的策略承诺与实际执行不一致。

   policy.py 将未限定表名视为 analytics（第 79 行），测试也将 SELECT * FROM customers 视为允许；但执行器没有设置 search_path。实际 POST SELECT id FROM customers LIMIT 1 被策略允许后返回 HTTP 200、status=failed、EXECUTION_ERROR。若产品保留未限定表名的允许语义，需要使执行会话与策略使用同一默认 schema；否则应在策略中拒绝或在文档中取消该承诺。

3. P1／高优先级测试缺口（不等同于 P1 封顶）：SQL 策略绿灯未覆盖关键绕过。

   api/tests/test_policy.py 覆盖了直接系统目录、DML、DDL 和多语句，但没有 CTE alias 与 schema 限定表名相同的组合。36 项单元测试全绿仍漏过上述 P0，因此测试集不能证明对象范围控制的安全性。

4. P2／建议修改：README 与实际交付状态不一致。

   README.md 仍描述“应用源码、依赖、容器配置、迁移、测试和运行命令尚未建立”，而本提交新增了 Makefile、docker-compose.yml、api、web、迁移与测试。读者无法从 README 获得当前启动和测试入口。

5. P2／建议修改：依赖解析缺少严格锁定。

   api/pyproject.toml 只给出 >= 依赖下限且没有 Python 锁定文件；web/Dockerfile 使用 npm install。它们不影响本次已运行的后端镜像，但会增加未来干净环境复现出现依赖漂移的概率。

## 未验证项

- 完整 Web/API/PostgreSQL 的原生 make up 成功路径、Web 健康可用性和完整三服务重启。
- Playwright 浏览器主链及完整 make test；静态 e2e 脚本不作为通过证据。
- 含 Web 服务的两套并行 Compose 实例。

这些未验证项的直接环境证据是：对 auth.docker.io 的独立 curl 在 443 超时（exit 28），Docker 构建 node:24-slim 的匿名令牌请求 DeadlineExceeded，且本机没有 node:24-slim 镜像。

## 最终资源与 Git 状态

- 本次创建的 dhzcode0721 与 dhzcode0721b Compose 容器、网络及数据卷均已执行 down --volumes --remove-orphans 并复查为空。
- 候选工作树最终 HEAD 为 e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde；git status --short --branch 无未提交改动；git diff --check 通过。
