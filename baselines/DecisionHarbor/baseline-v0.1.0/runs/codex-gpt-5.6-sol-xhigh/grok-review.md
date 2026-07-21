# DecisionHarbor v0.1.0 — Grok 首轮独立评审

## 1. 独立性声明

- 本报告由 Grok Build 在 AgentShip 工作区内对冻结候选做只读复现与审查。
- 全程未读取其他候选的 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md` 或任何 Codex 首轮结论。
- 未修改候选源码、候选分支、baseline 产品仓库、评分规范或其他归档文件；未执行 `git add` / `commit` / `push` / 创建 PR。
- 唯一写入文件为本 `grok-review.md`。
- 评分仅依据本次可复核的代码审查与运行证据；不因 Agent 名称、模型标签、耗时、token 或既往印象调整分数。
- 无新鲜证据的项目一律标为「未验证」，不以 Agent 自述计为通过。

## 2. 评审对象、环境与执行命令

### 2.1 候选冻结信息

| 项 | 值 |
| --- | --- |
| 产品仓库 | `/home/liangjiaqi/projects/DecisionHarbor` |
| 候选工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-sol-xhigh` |
| 候选分支 | `v0.1.0/codex-gpt-5.6-sol-xhigh` |
| 冻结 commit（HEAD） | `6e3964f05b72d44a50f7d2a7657304a83cfa11c1` |
| baseline commit | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始前 `git status` | 干净，无未提交改动 |
| 结束后 `git status` / `git diff --check` | 干净；`git diff --check` 退出码 0 |

### 2.2 评测环境

| 组件 | 版本/说明 |
| --- | --- |
| 宿主 | WSL2 Linux `6.18.33.2-microsoft-standard-WSL2` x86_64 |
| Docker | `29.1.3` |
| Docker Compose | `2.40.3` |
| 宿主 Python | `3.10.12`（应用与测试在容器内 Python 3.13 运行） |
| 宿主 Node.js | `v24.16.0` |
| 评审 Compose 项目 | `dhgrok-review`（API `127.0.0.1:18080`，Web `127.0.0.1:15173`） |
| 并行第二实例 | `dhgrok-review2`（API `127.0.0.1:18081`，Web `127.0.0.1:15174`） |

### 2.3 实际执行的主要命令（摘要）

```bash
# 冻结确认
git rev-parse HEAD   # 6e3964f05b72d44a50f7d2a7657304a83cfa11c1
git status --short --branch

# 数据集
python3 datasets/sales-analytics-v1/validate.py

# 主实例启动
COMPOSE_PROJECT_NAME=dhgrok-review HOST_BIND_ADDRESS=127.0.0.1 \
  WEB_HOST_PORT=15173 API_HOST_PORT=18080 ./dev up

# 健康/就绪/API/拒绝与允许 SQL/截断/超时
curl http://127.0.0.1:18080/health
curl http://127.0.0.1:18080/ready
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:18080/api/v1/query-runs
curl http://127.0.0.1:18080/api/v1/query-runs/<id>

# 双库身份与 seed
docker compose exec postgres ...  # analytics_reader / platform_app 权限与 CONNECT 隔离
docker compose run --rm init      # bootstrap complete: dataset unchanged
docker compose restart api

# 统一测试
COMPOSE_PROJECT_NAME=dhgrok-review ... ./dev test
# → pytest 62 passed；Vitest 6 passed；Playwright 4 passed；exit 0

# 并行第二实例
COMPOSE_PROJECT_NAME=dhgrok-review2 WEB_HOST_PORT=15174 API_HOST_PORT=18081 ./dev up

# 故障可见性（仅 stop 第二实例 postgres）
COMPOSE_PROJECT_NAME=dhgrok-review2 docker compose stop postgres
curl --max-time 5 http://127.0.0.1:18081/ready
curl http://127.0.0.1:18080/ready   # 第一实例仍 ready

# 收尾（仅本评审项目）
COMPOSE_PROJECT_NAME=dhgrok-review2 ./dev destroy
COMPOSE_PROJECT_NAME=dhgrok-review  ./dev destroy
git status --short --branch
git diff --check
```

阅读范围：`AGENTS.md`、`README.md`、`docs/index.md`、`docs/background/`、`docs/design/`、`docs/plan/`、`docs/status/`，以及 `apps/api`、`apps/web`、`compose.yaml`、`dev`、`datasets/sales-analytics-v1` 相关实现与测试。

## 3. 技术评分（/90）

评分档位遵循规范：子项 **未通过 = 0**，**部分通过 = 50%**，**完全通过 = 满分**。证据均为本次新鲜运行或代码审查。

### 3.1 功能与外部契约 — **25 / 25**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**证据**

