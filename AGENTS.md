# AgentShip Agent 工作规则

## 适用范围

本文件只适用于 `main` 分支上的 AgentShip 元项目内容。独立 baseline 分支应建立各自的项目规则，不继承本文件中的评测叙事。

## 分支边界

- `main` 只维护项目介绍、方法、任务、提示词、运行记录和结果展示。
- baseline 项目使用没有共同祖先的 orphan branch。
- 不要把 baseline 产品源码、依赖或产品内部文档放入 `main`。
- 不要把 AgentShip 的评分、比较和实验提示放入 baseline 项目。
- `main` 和 baseline 分支之间不进行 merge、rebase 或 cherry-pick。

## 当前阶段

当前只建设主分支文档和 baseline 基础骨架，不提前实现自动化评测平台、排行榜或批量运行系统。

## 文档维护

- 重要设计结论应落入 `docs/`，不要只保留在对话中。
- 修改仓库模型时同步更新 `README.md` 和 `docs/repository-model.md`。
- 新增 baseline 方向时在 `docs/baselines/` 中登记，但详细产品文档应写入对应 baseline 分支。
- 文档应区分已经实现的事实、已经确定的设计和仍待讨论的计划。
