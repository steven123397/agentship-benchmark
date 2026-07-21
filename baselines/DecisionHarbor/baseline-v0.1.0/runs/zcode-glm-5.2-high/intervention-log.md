# ZCode 人工介入记录

本记录只保留总调度可确认的非标准介入，不将冻结的开发委托或 Agent 自述视为评分证据。

截至启动前，未记录非标准人工介入。

## 完成声明后的归档事实

- Agent 已宣告提示词 3 的实现工作完成，并提供了部分构建和验证用时；完整墙钟时长与累计 token 用量均不可观测，详情见 `efficiency.json`。
- 冻结前只读检查时，候选工作树仍位于 baseline commit `1fb48f499d67677a47fb9b60e1f99346b46e0aee`，且包含未提交的交付改动。随后在用户明确授权下，协调方只补充 `*.egg-info/` 忽略规则，创建结果提交 `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde` 并推送 `v0.1.0/zcode-glm-5.2-high`。
- 同次检查发现 `decisionharbor-db-1` 正在运行，其 Compose 工作目录为该候选工作树。在用户明确授权下，协调方执行 `docker compose down`，容器和网络已移除；冻结后工作树干净。

## 本地归档清理

- 远端分支从 `run/zcode-glm-5.2-high` 迁移至 `v0.1.0/zcode-glm-5.2-high`，迁移前后均以结果 SHA `e3934d3dbaf8ecf384c38d9bb27e84f70a0abcde` 核验。
- 2026-07-21，在 AgentShip 归档推送后，协调方删除原候选工作树、当地分支及 `dhzcode*` 镜像标签。没有仍在运行或可归属的 ZCode 容器、网络、卷；全局缓存和通用镜像保持不动。
- 本地清理不改变首轮质量分、风险标记或后续从远端 SHA 重建临时工作树的能力。
