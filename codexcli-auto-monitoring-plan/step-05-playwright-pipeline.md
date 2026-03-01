# Step 05: Playwright 执行与证据链

## 目标

即使 Codex 子进程结束，Runner 仍按 pipeline 执行自动化并持续记录证据。

## 前置条件

- Step 02 与 Step 03 运行中或已完成 CLI 阶段。

## 输入

- 自动化步骤计划（结构化或静态配置）
- `artifact_root`

## 执行动作

1. 每个自动化步骤统一发事件：
   - `step.started`
   - `step.completed` 或 `step.failed`
2. Playwright 证据策略：
   - 关键节点截图：`page.screenshot(full_page=True)`
   - 录像：`record_video_dir=...`
   - trace：`context.tracing.start/stop`
3. `try/finally` 强制执行：
   - `tracing.stop()`
   - `context.close()`（触发视频落盘）
4. 失败路径至少保留：
   - `error screenshot`
   - `trace.zip`
   - 最后 N 行 `cli.stderr`

## 目录建议

```text
runtime/<run_id>/artifacts/
  screenshots/
  videos/
  traces/
```

## 产出

- 自动化步骤事件
- 可审计媒体文件（截图/视频/trace）

## 验收标准

- 人工复盘一次失败任务时，不依赖口头信息即可还原故障路径。
- `context.close()` 在异常场景也被执行。

## 失败处理

- step 超时：标记 `step.failed(timeout)`，进入可配置重试。
- 浏览器启动失败：记录失败并跳过后续依赖该浏览器的步骤。

