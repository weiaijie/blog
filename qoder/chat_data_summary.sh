#!/bin/bash

# Qoder 聊天数据摘要报告
echo "==========================================="
echo "��� Qoder 聊天数据位置摘要报告"
echo "==========================================="

APPDATA_DIR=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d "\r")
QODER_PATH="$APPDATA_DIR/Qoder/User"

if [ -d "$QODER_PATH" ]; then
    echo "✅ Qoder 数据目录: $QODER_PATH"
    echo ""
    
    # 统计聊天相关目录
    chat_dirs=$(find "$QODER_PATH" -type d -name "*chat*" 2>/dev/null | wc -l)
    echo "��� 发现 $chat_dirs 个聊天相关目录"
    
    # 统计聊天相关文件
    chat_json_files=$(find "$QODER_PATH" -name "*chat*.json" 2>/dev/null | wc -l)
    echo "��� 发现 $chat_json_files 个聊天相关的JSON文件"
    
    # 统计state.vscdb文件
    db_files=$(find "$QODER_PATH" -name "state.vscdb" 2>/dev/null | wc -l)
    echo "���️ 发现 $db_files 个数据库文件(state.vscdb)"
    
    # 统计history目录中的文件
    history_files=$(find "$QODER_PATH/History" -type f 2>/dev/null | wc -l)
    echo "��� 发现 $history_files 个历史记录文件"
    
    echo ""
    echo "��� 重要发现:"
    echo "------------------------"
    
    # 显示聊天会话目录
    echo "��� 聊天会话目录:"
    find "$QODER_PATH/workspaceStorage" -type d -name "*chatSessions*" 2>/dev/null | while read -r dir; do
        session_count=$(find "$dir" -type f -name "*.json" | wc -l)
        echo "   • $(basename "$dir") - $session_count 个会话文件"
    done
    
    echo ""
    # 显示聊天编辑会话目录
    echo "✍️ 聊天编辑会话目录:"
    find "$QODER_PATH/workspaceStorage" -type d -name "*chatEditingSessions*" 2>/dev/null | while read -r dir; do
        session_count=$(find "$dir" -maxdepth 1 -mindepth 1 -type d | wc -l)
        echo "   • $(basename "$dir") - $session_count 个编辑会话"
    done
    
    echo ""
    echo "��� 数据导出建议:"
    echo "------------------------"
    echo "1. 聊天记录主要位置:"
    echo "   - $QODER_PATH/workspaceStorage/*/chatSessions/"
    echo "   - $QODER_PATH/workspaceStorage/*/chatEditingSessions/"
    echo ""
    echo "2. 数据库文件 (需要SQLite工具查看):"
    echo "   - $QODER_PATH/workspaceStorage/*/state.vscdb"
    echo ""
    echo "3. 历史记录:"
    echo "   - $QODER_PATH/History/"
    echo ""
    echo "4. 导出方法:"
    echo "   a) 复制整个目录: $(dirname "$QODER_PATH")/Qoder/"
    echo "   b) 或只复制关键目录: workspaceStorage, History"
    echo "   c) 使用SQLite工具打开 .vscdb 文件查看具体内容"
    echo ""
    echo "��� 提示: 聊天内容很可能存储在 chatSessions 和 chatEditingSessions 目录中"
    echo "   的 JSON 文件或 state.vscdb 数据库中"
else
    echo "❌ 未找到 Qoder 数据目录"
fi

echo ""
echo "��� 报告生成完成"
echo "==========================================="

