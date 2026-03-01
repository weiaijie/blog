# Windows Runner: 原生界面自动化与截图

## 目标

当任务需要 Windows 原生界面（而不仅是网页）时，使用专用 Windows Runner 执行，并接入同一套 run/event/artifact 体系。

## 适用场景

- 必须操作 Windows 原生应用窗口（Win32/WPF/UWP）。
- 必须处理系统级弹窗（文件选择器、权限弹窗、系统对话框）。
- 必须使用仅支持 Windows GUI 的第三方工具。

## 非适用场景

- 纯网页自动化、网页截图、API 调用验证。
- 这些任务继续走 WSL/macOS Runner 即可。

## 调度规则（建议）

在创建 run 时增加能力标签：

```json
{
  "requires_windows_ui": true,
  "capabilities": ["desktop_ui", "native_dialog", "screen_capture"]
}
```

调度器策略：

1. `requires_windows_ui=true` -> 路由 Windows Runner。
2. 否则默认路由 WSL/macOS Runner。
3. 无可用 Windows 节点时，直接返回 `QUEUE_WAITING_WINDOWS_RUNNER`，不要降级到 WSL/macOS 硬跑。

## 执行前硬性检查

1. 机器在线且 Runner 心跳正常。
2. 存在可交互桌面会话（已登录用户会话）。
3. 目标应用可启动，屏幕分辨率与缩放设置固定。
4. 截图路径与 artifact 路径可写入。

## 关键实现约束

- Windows 界面截图依赖真实桌面上下文；无桌面会话时通常无法稳定捕获窗口。
- 统一事件协议：
  - `step.started/step.completed/step.failed`
  - `artifact.created`
  - `heartbeat`
- 统一上传协议：
  - `POST /v1/artifacts/init`
  - 上传对象存储
  - `POST /v1/artifacts/complete`

## 失败恢复建议

1. 截图失败：立即抓取当前会话状态与错误码，上报 `step.failed(capture_error)`。
2. 应用无响应：执行超时回收，保留最后一次可用截图和日志。
3. 会话丢失（锁屏/注销）：标记 `runner_offline_or_no_desktop_session`，触发告警并暂停任务。

## 验收标准

- `requires_windows_ui=true` 的任务不会误路由到 WSL/macOS。
- 失败路径可产出最少证据：`error screenshot + stderr/log + step.failed`。
- Windows Runner 的事件与 artifact 在主监控页面可与其他平台统一展示。

