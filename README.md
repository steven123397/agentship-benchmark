# AgentShip

> Can AI agents ship real software?

Real-world, reproducible evaluations of complete AI coding agents through
isolated project baselines and end-to-end software development tasks.

AgentShip 是一个面向真实软件工程场景的 AI Agent 评测项目。它关注的不是脱离工具环境的裸模型能力，而是开发者实际使用的完整系统：模型、Agent 外层工具、上下文管理、终端与代码工具、执行策略和交互流程。

## 评测目标

AgentShip 希望回答的问题是：

> 面对同一个真实项目起点和同一项端到端需求，不同 AI Agent 系统能否可靠地理解、实现、验证并交付软件？

评测重点包括：

- 功能正确性与需求完成度
- 跨前端、后端、数据库和基础设施的工程能力
- 调试、验证和失败恢复能力
- 权限、安全、数据一致性和回归风险
- 代码质量、可维护性和修改范围
- 完成时间、成本、人工介入和实际使用体验

## 仓库模型

`main` 只维护 AgentShip 自身的内容，包括项目介绍、评测方法、任务与提示词、运行记录以及结果展示。

每个 baseline 项目位于独立的 orphan branch 中，拥有自己的根提交和完整项目历史。baseline 分支被当作真实软件项目维护，不包含模型比较、评分规则或其他评测提示，也不会与 `main` 合并。

```text
main                              AgentShip 项目历史
  M0 -> M1 -> M2

baseline/enterprise-rag           企业知识库项目历史
  R0 -> R1 -> R2

baseline/facility-operations      未来可能新增的项目历史
  F0 -> F1
```

某次评测使用的是 baseline 分支上的固定 commit，而不是持续移动的分支名称。正式运行时还需要将该 commit 导出为干净的独立 Git 仓库，防止候选 Agent 读取 `main` 上的评测规则或其他结果。

详细约定见 [仓库与分支模型](docs/repository-model.md)。

## 首个 Baseline 方向

首个计划中的项目是一个企业知识治理与可追溯智能问答平台，覆盖文档解析、异步处理、向量检索、RAG 问答、引用溯源、权限隔离、历史反馈和成本观测。

它将作为正常产品进行可行性分析、需求分析、架构设计和基础骨架建设，不在项目内部描述自己是评测样例。

方向说明见 [企业 RAG baseline](docs/baselines/enterprise-rag.md)。

## 当前阶段

项目目前处于设计和基础建设阶段，近期只关注：

1. 建立 AgentShip 的主分支文档。
2. 明确仓库、baseline 和快照之间的边界。
3. 在独立 orphan branch 中建设首个真实项目骨架。

自动化评测平台、排行榜和批量运行器暂不属于当前阶段。

## 文档

- [仓库与分支模型](docs/repository-model.md)
- [评测原则](docs/evaluation-principles.md)
- [企业 RAG baseline](docs/baselines/enterprise-rag.md)
- [路线图](docs/roadmap.md)
