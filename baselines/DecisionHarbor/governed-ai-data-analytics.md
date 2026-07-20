# DecisionHarbor：受治理的 AI 数据分析平台

## 1. 文档职责

本文是 Windows 侧 AgentShip 对首个产品方向的需求和技术边界定稿。固定数据集位于 [`datasets/sales-analytics-v1`](datasets/sales-analytics-v1/)。

本文不定义最终评分方案，也不提供产品源码或产品仓库的初始目录结构。评审方案和真实产品仓库的初始结构由 WSL 侧根据本文及数据集完成。

产品仓库不得出现 AgentShip、候选模型、横向比较、评分标准、隐藏测试或“所有模型保持同一进度”等评测叙事。

## 2. 产品定位

这是一个面向企业内部业务人员的受治理数据分析平台。长期方向可以支持自然语言分析、语义层、权限和 AI 辅助，但首轮只实现一条受控 SQL 查询链路，先验证跨前端、API、数据库和本地基础设施的工程基座。

首轮不是完整产品闭环，也不接入 LLM、自然语言转 SQL、MCP、A2A 或 RAG。手工提交 SQL 的模块是验证项目基座可用性的最小业务探针。

## 3. 首轮目标

候选 Agent 从固定产品起点开始，完成：

1. 可在干净 WSL 环境中启动、迁移、填充数据和运行测试的项目基座。
2. 一个受治理 SQL 查询执行模块：接收显式 SQL，进行 AST 和访问范围校验，通过只读数据库身份执行，并返回结果或清晰的拒绝/错误信息。
3. 一个最小查询工作台：输入 SQL、提交执行、显示执行中/成功/失败状态、展示结果表格或拒绝原因。
4. 可追踪的查询记录，至少覆盖原始 SQL、策略判定或拒绝原因、执行成功/失败、返回行数、耗时、错误摘要和创建时间。

首轮不要求完整运营后台、用户注册、复杂 RBAC、图表编辑器或前端视觉专项设计。界面必须可用，但视觉表现不是明示任务目标。

## 4. 固定分析数据契约

数据契约由本仓库固定，候选 Agent 负责设计迁移和 seed 流程，不得改名、删除或重新解释字段。契约包含五张表：

| 表 | 字段 |
| --- | --- |
| `customers` | `id`, `customer_code`, `display_name`, `region`, `segment`, `created_at` |
| `product_categories` | `id`, `category_code`, `name` |
| `products` | `id`, `sku`, `name`, `category_id`, `list_price`, `cost_price`, `active` |
| `orders` | `id`, `order_no`, `customer_id`, `ordered_at`, `status`, `currency` |
| `order_items` | `id`, `order_id`, `product_id`, `quantity`, `unit_price`, `discount_rate` |

公开数据固定包含 100 个客户、8 个类别、50 个产品、1,000 张订单和 3,000 条明细，订单日期覆盖 2024-01-01 至 2025-12-31，货币为 CNY。数据无真实个人信息，使用固定种子生成并带有 manifest 和校验脚本。

订单状态固定为：

- `pending`：待处理，不计入已实现销售额。
- `confirmed`：已确认，计入销售额和毛利。
- `cancelled`：已取消，不计入销售额。
- `refunded`：已退款，不计入已实现销售额，但保留用于状态分析。

统计口径固定为：

```text
sales_amount = quantity * unit_price * (1 - discount_rate)
cost_amount = quantity * products.cost_price
gross_margin = sales_amount - cost_amount
```

金额使用定点数，`discount_rate` 范围为 0 到 1。订单总额不作为冗余字段保存。

## 5. 数据库与访问边界

本地环境使用一个 PostgreSQL 容器承载两个逻辑数据库：

- `platform`：保存查询审计等产品自身状态，由平台可写身份访问。
- `analytics`：承载上述固定销售数据，只向查询执行器提供独立的只读身份。

执行用户提交的 SQL 时不得使用平台写入身份、跨库访问平台状态或绕过只读连接。数据库权限是应用层策略之外的第二道边界。

## 6. SQL 治理规则

允许一条 PostgreSQL 只读查询表达式，包括：

- `SELECT`
- `WITH ... SELECT`
- 连接、子查询、聚合和窗口函数
- `UNION`、`INTERSECT`、`EXCEPT`

必须拒绝：

- 多条语句
- `INSERT`、`UPDATE`、`DELETE`、`MERGE`
- `CREATE`、`ALTER`、`DROP`、`TRUNCATE`、`COPY`、`CALL`、`DO`
- 数据修改型 CTE、`SELECT INTO`
- 非 `analytics` 业务表、系统目录或未授权对象
- 任何绕过只读数据库身份的执行方式

策略检查必须基于 SQL AST 和对象访问范围，不能只依赖字符串黑名单。执行还必须设置语句超时、结果行数上限，并对策略判定、拒绝原因和执行结果形成稳定记录。

## 7. 最小外部 API

以下端点是黑盒验证使用的最小接口，内部模块和目录结构由候选 Agent 自主决定：

- `GET /health`：进程存活检查。
- `GET /ready`：依赖数据库和迁移已就绪时返回成功，否则返回未就绪。
- `POST /api/v1/query-runs`：提交 `{ "sql": "..." }` 并返回查询运行记录或明确的策略拒绝/执行错误。
- `GET /api/v1/query-runs/{id}`：按标识读取一次查询运行的状态和审计事实。

响应应使用统一 JSON 结构，至少能区分 `succeeded`、`rejected` 和 `failed`，并在成功时返回列定义、行数据、行数和耗时，在拒绝或失败时返回稳定错误码、可读说明和记录标识。具体内部审计表结构不固定。

## 8. 技术栈

主要技术栈固定为：

- Node.js 24
- React 19
- TypeScript
- Vite
- Python 3.13
- FastAPI、Pydantic
- PostgreSQL 18
- SQLAlchemy 2.0、Alembic、psycopg 3
- SQLGlot
- Docker Compose
- pytest、Vitest、Playwright

主要组件的版本和用途应在产品仓库中记录。技术栈之外的目录、模块、状态管理、配置、错误模型、日志、测试组织和容器细节由候选 Agent 自主设计。

## 9. 本地可运行要求

在只安装 Git、Docker 和 Docker Compose 的干净 WSL 环境中，应能够通过一条项目命令：

- 构建并启动 Web、API 和 PostgreSQL；
- 创建两个逻辑数据库和所需身份；
- 执行迁移并填充固定数据；
- 等待健康检查和就绪状态；
- 打开可用的最小查询工作台；
- 重复启动、迁移和 seed 而不产生破坏性重复。

应提供一条统一测试命令，至少覆盖 SQL 策略单元测试、双数据库集成测试和浏览器主流程测试。

多个 Agent worktree 需要能够并行运行：Compose 项目名和 Web/API 宿主端口可配置，不使用固定 `container_name`、全局网络名、全局数据卷名或共享绑定目录；数据库不要求暴露固定宿主端口。性能和耗时比较在资源竞争时应另行串行复测。

## 10. 候选 Agent 的自主范围

候选 Agent 可以自主决定：

- 仓库目录和模块划分；
- API 客户端和前端状态管理；
- 平台内部审计结构；
- 查询策略、执行器和配置接口的内部抽象；
- 容器依赖顺序、开发命令、日志和错误模型；
- 测试目录和测试替身组织；
- 是否以及如何维护符合产品自身规则的需求、状态和历史文档。

不要求额外提交面向评测的 `architecture.md` 或评分说明。候选 Agent 可以像真实项目成员一样提问、提出取舍并请求确认；这些过程由 AgentShip 侧记录，不改变产品仓库的正常叙事。
