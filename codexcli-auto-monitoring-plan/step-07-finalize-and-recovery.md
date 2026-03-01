# Step 07: 收尾、终态写入与恢复重放

## 目标

将 run 可靠地收敛到终态，并确保 Runner 崩溃或断网后可恢复。

## 前置条件

- CLI 阶段与自动化阶段已执行。
- 本地 spool 与 artifact 队列可访问。

## 输入

- 子进程退出码
- step 执行结果
- 上传结果
- 本地未上报事件列表

## 执行动作

1. 进入 `finalizing` 阶段。
2. 等待：
   - sender 队列清空
   - artifact 补偿队列清空或达到失败阈值
3. 根据规则写终态：
   - 全部成功：`run.completed`
   - 存在不可恢复失败：`run.failed`
   - 被人工取消：`run.aborted`
4. 发送最终心跳（`phase=finished`）并关闭进程。

## 恢复重放流程

1. Runner 启动时扫描 `runtime/*/spool/events.ndjson`。
2. 读取每条事件并按 `idempotency_key` 重放到后端。
3. 后端去重成功后删除或归档本地 spool。
4. 若重放失败超过阈值，移动到 `dlq/` 并告警。

## 产出

- 明确终态
- 可复盘的恢复日志

## 验收标准

- Runner 在任意时刻崩溃重启后，run 可继续或正确终结。
- 不出现“前端显示运行中但后端已终止”的悬空状态。

