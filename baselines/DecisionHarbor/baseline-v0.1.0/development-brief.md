# DecisionHarbor v0.1.0 开发委托

将以下 3 段提示词依次发送给同一位 Agent。每段完成并汇报验证结果后，再发送下一段。Agent 只处理分配的 DecisionHarbor worktree；不得读取相邻 worktree 或其他分支，不得推送远端或修改既有 tag。

## 提示词一：建立治理

```text
你负责继续开发 DecisionHarbor。全程不要查看其他并行工作树。先运行 `git status --short --branch`，再阅读 `AGENTS.md`、`README.md`、全部 `docs/background/` 和 `datasets/sales-analytics-v1/{README.md,contract.json}`。

本阶段使用 Bootstrap Project Governance skill：先阅读 skill 当前说明，再按其流程建立最小、长期可维护的文档治理体系。保留现有根规则、README 和背景资料，优先扩展而非复制。建立清晰的 `docs/index.md`，并区分 `background`、`design`、`plan` 与 `status` 的职责。

完成后运行 skill 要求的验证和 `git diff --check`，汇报阅读顺序、文档职责与变更内容，然后停止。
```

## 提示词二：完成设计

```text
现在进入设计阶段。先按新建的项目规则阅读背景、索引和当前状态，再将可实现的正式设计写入 `docs/design/`，同步更新索引和状态；本阶段不写代码或计划。

设计必须明确：首轮范围与非目标、模块与数据流、查询运行状态和审计事实、双数据库与只读身份边界、SQLGlot AST 策略和资源限制、最小 API 与错误语义、查询工作台、迁移与幂等 seed、Compose 并行隔离，以及单元、集成和浏览器测试接缝。背景资料已固定的契约和约束不得改写。会影响安全或外部行为的决定必须写清理由；真正的需求歧义才提问。

检查设计与背景资料一致并运行 `git diff --check`，汇报设计结论后停止。
```

## 提示词三：计划并实现

```text
现在开始实现。先按项目规则阅读背景、设计、状态和已有计划；设计与背景冲突时停下说明，不得自行降低约束。

仅在多模块或有依赖顺序时，在 `docs/plan/` 写最小可执行计划，并立即按计划推进，不要停在计划阶段。对行为变化先补最窄的失败测试，再实现并验证。完成 DecisionHarbor 首轮目标：可运行的 Web、API 和 PostgreSQL 基座；受 AST 与对象范围治理的只读 SQL 执行；查询审计；最小工作台；固定数据的迁移与重复 seed；可并行的 Compose 配置；以及项目要求的 HTTP 接口和测试覆盖。

完成或真实阻塞前，运行并记录 `git diff --check`、数据集校验、项目测试、Compose 启动、`/health`、`/ready`、允许与拒绝查询的 API 证据和浏览器主链。环境缺失时如实说明未验证范围。汇报实现、验证、风险或阻塞、当前 commit 和工作区状态。
```
