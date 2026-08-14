# DecisionHarbor v0.1.0 — Grok 首轮独立评审

**候选：** `v0.1.0/claudecode-claude-fable-5` @ `9e11644de468e1008784c42ff093ce6a0c96aae9`  
**RESULT_COMMIT：** `9e11644de468e1008784c42ff093ce6a0c96aae9`  
**冻结：** `completion.coordinatorFrozen=true`

## 1. 独立性声明

- 本报告由 Grok Build 对本候选冻结 commit 做只读复现与审查。
- 全程未读取其他候选 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未修改候选源码/分支/baseline/评分规范；未 git add/commit/push/创建 PR。
- 唯一写入：本 `grok-review.md`。
- 评分仅依据本次对冻结 commit 的代码与运行证据；不因 Agent/模型/耗时/既往印象调分。
- 无新鲜证据标「未验证」，不按通过处理。

## 2. 评审对象、环境与命令

### 2.1 冻结确认

| 项 | 值 |
| --- | --- |
| 工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/claudecode-claude-fable-5` |
| 分支 | `v0.1.0/claudecode-claude-fable-5` |
| HEAD | `9e11644de468e1008784c42ff093ce6a0c96aae9` |
| baseline | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始/结束 git status | 干净 |
| `git diff --check` | 0 |

### 2.2 环境

| 组件 | 版本 |
| --- | --- |
| Docker / Compose | 29.1.3 / 2.40.3 |
| 宿主 Python / Node | 3.10.12 / v24.16.0 |
| 主实例 | `decisionharbor-claudecode-claude-fable-5` — API `127.0.0.1:8100`，Web `127.0.0.1:5173` |
| 并行实例 | `dhclaude-rev2` — API `127.0.0.1:18581`，Web `127.0.0.1:15574` |

### 2.3 主要命令摘要

```bash
git rev-parse HEAD && git status --short --branch
python3 datasets/sales-analytics-v1/validate.py

./dev.sh up          # 构建、迁移、seed、等待 /ready
curl http://127.0.0.1:8100/health   # 200 {"status":"ok"}
curl http://127.0.0.1:8100/ready    # 200 {"status":"ready"}

# 允许/拒绝/截断/超时
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:8100/api/v1/query-runs

# 双库身份、seed 跳过、restart、stop db
docker compose exec -T db ...
docker compose run --rm ... api python -m app.seed
docker compose restart api
docker compose stop db && curl --max-time 8 .../ready

# 测试
docker compose run --rm --no-deps api pytest -m "not integration" -q  # 47
docker compose run --rm api pytest -m integration -q                  # 19
docker compose run --rm --no-deps web npx vitest run                  # 5
docker compose --profile test run --rm e2e                            # 3

# 并行第二项目
COMPOSE_PROJECT_NAME=dhclaude-rev2 WEB_PORT=15574 API_PORT=18581 ...

