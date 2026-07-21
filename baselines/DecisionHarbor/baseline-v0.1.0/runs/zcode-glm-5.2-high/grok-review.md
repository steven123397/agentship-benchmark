# DecisionHarbor v0.1.0 — Grok 首轮独立评审

**候选：** `v0.1.0/zcode-glm-5.2-high` @ `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde`  
**RESULT_COMMIT（metadata）：** `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde`  
**冻结条件：** `completion.coordinatorFrozen=true`，且 `candidate.resultCommit` 非空完整 SHA。

## 1. 独立性声明

- 本报告由 Grok Build 对本候选冻结 commit 做只读复现与审查。
- 全程未读取其他候选的 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未修改候选源码、候选分支、baseline 产品仓库、评分规范或其他归档文件；未执行 `git add` / `commit` / `push` / 创建 PR。
- 唯一写入文件为本 `grok-review.md`。
- 评分仅依据**本次**对冻结 commit 的代码审查与新鲜运行证据；不因 Agent/模型名称或既往印象调整分数。
- 无新鲜证据的项目标为「未验证」，不按通过计分。
- **环境说明：** 首次直连 PyPI 构建极慢；经用户授权，API 镜像构建使用宿主既有 HTTP(S)_PROXY（`http://172.22.112.1:7897`）作为 build-arg，**未改仓库文件**。

## 2. 评审对象、环境与执行命令

### 2.1 冻结确认

| 项 | 值 |
| --- | --- |
| 工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.2-high` |
| 分支 | `v0.1.0/zcode-glm-5.2-high` |
| HEAD / RESULT_COMMIT | `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde` |
| baseline | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始/结束 `git status` | 干净 |
| `git diff --check` | 退出码 0 |

### 2.2 环境

| 组件 | 版本 |
| --- | --- |
| 宿主 | WSL2 `6.18.33.2-microsoft-standard-WSL2` |
| Docker / Compose | `29.1.3` / `2.40.3` |
| Python / Node（宿主） | `3.10.12` / `v24.16.0` |
| 评审项目 1 | `dhzcode-rev` — API `127.0.0.1:18380`，Web `127.0.0.1:15373` |
| 评审项目 2 | `dhzcode-rev2` — API `127.0.0.1:18381`，Web `127.0.0.1:15374` |

### 2.3 主要命令（摘要）

```bash
git rev-parse HEAD   # e3934d3...
python3 datasets/sales-analytics-v1/validate.py

# 代理构建 API（用户授权）
docker build --build-arg HTTP_PROXY=... --build-arg HTTPS_PROXY=... -t dhzcode-rev-api:latest ./api

export DH_PROJECT_NAME=dhzcode-rev DH_API_PORT=18380 DH_WEB_PORT=15373
docker compose up -d
bash scripts/wait-ready.sh
curl http://127.0.0.1:18380/health   # 200 ok
curl http://127.0.0.1:18380/ready    # 200 ready

# 允许/拒绝/行数/超时 API
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:18380/api/v1/query-runs

# 双库身份、restart、stop db
docker compose exec -T db ...
docker compose restart api
docker compose stop db && curl --max-time 5 .../ready

# 测试
docker compose exec -T api pytest tests/test_policy.py -q       # 36 passed
docker compose exec -T api pytest tests/test_integration.py -q  # 14 passed
cd web && DH_WEB_PORT=15373 npx playwright test                 # 3 passed

# 并行（retag + --no-build）
DH_PROJECT_NAME=dhzcode-rev2 DH_API_PORT=18381 DH_WEB_PORT=15374 docker compose up -d --no-build

