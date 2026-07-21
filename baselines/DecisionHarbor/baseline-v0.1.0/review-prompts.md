# DecisionHarbor v0.1.0 首轮评审提示词

本文保存各候选的首轮评审委托。每段提示词独立使用：Grok Build 和 Codex CLI 各对每个候选完成一次互盲审查。Grok 可以在同一会话内按顺序执行多段提示词；Codex 亦可在同一会话内按顺序执行多段提示词，但后续任务不得复用、比较或引用前一候选的分数、问题或结论。

所有提示词都直接使用已冻结的候选工作树，不再创建额外 review worktree。评审完成后，审查者只写自己的首轮报告；汇总、人工文档分、视觉分、风险标记和过程记录由协调方在两份报告都冻结后处理。

| 编号 | 审查者 | 候选 | 冻结 commit | 唯一报告文件 |
| --- | --- | --- | --- | --- |
| 1 | Grok Build | Codex CLI | `6e3964f05b72d44a50f7d2a7657304a83cfa11c1` | `runs/codex-gpt-5.6-sol-xhigh/grok-review.md` |
| 2 | Grok Build | Grok Build | `8bbe8de2875d32804067d8418fb5bc6fc8cb431c` | `runs/grok-grok-4.5-high/grok-review.md` |
| 3 | Grok Build | Kimi Code | `d14dbba7b2d36f71483853995022b5898f386309` | `runs/kimi-kimi-k3-thinking/grok-review.md` |
| 4 | Codex CLI | Grok Build | `8bbe8de2875d32804067d8418fb5bc6fc8cb431c` | `runs/grok-grok-4.5-high/codex-review.md` |
| 5 | Codex CLI | Codex CLI | `6e3964f05b72d44a50f7d2a7657304a83cfa11c1` | `runs/codex-gpt-5.6-sol-xhigh/codex-review.md` |
| 6 | Codex CLI | Kimi Code | `d14dbba7b2d36f71483853995022b5898f386309` | `runs/kimi-kimi-k3-thinking/codex-review.md` |
| 7 | Grok Build | ZCode（glm-5.2-high） | 冻结后读取 ZCode `metadata.json` 的 `candidate.resultCommit` | `runs/zcode-glm-5.2-high/grok-review.md` |
| 8 | Codex CLI | ZCode（glm-5.2-high） | 冻结后读取 ZCode `metadata.json` 的 `candidate.resultCommit` | `runs/zcode-glm-5.2-high/codex-review.md` |
| 9 | Grok Build | Qoder（Qwen3.8-Max-Preview-thinking） | 冻结后读取 Qoder `metadata.json` 的 `candidate.resultCommit` | `runs/qoder-qwen3.8-max-preview-thinking/grok-review.md` |
| 10 | Codex CLI | Qoder（Qwen3.8-Max-Preview-thinking） | 冻结后读取 Qoder `metadata.json` 的 `candidate.resultCommit` | `runs/qoder-qwen3.8-max-preview-thinking/codex-review.md` |

## 1. Grok Build 评审 Codex CLI

```text
你现在执行 DecisionHarbor v0.1.0 的 Grok 首轮独立评审。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-sol-xhigh
- 候选分支：v0.1.0/codex-gpt-5.6-sol-xhigh
- 冻结 commit：6e3964f05b72d44a50f7d2a7657304a83cfa11c1
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/grok-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 codex-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 grok-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 6e3964f05b72d44a50f7d2a7657304a83cfa11c1。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 grok-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 2. Grok Build 评审 Grok Build

```text
你现在执行 DecisionHarbor v0.1.0 的 Grok 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论。即使你拥有该候选的开发阶段记忆，也只能依据本次对冻结 commit 的代码与运行证据评分，不得引用开发自述或给予自我信用。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.5-high
- 候选分支：v0.1.0/grokbuild-grok-4.5-high
- 冻结 commit：8bbe8de2875d32804067d8418fb5bc6fc8cb431c
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/grok-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 codex-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 grok-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 8bbe8de2875d32804067d8418fb5bc6fc8cb431c。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 grok-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 3. Grok Build 评审 Kimi Code

