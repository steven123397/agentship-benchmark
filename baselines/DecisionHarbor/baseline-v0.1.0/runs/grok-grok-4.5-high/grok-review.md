# DecisionHarbor v0.1.0 — Grok 首轮独立评审

**候选：** `v0.1.0/grokbuild-grok-4.5-high` @ `8bbe8de2875d32804067d8418fb5bc6fc8cb431c`

## 1. 独立性声明

- 本报告由 Grok Build 对本候选冻结 commit 做只读复现与审查。
- 全程未读取其他候选的 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md` 或任何其他首轮审查结论。
- 未修改候选源码、候选分支、baseline 产品仓库、评分规范或其他归档文件；未执行 `git add` / `commit` / `push` / 创建 PR。
- 唯一写入文件为本 `grok-review.md`。
- 评分仅依据**本次**对冻结 commit 的代码审查与新鲜运行证据；不因 Agent/模型名称、开发阶段记忆、自述或既往印象调整分数。
- 无新鲜证据的项目标为「未验证」，不按通过计分。

## 2. 评审对象、环境与执行命令

### 2.1 冻结确认

| 项 | 值 |
| --- | --- |
| 产品仓库 | `/home/liangjiaqi/projects/DecisionHarbor` |
| 候选工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.5-high` |
| 分支 | `v0.1.0/grokbuild-grok-4.5-high` |
| 冻结 HEAD | `8bbe8de2875d32804067d8418fb5bc6fc8cb431c` |
| baseline | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始前 `git status` | 干净（无未提交改动） |
| 结束后 `git status` / `git diff --check` | 干净；`git diff --check` 退出码 0 |

### 2.2 环境

| 组件 | 版本 |
| --- | --- |
| 宿主 | WSL2 Linux `6.18.33.2-microsoft-standard-WSL2` |
| Docker | `29.1.3` |
| Docker Compose | `2.40.3` |
| 宿主 Python | `3.10.12`（应用/测试在容器内） |
| 宿主 Node | `v24.16.0` |
| 评审项目 1 | `dhgrok-self-rev` — API `127.0.0.1:18180`，Web `127.0.0.1:15183` |
| 评审项目 2 | `dhgrok-self-rev2` — API `127.0.0.1:18181`，Web `127.0.0.1:15184` |

### 2.3 主要执行命令（摘要）

```bash
git rev-parse HEAD && git status --short --branch
python3 datasets/sales-analytics-v1/validate.py

# 干净项目启动（shell 覆盖 .env 中的项目名/端口）
export COMPOSE_PROJECT_NAME=dhgrok-self-rev API_HOST_PORT=18180 WEB_HOST_PORT=15183 \
  VITE_API_BASE_URL=http://127.0.0.1:18180
docker compose up -d --build
curl -fsS http://127.0.0.1:18180/health
curl -fsS http://127.0.0.1:18180/ready

# 允许/拒绝/失败/行数/超时 API
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:18180/api/v1/query-runs
curl http://127.0.0.1:18180/api/v1/query-runs/<id>

# 双库身份（postgres 容器内 psql）
# analytics_readonly / platform_app 跨库 CONNECT 与写权限探测

docker compose restart api
docker compose exec -T api pytest tests/unit -q          # 18 passed
docker compose exec -T api pytest tests/integration -q   # 8 passed（栈健康后）

# 非默认 Web 端口需覆盖 CORS_ORIGINS，否则浏览器 CORS 失败
export CORS_ORIGINS=http://127.0.0.1:15183,http://localhost:15183
docker compose up -d api
(cd apps/web && WEB_BASE_URL=http://127.0.0.1:15183 npm run test:e2e)  # 2 passed

# 并行第二实例（本地镜像 retag + --no-build；Docker Hub 拉 nginx 曾 EOF）
export COMPOSE_PROJECT_NAME=dhgrok-self-rev2 API_HOST_PORT=18181 WEB_HOST_PORT=15184
docker compose up -d --no-build

# 收尾
COMPOSE_PROJECT_NAME=dhgrok-self-rev2 docker compose down -v
COMPOSE_PROJECT_NAME=dhgrok-self-rev  docker compose down -v
git status --short --branch && git diff --check
```

阅读：`AGENTS.md`、`README.md`、`docs/index.md`、`docs/background/`、`docs/design/`、`docs/plan/`、`docs/status/`，以及 `apps/api`、`apps/web`、`docker-compose.yml`、`scripts/*`。

