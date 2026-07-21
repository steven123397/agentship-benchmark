# ZCode 人工介入记录

本记录只保留总调度可确认的非标准介入，不将冻结的开发委托或 Agent 自述视为评分证据。

截至启动前，未记录非标准人工介入。

## 完成声明后的归档事实

- Agent 已宣告提示词 3 的实现工作完成，并提供了部分构建和验证用时；完整墙钟时长与累计 token 用量均不可观测，详情见 `efficiency.json`。
- 冻结前只读检查时，候选工作树仍位于 baseline commit `1fb48f499d67677a47fb9b60e1f99346b46e0aee`，且包含未提交的交付改动。随后在用户明确授权下，协调方只补充 `*.egg-info/` 忽略规则，创建结果提交 `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde` 并推送 `v0.1.0/zcode-glm-5.2-high`。
- 同次检查发现 `decisionharbor-db-1` 正在运行，其 Compose 工作目录为该候选工作树。在用户明确授权下，协调方执行 `docker compose down`，容器和网络已移除；冻结后工作树干净。
