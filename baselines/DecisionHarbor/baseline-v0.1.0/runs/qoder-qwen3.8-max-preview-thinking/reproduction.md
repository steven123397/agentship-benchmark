# Qoder 复现记录

## 状态

- 候选已冻结于 `fffe1f6bbe15872479d3579ea99d57deba7445f3`（`feat(首轮): 交付受治理 SQL 查询平台`），并已推送 `v0.1.0/qoder-qwen3.8-max-preview-thinking`。
- 当前工作树干净，本地与远端 SHA 一致；基线为 `baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 用户报告 Agent 完成了三段委托，但未提供可归档的最终测试、构建或端到端验证明细；这些项目均待独立复现，不按通过处理。
- 在用户明确授权后，协调方已执行 `docker compose down --remove-orphans`；Qoder 的 Compose 容器和网络均已停止并移除，数据卷保留。
- 两份首轮独立评审尚未开始；本文件不含评分结论。

Grok 与 Codex 可按各自互盲提示词，在冻结候选工作树或独立 review worktree 中执行启动、数据集校验、测试、健康检查、允许/拒绝 SQL、浏览器主链和并行 Compose 复现。直接使用候选工作树时，开始与结束均记录 `HEAD`、`git status --short --branch` 和 `git diff --check`。