**说明：** 首次按默认 `COMPOSE_PROJECT_NAME=decisionharbor` 启动时 API 因 postgres 密码认证失败退出（疑似历史卷凭据不一致）；`docker compose down -v` 后换干净项目名可正常启动。不计入环境故障免责，记为可运行性相关风险。

## 3. 技术评分（/90）

子项档位：未通过 `0`，部分通过 `50%`，完全通过满分。

### 3.1 功能与外部契约 — **25 / 25**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**证据**

1. **API 生命周期**  
   - `POST /api/v1/query-runs` 返回 envelope：`status`、`id`、`data`/`error`。  
   - 成功例：`SELECT count(*) AS customer_count FROM customers` → `status=succeeded`，`rows:[[100]]`，`id=7f04e858-29c3-4f61-ae6e-2fbb22bfe4b9`。  
   - `GET /api/v1/query-runs/{id}` 返回审计事实（`sql_text`、`status`、`row_count`、`duration_ms`、时间戳），**不含结果行**。

2. **允许查询正确性**  
   - 客户数 100。  
   - 区域营收（`confirmed` × `quantity * unit_price * (1 - discount_rate)`）：East `2768355.33`，South `2329370.48`，Central `2076252.00`，West `1989615.57`，North `1895196.27`。

3. **拒绝与失败**（HTTP 均为 200，以 body `status` 区分——与本候选设计一致，未伪装为 `succeeded`）  

   | 输入 | body status | error.code |
   | --- | --- | --- |
   | `DELETE FROM customers` | `rejected` | `POLICY_FORBIDDEN_STATEMENT` |
   | `SELECT 1; SELECT 2` | `rejected` | `POLICY_MULTI_STATEMENT` |
   | `pg_catalog.pg_class` | `rejected` | `POLICY_FORBIDDEN_OBJECT` |
   | `query_runs` 表名 | `rejected` | `POLICY_FORBIDDEN_OBJECT` |
   | 修改型 CTE | `rejected` | `POLICY_FORBIDDEN_STATEMENT` |
   | `SELECT INTO TEMP` | `rejected` | `POLICY_FORBIDDEN_STATEMENT` |
   | 未知列 | `failed` | `EXECUTION_DATABASE_ERROR` |
   | 超行数 | `failed` | `EXECUTION_ROW_LIMIT` |
   | 重 CROSS JOIN | `failed` | `EXECUTION_TIMEOUT` |

4. **工作台**  
   - Web 根路径 HTTP 200；Playwright `e2e/workbench.spec.ts` 在 CORS 配置正确后 **2/2 通过**（允许聚合 + 拒绝 DELETE）。  
   - UI 展示执行中、成功表、拒绝/错误信息。

**未验证项：** 无。

### 3.2 SQL 治理与数据正确性 — **18 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| AST 只读语义与单语句约束 | 6 | 6 | 完全通过 |
| 授权对象与 schema 范围 | 4 | 4 | 完全通过 |
| 数据库身份与双库隔离 | 4 | 2 | **部分通过** |
| 执行资源限制 | 3 | 3 | 完全通过 |
| 固定数据契约与业务口径 | 3 | 3 | 完全通过 |

**证据**

1. **AST（`apps/api/app/policy.py`）**  
   - SQLGlot `parse(..., read="postgres")` + 禁止节点类型 + 对象白名单；单元测试覆盖允许 SELECT/JOIN/CTE/UNION、拒绝 DML/DDL/多语句/修改型 CTE/SELECT INTO/系统目录等（`tests/unit/test_policy.py`，**18 passed**）。

2. **对象范围**  
   - 仅五张业务表；schema 限 `public`（分析库内表在 public）；`pg_catalog` / `information_schema` / 未授权表运行时拒绝。

3. **双库身份（部分）**  
   - **通过：** 用户执行路径使用 `ANALYTICS_READONLY_URL`；`SET TRANSACTION READ ONLY`；`analytics_readonly` 对 `customers` 的 `INSERT` 被拒；`platform_app` 对 analytics 业务表无写权限。  
   - **不足：**  
     - `analytics_readonly` **可 CONNECT `platform`** 并 `\dt` 列出 `query_runs` / `alembic_version`（`SELECT` 被表级权限拒绝，但连接与对象发现未隔断）。  
     - `platform_app` **可 CONNECT `analytics`**（bootstrap 显式 `GRANT CONNECT ... TO platform_app`）。  
     - `default_transaction_read_only` 对 `analytics_readonly` 为 **off**（依赖表权限与执行器 SET）。  
     - API 容器环境同时注入 `POSTGRES_ADMIN_URL` 与 `ANALYTICS_MIGRATOR_URL`（引导/迁移身份与查询进程同驻）。  
   - 故「独立只读身份执行用户 SQL」成立，但「双库隔离」不完整 → **2/4**。