1. **API 生命周期**  
   - `POST /api/v1/query-runs` 成功返回 `query_run` + `result`，状态 `succeeded`，含 `id`、策略版本、`referenced_objects`、`duration_ms` 等。  
   - 示例：`SELECT count(*) AS customer_count FROM customers` → `rows: [["100"]]`，`id=8d30b59c-8664-4898-8df3-8921e2afb666`。  
   - `GET /api/v1/query-runs/{id}` 仅返回 `{"query_run": ...}`，**不含**结果单元格（`result` key 不存在），符合设计。

2. **允许查询正确性**  
   - 客户数 100 与契约一致。  
   - 区域营收聚合（`confirmed` 订单 × `quantity * unit_price * (1 - discount_rate)`）结果：  
     East `2768355.33`，South `2329370.48`，Central `2076252.00`，West `1989615.57`，North `1895196.27`。  
   - 与 `harbor_admin` 在 analytics 上同口径 SQL 结果一致。

3. **拒绝与失败语义**  
   | 输入 | HTTP | code | status |
   | --- | ---: | --- | --- |
   | `DELETE FROM customers` | 422 | `sql_statement_not_allowed` | `rejected` |
   | `SELECT 1; SELECT 2` | 422 | `multiple_statements` | `rejected` |
   | `SELECT * FROM pg_catalog.pg_class` | 422 | `sql_object_not_allowed` | `rejected` |
   | `SELECT * FROM platform.query_runs` | 422 | `sql_object_not_allowed` | `rejected` |
   | 修改型 CTE / SELECT INTO / TRUNCATE / ALTER / CREATE AS | 422 | `sql_statement_not_allowed` 等 | `rejected` |
   | `SELECT missing_column FROM customers` | 400 | `query_semantic_error` | `failed` |
   | 重 CROSS JOIN | 504 | `query_timeout` | `failed` |
   - 错误均带 `query_run_id`；失败消息不泄露列级数据库原文（语义错误为固定摘要）。

4. **最小查询工作台**  
   - Web `http://127.0.0.1:15173` 可访问 SPA；经 Vite proxy 的 `/ready`、`/health`、`/api/v1/query-runs` 在栈健康时 HTTP 200。  
   - Playwright e2e（`./dev test`）：允许查询成功表格、拒绝 vs 执行失败、截断提示、就绪恢复后启用提交 — **4/4 通过**。  
   - UI 覆盖 idle / running / succeeded / rejected / failed / truncated / unavailable。

**未验证项：** 无（本维度所需证据均已新鲜采集）。

### 3.2 SQL 治理与数据正确性 — **20 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| AST 只读语义与单语句约束 | 6 | 6 | 完全通过 |
| 授权对象与 schema 范围 | 4 | 4 | 完全通过 |
| 数据库身份与双库隔离 | 4 | 4 | 完全通过 |
| 执行资源限制 | 3 | 3 | 完全通过 |
| 固定数据契约与业务口径 | 3 | 3 | 完全通过 |

**证据**

1. **AST 策略（`apps/api/src/decisionharbor/policy.py`）**  
   - 使用 SQLGlot `parse(..., read="postgres")` + 节点遍历；非字符串黑名单。  
   - 单语句、`PROHIBITED_NODES`、函数允许表、`SUPPORTED_NODES` 默认拒绝未知构造。  
   - 运行拒绝：多语句、DML/DDL、修改型 CTE、`SELECT INTO`、`FOR UPDATE`、`COPY`、`BEGIN;...` 等。  
   - 单元测试 `tests/unit/test_policy.py` 覆盖允许形态与大量拒绝用例。

2. **对象范围**  
   - 仅 `analytics` 下五张契约表；`information_schema`、`maintenance.dataset_seeds`、`public.alembic_version`、`pg_catalog`、CTE 遮蔽表名均拒绝。  
   - 运行时 `sql_object_not_allowed` / `sql_function_not_allowed` 已验证。

3. **双库身份**  
   - 真实登录 `analytics_reader`：`default_transaction_read_only=on`；`INSERT`/`UPDATE` 报 read-only；不可 CONNECT `platform`/`postgres`/`template1`。  
   - `platform_app` 仅能连 `platform`，不可 CONNECT `analytics`。  
   - API 容器环境仅有 `PLATFORM_DATABASE_URL` / `ANALYTICS_DATABASE_URL`，无 admin DSN。  
   - 执行器每次 `SET TRANSACTION READ ONLY` + `statement_timeout`。  
   - 集成测试 `test_runtime_database_identities_are_independently_bounded` 同路径覆盖。

4. **资源限制**  
   - 默认 `QUERY_MAX_ROWS=500`：`SELECT id FROM orders ORDER BY id` → 返回 500 行且 `truncated=true`。  
   - 默认 5s 超时：重 CROSS JOIN → HTTP 504 / `query_timeout` / `failed`。  
   - 集成测试另有 `QUERY_MAX_ROWS=2`、`QUERY_STATEMENT_TIMEOUT_MS=1` 配置路径。

