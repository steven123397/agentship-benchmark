# DecisionHarbor v0.1.0 — Grok 首轮独立评审

**候选：** `v0.1.0/kimicode-kimi-k3-thinking` @ `d14dbba7b2d36f71483853995022b5898f386309`

## 1. 独立性声明

- 本报告由 Grok Build 对本候选冻结 commit 做只读复现与审查。
- 全程未读取其他候选的 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未修改候选源码、候选分支、baseline 产品仓库、评分规范或其他归档文件；未执行 `git add` / `commit` / `push` / 创建 PR。
- 唯一写入文件为本 `grok-review.md`。
- 评分仅依据**本次**对冻结 commit 的代码审查与新鲜运行证据；不因 Agent/模型名称、开发自述或既往印象调整分数。
- 无新鲜证据的项目标为「未验证」，不按通过计分。

## 2. 评审对象、环境与执行命令

### 2.1 冻结确认

| 项 | 值 |
| --- | --- |
| 产品仓库 | `/home/liangjiaqi/projects/DecisionHarbor` |
| 候选工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/kimi-kimi-k3-thinking` |
| 分支 | `v0.1.0/kimicode-kimi-k3-thinking` |
| 冻结 HEAD | `d14dbba7b2d36f71483853995022b5898f386309` |
| baseline | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始前 `git status` | 干净 |
| 结束后 `git status` / `git diff --check` | 干净；`git diff --check` 退出码 0 |

### 2.2 环境

| 组件 | 版本 |
| --- | --- |
| 宿主 | WSL2 Linux `6.18.33.2-microsoft-standard-WSL2` |
| Docker | `29.1.3` |
| Docker Compose | `2.40.3` |
| 宿主 Python | `3.10.12`（应用在容器内 Python 3.13） |
| 宿主 Node | `v24.16.0` |
| 评审项目 1 | `dhkimi-rev` — API `127.0.0.1:18280`，Web `127.0.0.1:15273` |
| 评审项目 2 | `dhkimi-rev2` — API `127.0.0.1:18281`，Web `127.0.0.1:15274` |

### 2.3 主要执行命令（摘要）

```bash
git rev-parse HEAD && git status --short --branch
python3 datasets/sales-analytics-v1/validate.py

export DH_PROJECT_NAME=dhkimi-rev DH_API_PORT=18280 DH_WEB_PORT=15273
docker compose up --build --wait --detach
curl -sS http://127.0.0.1:18280/health
curl -sS http://127.0.0.1:18280/ready

# 允许/拒绝/失败/截断/超时
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:18280/api/v1/query-runs
curl http://127.0.0.1:18280/api/v1/query-runs/<id>

# 双库身份、重复 migrate/seed、restart、stop db 故障探活
docker compose exec -T db ...
docker compose run --rm migrate
docker compose restart api
docker compose stop db && curl --max-time 5 .../ready

# 测试
docker compose run --rm --no-deps --entrypoint python api -m pytest tests/unit -q
docker compose run --rm --no-deps --entrypoint python migrate -m pytest tests/integration -q
docker compose --profile test run --rm web-unit
docker compose --profile test run --rm e2e

# 并行
export DH_PROJECT_NAME=dhkimi-rev2 DH_API_PORT=18281 DH_WEB_PORT=15274
docker compose up --build --wait --detach

