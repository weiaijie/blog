# Qoder 数据查询与备份工具

此目录包含一系列自动化脚本，用于查询、分析和备份 Qoder 编辑器的本地数据，特别是 AI 聊天相关数据。

## 脚本列表

### 1. `find_qoder_data.ps1` (PowerShell脚本)
- 自动查找并显示 Qoder 本地数据目录结构
- 分析 workspaceStorage 和 globalStorage 目录内容
- 检测 aicoding 相关扩展目录
- 计算数据总大小

**运行方法：**
```powershell
.\find_qoder_data.ps1
```

### 2. `find_qoder_data.bat` (批处理脚本)
- Windows 批处理版本的查找工具
- 功能与 PowerShell 版本相同
- 适用于没有 PowerShell 访问权限的环境

**运行方法：**
```cmd
.\find_qoder_data.bat
```

### 3. `analyze_qoder_data.py` (Python 脚本)
- 深度分析 Qoder 数据结构
- 解析 SQLite 数据库 (state.vscdb) 中的键值对
- 识别可能包含聊天数据的键
- 搜索 aicoding 相关扩展中的数据文件

**运行方法：**
```bash
python analyze_qoder_data.py
```

### 4. `backup_qoder_data.ps1` (备份脚本)
- 自动备份整个 Qoder 用户数据目录
- 创建带时间戳的备份文件夹
- 验证备份完整性

**运行方法：**
```powershell
.\backup_qoder_data.ps1
# 或者指定自定义备份位置
.\backup_qoder_data.ps1 -BackupDestination "C:\MyBackups\qoder"
```

## 数据位置

根据分析，Qoder 在 Windows 11 上的数据存储在以下位置：

- **主数据目录**: `%APPDATA%\Qoder\User`
- **工作区数据**: `%APPDATA%\Qoder\User\workspaceStorage`
- **扩展数据**: `%APPDATA%\Qoder\User\globalStorage`
- **AI 聊天数据高概率位置**: 
  - `workspaceStorage/*/state.vscdb` (SQLite 数据库)
  - `globalStorage/aicoding*` (扩展存储)

## 使用场景

1. **数据导出**: 使用这些脚本来定位并提取 AI 聊天记录
2. **数据备份**: 定期备份 Qoder 用户数据防止丢失
3. **数据迁移**: 在不同设备间转移 Qoder 设置和数据
4. **数据分析**: 分析 Qoder 使用模式和数据结构

## 注意事项

- 运行脚本需要相应权限访问 `%APPDATA%` 目录
- Python 脚本需要安装 Python 3.x 环境
- 备份脚本会创建大量数据副本，请确保有足够的磁盘空间
- 建议在 Qoder 关闭状态下运行备份脚本以确保数据一致性

## 中文乱码问题解决方案

如果在运行脚本时遇到中文显示乱码问题，请参考 `CHINESE_ENCODING_FIX.md` 文件中的解决方案，我们提供了多种版本的脚本供您选择：

- `find_qoder_data.ps1` - 原版PowerShell脚本（含中文）
- `find_qoder_data_fixed.ps1` - 修复版PowerShell脚本（含中文，添加编码设置）
- `find_qoder_data_with_encoding_fix.ps1` - 带编码修复的中文脚本
- `find_qoder_data_english.ps1` - 英文版PowerShell脚本（推荐，避免乱码）
- `find_qoder_data_fixed.bat` - 修复版批处理脚本
- `SETUP_UTF8_PERMANENT.ps1` - PowerShell永久UTF-8编码配置脚本

对于乱码问题，推荐使用英文版脚本或参考 `CHINESE_ENCODING_FIX.md` 中的系统级设置方法。

## 聊天日志搜索功能

我们还提供了专门用于搜索Qoder聊天日志的工具：

- `search_chat_logs_basic.ps1` - PowerShell基础版聊天日志搜索脚本
- `search_chat_logs_python.py` - Python版聊天日志搜索脚本
- `search_chat_logs.sh` - Bash版聊天日志搜索脚本（适用于Git Bash）
- `detailed_search.sh` - 详细搜索脚本
- `quick_chat_search.sh` - 快速搜索脚本（限制结果长度）
- `chat_data_summary.sh` - 数据摘要报告脚本
- `CHAT_LOG_SEARCH_RESULTS.md` - 搜索结果总结报告

使用bash脚本可以绕过PowerShell的编码问题，推荐使用 `./quick_chat_search.sh` 进行快速搜索。

## Web历史记录查看器

我们还创建了一个Web服务来可视化查看和搜索Qoder历史记录：

- `web_service/` - Web应用主目录
  - `app.py` - Flask主应用
  - `start_server.py` - Python启动脚本
  - `start.bat` - Windows批处理启动脚本
  - `start.ps1` - PowerShell启动脚本
  - `requirements.txt` - 依赖列表
  - `templates/` - HTML模板
  - `static/` - 静态资源 (CSS, JS)

### 启动Web服务

**Windows 用户:**
1. 确保已安装Python 3.6+
2. 安装Flask: `pip install Flask`
3. 运行 `python web_service/start_server.py` 或双击 `web_service/start.bat`

**Git Bash 用户:**
1. 确保已安装Python 3.6+
2. 安装Flask: `pip install Flask`
3. 在Git Bash中运行 `bash web_service/start_git_bash.sh`

**通用 Bash 用户:**
1. 确保已安装Python 3.6+
2. 安装Flask: `pip install Flask`
3. 运行 `bash web_service/start.sh`

4. 在浏览器中访问 `http://127.0.0.1:5000`

### Web服务功能

- 查看聊天会话和编辑会话
- 浏览历史文件
- 搜索功能
- 统计信息展示
- 消息发送窗口（预留功能）