4. **资源限制**  
   - 默认 `MAX_RESULT_ROWS=1000`：`order_items` 全表扫描 → `EXECUTION_ROW_LIMIT`。  
   - 默认 5s：`CROSS JOIN` 三重 → `EXECUTION_TIMEOUT`。  
   - 注：超限表现为 **failed**，非截断成功（与设计文档一致）。

5. **数据契约**  
   - `validate.py` 通过；行数 100/8/50/1000/3000；营收口径见 3.1。

**未验证项：** 无。

### 3.3 可运行性与可靠性 — **18.5 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | **部分通过** |

**证据**

1. **启动与就绪**  
   - 干净项目 `docker compose up -d --build` 后 `/health` → `{"status":"ok"}`，`/ready` → `{"status":"ready",... seed ...}`。  
   - 无 `container_name`；DB 不映射宿主端口；项目名与端口可配置。

2. **迁移与 seed**  
   - entrypoint 执行 bootstrap + 双 Alembic + seed + readonly grants。  
   - 固定数据行数与 `analytics_seed_meta` 正确。  
   - 注：`seed_analytics.py` **每次 TRUNCATE 后全量重载**（非「摘要匹配则 no-op」）；终态可重复、不重复累加行数。仍计完全通过（不破坏契约终态）。

3. **并行隔离**  
   - `dhgrok-self-rev` 与 `dhgrok-self-rev2` 同时 healthy；独立网络与 `pgdata` 卷；审计计数 **25 vs 1**。  
   - （二次构建时 Docker Hub 对 `nginx:1.27-alpine` 曾 EOF；用本地已有镜像 retag + `--no-build` 完成并行复现。属评测网络波动，产品侧并行配置本身成立。）

4. **重启与故障（部分）**  
   - `docker compose restart api` 后 `/ready` 迅速 200。  
   - `stop db` 后对 `/ready` 的 5s curl **超时无响应**；db 再启动后先 **503 `not_ready`** 再 200。依赖完全不可达时不能稳定「准确失败」→ **1.5/3**。

**额外观察（计入问题清单，未再重复扣本子项满分以外分数）：**

- 仓库 `.env` 将 `CORS_ORIGINS` 钉在 `5173`；仅改 `WEB_HOST_PORT` 时浏览器工作台 CORS 失败（Playwright 曾报 `Failed to fetch`）。覆盖 `CORS_ORIGINS` 后 e2e 通过。

**未验证项：** 无。

### 3.4 测试与验证证据 — **15 / 15**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 3 | 完全通过 |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**证据（本次新鲜）**

| 套件 | 结果 |
| --- | --- |
| `pytest tests/unit`（容器） | **18 passed** |
| `pytest tests/integration`（容器，栈健康时） | **8 passed**（中途 db stop 后曾 1 fail on `/ready`，恢复后全绿） |
| Playwright `npm run test:e2e` | **2 passed**（允许 + 拒绝；需正确 CORS） |
| `scripts/test.sh` | 入口存在且串联 validate/up/pytest/e2e；组件已分别验证 |

统一入口失败会产生非零退出（`set -e`）。策略单元与集成覆盖允许/拒绝/只读写拒绝/行数/seed 行数等。

**未验证项：** 无（未在单次命令中完整跑通 `scripts/test.sh` 全链路，但等价组件均有新鲜通过证据）。

### 3.5 代码质量与可维护性 — **8.5 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | **部分通过** |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- **边界：** `policy` / `service` / `executor` / `repository` / `main` 职责清晰；用户 SQL 走只读 engine。  
- **配置与错误（部分）：**  
  - 执行失败 `_short_error` **回传 PostgreSQL 原文**（例：`column "missing_column" does not exist LINE 1: ...`），违反「不暴露数据库原始错误」类质量预期。  
  - API 进程持有 admin/migrator DSN；就绪检查无明确 `connect_timeout`。  
  - `.env` 中 `CORS_ORIGINS` 与 `WEB_HOST_PORT` 脱钩，并行端口易踩坑。  
- **可测试性：** 策略纯模块 + DI `create_app`；依赖 `requirements.txt` 固定版本。  

**未验证项：** 无。

## 4. 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 |
| SQL 治理与数据正确性 | 18 |
| 可运行性与可靠性 | 18.5 |
| 测试与验证证据 | 15 |
| 代码质量与可维护性 | 8.5 |
| **技术总分** | **75 / 90** |

