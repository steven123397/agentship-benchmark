# Claude Code 人工介入记录

本记录只保留总调度可确认的非标准介入，不将冻结的开发委托或 Agent 自述视为评分证据。

截至启动前，未记录非标准人工介入。

## 完成与冻结

- 用户报告 Claude Code 已完成三段开发委托，并于 2026-07-26 19:39 形成提交 9e11644de468e1008784c42ff093ce6a0c96aae9。
- 用户提供的时间戳统计为全程约 1 小时 40 分钟；精确 token 数据未取得，相关估算与环境等待记入 efficiency.json。
- 用户仅确认正式调用过一次 bootstrap-project-governance 外部 skill。TDD、完成前验证、中文文档和中文提交约定仅报告为遵循的原则或规范，不计为正式外部 skill 调用。
- 协调方独立运行固定数据集校验，以及项目测试入口所包含的 4 组容器测试：pytest 单元 47 passed、pytest 双库集成 19 passed、Vitest 5 passed、Playwright 3 passed。FastAPI/Starlette 仅出现弃用警告，无测试失败。
- 在用户明确授权后，协调方运行 ./dev.sh down --remove-orphans，停止并移除本候选的 Web、API、DB 容器和默认网络，保留命名数据卷。
- 协调方将现有结果提交推送到 v0.1.0/claudecode-claude-fable-5，未修改候选源码。

## 首轮评审与汇总

- 用户确认 Codex 与 Grok 首轮评审均已完成。两份报告仅写入各自指定的归档文件，候选源码、分支和 baseline 未被本汇总流程改写。
- Codex 报告技术分为 77 / 90、文档建议为 5 / 5，并报告 P0；Grok 报告技术分为 88.5 / 90、文档建议为 5 / 5，并未报告风险标记。汇总保留两份独立评分原文，不以协调方判断改写任一评分。
- 因两份报告对 SQL 对象范围结论不一致，协调方在用户要求停止进一步复现前已启动一次仅含 db + API 的 dhclaude-archive-audit 隔离实例。该实例通过公开 API 返回了两条系统目录访问 SQL 的 succeeded 响应；此记录只用于汇总风险事实，不构成第三份评分或对独立评分的重算。随后用户明确表示无需继续复现，协调方只完成资源清理。
- dhclaude-archive-audit 的容器、网络和专用数据卷已删除；候选工作树保持冻结 SHA 且干净。
- 首轮评审结束后的 Docker 检查显示 decisionharbor-claudecode-claude-fable-5_dbdata 已不存在。Grok 报告的资源段声明使用 ./dev.sh down --remove-orphans --volumes；该事实作为运行记录保留，不改变质量分，也未尝试恢复数据卷。
