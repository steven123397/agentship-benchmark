# DecisionHarbor v0.1.0 — Grok 首轮独立评审

**候选：** `v0.1.0/qoder-qwen3.8-max-preview-thinking` @ `fffe1f6bbe15872479d3579ea99d57deba7445f3`  
**RESULT_COMMIT：** `fffe1f6bbe15872479d3579ea99d57deba7445f3`  
**冻结：** `completion.coordinatorFrozen=true`

## 1. 独立性声明

- 本报告由 Grok Build 对本候选冻结 commit 做只读复现与审查。
- 全程未读取其他候选的 worktree、分支、运行记录或评审材料。
- 全程未读取本候选的 `codex-review.md`、`review-summary.md`、`scorecard.md`。
- 未修改候选源码/分支/baseline/评分规范；未 git add/commit/push/创建 PR。
- 唯一写入：本 `grok-review.md`。
- 评分仅依据本次对冻结 commit 的代码与运行证据；不因 Agent/模型/耗时/既往印象调分。
- 无新鲜证据标「未验证」，不按通过处理。
- **环境：** 构建使用宿主既有 HTTP(S)_PROXY（`http://172.22.112.1:7897`）作为 build-arg，未改仓库文件。

## 2. 评审对象、环境与命令

### 2.1 冻结确认

| 项 | 值 |
| --- | --- |
| 工作树 | `/home/liangjiaqi/projects/DecisionHarbor/.worktrees/qoder-qwen3.8-max-preview-thinking` |
| 分支 | `v0.1.0/qoder-qwen3.8-max-preview-thinking` |
| HEAD | `fffe1f6bbe15872479d3579ea99d57deba7445f3` |
| baseline | `1fb48f499d67677a47fb9b60e1f99346b46e0aee` |
| 开始/结束 git status | 干净 |
| `git diff --check` | 0 |

### 2.2 环境

| 组件 | 版本 |
| --- | --- |
| Docker / Compose | 29.1.3 / 2.40.3 |
| 宿主 Python / Node | 3.10.12 / v24.16.0 |
| 项目 1 | `dhqoder-rev` API `127.0.0.1:18480` Web `127.0.0.1:15473` |
| 项目 2 | `dhqoder-rev2` API `127.0.0.1:18481` Web `127.0.0.1:15474` |

### 2.3 主要命令摘要

```bash
git rev-parse HEAD && git status --short --branch
python3 datasets/sales-analytics-v1/validate.py

export COMPOSE_PROJECT_NAME=dhqoder-rev API_HOST_PORT=18480 WEB_HOST_PORT=15473
# 代理 build-arg 后
docker compose build ... && docker compose up -d
curl http://127.0.0.1:18480/health   # 200 {"status":"ok"}
curl http://127.0.0.1:18480/ready    # 200 {"status":"ok"}

# 允许/拒绝/行数/超时 API
curl -H 'content-type: application/json' --data '{"sql":"..."}' \
  http://127.0.0.1:18480/api/v1/query-runs

# 双库身份、restart、stop db
docker compose exec -T db ...

# 测试（镜像未打包 tests，挂载 host 路径后运行）
docker compose run --rm --no-deps -v $PWD/api/tests:/app/tests:ro \
  --entrypoint sh api -c 'pip install -q pytest httpx && pytest tests/unit -q'
# → 29 passed
# integration 类似，API_BASE_URL=http://api:8000
# → 10 passed

# Playwright
WEB_BASE_URL=http://127.0.0.1:15473 npx playwright test  # 3 passed

# 并行 retag + --no-build
COMPOSE_PROJECT_NAME=dhqoder-rev2 API_HOST_PORT=18481 WEB_HOST_PORT=15474 docker compose up -d --no-build

docker compose down -v  # 两项目
```

阅读：`AGENTS.md`、`README.md`、`docs/**`、`api/`、`web/`、`db/`、`docker-compose*.yml`、`tests/e2e/`。

## 3. 技术评分（/90）

### 3.1 功能与外部契约 — **25 / 25**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 查询运行 API 生命周期 | 8 | 8 | 完全通过 |
| 允许查询结果正确性 | 7 | 7 | 完全通过 |
| 拒绝与执行失败语义 | 5 | 5 | 完全通过 |
| 最小查询工作台 | 5 | 5 | 完全通过 |

**证据**

