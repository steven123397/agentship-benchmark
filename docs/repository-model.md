# 仓库与分支模型

## 1. 设计目标

AgentShip 需要同时保存评测方法和多个真实项目 baseline，但不能让 baseline 项目携带评测叙事，也不能让不同项目被迫共享历史、依赖和工程结构。

因此，本仓库采用多条无共同祖先的 Git 历史：

- `main` 是 AgentShip 元项目。
- 每个 baseline 项目是一条独立 orphan branch。
- 分支之间不合并，也不共享根提交。

## 2. main 分支

`main` 可以保存：

- AgentShip 的公开介绍和方法说明
- baseline 项目索引
- 不同阶段的任务和提示词
- 统一测试与评审规则
- 运行元数据、结果和比较报告
- 未来可能建设的辅助脚本与展示工具

`main` 不保存 baseline 项目的产品源码、产品依赖或详细产品内部文档。

## 3. Baseline 项目分支

每个 baseline 分支都是可长期发展的真实软件项目，例如：

```text
baseline/enterprise-rag
baseline/facility-operations
```

它应拥有正常项目所需的：

- 产品 README
- 可行性分析和需求分析
- 架构、数据模型与第一版设计
- 源码、依赖、迁移、测试和 CI
- 项目自身的 Agent 与文档治理规则

baseline 项目中不出现候选模型、横向评测、评分标准、隐藏测试或“所有模型保持同一进度”等表述。

## 4. 分支与快照

baseline 分支可以继续开发，因此分支名称不能独立标识一次可重复实验。每次任务必须绑定一个固定 commit：

```text
baseline/enterprise-rag@<commit-sha>
```

必要时可以使用带项目前缀的版本标签辅助识别，但 commit SHA 始终是最终依据。

## 5. 访问隔离

Git 分支不是安全边界。直接在中央仓库创建 worktree 时，Agent 仍可能通过 Git 命令读取 `main` 或其他 baseline 的内容。

正式评测时应：

1. 从固定 baseline commit 导出一个干净的独立仓库。
2. 只保留该项目需要的历史和引用。
3. 将候选仓库的默认分支正常命名为 `main`。
4. 在这个隔离仓库中为不同 Agent 创建独立分支或 worktree。
5. 将评测规则、隐藏测试和其他 Agent 结果保留在候选仓库外部。

当前阶段只记录这一原则，不实现自动化导出和运行系统。

## 6. 禁止的历史操作

- 不在 `main` 与 baseline 分支之间 merge。
- 不在不同 baseline 项目之间 merge。
- 不通过 rebase 让 baseline 项目继承 `main` 历史。
- 不直接把某个 Agent 的评测结果合并回 baseline 项目。

若评测暴露了基础项目缺陷，应由项目维护者在 baseline 分支中独立修复，并以新的 commit 作为未来任务起点。
