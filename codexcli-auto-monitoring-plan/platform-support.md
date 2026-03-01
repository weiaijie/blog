# Platform Support: WSL 与 macOS

## 结论

- 当前实施方案以 `WSL2 (Ubuntu)` 和 `macOS` 为第一优先支持平台。
- 两个平台都可以完整实现：Codex CLI 运行、JSONL 采集、心跳上报、Playwright 证据链、上传与重放。
- 对于必须依赖 Windows 原生界面的流程，使用单独的 Windows Runner 执行（见 `windows-runner.md`）。

## 支持矩阵

| 能力 | WSL2 | macOS |
|---|---|---|
| `codex exec --json` | 支持 | 支持 |
| stdout/stderr 双流采集 | 支持 | 支持 |
| 心跳与事件上报 | 支持 | 支持 |
| Playwright screenshot/video/trace | 支持 | 支持 |
| 本地 spool + 重放 | 支持 | 支持 |

## Windows 原生 UI 场景

| 能力 | Windows Desktop Runner |
|---|---|
| 原生应用窗口截图 | 支持 |
| 系统弹窗/文件选择器操作 | 支持 |
| 仅 Windows 可用工具自动化 | 支持 |

说明：

- 这类任务不建议在 WSL/macOS 上模拟，直接路由到 Windows Runner 更稳。
- Windows Runner 与其他平台共用同一套事件协议和 artifact 上传接口。

## 统一约束

1. 统一目录规范
   - `runtime/<run_id>/spool/events.ndjson`
   - `runtime/<run_id>/artifacts/{screenshots,videos,traces}`
2. 统一 shell 启动方式
   - 使用 `bash -lc`（CI 和本地一致）
3. 统一超时参数
   - `H=5s`, `T_dead=20s`, `T_idle=30~90s`, `T_stall=5~15min`

## 平台差异处理

1. 路径
   - WSL 全部使用 Linux 路径；不要混用 Windows 风格路径。
   - macOS 保持 POSIX 路径，不依赖 GNU-only 命令参数。
2. 依赖安装
   - WSL 和 macOS 都固定 Node/Python 版本，并锁定 Playwright 版本。
3. 文件系统性能
   - WSL 不建议把高频 I/O 放 `/mnt/c`。
   - macOS 建议将浏览器缓存目录与 artifact 目录分离。

## 最小自检命令

```bash
codex --version
python3 --version
node --version
```

```bash
# WSL
uname -a
```

```bash
# macOS
uname -s && sw_vers
```