1. **API：** `POST /api/v1/query-runs` → HTTP 201，`status=succeeded/rejected/failed`，含 `data.id`；`GET` 返回审计（成功含 columns/row_count/duration，**不含 rows**）。  
2. **允许：** `COUNT(*) FROM customers` → `[[100]]`；区域营收 East `2768355.33` … North `1895196.27`。  
3. **拒绝/失败：** DELETE/多语句/pg_catalog/修改型 CTE/SELECT INTO/未知表 → `rejected` + 稳定 code；语义错误 → `failed` `EXECUTION_ERROR`；超时 → `TIMEOUT`。  
4. **工作台：** Web 200；Playwright 3/3（结果表、策略拒绝、空 SQL 禁用按钮）。

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

1. **AST：** SQLGlot postgres；单语句；写操作/CTE 修改/`SELECT INTO` 拒绝。单元 **29 passed**。策略会 **改写 LIMIT** 注入行数上限（仍基于 AST，非字符串黑名单）。  
2. **对象：** 五表白名单；系统前缀/`pg_catalog`/`information_schema`/未授权表拒绝。业务表在 analytics 库的 `public` schema。  
3. **双库身份（部分）：**  
   - **通过：** 用户执行路径用 `analytics_reader`；`INSERT` 被拒；API 用 `platform_app` 写审计。  
   - **不足：** `analytics_reader` **可 CONNECT `platform`** 并 `\dt` 列出 `query_runs`（SELECT 被表权限拒绝）；`platform_app` **可 CONNECT `analytics`** 并列出全部业务表。init **未 REVOKE CONNECT FROM PUBLIC**。  
   - API 环境含 `ANALYTICS_ADMIN_DATABASE_URL`（启动时 migrate+seed）。  
4. **资源：** 行数经 LIMIT 注入 → `order_items` 返回 1000 行；`pg_sleep(32)` → `TIMEOUT`。  
5. **契约：** validate 通过；行数 100/1000/3000；营收口径正确。

**未验证项：** 无。

### 3.3 可运行性与可靠性 — **18.5 / 20**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 干净环境启动与就绪 | 6 | 6 | 完全通过 |
| 迁移与固定数据初始化 | 6 | 6 | 完全通过 |
| 并行实例隔离 | 5 | 5 | 完全通过 |
| 重启与故障可见性 | 3 | 1.5 | **部分通过** |

**证据**

1. **启动：** `docker compose up` 后 health/ready 200；项目名与端口可配置；无 `container_name`；db 默认不映射宿主端口（test overlay 可映射）。  
2. **迁移/seed：** 容器 CMD 跑 `migrate` + `seed`（TRUNCATE+INSERT CSV）；重复启动可收敛。  
3. **并行：** 两项目同时 ready；独立网络/卷；审计 **16 vs 1**。  
4. **重启/故障（部分）：** restart 后可恢复 ready；`stop db` 后 5s curl **超时 0 字节**，恢复后 503→200。`/ready` **仅探测 platform**，不验证 analytics/seed。→ **1.5/3**。

**未验证项：** 无。

### 3.4 测试与验证证据 — **13.5 / 15**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 统一测试入口与可靠断言 | 3 | 1.5 | **部分通过** |
| SQL 策略单元测试 | 5 | 5 | 完全通过 |
| 双数据库集成测试 | 4 | 4 | 完全通过 |
| 浏览器主链测试 | 3 | 3 | 完全通过 |

**证据**

| 套件 | 本次结果 |
| --- | --- |
| `pytest tests/unit`（挂载） | **29 passed** |
| `pytest tests/integration`（挂载 + 运行栈） | **10 passed** |
| Playwright e2e | **3 passed** |

- **部分：** 无 `make test`/`scripts/test.sh` 类统一入口；README 未写测试命令；**运行镜像不包含 `tests/`**（Dockerfile 未 COPY），需挂载或改镜像才能在容器内跑。存在可执行用例且失败可非零，但入口不完整。  
- 集成覆盖 health/ready、允许/拒绝、只读写拒绝；跨库 CONNECT 未在测试中收紧验证。

**未验证项：** 无（有用例且已跑通；统一入口仅部分达标）。

### 3.5 代码质量与可维护性 — **8.5 / 10**

| 子项 | 分值 | 得分 | 结论 |
| --- | ---: | ---: | --- |
| 模块边界与职责分离 | 3 | 3 | 完全通过 |
| 配置、错误处理与资源清理 | 3 | 1.5 | **部分通过** |
| 类型、命名、重复控制与可测试性 | 2 | 2 | 完全通过 |
| 依赖、变更范围与维护负担 | 2 | 2 | 完全通过 |

