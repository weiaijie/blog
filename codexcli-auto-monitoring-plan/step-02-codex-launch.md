# Step 02: 启动 Codex CLI（JSONL 模式）

## 目标

以子进程方式稳定启动 `codex exec --json`，让 stdout 输出事件流，stderr 输出进度文本。

## 前置条件

- Step 01 已完成，`run_id` 已创建。
- `workdir` 和权限模式已确定。

## 输入

- `run_id`
- `prompt`
- `workdir`
- 安全策略参数（sandbox mode）

## 推荐命令

```bash
codex exec --json --full-auto "<prompt>"
```

可选参数：

- `--output-last-message <file>`：落最终自然语言总结
- `--output-schema <json-schema-file>`：约束最终输出结构
- `--skip-git-repo-check`：仅在非 Git 场景且风险已接受时启用

## 执行动作

1. 使用 `subprocess.Popen` 启动，显式接管 `stdout`/`stderr`。
2. 为 stdout 和 stderr 分配独立读取线程（或异步任务）。
3. 记录 `pid`、启动时间、完整命令参数（脱敏后）。
4. 立即发送 `step.started`（step=`codex_exec`）。

## 产出

- 活跃的 Codex 子进程
- 管道读取器（stdout/stderr）运行中
- 首条运行事件入库

## 验收标准

- CLI 进程存活且可读取两路输出。
- 无阻塞（不能只读一条流导致另一条堵塞）。
- 监控端看到 `cli_alive=true`。

## 失败处理

- 启动失败（命令不存在、权限问题）：写 `run.failed` 并附错误原因。
- 进程秒退：抓取退出码和最后 50 行 stderr 上报。