./dev.sh down --remove-orphans --volumes  # 两项目均停止
```

阅读：`AGENTS.md`、`README.md`、`docs/**`、`dev.sh`、`compose.yaml`、`api/`、`web/`、`e2e/`、`db/init/`。

## 3. 技术评分（/90）

### 3.1 功能与外部契约 — **25 / 25**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**证据**

1. **API：** `POST /api/v1/query-runs` → 201，`query_run` + 可选 `result`；`GET` 返回审计（含 `sql_text`），**无结果行**。  
2. **允许：** `count(*) FROM customers` → `[[100]]`；`confirmed` 订单 `[[720]]`；区域营收 East `2768355.33` … North `1895196.27`；numeric 以字符串返回。  
3. **拒绝/失败：** DELETE/多语句/系统目录/`public.customers`/修改型 CTE/`SELECT INTO` → `rejected` + 稳定 code；`1/0` → `failed` `execution_error`「division by zero」；`PG_SLEEP(10)` → `execution_timeout`。  
4. **工作台：** Web 200；Playwright 3/3（成功表、执行中、拒绝码）。

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

1. **AST（`api/app/policy.py`）：** SQLGlot postgres；单语句；禁止 DML/DDL/事务/COPY/CALL 等；`SELECT INTO`/行锁；归一化后执行。单元 **47 passed**。  
2. **对象：** 仅契约五表；schema 限 `analytics` 或未限定（`search_path=analytics`）；`public.*`、`pg_catalog`、三段限定拒绝。  
3. **双库身份：**  
   - API 环境仅 `PLATFORM_DATABASE_URL` + `ANALYTICS_READER_URL`（**无 owner/super**）。  
   - owner 仅一次性 `docker compose run` 迁移/seed。  
   - 实测：reader `default_transaction_read_only=on`；INSERT 只读事务失败；**双向 CONNECT 拒绝**；writer 不可连 analytics。  
4. **资源：** `SET LOCAL statement_timeout`；`fetchmany(row_limit+1)` 截断 `truncated=true`、`row_count=1000`。  
5. **契约：** validate 通过；行数与 confirmed=720、营收口径正确；seed 匹配则「跳过」。

**未验证项：** 无。

### 3.3 可运行性与可靠性 — **18.5 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | **部分通过** |

**证据**

1. **启动：** `./dev.sh up` 构建、双 Alembic、seed、等待 `/ready` 成功。`/health`、`/ready` 200；`/ready` 校验两库迁移 head。  
2. **迁移/seed：** 空卷装载；已装载则跳过；冲突中止。  
3. **并行：** 两项目同时运行；独立网络/卷；审计计数 **77 vs 2**。  
4. **重启/故障（部分）：**  
   - `restart api` 后 ready 立即 200。  
   - `stop db` 后多次 curl **HTTP 000/超时无 body**（非 503）；db 恢复后出现 **503 unavailable** 再 200。  
   - 依赖完全不可达时未能「准确失败」→ **1.5/3**。

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
| `pytest -m "not integration"` | **47 passed** |
| `pytest -m integration` | **19 passed** |
| Vitest | **5 passed** |
| Playwright e2e | **3 passed** |

`./dev.sh test` 统一入口串行上述四层；失败非零。集成覆盖跨库 CONNECT、只读写拒绝、超时、截断、API 主链。

**未验证项：** 无。

### 3.5 代码质量与可维护性 — **10 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 3 | 完全通过 |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- **边界：** policy 纯函数 → executor 只收归一化 SQL → query_runs 仅 platform；owner 仅 CLI 一次性流程。  
- **配置/错误：** 错误摘要截断首行；超长 SQL 不入审计；就绪双库；设计文档与代码注释对齐。DB 全挂时 ready 阻塞属可改进点，已在可运行性扣分，结构本身不额外降档。  
- **可测试性：** 镜像含 dev 依赖与 tests；契约模块集中；分层清晰。  
- **依赖：** `PIP_INDEX_URL`/`NPM_CONFIG_REGISTRY` 可配置。

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

（不评视觉；不计算 100 分或平均分。）

## 5. 产品文档建议分 — **5 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | `docs/index.md` 分 design/plan/status；根 AGENTS 阅读顺序清晰。 |
| 设计完整性与可追溯性 | 2 | 2 | architecture、query-governance、query-runs-api、workbench、local-runtime 与实现一致。 |
| 计划、运行/测试说明与实现一致性 | 2 | 2 | README/`./dev.sh` 与 status 一致；幂等 seed、并行端口文档可执行。 |

**文档建议：5 / 5**。

## 6. P0 / P1 / P2 风险标记

| 级别 | 条件 | 命中 | 证据 |
| --- | --- | --- | --- |
| **P0** | 用户 SQL 可写/越权/平台身份执行/绕过 AST | **否** | 写操作策略拒绝；reader 只读事务；CONNECT 双向隔离；用户 SQL 仅 reader。 |
| **P1** | 无法启动或 health/ready/迁移/seed 失败 | **否** | `./dev.sh up` 成功；health/ready/迁移/seed 成立。 |
| **P2** | 不能同时证明允许+拒绝，或工作台不可用 | **否** | API 与 Playwright 均证明。 |

**风险标记：无。**

## 7. 问题清单（按严重度）

### 中 — DB 完全停止时 `/ready` 可能阻塞

- `stop db` 后多次 8s curl 得 HTTP 000、无 body；恢复后先 503 再 200。  
- 建议：连接 `connect_timeout` + 有界就绪，避免池连接挂死。

### 低 — 无函数允许列表

- `SELECT PG_SLEEP(...)` 可通过策略（e2e 依赖）；依赖超时兜底。

### 低 — 执行错误摘要仍可能含数据库首行原文

- 当前 `1/0` 为「division by zero」，相对克制；可进一步映射固定用户文案。

### 信息 — FastAPI TestClient 弃用警告

- 不影响退出码；依赖升级时跟踪 httpx2。

## 8. Compose 停止与最终 Git

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `decisionharbor-claudecode-claude-fable-5` | `down --volumes` | 已移除 |
| `dhclaude-rev2` | `down --volumes` | 已移除 |
| 其他项目 | 未停止 | — |

```text
HEAD: 9e11644de468e1008784c42ff093ce6a0c96aae9
git status: 干净
git diff --check: 0
```

---

## 9. 一览

| 项 | 值 |
| --- | --- |
| 技术总分 | **88.5 / 90** |
| 文档建议分 | **5 / 5** |
| 风险标记 | **无** |
| 主要扣分 | 故障可见性 −1.5（DB 全挂时 ready 阻塞） |
| 未验证项 | **无** |
