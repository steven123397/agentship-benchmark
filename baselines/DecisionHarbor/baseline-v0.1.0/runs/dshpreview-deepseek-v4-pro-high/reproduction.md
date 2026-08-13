# DeepSeek Harness Web 复现记录

## 状态

- 候选尚在开发中，尚未产生结果提交、运行时验证材料或首轮评审结论。
- 基线为 baseline-v0.1.0 / 1fb48f499d67677a47fb9b60e1f99346b46e0aee。
- 候选工作树为 /home/liangjiaqi/projects/DecisionHarbor/.worktrees/dshpreview-deepseek-v4-pro-high，分支为 v0.1.0/dshpreview-deepseek-v4-pro-high。
- 创建时已确认工作树 HEAD 为基线提交、无未提交改动，git diff --check 通过；固定数据集校验已通过。
- DeepSeek Harness Web 已于 2026-08-13T14:21:20Z 在 http://127.0.0.1:54173 启动，GET / 返回 HTTP 200。该服务不是候选产品的 Web、API 或 Compose 运行证据。

候选完成并冻结后，本文件将记录协调方独立执行的固定数据集校验、项目测试、Compose 启动、health/ready、允许与拒绝 SQL API 证据和浏览器主链。没有新鲜证据的项目保持未验证。
