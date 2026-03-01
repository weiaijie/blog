# Qoder 聊天日志搜索工具使用指南

## 快速开始

### 在 Git Bash 中搜索聊天日志
```bash
cd /c/Users/saber/Desktop/work/blog/qoder
./quick_chat_search.sh
```

### 获取详细报告
```bash
./chat_data_summary.sh
```

## 数据位置

### 主要聊天数据目录
- `%APPDATA%\Qoder\User\workspaceStorage\*\chatSessions\` - 聊天会话
- `%APPDATA%\Qoder\User\workspaceStorage\*\chatEditingSessions\` - 聊天编辑会话
- `%APPDATA%\Qoder\User\workspaceStorage\*\state.vscdb` - SQLite数据库

## 导出聊天记录

### 方法1：使用批处理脚本导出
```batch
xcopy "%APPDATA%\Qoder\User" "C:\Qoder_Backup\User" /E /I /H
```

### 方法2：仅导出聊天相关数据
```batch
mkdir "C:\Qoder_Chat_Export"
xcopy "%APPDATA%\Qoder\User\workspaceStorage\*\chatSessions" "C:\Qoder_Chat_Export\chatSessions" /E /I /H
xcopy "%APPDATA%\Qoder\User\workspaceStorage\*\chatEditingSessions" "C:\Qoder_Chat_Export\chatEditingSessions" /E /I /H
xcopy "%APPDATA%\Qoder\User\History" "C:\Qoder_Chat_Export\History" /E /I /H
```

## 查看数据库内容

要查看 `state.vscdb` 数据库中的聊天内容，需要使用SQLite工具：

1. 下载 [DB Browser for SQLite](https://sqlitebrowser.org/)
2. 打开 `state.vscdb` 文件
3. 查看表结构和数据

或使用命令行：
```bash
sqlite3 path/to/state.vscdb
.tables  # 查看所有表
SELECT * FROM table_name LIMIT 5;  # 查看表内容
```

## 工具脚本说明

- `quick_chat_search.sh` - 快速搜索，限制结果长度，适合初步探索
- `chat_data_summary.sh` - 生成详细统计报告
- `detailed_search.sh` - 深度搜索，查找关键词
- `search_chat_logs.sh` - 基础搜索脚本

## 注意事项

1. 确保Qoder已关闭后再导出数据，以保证数据一致性
2. SQLite数据库文件可能被Qoder锁定，导出前请关闭应用程序
3. 聊天内容可能存储在JSON文件或SQLite数据库中
4. 每个工作区有独立的存储目录，需要全部导出以获得完整聊天记录