# 2026 年 AgentShip Baseline 选题调研

## 最终选择（2026-07-20）

首个 baseline 最终选择“受治理的 AI 数据分析平台”。主要原因是它可以在 WSL 和 Docker Compose 中完整复现，SQL 与数据库结果便于确定性评审，并且仍能覆盖前端、后端、数据库、LLM 编排、安全策略和可观测性。

“企业级 Agent 协作与工具治理控制平面”保留为未来 baseline 候选。它的热点和工程深度更高，但首轮本地环境、协议模拟和分布式任务成本也更高。

## 结论

调研阶段认为比通用企业 RAG 更有区分度的前沿方向是：

> 企业级 Agent 协作与工具治理控制平面（A2A + MCP）

RAG 可以保留为策略、工具说明和运行手册的辅助知识能力，但不再作为产品主题。

## 一手资料依据

1. A2A 将不同厂商、框架和语言实现的 Agent 之间的发现、协作和长任务交互标准化。其规范包含 Agent Card、状态化任务、流式更新、推送通知、身份认证和授权，适合形成真实的跨服务产品闭环。
   - https://a2a-protocol.org/latest/specification/
2. A2A 官方 2026 路线图正在推进 1.0、扩展机制、Inspector 和技术兼容性测试，表明 Agent 互操作和验证工具仍处于快速建设期。
   - https://a2a-protocol.org/latest/roadmap/
3. MCP 将 Prompt、Resource 和 Tool 定义为模型与外部能力交互的核心原语，Tool 明确对应由模型控制的实际操作。
   - https://modelcontextprotocol.io/specification/2025-11-25/server/index
4. MCP 授权规范围绕 OAuth 2.1、受保护资源发现、作用域最小化和资源绑定设计，能自然引出企业级凭据与权限治理需求。
   - https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
5. MCP Tasks 定义了可轮询、可取消、可延迟取回结果的持久状态机，并明确任务隔离、访问控制、审计和日志要求。该部分仍为实验能力，适合考察 Agent 对不稳定协议边界和工程取舍的处理。
   - https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks
6. OpenTelemetry 已为 Agent、Tool Call、Workflow、Token 使用和检索等 GenAI 行为定义观测属性，说明 Agent 可观测性正在形成独立工程面。
   - https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
7. OWASP Agentic Security Initiative 持续发布 Agentic AI 威胁、治理和缓解材料，工具误用、身份与权限、数据泄漏和不可控行动已经成为独立安全问题。
   - https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/

## 推荐候选

### 1. 企业级 Agent 协作与工具治理控制平面

核心模块包括 Agent 注册与发现、MCP Tool Registry、A2A 任务路由、权限和策略、人类审批、持久任务、流式状态、凭据代理、审计、追踪和成本统计。

优势：热点明确、跨栈面广、协议和安全约束真实，并且可以通过本地模拟 Agent 与 Tool 做确定性隐藏测试。

### 2. 受治理的 AI 数据分析平台

围绕自然语言到 SQL、语义层、只读查询沙箱、行级权限、查询成本限制、结果可视化、数据血缘和审计形成闭环。

优势：结果高度可验证，数据库和权限逻辑强；不足是协议热点和产品辨识度弱于 A2A + MCP。

### 3. AI SRE 事件响应与变更审批平台

围绕告警聚合、运行手册、诊断计划、人工审批、受控修复、回滚和复盘形成闭环。

优势：工程深度高；不足是本地复现真实基础设施故障的成本较高。

### 4. 多模态合规审查与人工复核平台

围绕 PDF、图片和邮件解析、结构化抽取、规则比对、证据引用、人工复核和版本审计形成闭环。

优势：业务感强；不足是仍与文档 RAG 接近，OCR 与模型波动会增加评测噪声。

## 推荐的首个端到端任务方向

实现“需要人工审批的跨 Agent 工具执行”：

1. 用户提交一项长任务。
2. 控制平面根据 Agent Card 选择远端 Agent。
3. Agent 请求调用一个高风险 MCP Tool。
4. 策略引擎阻止直接执行并创建审批。
5. 审批通过后使用最小权限凭据恢复任务。
6. Tool 只执行一次，重复事件不能产生重复副作用。
7. 前端持续展示状态、产物、调用链、成本和审计证据。
8. 拒绝、超时、取消、断线重连和跨租户访问均有明确行为。

该任务同时覆盖前端、后端、数据库、异步任务、流式协议、权限、安全、幂等、可观测性和测试，比“上传文档后问答”更难退化为 CRUD 或 API 拼装。
