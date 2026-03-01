# Step 03: 事件流解析与本地 Spool

## 目标

将 Codex 的 stdout(JSONL) 与 stderr(进度文本)统一封装为系统事件，并保证断网不丢。

## 前置条件

- Step 02 子进程已启动。

## 输入

- stdout 行流
- stderr 行流
- `run_id`

## 执行动作

1. 标准化事件 envelope：
   - `event_id`
   - `run_id`
   - `source`
   - `event_type`
   - `payload`
   - `idempotency_key`
2. stdout 每行尝试 JSON 解析：
   - 成功：`event_type=cli.jsonl`
   - 失败：`event_type=cli.stdout.non_json`
3. stderr 每行直接入事件：
   - `event_type=cli.stderr`
4. 先写本地 append-only spool，再异步批量上报：
   - 文件建议：`./runtime/<run_id>/spool/events.ndjson`
5. sender 线程批量提交 `POST /v1/runs/{run_id}/events:batch`。

## 幂等键建议

- 采用单调递增序号，不要用毫秒时间戳直接拼接。
- 示例：`run:<run_id>:src:<source>:seq:<00000123>`

## 产出

- 可重放的本地事件日志
- 后端实时事件流

## 验收标准

- 网络中断 3 分钟后恢复，不丢事件、无重复写入。
- 事件顺序在同一 source 内可重建。

## 失败处理

- 上报失败：指数退避 + 本地积压（内存队列达到阈值后仅写盘）。
- spool 写盘失败：立即触发 `run.failed`（该错误属于致命错误）。

