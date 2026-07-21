# ZCode 复现记录

## 状态

- 候选已冻结于 `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde`（`feat(首轮): 交付受治理 SQL 查询平台`），并已推送 `v0.1.0/zcode-glm-5.2-high`。
- 冻结前后均记录了 `HEAD`、`git status --short --branch` 和 `git diff --check`；冻结后工作树无未提交改动，本地与远端 SHA 一致。
- 在用户明确授权下，协调方已执行 `docker compose down`；ZCode 的 Compose 容器和网络均已停止并移除。
- 提交前协调方复验通过：数据集校验、策略测试 `36 passed in 0.06s`、Vite 构建 `606 ms`、Shell 语法与 Python 编译。集成测试和浏览器主链的完成证据仍为 Agent 报告，尚未独立复现。
- 2026-07-21 完成远端分支命名迁移和本地归档清理；原候选工作树与本地分支均已删除，后续复现须从远端结果分支的冻结 SHA 建立临时工作树。
- Codex 与 Grok 的首轮独立评审均已冻结，当前等待人工文档分与视觉分；本文件不重新陈述评分结论。

Grok 与 Codex 可按各自互盲提示词，在冻结候选工作树或独立 review worktree 中执行启动、数据集校验、测试、健康检查、允许/拒绝 SQL API、浏览器主链和并行 Compose 复现。直接使用候选工作树时，开始与结束均记录 `HEAD`、`git status --short --branch` 和 `git diff --check`。