（不计算与其他审查者的平均分，不计算质量原始 100 分，不评视觉分。）

## 5. 产品文档建议分 — **4 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | `docs/index.md`、根/`docs` `AGENTS.md`、README 入口清晰。 |
| 设计完整性与可追溯性 | 2 | 2 | `docs/design/first-round-system.md` + `CONTEXT.md` 覆盖状态、策略、API、双库、测试接缝。 |
| 计划、运行/测试说明与实现一致性 | 2 | 1 | README/`scripts` 与实现大体一致；但文档/状态强调「幂等 seed」，实现为 **每次 TRUNCATE 全量重载**；并行端口与 `.env` CORS 钉死未充分警示。 |

**文档建议总分：4 / 5**（供人工最终裁定）。

## 6. P0 / P1 / P2 封顶判断

| 级别 | 条件 | 命中 | 证据 |
| --- | --- | --- | --- |
| **P0** | 用户 SQL 可写、可访问系统/未授权对象、经平台写入身份执行，或绕过 AST | **否** | 写操作/系统对象策略拒绝；执行器用只读 URL；只读角色写表被拒；未发现 AST 绕过写路径。跨库 CONNECT 弱点不构成「用户 SQL 经平台写入身份执行」。 |
| **P1** | 无法启动或 health/ready/迁移/seed 核心失败 | **否** | 干净卷上启动成功；health/ready/迁移/seed 成立。 |
| **P2** | 不能同时证明允许+拒绝，或工作台不可用 | **否** | 允许与拒绝 API 均证明；Playwright 主链 2 passed。 |

**封顶：不适用。**

## 7. 问题清单（按严重度）

### 高 — 双库 CONNECT 隔离不完整

- `analytics_readonly` 可连接 `platform` 并枚举表；`platform_app` 可连接 `analytics`。  
- 建议：REVOKE 跨库 CONNECT；角色级 `default_transaction_read_only=on`；收紧 bootstrap grants。

### 高 — API 进程持有 admin / migrator 凭据

- Compose 将 `POSTGRES_ADMIN_URL`、`ANALYTICS_MIGRATOR_URL` 注入 **api** 服务；引导与查询同进程。  
- 建议：一次性 init 容器持有 admin；API 仅 runtime 双 URL。

### 中 — 错误摘要泄露数据库原文

- `EXECUTION_DATABASE_ERROR` 消息含列名与 `LINE 1` 片段。  
- 建议：对用户固定安全摘要，细节仅写服务端日志。

### 中 — 非默认端口下 CORS / 工作台失败

- `.env` 固定 `CORS_ORIGINS=...:5173`；改 `WEB_HOST_PORT` 后浏览器 `Failed to fetch`。  
- 建议：默认由 `WEB_HOST_PORT` 推导 CORS，或文档强制同步变量。

### 中 — `/ready` 在 DB 完全停止时阻塞

- 5s curl 超时无 body；恢复后才见 503。  
- 建议：连接 `connect_timeout` + 有界就绪检查。

### 低 — 每次 API 启动 seed TRUNCATE 重载

- 重启期间分析数据被清空重写；非「匹配则 unchanged」。  
- 建议：摘要一致则跳过；冲突再失败。

### 低 — 结果列类型恒为 `unknown`

- `executor` 未映射 PG 类型 OID。

### 信息 — 无应用鉴权；宿主端口默认 `0.0.0.0`

- README 已提示仅可信本地；绑定范围仍偏宽。

## 8. Compose 资源停止与最终 Git 状态

### 8.1 Compose

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `dhgrok-self-rev` | `docker compose down -v` | 已移除 |
| `dhgrok-self-rev2` | `docker compose down -v` | 已移除 |
| 其他项目（examforge* 等） | **未停止** | 仍在运行 |

### 8.2 Git

```text
HEAD: 8bbe8de2875d32804067d8418fb5bc6fc8cb431c
branch: v0.1.0/grokbuild-grok-4.5-high...origin/v0.1.0/grokbuild-grok-4.5-high
git status --short --branch: 无未提交改动
git diff --check: 退出码 0
```

---

## 9. 一览

| 项 | 值 |
| --- | --- |
| 技术总分 | **75 / 90** |
| 文档建议分 | **4 / 5** |
| 视觉 / 最终 100 / 平均 | 不评 / 不计算 |
| 封顶 | **无** |
| 主要扣分 | 双库隔离部分 −2；就绪阻塞 −1.5；配置/错误泄露 −1.5 |
| 未验证项 | **无** |
