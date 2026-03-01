#!/bin/bash

# Qoder 聊天数据搜索脚本 - 简化版，限制结果长度
echo "��� Qoder 聊天数据搜索 (简化版)"

# 获取路径
APPDATA_DIR=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d "\r")
QODER_PATH="$APPDATA_DIR/Qoder/User"

if [ -d "$QODER_PATH" ]; then
    echo "✅ 找到 Qoder 数据目录"
    
    # 搜索聊天相关目录 (限制显示前10个)
    echo "��� 聊天相关目录 (前10个):"
    find "$QODER_PATH" -type d -name "*chat*" 2>/dev/null | head -10 | while read -r dir; do
        rel_path=${dir#$QODER_PATH/}
        echo "   • $rel_path"
    done
    
    # 搜索 JSON 文件 (限制显示前15个)
    echo ""
    echo "��� JSON 文件 (前15个，可能包含聊天记录):"
    find "$QODER_PATH" -type f -name "*.json" -size +100c 2>/dev/null | head -15 | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null)
        kb_size=$(printf "%.1f" $(echo "$size/1024" | bc -l 2>/dev/null))
        rel_path=${file#$QODER_PATH/}
        echo "   • $rel_path (${kb_size}KB)"
    done
    
    # 搜索包含聊天关键词的文件 (限制显示前10个)
    echo ""
    echo "��� 包含聊天内容的文件 (前10个):"
    find "$QODER_PATH" -type f -exec grep -l -i "chat\\|message\\|role\\|content" {} \; 2>/dev/null | head -10 | while read -r file; do
        rel_path=${file#$QODER_PATH/}
        echo "   • $rel_path"
    done
    
    echo ""
    echo "�� 核心发现:"
    echo "   1. 聊天会话: workspaceStorage/*/chatSessions/"
    echo "   2. 聊天编辑: workspaceStorage/*/chatEditingSessions/"
    echo "   3. 数据库: workspaceStorage/*/state.vscdb"
    echo ""
    echo "��� 完整路径: $QODER_PATH"
else
    echo "❌ 未找到 Qoder 数据目录"
fi

echo "��� 搜索完成"

