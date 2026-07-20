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

`agentship-benchmark` 只维护 AgentShip 自身的内容，包括项目介绍、评测方法、任务与提示词、运行记录以及结果展示。未来的模型比较结果网站、自动评审系统和实验辅助工具也可以在本仓库中发展。

Windows 与 WSL 使用同一个 AgentShip 远端仓库分阶段协作：Windows 侧先准备项目说明、需求、技术栈、数据契约和数据集；WSL 侧拉取后继续确定提示词、协作记录、运行结果、评审方案和 baseline 产品仓库的初始结构。

每个 baseline 都是一个拥有独立本地目录和远端仓库的真实产品项目。它按照正常软件项目维护自己的 `main`、文档、源码、测试、CI 和发布历史，不包含模型比较、评分规则或其他评测提示。

```text
/AgentShip
  -> steven123397/agentship-benchmark
     项目介绍、任务、提示词、规则、结果和未来评测工具

/<真实产品名>
  -> steven123397/<真实产品名>
     独立的真实产品源码、文档、测试和项目历史
```

某次评测使用的是产品仓库 `main` 上的固定 tag 或 commit，而不是持续移动的分支名称。不同 Agent 从同一起点创建本地结果分支和 worktree；正式测试期间不向共享远端推送其他 Agent 的结果，评测规则和隐藏验证也保留在产品仓库之外。

详细约定见 [仓库模型](docs/repository-model.md)。

## 首个 Baseline 方向

首个计划中的项目是一个受治理的 AI 数据分析平台。长期方向包含自然语言分析，但首轮只要求用户提交显式 SQL，系统对其进行解析、策略校验和只读执行，并展示结果与审计证据。这样首轮可以观察从空项目搭建跨层基座和安全边界的能力，不把 LLM 接入质量混入基础任务。

需求、技术栈、数据契约和公开合成数据先在 Windows 侧确定；WSL 侧据此编写首轮开发提示词，并建立独立的真实产品仓库和 baseline 初始结构。候选 Agent 从固定产品起点继续搭建可运行项目和第一条最小纵向业务闭环。

方向说明见 [DecisionHarbor baseline 准备材料](baselines/DecisionHarbor/governed-ai-data-analytics.md)。

## 当前阶段

项目目前处于设计和基础建设阶段，近期只关注：

1. 在 Windows 侧完成项目说明、需求、技术栈、数据契约和公开数据集。
2. 通过 Git 将准备材料交接给 WSL 侧的同一 AgentShip 仓库。
3. 在 WSL 侧形成提示词、协作记录、运行结果、独立产品仓库初始结构和最终评审方案。

自动化评测平台、排行榜和批量运行器暂不属于当前阶段。

## 文档

- [仓库模型](docs/repository-model.md)
- [评测原则](docs/evaluation-principles.md)
- [DecisionHarbor baseline 准备材料](baselines/DecisionHarbor/governed-ai-data-analytics.md)
- [路线图](docs/roadmap.md)