5. **数据契约**  
   - `validate.py` 通过。  
   - 行数：customers 100、categories 8、products 50、orders 1000、order_items 3000。  
   - seed 标记 `maintenance.dataset_seeds` 与 contract/manifest 摘要一致。  
   - 重复 `docker compose run --rm init` → `bootstrap complete: dataset unchanged`。  
   - 业务营收口径与契约公式一致（见 3.1）。

**未验证项：** 无。

### 3.3 可运行性与可靠性 — **18.5 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | 部分通过 |

**证据**

1. **启动与就绪**  
   - `./dev up`（`--build --wait`）成功；postgres healthy → init 退出成功 → api healthy → web healthy。  
   - `/health` → 200 `{"data":{"status":"ok"}}`；`/ready` → 200 `{"data":{"status":"ready"}}`。  
   - 无 `container_name`；卷为项目级命名卷；宿主绑定 `127.0.0.1`。

2. **迁移与 seed**  
   - bootstrap：双库、角色、两套 Alembic、seed、授权。  
   - 幂等：二次 init `unchanged`。  
   - 集成测试 `test_seed_is_repeatable_and_conflicts_without_overwriting_rows` 覆盖冲突不覆盖数据。

3. **并行隔离**  
   - `dhgrok-review` 与 `dhgrok-review2` 同时 healthy。  
   - 独立网络 `dhgrok-review_default` / `dhgrok-review2_default`，独立卷，独立端口。  
   - 审计计数隔离：实例 1 `query_runs` 计数 37，实例 2 为 1（第二实例仅少量请求）。  
   - 停第二实例 postgres 时第一实例 `/ready` 仍 200。

4. **重启与故障可见性（部分）**  
   - **通过部分：** `docker compose restart api` 后 `/ready` 迅速恢复 200；Playwright 覆盖未就绪禁用提交与手动 recheck。  
   - **不足部分：** 将第二实例 `postgres` 完全 `stop` 后，对 `http://127.0.0.1:18081/ready` 使用 `curl --max-time 5` **超时且 0 字节**（未在时限内返回 503）。postgres 再启动后曾出现 503 `service_not_ready`，随后恢复 200。  
   - 根因倾向：SQLAlchemy 引擎未配置 `connect_timeout`（及就绪路径可能阻塞在连接池），依赖完全不可达时 `/ready` 不能稳定地「准确失败」。  
   - 故该 3 分子项按部分通过计 **1.5**。

**未验证项：** 无（故障场景已实测，结论为部分达标而非未执行）。

### 3.4 测试与验证证据 — **15 / 15**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 3 | 完全通过 |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**证据（本次 `./dev test`，exit 0）**

```text
pytest:  62 passed, 1 warning in ~1.27s
Vitest:  6 passed
Playwright e2e: 4 passed (~2.0s)
```

- 统一入口 `./dev` 的 `test` 子命令串行 api-test / web-test / e2e，失败会非零退出。  
- SQL 策略：`tests/unit/test_policy.py` 覆盖允许 SELECT/JOIN/CTE/窗口函数与拒绝 DML/多语句/对象/函数/TABLESAMPLE 等。  
- 双库集成：`test_postgres_contract.py`、`test_query_chain.py`、`test_seed.py`（schema、行数、身份、成功/拒绝/失败审计、截断、超时、启动恢复）。  
- 浏览器：`e2e/workbench.spec.ts` 四场景全部通过。  
- 警告：Starlette/FastAPI `TestClient` 关于 httpx2 的弃用提示 1 条，不影响退出码。

**未验证项：** 无。

### 3.5 代码质量与可维护性 — **10 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 3 | 完全通过 |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- 模块边界清晰：`api` → `QueryRunService` → `SqlPolicy` / `QueryRunRepository` / `PostgresQueryExecutor`；策略纯函数、执行器与仓储分离连接池；bootstrap 仅 init 服务持有 admin。  
- 错误码表完整、envelope 统一；状态机条件更新（`expected_status`）；容量信号量在 `finally` 释放；启动恢复 `execution_interrupted`。  
- 依赖版本钉死（FastAPI、SQLAlchemy、SQLGlot、psycopg、Vite/Playwright 等）；变更集中在 `apps/*`、`compose`、`datasets`、文档，未污染契约 CSV/contract 语义。  
- 可测试性：DI 构造 `create_app`、FakeService/FakeRepository 单元测试与真实集成测试分层良好。  

**说明：** `/ready` 在 DB 完全不可达时阻塞已在「可运行性」子项扣分，避免双重惩罚；代码结构本身不构成额外质量档降级。

**未验证项：** 无。

## 4. 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 |
| SQL 治理与数据正确性 | 20 |
| 可运行性与可靠性 | 18.5 |
| 测试与验证证据 | 15 |
| 代码质量与可维护性 | 10 |
| **技术总分** | **88.5 / 90** |

