# AgentShip

AgentShip 使用真实产品起点和受控开发任务，比较完整 AI 开发 Agent 的软件交付能力。

## Language

**项目基座（Project Foundation）**:
能够在干净环境中启动、验证并继续开发的前端、后端、数据和测试基础，不是只有目录与占位文件的脚手架。
_Avoid_: 空框架、脚手架成品

**受控 SQL 查询执行模块（Governed SQL Execution Module）**:
接收显式 SQL，在治理规则内校验并执行只读查询，同时返回结果和可追踪记录的产品模块。
_Avoid_: NL2SQL 模块、AI 查询模块

**受控查询（Governed Query）**:
通过 AST、数据访问范围、数据库只读身份、执行超时和返回行数限制的单条只读 SQL 查询表达式。
_Avoid_: 包含 SELECT 的 SQL、字符串黑名单通过的 SQL

**最小查询工作台（Minimal Query Workbench）**:
首轮用于提交 SQL、观察执行状态并查看结果或拒绝原因的可用界面；它证明跨栈链路成立，但不承担前端视觉专项评测。
_Avoid_: 完整运营前端、前端设计成品

**自发视觉质量（Unprompted Visual Quality）**:
候选 Agent 在产品需求未强调视觉表现时自主交付的界面专业度，作为首轮不超过 10% 的隐藏评审维度。
_Avoid_: 明示视觉任务、前端专项评分

**分析数据契约（Analytics Data Contract）**:
首轮统一规定的销售分析表、字段、关系、约束、固定数据和统计口径；数据由项目自有的确定性生成脚本产出，候选 Agent 实现其迁移与填充流程，但不重新设计契约。
_Avoid_: 自由数据模型、示例数据库建议

**项目自有合成数据集（Project-Owned Synthetic Dataset）**:
为分析数据契约专门设计的、无真实个人信息、固定随机种子且可重复生成的销售数据；不直接复用 Northwind、Chinook 等公开样例库，便于控制业务语义、边界情况和评测输入。
_Avoid_: 随意手写样例数据、外部样例库原样导入、不可重复的随机数据

首轮分析数据契约固定包含 `customers`、`product_categories`、`products`、`orders`、`order_items` 五张表；平台数据库中的审计结构不属于该契约。

固定字段契约为：`customers(id, customer_code, display_name, region, segment, created_at)`、`product_categories(id, category_code, name)`、`products(id, sku, name, category_id, list_price, cost_price, active)`、`orders(id, order_no, customer_id, ordered_at, status, currency)`、`order_items(id, order_id, product_id, quantity, unit_price, discount_rate)`。金额使用定点数，总额由订单明细计算，不额外存储冗余总额；候选 Agent 不得改名、删除或重新解释这些字段。

订单状态固定为 `pending`、`confirmed`、`cancelled`、`refunded`。只有 `confirmed` 订单计入已实现销售额和毛利；`discount_rate` 的范围为 0 到 1。销售额按 `quantity * unit_price * (1 - discount_rate)` 计算，成本按 `quantity * products.cost_price` 计算，毛利为二者之差。

公开合成数据集固定包含 100 个客户、8 个产品类别、50 个产品、1,000 张订单和 3,000 条订单明细，订单日期覆盖 2024-01-01 至 2025-12-31，货币统一为 CNY。生成器使用固定随机种子并随数据契约版本化；具体样本值、状态分布和边界样例由项目维护者自行确定。

**查询审计事实（Query Audit Facts）**:
首轮统一要求保留的查询文本、策略判定、执行结果、行数、耗时、错误摘要和时间信息；候选 Agent 自主设计其内部数据结构。
_Avoid_: 固定审计表结构、可选日志字段

**平台数据库（Platform Database）**:
保存查询审计等产品自身状态的数据库，由平台写入身份访问。
_Avoid_: 审计库、主库

**分析数据库（Analytics Database）**:
承载固定销售分析数据契约的被查询数据库，只通过独立只读身份向查询执行器开放。
_Avoid_: 业务库、目标库、平台数据库

**运行实例（Run Instance）**:
绑定单个 Agent worktree 的独立 Compose 项目，拥有可配置的项目名、宿主端口、网络和数据卷，并可与其他运行实例并行存在。
_Avoid_: 共享开发栈、共用 Compose 环境

**首轮任务（Foundation Round）**:
从只有需求和技术边界的空项目开始，自主设计并落地项目基座的评测阶段；手工提交 SQL 的受控执行模块是验证基座可用性的最小业务探针，首轮不接入 LLM。
_Avoid_: 产品第一版、完整功能闭环、SQL 功能赛

**项目内生文档（Project-Native Documentation）**:
按照产品仓库自身治理规则，因真实开发需要而维护的需求、状态和历史进度文档；首轮不增加面向评分的专用架构交付物。
_Avoid_: 评测架构报告、得分说明文档

**开发委托（Development Brief）**:
以真实产品阶段目标交给候选 Agent 的工作说明，只包含项目事实、业务目标和开发边界，不暴露 AgentShip、评分或竞争关系；首轮采用一份连续委托，不强制拆成设计和实现提示词。
_Avoid_: 测试题、比赛提示词、评分导向任务

**开放式开发协作（Open Development Collaboration）**:
用户像真实项目负责人一样自主回答、追问或授权 Agent 决策的开发过程；有价值的提问与转向被记录，但不强制统一交互脚本。
_Avoid_: 标准化问答实验、禁止澄清模式

**阶段完成制（Milestone Completion Model）**:
候选 Agent 持续工作到首轮阶段目标完成或明确失败，时间和 token 消耗作为效率结果记录，而不是预先截断正常开发的限额。
_Avoid_: 固定时长赛、固定 token 赛

**最小验证集（Minimum Verification Set）**:
证明首轮项目基座成立的 SQL 策略单元测试、双数据库集成测试和最小查询工作台浏览器主链测试，不以覆盖率或测试数量为目标。
_Avoid_: 覆盖率竞赛、全组件测试要求