# 收尾
DH_PROJECT_NAME=dhkimi-rev2 docker compose down -v
DH_PROJECT_NAME=dhkimi-rev  docker compose down -v
git status --short --branch && git diff --check
```

阅读：`AGENTS.md`、`README.md`、`docs/index.md`、`docs/background/`、`docs/design/`、`docs/plan/`、`docs/status/`，以及 `api/`、`web/`、`db/`、`e2e/`、`scripts/`、`docker-compose.yml`。

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
   - `POST /api/v1/query-runs` 返回 `{record, result}`；成功例 `id=546a3134-565c-4c80-b242-5d5462e3a834`，`status=succeeded`，`rows:[[100]]`。  
   - `GET /api/v1/query-runs/{id}` 仅返回 `record`（含 `sql`、状态、行数、耗时），**不含结果行**。

2. **允许查询正确性**  
   - 客户数 100。  
   - 区域营收（`confirmed` × `quantity * unit_price * (1 - discount_rate)`）：East `2768355.33`，South `2329370.48`，Central `2076252.00`，West `1989615.57`，North `1895196.27`。列类型映射为 `character varying` / `numeric`。

3. **拒绝与失败**  

   | 输入 | status | error_code |
   | --- | --- | --- |
   | `DELETE FROM customers` | `rejected` | `POLICY_NON_QUERY_STATEMENT` |
   | `SELECT 1; SELECT 2` | `rejected` | `POLICY_MULTI_STATEMENT` |
   | `pg_catalog.pg_class` | `rejected` | `POLICY_UNAUTHORIZED_OBJECT` |
   | `platform.query_runs` | `rejected` | `POLICY_UNAUTHORIZED_OBJECT` |
   | 修改型 CTE | `rejected` | `POLICY_WRITE_OPERATION` |
   | `SELECT INTO TEMP` | `rejected` | `POLICY_WRITE_OPERATION` |
   | 未知列 | `failed` | `EXECUTION_ERROR` |
   | `pg_sleep(6)` | `failed` | `QUERY_TIMEOUT` |
   | 交叉积超行 | `succeeded` + `truncated=true`，`row_count=1000` | — |

4. **工作台**  
   - nginx 反代 `/api`、`/health`、`/ready`；Playwright **3/3 通过**（结果表、执行中、拒绝码与记录标识）。

**未验证项：** 无。

### 3.2 SQL 治理与数据正确性 — **20 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| AST 只读语义与单语句约束 | 6 | 6 | 完全通过 |
| 授权对象与 schema 范围 | 4 | 4 | 完全通过 |
| 数据库身份与双库隔离 | 4 | 4 | 完全通过 |
| 执行资源限制 | 3 | 3 | 完全通过 |
| 固定数据契约与业务口径 | 3 | 3 | 完全通过 |

**证据**

1. **AST（`api/app/policy.py`）**  
   - SQLGlot PostgreSQL 解析；单语句；根须为查询表达式；全树禁止写节点与 `Into`；对象白名单 + schema `analytics`。  
   - 单元测试 **39 passed**（允许 JOIN/CTE/UNION/窗口/业务公式；拒绝 DML/DDL/多语句/修改型 CTE/系统目录/跨 schema）。

2. **对象范围**  
   - 仅五张契约表；`analytics.` 限定或默认 search_path；`public.customers`、`pg_catalog`、`platform.*` 运行时拒绝。

3. **双库身份**  
   - 用户 SQL 经 `analytics_readonly` + psycopg 执行。  
   - 实测：`analytics_readonly` **不可 CONNECT `platform`**；`platform_app` **不可 CONNECT `analytics`**；只读身份 `INSERT` 被拒。  
   - 集成测试同路径覆盖（`test_readonly_cannot_*`、`test_*_cannot_reach_*`）。  
   - 注：`default_transaction_read_only` 为 off，执行器未 `SET TRANSACTION READ ONLY`；在已验证的表级/库级权限下仍计完全通过，记入改进项。

4. **资源限制**  
   - `MAX_ROWS=1000` 截断成功；`STATEMENT_TIMEOUT_MS=5000` 映射 `QUERY_TIMEOUT`。

5. **数据契约**  
   - `validate.py` 通过；行数 100/8/50/1000/3000；营收口径正确。  
   - seed 为事务内 TRUNCATE+COPY+计数校验；重复 `migrate` 终态一致。

**未验证项：** 无。

### 3.3 可运行性与可靠性 — **18.5 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | **部分通过** |

**证据**

1. **启动**  
   - `docker compose up --build --wait`（等价 `scripts/run.sh` 核心）成功；`/health` 200、`/ready` 200。  
   - 无 `container_name`；db 不映射宿主端口；`DH_PROJECT_NAME` / 端口可配置；独立 migrate 服务。

2. **迁移与 seed**  
   - 首次 init 建库角色；Alembic 双链；seed 行数校验；重复 migrate 输出 `seed ok` 且计数不变。

3. **并行**  
   - `dhkimi-rev` 与 `dhkimi-rev2` 同时 healthy；独立网络/卷；审计计数 **24 vs 1**。

4. **重启与故障（部分）**  
   - `restart api` 后 `/ready` 立即 200。  
   - `stop db` 后对 `/ready` 的 5s curl **超时无响应**；db 启动后先 **503 `not_ready`** 再 200。  
   - 代码已对就绪路径使用 `connect_timeout=2`，但依赖完全不可达时仍可能阻塞（如已建立连接/池路径），→ **1.5/3**。

**未验证项：** 无。

### 3.4 测试与验证证据 — **15 / 15**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 3 | 完全通过 |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**本次新鲜结果**

| 套件 | 结果 |
| --- | --- |
| `pytest tests/unit` | **39 passed** |
| `pytest tests/integration` | **15 passed**（1 条 TestClient 弃用警告） |
| Vitest `web-unit` | **6 passed** |
| Playwright e2e | **3 passed** |

`scripts/test.sh` 串联上述四层；组件均以非零失败语义的 pytest/vitest/playwright 执行。集成覆盖身份分离、超时、截断、seed 幂等、API 主链。

**未验证项：** 无（未再单独跑一遍完整 `scripts/test.sh` 单体 shell，但各步骤已按同一入口等价命令验证）。

### 3.5 代码质量与可维护性 — **8.5 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | **部分通过** |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- **边界：** `policy` / `executor` / `audit` / `routers` / 独立 `migrate` 服务清晰；用户路径仅 readonly URL。  
- **配置与错误（部分）：**  
  - `EXECUTION_ERROR` 消息含 PostgreSQL primary 文本（如 `column "missing_column" does not exist`）。  
  - Compose 将 `ANALYTICS_OWNER_DATABASE_URL` 一并注入 **api** 服务（设计写「API 运行路径不使用 owner」，但凭据仍在进程环境中）。  
  - 执行器未强制 `SET TRANSACTION READ ONLY` / 角色默认只读。  
- **可测试性：** 策略纯函数、分层测试完备；依赖 `requirements.txt` 固定。

**未验证项：** 无。

## 4. 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 |
| SQL 治理与数据正确性 | 20 |
| 可运行性与可靠性 | 18.5 |
| 测试与验证证据 | 15 |
| 代码质量与可维护性 | 8.5 |
| **技术总分** | **87 / 90** |

（不计算平均分或质量原始 100 分；不评视觉分。）

## 5. 产品文档建议分 — **4 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | `docs/index.md`、AGENTS、README 清晰；design 拆分为 overview/governance/api/data/testing。 |
| 设计完整性与可追溯性 | 2 | 2 | 设计文档与实现高度对应（双库身份、seed 截断重载理由、Compose 约束）。 |
| 计划、运行/测试说明与实现一致性 | 2 | 1 | `scripts/run.sh`/`test.sh` 与 README 可复现；但 `docs/status/project_status.md` 仍写 HEAD `1fb48f4`、工作区「尚未提交」，与冻结结果不一致。 |

**文档建议总分：4 / 5**。

## 6. P0 / P1 / P2 封顶判断

| 级别 | 条件 | 命中 | 证据 |
| --- | --- | --- | --- |
| **P0** | 用户 SQL 可写/越权/平台身份执行/绕过 AST | **否** | 写操作与未授权对象策略拒绝；只读角色无写权限；跨库 CONNECT 被拒；执行器用 readonly URL。 |
| **P1** | 无法启动或 health/ready/迁移/seed 失败 | **否** | 干净启动成功；health/ready/迁移/seed 成立。 |
| **P2** | 不能同时证明允许+拒绝，或工作台不可用 | **否** | API 与 Playwright 均证明允许与拒绝。 |

**封顶：不适用。**

## 7. 问题清单（按严重度）

### 中 — DB 完全停止时 `/ready` 可能阻塞

- 5s curl 超时 0 字节；恢复后 503→200。  
- 建议：确保所有就绪连接路径均有界超时，并避免依赖已失效的池连接挂起。

### 中 — 执行错误向客户端泄露数据库原文

- `EXECUTION_ERROR`：`数据库执行错误：column "missing_column" does not exist`。  
- 建议：用户侧固定安全摘要；详情写日志。

### 低 — API 进程环境含 `ANALYTICS_OWNER_DATABASE_URL`

- 与设计「运行路径不使用 owner」不完全一致；migrate 服务已分离，但 api 仍注入 owner DSN。  
- 建议：api 仅注入 platform + readonly。

### 低 — 缺少角色级/事务级只读加固

- `default_transaction_read_only=off`；执行器未 `SET TRANSACTION READ ONLY`。  
- 当前靠表权限成立，纵深不足。

### 低 — 无函数允许列表

- `SELECT pg_sleep(2)` 可通过策略（e2e 依赖此点）；依赖超时兜底。首轮可接受，但任意函数面较宽。

### 信息 — 状态文档过时

- `project_status.md` 写 baseline HEAD 与「未提交」，与冻结交付不符。

## 8. Compose 资源停止与最终 Git 状态

### 8.1 Compose

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `dhkimi-rev` | `docker compose down -v` | 已移除 |
| `dhkimi-rev2` | `docker compose down -v` | 已移除 |
| 其他项目（examforge* 等） | **未停止** | 仍在运行 |

### 8.2 Git

```text
HEAD: d14dbba7b2d36f71483853995022b5898f386309
branch: v0.1.0/kimicode-kimi-k3-thinking...origin/v0.1.0/kimicode-kimi-k3-thinking
git status --short --branch: 无未提交改动
git diff --check: 退出码 0
```

---

## 9. 一览

| 项 | 值 |
| --- | --- |
| 技术总分 | **87 / 90** |
| 文档建议分 | **4 / 5** |
| 视觉 / 最终 100 / 平均 | 不评 / 不计算 |
| 封顶 | **无** |
| 主要扣分 | 故障可见性 −1.5；配置/错误处理 −1.5 |
| 未验证项 | **无** |
