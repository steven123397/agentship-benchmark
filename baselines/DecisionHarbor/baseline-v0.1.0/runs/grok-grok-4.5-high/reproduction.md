# Grok Build 复现记录

## 状态

- 候选结果已冻结为 `8bbe8de2875d32804067d8418fb5bc6fc8cb431c`。
- 远端结果分支为 `origin/v0.1.0/grokbuild-grok-4.5-high`。
- 收尾时已执行 `./scripts/down.sh`，当前 Compose 栈已停止。
- 2026-07-21 完成远端分支命名迁移和本地归档清理；原候选工作树与本地分支均已删除，后续复现须从远端结果分支的冻结 SHA 建立临时工作树。
- Codex 与 Grok 的首轮独立评审均已冻结，当前等待人工文档分与视觉分；本文件不重新陈述评分结论。

## Agent 自述（未独立采信）

Agent 报告其在完成前执行过数据集校验、Compose 启动、允许和拒绝查询 API、`pytest`（26 passed）及 Playwright（2 passed）。这些陈述仅供后续复现定位，不构成通过证据。

## 协调方收尾观察

1. 在停止前，`GET /health` 返回 `{"status":"ok"}`，`GET /ready` 返回 `{"status":"ready",...}`，Web 根路径返回 HTTP 200。
2. 协调方随后启动 `./scripts/test.sh`。数据集校验通过，但脚本在 Compose 构建时无法从 Docker Hub 获取 `python:3.13-slim` 的匿名令牌，报 `dial tcp ...:443: i/o timeout`。
3. 用户明确要求不重试该验证，直接冻结候选源码。因此本次协调方完整测试状态为“未验证”，不应按通过计分。

## 待执行的独立复现

在冻结候选工作树或独立 review worktree 中，从冻结 commit 重新执行项目支持的启动、数据集校验、统一测试、健康检查、允许/拒绝 SQL API 和浏览器主链，并保存命令与输出。直接使用候选工作树时，开始与结束均记录 `HEAD`、`git status --short --branch` 和 `git diff --check`。