```text
你现在执行 DecisionHarbor v0.1.0 的 Grok 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/kimi-kimi-k3-thinking
- 候选分支：v0.1.0/kimicode-kimi-k3-thinking
- 冻结 commit：d14dbba7b2d36f71483853995022b5898f386309
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/grok-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 codex-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 grok-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 d14dbba7b2d36f71483853995022b5898f386309。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 grok-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 4. Codex CLI 评审 Grok Build

```text
你现在执行 DecisionHarbor v0.1.0 的 Codex 首轮独立评审。
这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论。即使你拥有该候选的开发阶段记忆，也只能依据本次对冻结 commit 的代码与运行证据评分，不得引用开发自述或给予自我信用。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/grok-grok-4.5-high
- 候选分支：v0.1.0/grokbuild-grok-4.5-high
- 冻结 commit：8bbe8de2875d32804067d8418fb5bc6fc8cb431c
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/codex-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/grok-grok-4.5-high/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 codex-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 8bbe8de2875d32804067d8418fb5bc6fc8cb431c。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 codex-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 5. Codex CLI 评审 Codex CLI

```text
你现在执行 DecisionHarbor v0.1.0 的 Codex 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论。即使你拥有该候选的开发阶段记忆，也只能依据本次对冻结 commit 的代码与运行证据评分，不得引用开发自述或给予自我信用。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/codex-gpt-5.6-sol-xhigh
- 候选分支：v0.1.0/codex-gpt-5.6-sol-xhigh
- 冻结 commit：6e3964f05b72d44a50f7d2a7657304a83cfa11c1
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/codex-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/codex-gpt-5.6-sol-xhigh/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 codex-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 6e3964f05b72d44a50f7d2a7657304a83cfa11c1。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 codex-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 6. Codex CLI 评审 Kimi Code

```text
你现在执行 DecisionHarbor v0.1.0 的 Codex 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/kimi-kimi-k3-thinking
- 候选分支：v0.1.0/kimicode-kimi-k3-thinking
- 冻结 commit：d14dbba7b2d36f71483853995022b5898f386309
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/codex-review.md

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/kimi-kimi-k3-thinking/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 codex-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- git rev-parse HEAD 必须是 d14dbba7b2d36f71483853995022b5898f386309。
- git status --short --branch 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 git status --short --branch 和 git diff --check。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 codex-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 7. Grok Build 评审 ZCode（glm-5.2-high）

```text
你现在执行 DecisionHarbor v0.1.0 的 Grok 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.2-high
- 候选分支：v0.1.0/zcode-glm-5.2-high
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/grok-review.md

冻结前置条件：
- 先读取 `baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/metadata.json`。
- 只有当 `completion.coordinatorFrozen` 为 `true`，且 `candidate.resultCommit` 是非空完整 SHA 时才能开始；将其记为 `RESULT_COMMIT`。
- 若任一条件不满足，停止并报告“候选尚未冻结”；不要评审、checkout、reset 或清理。

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 codex-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 grok-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- `git rev-parse HEAD` 必须等于 `RESULT_COMMIT`。
- `git status --short --branch` 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 `git status --short --branch` 和 `git diff --check`。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 grok-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 8. Codex CLI 评审 ZCode（glm-5.2-high）

```text
你现在执行 DecisionHarbor v0.1.0 的 Codex 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/zcode-glm-5.2-high
- 候选分支：v0.1.0/zcode-glm-5.2-high
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/codex-review.md

冻结前置条件：
- 先读取 `baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/metadata.json`。
- 只有当 `completion.coordinatorFrozen` 为 `true`，且 `candidate.resultCommit` 是非空完整 SHA 时才能开始；将其记为 `RESULT_COMMIT`。
- 若任一条件不满足，停止并报告“候选尚未冻结”；不要评审、checkout、reset 或清理。

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/zcode-glm-5.2-high/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 codex-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- `git rev-parse HEAD` 必须等于 `RESULT_COMMIT`。
- `git status --short --branch` 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 `git status --short --branch` 和 `git diff --check`。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 codex-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 9. Grok Build 评审 Qoder（Qwen3.8-Max-Preview-thinking）

