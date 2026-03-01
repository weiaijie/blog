# Codex CLI Auto Monitoring 实施拆解

本目录将 [codexcli自动对话.md](/home/saber/projects/blog/codexcli自动对话.md) 里的端到端方案拆成可执行步骤。

## 目标

- AI 输出停止后，Runner 继续记录自动化执行过程。
- 监控端实时判断 `CLI 是否在工作`，区分 `running/idle/stall/offline/finished`。
- 全程保留审计链：事件、截图、视频、trace、上传记录、最终结论。

## 执行顺序

1. `step-01-run-init.md`：Run 初始化与最小权限准备
2. `step-02-codex-launch.md`：启动 `codex exec --json`
3. `step-03-stream-and-spool.md`：stdout/stderr 解析与本地缓冲
4. `step-04-heartbeat-and-state.md`：心跳、派生状态与告警
5. `step-05-playwright-pipeline.md`：自动化步骤和证据链
6. `step-06-artifact-upload.md`：媒体上传与两阶段提交
7. `step-07-finalize-and-recovery.md`：收尾、失败恢复、重放
8. `step-08-security-and-deploy.md`：安全与部署
9. `step-09-acceptance.md`：验收标准与压测

## 最低交付标准

- 事件不丢失：Runner 异常重启后可重放本地 spool。
- 监控可解释：前端看到状态变化必须能追溯到具体事件。
- 证据完整：失败场景至少保留 `stderr + screenshot + trace`。

