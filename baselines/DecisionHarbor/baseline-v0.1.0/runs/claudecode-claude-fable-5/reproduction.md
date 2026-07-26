# Claude Code 复现记录

## 状态

- 候选已冻结于 9e11644de468e1008784c42ff093ce6a0c96aae9（feat(基座): 建立文档治理、首轮设计与受治理查询链路），并已推送 v0.1.0/claudecode-claude-fable-5。
- 冻结前后均确认工作树干净，git diff --check 通过；基线为 baseline-v0.1.0 / 1fb48f499d67677a47fb9b60e1f99346b46e0aee，本地与远端结果 SHA 一致。
- 协调方运行 python3 datasets/sales-analytics-v1/validate.py 成功，并按 ./dev.sh test 的内部顺序独立执行容器测试：pytest 单元 47 passed、pytest 双库集成 19 passed、Vitest 5 passed、Playwright 3 passed。测试输出只有 FastAPI/Starlette 弃用警告。
- 在用户明确授权后，协调方运行 ./dev.sh down --remove-orphans；本候选的 Compose 容器和网络均已停止并移除，数据卷 decisionharbor-claudecode-claude-fable-5_dbdata 保留。
- 两份首轮独立评审尚未开始；本文件不含评分结论。

Grok 与 Codex 可按各自互盲提示词，在冻结候选工作树或独立 review worktree 中执行启动、数据集校验、测试、健康检查、允许/拒绝 SQL、浏览器主链和并行 Compose 复现。直接使用候选工作树时，开始与结束均记录 HEAD、git status --short --branch 和 git diff --check。
