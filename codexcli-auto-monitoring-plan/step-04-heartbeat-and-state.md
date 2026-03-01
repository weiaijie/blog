# Step 04: 心跳、状态派生与告警

## 目标

稳定判定运行状态，不把“无输出”误判为“已停止”。

## 前置条件

- Step 03 事件采集已运行。

## 输入

- `cli_alive`
- `last_stdout_ts`
- `last_stderr_ts`
- `last_event_ts`
- `last_heartbeat_ts`
- `steps_done/steps_total`

## 参数建议

- `H=5s`（心跳间隔）
- `T_dead=20s`（Runner 离线阈值）
- `T_idle=30~90s`（AI 静默阈值）
- `T_stall=5~15min`（疑似卡顿阈值）

## 状态定义

- `RUNNER_OFFLINE`
- `CLI_RUNNING`
- `CLI_STOPPED`
- `AI_IDLE`
- `STALL_SUSPECTED`
- `FINISHED`

## 状态优先级

`RUNNER_OFFLINE > FINISHED > STALL_SUSPECTED > AI_IDLE > CLI_RUNNING > CLI_STOPPED`

## 严格转移表

| 当前状态 | 触发条件 | 下一个状态 | 动作 |
|---|---|---|---|
| `CLI_RUNNING` | `now-last_output > T_idle` 且 `cli_alive=true` | `AI_IDLE` | 标记“静默中” |
| `AI_IDLE` | 收到任意新 stdout/stderr | `CLI_RUNNING` | 清空 idle 计时 |
| `CLI_RUNNING/AI_IDLE` | `now-last_event > T_stall` 且 step 无变化 | `STALL_SUSPECTED` | 触发告警 |
| `STALL_SUSPECTED` | 任意事件恢复流动 | `CLI_RUNNING` | 关闭告警 |
| 任意运行态 | `now-last_heartbeat > T_dead` | `RUNNER_OFFLINE` | 置离线，等待恢复 |
| `RUNNER_OFFLINE` | 心跳恢复且 `cli_alive=true` | `CLI_RUNNING` | 补传 spool |
| 任意运行态 | `cli_alive=false` 且 pipeline 未完成 | `CLI_STOPPED` | 转后处理阶段 |
| `CLI_STOPPED` | 后处理与上传完成 | `FINISHED` | 发送 run 终态 |

## 产出

- 周期性 `heartbeat` 事件
- 后端派生状态
- 告警事件（如 `stall_detected`）

## 验收标准

- 前端状态变化与事件时间线一致。
- `RUNNER_OFFLINE` 与 `AI_IDLE` 不混淆。