# 收尾
docker compose down -v   # 两个项目
```

阅读：`AGENTS.md`、`README.md`、`docs/**`、`api/`、`web/`、`db/`、`Makefile`、`docker-compose.yml`。

## 3. 技术评分（/90）

子项：未通过 `0`，部分通过 `50%`，完全通过满分。

### 3.1 功能与外部契约 — **25 / 25**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**证据**

1. **API**  
   - `POST /api/v1/query-runs` 创建记录并返回 `id/status/sql/error_*/columns/rows/row_count/duration_ms/created_at`。  
   - `GET /api/v1/query-runs/{id}`：`rows` 为 `null`（不返回结果单元格）。  
   - 成功例：`SELECT count(*) ... FROM analytics.customers` → `status=succeeded`，`rows:[[100]]`，`id=12`。

2. **允许查询正确性**  
   - 客户数 100。  
   - 区域营收（`confirmed` × 折扣公式）：East `2768355.33`，South `2329370.48`，Central `2076252.0`，West `1989615.57`，North `1895196.27`。  
   - **注意：** 未限定 schema 的 `FROM customers` 策略放行但执行失败（`relation "customers" does not exist`），因只读角色 `search_path` 为 `"$user", public`，未设 `analytics`。工作台与集成测试使用 `analytics.` 前缀，主路径正确。缺陷记入问题清单，不把允许主路径计为失败。

3. **拒绝与失败**  

   | 输入 | HTTP | status | error_code |
   | --- | ---: | --- | --- |
   | `DELETE FROM customers` | 422 | `rejected` | `FORBIDDEN_STATEMENT` |
   | 多语句 | 422 | `rejected` | `MULTI_STATEMENT` |
   | `pg_catalog.pg_class` | 422 | `rejected` | `FORBIDDEN_OBJECT` |
   | `platform.query_runs` | 422 | `rejected` | `FORBIDDEN_OBJECT` |
   | 修改型 CTE | 422 | `rejected` | `DATA_MODIFYING_CTE` |
   | `SELECT INTO` | 422 | `rejected` | `SELECT_INTO` |
   | 超行数 `order_items` | 200 | `failed` | `ROW_LIMIT_EXCEEDED` |
   | `pg_sleep(31)` | 200 | `failed` | `STATEMENT_TIMEOUT` |

4. **工作台**  
   - Web `15373` HTTP 200；经 Vite proxy 的 API 成功。  
   - Playwright **3/3 通过**（允许表、拒绝 DELETE、多语句）。

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
   - SQLGlot `read=postgres`；单语句；只读根；DML/DDL/`Into`/Command 拒绝。  
   - 单元测试 **36 passed**。

2. **对象范围**  
   - 白名单 `(analytics, 五表)`；系统 schema 与未授权表拒绝。运行时 `FORBIDDEN_OBJECT` 已验证。

3. **双库身份**  
   - 用户执行用 `dh_analytics_reader`；审计用 `dh_platform_writer`。  
   - 实测：reader 不可 CONNECT `platform`；writer 不可 CONNECT `analytics`；reader `INSERT` 被拒。  
   - 集成测试同覆盖。  
   - API 进程仍含 **bootstrap** 用户/口令（entrypoint 迁移/seed）；用户 SQL 路径未使用 bootstrap。

4. **资源限制**  
   - `DH_ROW_LIMIT=1000` → `ROW_LIMIT_EXCEEDED`（fail-closed，不截断返回）。  
   - `DH_STATEMENT_TIMEOUT_MS=30000` → `STATEMENT_TIMEOUT`，约 29988 ms。

5. **数据契约**  
   - `validate.py` 通过；行数 100/8/50/1000/3000；营收口径正确；seed 重复收敛。

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
   - `make up` / `docker compose up` + `scripts/wait-ready.sh`；`/health`、`/ready` 200。  
   - 无 `container_name`；db 不映射宿主端口；`DH_PROJECT_NAME`/端口可配置。  
   - 首次冷构建依赖 PyPI；默认无镜像源（环境风险，见问题清单）。

2. **迁移/seed**  
   - entrypoint：`alembic upgrade head` + `python -m app.seed`；init 建库角色；TRUNCATE+COPY+计数校验。

3. **并行**  
   - `dhzcode-rev` / `dhzcode-rev2` 同时 ready；独立网络/卷；审计计数 **26 vs 1**。  
   - （二次 `compose build` 曾遇 Docker Hub EOF；用本地镜像 retag + `--no-build` 完成并行——产品侧配置支持并行。）

4. **重启与故障（部分）**  
   - `restart api` 后 `/ready` 立即 200。  
   - `stop db` 后 5s curl **超时 0 字节**；db 恢复后 503 → 200。  
   - ready 路径无显式 `connect_timeout` 时仍可能阻塞 → **1.5/3**。

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
| `pytest tests/test_policy.py` | **36 passed** |
| `pytest tests/test_integration.py` | **14 passed**（1 弃用警告） |
| Playwright e2e | **3 passed** |

`Makefile` 提供 `make test` → unit + integration + e2e；失败非零退出。集成覆盖身份分离、允许/拒绝、行数、seed 幂等与计数。

**未验证项：** 无（未整包再跑 `make test` 单 shell，但各目标等价命令均已新鲜通过）。

### 3.5 代码质量与可维护性 — **8.5 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | **部分通过** |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- **边界：** policy / executor / audit / seed 分离；运行期 reader/writer 与引导职责在代码路径上分开。  
- **配置与错误（部分）：**  
  - 策略默认 schema=`analytics`，但 DB `search_path` 未对齐 → 未限定名失败且错误含 SQLAlchemy 全文。  
  - API 容器注入 bootstrap 凭据；错误消息截断但仍泄露驱动细节。  
  - numeric 以 `float` JSON 化（营收仍正确，精度风险）。  
- **可测试性：** 纯策略单测 + 集成清晰；`make` 入口完整。

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

## 5. 产品文档建议分 — **3 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | `docs/index.md`、AGENTS 目录职责清晰。 |
| 设计完整性与可追溯性 | 2 | 1 | `design/first-round.md` 较完整，但根 **README 仍写「应用源码…尚未建立」**，与实现严重不符。 |
| 计划、运行/测试说明与实现一致性 | 2 | 1 | status/Makefile 描述基本正确；README 无 `make up`/`make test`，新读者会被误导。 |

**文档建议总分：3 / 5**。

## 6. P0 / P1 / P2 封顶判断

| 级别 | 条件 | 命中 | 证据 |
| --- | --- | --- | --- |
| **P0** | 用户 SQL 可写/越权/平台身份执行/绕过 AST | **否** | 写操作与系统对象策略拒绝；跨库 CONNECT 被拒；执行器用 reader。 |
| **P1** | 无法启动或 health/ready/迁移/seed 失败 | **否** | 启动成功；health/ready/迁移/seed 成立。 |
| **P2** | 不能同时证明允许+拒绝，或工作台不可用 | **否** | 允许（schema 限定）与拒绝均证明；Playwright 3 通过。 |

**封顶：不适用。**

## 7. 问题清单（按严重度）

### 中 — 策略与执行对未限定表名不一致

- 策略将 `customers` 视为 `analytics.customers` 并允许；执行因 `search_path` 无 `analytics` 报 `UndefinedTable`。  
- 建议：`ALTER ROLE ... SET search_path = analytics` 或执行前 `SET search_path`，或策略要求显式 schema。

### 中 — DB 完全停止时 `/ready` 可能阻塞

- 5s curl 超时 0 字节；恢复后 503→200。  
- 建议：连接 `connect_timeout` + 有界就绪。

### 中 — 错误摘要泄露驱动/SQL 细节

- `EXECUTION_ERROR` / `STATEMENT_TIMEOUT` 消息含 psycopg/SQLAlchemy 原文。  
- 建议：用户侧固定码与短摘要。

### 低 — API 进程持有 bootstrap 凭据

- 迁移/seed 在 API entrypoint 执行，bootstrap 与运行期同容器。  
- 建议：独立 migrate 一次性任务。

### 低 — 默认冷构建无 PyPI 加速手段

- 直连官方源极慢；无 Dockerfile ARG 镜像源。影响可运行体验（非功能错误）。

### 低 — README 过时

- 仍称应用尚未建立，与 `make up` 及实现矛盾。

### 信息 — numeric 以 float 序列化

- 当前数据集下营收正确，存在一般精度风险。

## 8. Compose 资源停止与最终 Git 状态

### 8.1 Compose

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `dhzcode-rev` | `docker compose down -v` | 已移除 |
| `dhzcode-rev2` | `docker compose down -v` | 已移除 |
| 其他项目 | **未停止** | 保留 |

### 8.2 Git

```text
HEAD: e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde
branch: v0.1.0/zcode-glm-5.2-high...origin/v0.1.0/zcode-glm-5.2-high
git status: 干净
git diff --check: 0
```

---

## 9. 一览

| 项 | 值 |
| --- | --- |
| 技术总分 | **87 / 90** |
| 文档建议分 | **3 / 5** |
| 视觉 / 最终 100 / 平均 | 不评 / 不计算 |
| 封顶 | **无** |
| 主要扣分 | 故障可见性 −1.5；配置/错误 −1.5 |
| 未验证项 | **无** |
