# DecisionHarbor v0.2.0 开发委托

本轮从 DecisionHarbor 附注 tag `baseline-v0.2.0` 开始，冻结 commit 为 `9355032ecadd6d3c940d7977fe381f9f8a93b1ab`。产品仓库中的 `AGENTS.md`、`CONTEXT.md`、相关 ADR 和 `.scratch/decisionharbor-v0.2.0/spec.md` 是候选必须自行消费的事实源；本文件不复制产品规格。

候选只操作自己的分支和工作树，只读取产品仓库中完成开发所需的事实源。候选不得读取 AgentShip 的评分规范、评审提示词、隐藏 Harness、候选运行归档，也不得读取、比较或使用其他候选的分支、工作树、提交、运行记录或评审材料。候选可以创建本地提交，不向产品远端推送。

## 阶段 1：拆分 tickets

在从冻结 baseline 创建的干净候选工作树中开启新会话，只发送：

```text
/to-tickets .scratch/decisionharbor-v0.2.0/spec.md
```

候选提出拆分方案并等待确认后，协调方统一回复：

```text
批准该拆分。请将 tickets 写入 .scratch/decisionharbor-v0.2.0/issues/，按仓库本地 tracker 规则完成依赖、状态和验收条件，并创建一个本地规划提交。不要 push；提交后停止并汇报 ticket 顺序与完整 commit SHA。
```

规划提交是候选结果的一部分。协调方核对提交、ticket 路径、blocking edges 和当前 frontier 后，才进入实现阶段。

## 阶段 2：逐 ticket 实现

每张进入 frontier 的 ticket 使用一个全新会话。协调方把实际路径代入以下模板，只发送这一段：

```text
/implement .scratch/decisionharbor-v0.2.0/issues/<NN>-<slug>.md

你可以为完成本 ticket 创建本地交付提交。不要 push；解决这一张 ticket 后停止，并汇报验证结果与完整 commit SHA。
```

协调方在每张 ticket 后核对结果提交、ticket 的 `Resolution`、实际验证和新 frontier，再为下一张 ticket 开启新会话。一次会话不得顺带实现下一张 ticket。

## 完成边界

全部 tickets 均为 `resolved`、候选分支具有稳定结果 commit 且工作树状态已记录后，开发阶段结束。候选最后一次报告中的测试结果属于 Agent 自述；冻结与评分仍须由 AgentShip 按统一规范独立复现。