（本报告不计算与 Codex 的平均分，不计算质量原始 100 分，不给出视觉分。）

## 5. 产品文档建议分 — **5 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | 根 `AGENTS.md`、`docs/AGENTS.md`、`docs/index.md` 阅读顺序与职责清晰；README 指向正式入口。 |
| 设计完整性与可追溯性 | 2 | 2 | `docs/design/first-release-system-design.md` + `CONTEXT.md` 覆盖状态机、双库、策略、API、资源限制；与实现高度一致。 |
| 计划、运行/测试说明与实现一致性 | 2 | 2 | `docs/plan/first-release-implementation-plan.md`、`docs/status/project_status.md` 与 README 的 `./dev up|test|down|destroy`、并行端口说明可复现；本次运行命令与文档一致。 |

**文档建议总分：5 / 5**（供人工最终裁定；非技术 90 分组成部分的强制平均）。

## 6. P0 / P1 / P2 封顶判断

| 级别 | 条件 | 是否命中 | 可复核证据 |
| --- | --- | --- | --- |
| **P0 安全失败** | 用户 SQL 能写入、访问系统/未授权对象、经平台写入身份执行，或绕过 AST | **未命中** | 写操作与系统对象均策略拒绝；`analytics_reader` 只读且不可连 platform；API 无 admin；执行器显式只读事务。未发现可复核的治理绕过。 |
| **P1 基座失败** | 无法启动，或 health/ready/迁移/seed 核心链路不成立 | **未命中** | `./dev up` 成功；`/health`、`/ready` 200；init 迁移 seed 成功且可幂等。 |
| **P2 核心闭环缺失** | 不能同时证明允许+拒绝，或工作台不可用 | **未命中** | 允许查询与多种拒绝均 API 证明；Playwright 工作台主链 4 测通过。 |

**封顶结论：不适用封顶（无 P0/P1/P2）。**

## 7. 问题清单（按严重度）

### P2 / 中 — 依赖完全不可达时 `/ready` 可能阻塞

- **现象：** 停止 postgres 容器后，对 API `/ready` 的 5s curl 超时且无响应体；非及时 503。  
- **影响：** 故障可见性弱于设计「依赖未就绪时准确失败」；负载均衡/探活可能挂起。  
- **建议：** 为 SQLAlchemy/psycopg 设置 `connect_timeout`；就绪检查使用有界超时，失败即 `service_not_ready`。  
- **评分影响：** 已在「重启与故障可见性」记部分通过（1.5/3）。

### P3 / 低 — 前端已知错误码集合略窄

- **现象：** `App.tsx` 中 `KNOWN_ERRORS` 未包含例如 `unsupported_result_type`、`query_run_not_found`；未知码回落为通用文案。  
- **影响：** 少数失败路径 UX 信息略粗，不破坏安全或主链。  
- **建议：** 与 API `HTTP_STATUS_BY_CODE` 对齐维护。

### P3 / 低 — 测试弃用警告

- **现象：** `./dev test` 出现 Starlette TestClient / httpx2 弃用警告 1 条。  
- **影响：** 不改变 62 passed；未来依赖升级需关注。

### 信息 — 已文档化的首轮边界（不扣分）

- 无应用鉴权；查询并发容量为单 API 进程内信号量；结果不持久化。`docs/status/project_status.md` 已如实记录。

## 8. Compose 资源停止与最终 Git 状态

### 8.1 Compose

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `dhgrok-review` | `./dev destroy`（含 volumes） | 容器/网络/卷已移除 |
| `dhgrok-review2` | `./dev destroy`（含 volumes） | 容器/网络/卷已移除 |
| 其他宿主机项目（如 examforge*） | **未停止** | 仍在运行 |

收尾后 `docker ps -a --filter name=dhgrok`、`docker network/volume ls | grep dhgrok` 均为空。

### 8.2 候选工作树 Git

```text
HEAD: 6e3964f05b72d44a50f7d2a7657304a83cfa11c1
branch: v0.1.0/codex-gpt-5.6-sol-xhigh...origin/v0.1.0/codex-gpt-5.6-sol-xhigh
git status --short --branch: 无未提交改动
git diff --check: 退出码 0
```

评审过程未在候选工作树产生需清理的非忽略改动。

---

## 9. 评分一览（便于汇总）

| 项 | 值 |
| --- | --- |
| 技术总分 | **88.5 / 90** |
| 文档建议分 | **5 / 5** |
| 视觉分 | 不评 |
| 最终 100 分 / 平均分 | 不计算 |
| 封顶 | **无** |
| 关键扣分点 | `/ready` 在 DB 完全不可达时阻塞 → 可运行性 −1.5 |
| 未验证项 | **无**（计划内检查均有新鲜证据） |
