# DecisionHarbor v0.2.0 隐藏 Harness

本目录是冻结评测 artifact，不属于候选产品仓库。它通过公开 HTTP 接缝和统一故障场景验证 spec，不规定候选的表结构、SQL、锁、线程模型或 Compose 服务名。

## 运行顺序

1. 从候选冻结 commit 建立干净工作树，以独立 Compose 项目名和端口启动完整产品。
2. 运行公开合同套件：

   ```bash
   ./hidden-harness/run \
     --api-url http://127.0.0.1:<api-port> \
     --report /tmp/<candidate-id>-hidden-http.json
   ```

3. 按 [`scenarios.md`](scenarios.md) 执行故障与边界协议，将每个场景的实际命令、观察接缝、结果和未验证项写入候选 `reproduction.md`。
4. 停止本次评测启动的资源，再核对候选工作树仍位于冻结 commit 且没有非忽略改动。

HTTP runner 只依赖 Python 3 标准库。任一 case 失败时退出码为 1，全部通过时为 0；JSON 报告是原始复现证据，不直接包含分数。

## Artifact hash

`harness-manifest.json` 中的 SHA-256 由本目录所有受控文件计算。算法是在本目录内按相对路径排序普通文件，逐个生成 `sha256sum` 输出，再对完整输出计算 SHA-256；测试缓存、临时报告和其他生成物不计入 artifact。