```text
你现在执行 DecisionHarbor v0.1.0 的 Grok 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/qoder-qwen3.8-max-preview-thinking
- 候选分支：v0.1.0/qoder-qwen3.8-max-preview-thinking
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/grok-review.md

冻结前置条件：
- 先读取 `baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/metadata.json`。
- 只有当 `completion.coordinatorFrozen` 为 `true`，且 `candidate.resultCommit` 是非空完整 SHA 时才能开始；将其记为 `RESULT_COMMIT`。
- 若任一条件不满足，停止并报告“候选尚未冻结”；不要评审、checkout、reset 或清理。

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 codex-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 grok-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- `git rev-parse HEAD` 必须等于 `RESULT_COMMIT`。
- `git status --short --branch` 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 `git status --short --branch` 和 `git diff --check`。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 grok-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```

## 10. Codex CLI 评审 Qoder（Qwen3.8-Max-Preview-thinking）

```text
你现在执行 DecisionHarbor v0.1.0 的 Codex 首轮独立评审。

这是同一审查会话中的新候选。不要复用、比较、引用或继续使用此前候选的报告、分数、问题、命令输出或结论；只依据本次对冻结 commit 的代码与运行证据评分。

目标候选：
- 产品仓库：/home/liangjiaqi/projects/DecisionHarbor
- 候选工作树：/home/liangjiaqi/projects/DecisionHarbor/.worktrees/qoder-qwen3.8-max-preview-thinking
- 候选分支：v0.1.0/qoder-qwen3.8-max-preview-thinking
- baseline commit：1fb48f499d67677a47fb9b60e1f99346b46e0aee
- 唯一允许写入的文件：
  /home/liangjiaqi/projects/Agentship/baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/codex-review.md

冻结前置条件：
- 先读取 `baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/metadata.json`。
- 只有当 `completion.coordinatorFrozen` 为 `true`，且 `candidate.resultCommit` 是非空完整 SHA 时才能开始；将其记为 `RESULT_COMMIT`。
- 若任一条件不满足，停止并报告“候选尚未冻结”；不要评审、checkout、reset 或清理。

先阅读：
1. /home/liangjiaqi/projects/Agentship/AGENTS.md
2. baselines/DecisionHarbor/baseline-v0.1.0/evaluation-and-scoring.md
3. baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/metadata.json
4. baselines/DecisionHarbor/baseline-v0.1.0/runs/qoder-qwen3.8-max-preview-thinking/reproduction.md
5. 候选工作树中的 AGENTS.md、README.md、docs/index.md、docs/background/、docs/design/、docs/plan/。

独立性与写入边界：
- 可自由使用自身工具与 skills。
- 全程不要读取其他候选的 worktree、分支、运行记录或评审材料。
- 不要读取本候选的 grok-review.md、review-summary.md、scorecard.md。
- 不要修改候选源码、候选分支、baseline、评分规范或其他归档文件。
- 不要 git add、commit、push、创建 PR。
- 只改写 codex-review.md。
- 不因 Agent、模型、耗时、token 或既往印象改变评分。

开始前在候选工作树确认：
- `git rev-parse HEAD` 必须等于 `RESULT_COMMIT`。
- `git status --short --branch` 必须无未提交改动。
- 若不满足，停止并报告，不要 checkout、reset 或清理。

在候选工作树中按其支持的命令做只读复现与审查。覆盖启动、健康/就绪、迁移与 seed、允许与拒绝 SQL、双库隔离、资源限制、测试入口、浏览器主链，以及可行时的并行 Compose 隔离。没有新鲜证据的项目必须标为“未验证”，不能按通过处理。若启动了 Compose 资源，结束前停止本次评审启动的资源；不得停止无关项目。

只评以下技术 90 分：功能与外部契约 25 分、SQL 治理与数据正确性 20 分、可运行性与可靠性 20 分、测试与验证证据 15 分、代码质量与可维护性 10 分。另给出产品文档 0–5 的建议分和证据，但不要给视觉分，不要计算最终 100 分或任何平均分。

结束前再次检查候选工作树的 `git status --short --branch` 和 `git diff --check`。若有非忽略改动，记录并停止，不要自行清理。

将完整报告写入指定 codex-review.md，至少包含：独立性声明；评审 commit、环境与实际执行命令；每个技术子项的分数、证据与未验证项；技术总分 /90；文档建议分 /5；P0/P1/P2 风险标记判断及可复核证据；按严重度排序的问题清单；Compose 资源停止情况与最终 Git 状态。

完成后只汇报：报告路径、技术总分、文档建议分、风险标记、关键问题和未验证项。
```
