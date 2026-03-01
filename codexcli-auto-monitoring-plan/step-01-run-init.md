# Step 01: Run 初始化与环境准备

## 目标

创建一次可追踪运行 `run_id`，并准备 Runner 的执行上下文、鉴权与权限策略。

## 前置条件

- 已有后端服务，至少可提供 `POST /v1/runs`。
- Runner 机器可访问 OpenAI 与你的后端 API。
- `codex` 命令可执行。
- 支持平台为以下之一：
  - WSL2 (Ubuntu 22.04/24.04 推荐)
  - macOS 13+ (Intel/Apple Silicon)

## 输入

- 用户任务描述 `prompt`
- 执行目录 `workdir`
- 设备身份信息（runner_id, machine_id）
- 能力需求标签（例如 `requires_windows_ui`, `capabilities[]`）

## 执行动作

1. 调用 `POST /v1/runs`，获取 `run_id` 与流地址。
   - 同时传递能力标签，供调度器选择 WSL/macOS/Windows Runner。
2. 校验 `workdir`：
   - 推荐为 Git 仓库根目录。
   - 非 Git 仓库仅在明确风险可控时允许继续。
   - WSL 使用 Linux 路径（例如 `/home/<user>/...`），避免直接在 `/mnt/c` 上跑高 I/O 流程。
   - macOS 确认 `workdir` 在本地磁盘可读写且具备执行权限。
3. 构建最小权限策略：
   - 默认 `read-only`
   - 需要文件改动时启用 `--full-auto`
   - 仅在隔离环境考虑 `danger-full-access`
4. 注入运行时环境变量：
   - `CODEX_API_KEY`（或等价密钥来源）
   - `RUN_ID`
   - `RUNNER_ID`
5. 平台自检：
   - WSL: `uname -a` 包含 `microsoft-standard-WSL`
   - macOS: `sw_vers` 可执行，`uname -s` 返回 `Darwin`

## 产出

- `run_id`
- 运行元数据文件：`./runtime/<run_id>/run.meta.json`
- 当前运行权限级别记录（用于审计）

## 验收标准

- `run_id` 能在后端查询到。
- Runner 启动前就有完整元数据。
- 权限级别可追溯（谁在什么条件下提升了权限）。

## 失败处理

- `POST /v1/runs` 失败：指数退避重试，超过阈值直接失败退出。
- `workdir` 不可读或不存在：直接标记 `run.failed`，不要启动 Codex。