**证据**

- **边界：** policy / executor / router / migrate / seed 分离清楚。  
- **配置与错误（部分）：**  
  - CONNECT 未收紧；admin DSN 进 API；`fetchall` 依赖 LIMIT 改写；`/ready` 过浅。  
  - 错误摘要多数可接受；策略改写 SQL 再执行（审计存原始 SQL，可接受）。  
- **可测试性：** 策略纯函数；测试需额外挂载/装 pytest。

**未验证项：** 无。

## 4. 技术总分

| 维度 | 得分 |
| --- | ---: |
| 功能与外部契约 | 25 |
| SQL 治理与数据正确性 | 18 |
| 可运行性与可靠性 | 18.5 |
| 测试与验证证据 | 13.5 |
| 代码质量与可维护性 | 8.5 |
| **技术总分** | **83.5 / 90** |

（不评视觉；不计算 100 分或平均分。）

## 5. 产品文档建议分 — **3 / 5**

| 子项 | 分值 | 建议 | 证据 |
| --- | ---: | --- | --- |
| 治理、索引与阅读入口 | 1 | 1 | `docs/index.md` 有 design/plan/status 链接。 |
| 设计完整性 | 2 | 1 | 有架构设计；根 **README 仍写应用尚未建立**，与实现矛盾。 |
| 计划与实现一致性 | 2 | 1 | plan 任务状态仍「待开始」；status 称全部通过；缺统一运行/测试命令文档。 |

**文档建议：3 / 5**。

## 6. P0 / P1 / P2 风险标记

| 级别 | 条件 | 命中 | 证据 |
| --- | --- | --- | --- |
| **P0 安全失败** | 用户 SQL 可写/越权执行/平台身份执行/绕过 AST | **否** | 写操作策略拒绝；reader INSERT 拒绝；用户 SQL 走 reader；`query_runs` SELECT 被表权限拒绝。跨库 CONNECT 弱化隔离，但未证明用户 SQL 经平台写入身份执行或 AST 被绕过写入。 |
| **P1 基座失败** | 无法启动或 health/ready/迁移/seed 失败 | **否** | 启动成功；health/ready/迁移/seed 成立。 |
| **P2 核心闭环缺失** | 不能同时证明允许+拒绝，或工作台不可用 | **否** | 允许与拒绝 API + Playwright 均证明。 |

**风险标记：无 P0/P1/P2 命中。**（按当前规范：风险标记不封顶质量分。）

## 7. 问题清单（按严重度）

### 中 — 双库 CONNECT 未隔离

- `analytics_reader` 可连接 `platform` 并枚举表；`platform_app` 可连接 `analytics` 并枚举业务表。  
- 建议：`REVOKE CONNECT ON DATABASE ... FROM PUBLIC` 后仅授给对应角色。

### 中 — `/ready` 过浅且 DB 全挂时可能阻塞

- 仅 `SELECT 1` platform；不验证 analytics/seed。  
- `stop db` 后 ready 5s 超时无 body。

### 中 — 测试不进镜像、无统一测试入口

- Dockerfile 不 COPY tests；无 `scripts/test.sh`/`make test`；README 不指导测试。

### 低 — API 进程持有 analytics_admin

- 启动时 migrate+seed 共用 admin URL。

### 低 — 行数限制靠改写 LIMIT

- 依赖 AST 改写；`fetchall` 无第二道截断；复杂集合查询风险更高。

### 低 — 文档严重滞后

- README「尚未建立」；plan 状态「待开始」。

### 信息 — 首次超时请求曾 empty reply

- 复测可得到 `TIMEOUT`；偶发连接重置记为可靠性毛刺。

## 8. Compose 停止与最终 Git

| 项目 | 操作 | 结果 |
| --- | --- | --- |
| `dhqoder-rev` | `down -v` | 已移除 |
| `dhqoder-rev2` | `down -v` | 已移除 |
| 其他项目 | 未停止 | — |

```text
HEAD: fffe1f6bbe15872479d3579ea99d57deba7445f3
git status: 干净
git diff --check: 0
```

---

## 9. 一览

| 项 | 值 |
| --- | --- |
| 技术总分 | **83.5 / 90** |
| 文档建议分 | **3 / 5** |
| 风险标记 | **无** |
| 主要扣分 | 双库隔离 −2；故障可见 −1.5；统一测试入口 −1.5；配置/错误 −1.5 |
| 未验证项 | **无** |
