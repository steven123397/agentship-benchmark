# DecisionHarbor v0.2.0 首轮评审提示词

本版本由 Codex 与 Cursor 对每个冻结候选完成一次互盲首轮评审。两位审查者使用相同证据包和 100 分规范；不得读取对方报告、汇总、评分卡、其他候选资料或自身对该候选开发阶段的既往结论。

候选冻结后，协调方为每次评审确定 3 个参数：

- `<RUN_DIR>`：AgentShip 中该候选运行归档的绝对路径。
- `<候选工作树>`：从冻结结果 commit 建立或保留的干净工作树绝对路径。
- `<唯一报告文件>`：本次唯一允许写入的报告绝对路径；Codex 使用 `codex-review.md`，Cursor 使用 `cursor-review.md`。

不提前创建候选索引、`runs/` 目录或报告占位文件。只有候选满足冻结条件后，才能把上述参数写入评审任务记录并发送对应模板。

## Cursor 模型校准

在首个候选 `codex-gpt-5.6-sol-xhigh` 上，用户可以分别使用 Cursor 的 Composer 2.5、Grok 4.6 和 Claude Opus 5 执行同一评审，以判断哪一个结果最适合作为持续评审基线。用户最终选定的模型是本版本唯一正式的 Cursor 评审模型，并用于该候选的正式 `cursor-review.md` 和全部后续候选。

校准过程及未选模型的输出不进入候选运行归档、评审证据、评分、效率记录或模型比较材料。正式记录只写最终选定的 Cursor 模型及其报告，不说明试跑次数、未选模型或选择过程。

## 共同评审合同

审查者收到模板后必须完成以下流程：

1. 阅读 AgentShip 根 `AGENTS.md`、`baselines/AGENTS.md`、本目录的 `evaluation-and-scoring.md`、已经冻结的 `harness-manifest.json`，以及 `RUN_DIR` 中的 `metadata.json`、`workflow.json`、`skills.json`、`efficiency.json`、`reproduction.md` 和 `intervention-log.md`。
2. 验证 4 个 JSON 记录分别符合本目录的同名 schema；确认 `metadata.json` 中 `completion.coordinatorFrozen` 为 `true`，`candidate.resultCommit` 是完整 SHA，并记为 `RESULT_COMMIT`。
3. 在候选工作树读取产品 `AGENTS.md`、`CONTEXT.md`、相关 ADR、`.scratch/decisionharbor-v0.2.0/spec.md`、最终 tickets 及其 Resolution；确认 `HEAD` 等于 `RESULT_COMMIT` 且工作树干净。
4. 验证 `harness-manifest.json` 符合 `harness-manifest.schema.json`，再审查规格消费、ticket 演进和 skill 工作流证据；随后按评分规范复现公开测试、Compose、API、安全探针和浏览器主链，使用 manifest 指定的入口运行隐藏 HTTP runner，并逐项执行同一 artifact 中的故障场景协议。
5. 对评分规范的每个子项给出 `0% / 50% / 100%` 档位、分数、证据和未验证项，计算总分 `/100`，并单独报告 P0/P1/P2 风险标记。
6. 结束前检查候选工作树的 `git status --short --branch` 和 `git diff --check`；停止本次评审启动的资源，不停止无关项目。
7. 只写 `<唯一报告文件>`。报告至少包含：独立性声明；审查者产品、版本、模型与模式；候选和 `RESULT_COMMIT`；环境与实际命令；4 个维度及全部子项评分；总分；风险标记；按严重度排序的问题；未验证项；资源清理与最终 Git 状态。

任一参数、候选身份、schema、冻结状态、commit 或工作树状态无法对应时，停止并报告，不得猜测、checkout、reset、清理或开始评分。审查者可以使用自身工具和 skills，但不得修改候选源码、分支、baseline、评分规范、运行记录或另一位审查者的报告，也不得创建 commit、push 或 PR。

## Codex 模板

```text
你现在执行 DecisionHarbor v0.2.0 的 Codex 首轮独立评审。

RUN_DIR：<RUN_DIR>
候选工作树：<候选工作树>
唯一报告文件：<唯一报告文件>

严格执行 baseline-v0.2.0/review-prompts.md 的“共同评审合同”和 evaluation-and-scoring.md。你是互盲审查者之一，不读取 cursor-review.md、review-summary.md、scorecard.md 或其他候选材料。只有全部前置身份与冻结检查通过后才开始评审；最终只写唯一报告文件，并记录本次实际 Codex 版本、模型和 reasoning 配置。
```

## Cursor 模板

```text
你现在执行 DecisionHarbor v0.2.0 的 Cursor 首轮独立评审。

RUN_DIR：<RUN_DIR>
候选工作树：<候选工作树>
唯一报告文件：<唯一报告文件>

严格执行 baseline-v0.2.0/review-prompts.md 的“共同评审合同”和 evaluation-and-scoring.md。你是互盲审查者之一，不读取 codex-review.md、review-summary.md、scorecard.md 或其他候选材料。只有全部前置身份与冻结检查通过后才开始评审；最终只写唯一报告文件，并记录本次实际 Cursor 版本、所用模型和模式。
```
