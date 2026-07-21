# Qoder 复现记录

## 状态

- 候选尚处于开发阶段，尚无结果 commit。
- 当前分支为 `v0.1.0/qoder-qwen3.8-max-preview-thinking`，基线为 `baseline-v0.1.0` / `1fb48f499d67677a47fb9b60e1f99346b46e0aee`。
- 独立评审与运行复现均尚未开始；本文件不含评分结论。

候选冻结后，Grok 与 Codex 可按各自互盲提示词，在冻结候选工作树或独立 review worktree 中执行启动、数据集校验、测试、健康检查、允许/拒绝 SQL、浏览器主链和并行 Compose 复现。直接使用候选工作树时，开始与结束均记录 `HEAD`、`git status --short --branch` 和 `git diff --check`。
