#!/bin/bash

# Qoder 聊天数据搜索脚本 - 专注于聊天相关文件
echo "��� 深度搜索 Qoder 聊天数据..."

# 获取 Windows AppData 目录
APPDATA_DIR=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d "\r")

# 构建 Qoder 数据路径
QODER_PATH="$APPDATA_DIR/Qoder/User"

if [ -d "$QODER_PATH" ]; then
    echo "✅ 找到 Qoder 数据目录: $QODER_PATH"
    
    # 搜索聊天相关的特定目录和文件
    echo ""
    echo "��� 搜索聊天相关目录和文件..."
    
    # 查找所有包含 "chat" 的目录
    echo "��� 发现的聊天相关目录:"
    find "$QODER_PATH" -type d -name "*chat*" 2>/dev/null | while read -r dir; do
        dir_name=$(basename "$dir")
        parent_dir=$(basename "$(dirname "$dir")")
        echo "   • $parent_dir/$dir_name"
    done
    
    echo ""
    # 查找所有包含 "chat" 的文件
    echo "��� 发现的聊天相关文件:"
    find "$QODER_PATH" -type f -name "*chat*" 2>/dev/null | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null)
        kb_size=$(printf "%.2f" $(echo "$size/1024" | bc -l 2>/dev/null))
        rel_path=${file#$QODER_PATH/}
        echo "   • $rel_path (${kb_size}KB)"
    done
    
    echo ""
    # 查找 JSON 文件（通常存储聊天记录）
    echo "��� 发现的 JSON 文件 (可能包含聊天记录):"
    find "$QODER_PATH" -type f -name "*.json" 2>/dev/null | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null)
        # 只显示大于0字节的文件
        if [ "$size" -gt 0 ]; then
            kb_size=$(printf "%.2f" $(echo "$size/1024" | bc -l 2>/dev/null))
            rel_path=${file#$QODER_PATH/}
            echo "   • $rel_path (${kb_size}KB)"
        fi
    done
    
    echo ""
    # 搜索包含聊天关键词的文件内容
    echo "��� 搜索包含聊天内容的文件:"
    find "$QODER_PATH" -type f -exec grep -l -i "chat\\|message\\|role\\|content\\|prompt\\|response" {} \; 2>/dev/null | while read -r file; do
        size=$(stat -c%s "$file" 2>/dev/null)
        kb_size=$(printf "%.2f" $(echo "$size/1024" | bc -l 2>/dev/null))
        rel_path=${file#$QODER_PATH/}
        echo "   • $rel_path (${kb_size}KB)"
    done
    
    echo ""
    echo "��� 最重要的发现:"
    # 特别关注 chatSessions 和 chatEditingSessions 目录
    if [ -d "$QODER_PATH/workspaceStorage" ]; then
        echo "   在 workspaceStorage 中发现:"
        find "$QODER_PATH/workspaceStorage" -type d -name "*chat*" 2>/dev/null | while read -r dir; do
            file_count=$(find "$dir" -type f | wc -l)
            echo "     ��� $(basename "$dir"): $file_count 个文件"
            
            # 列出目录中最大的几个文件
            find "$dir" -type f -size +1K | sort -k5 -n | tail -5 | while read -r file; do
                size=$(stat -c%s "$file" 2>/dev/null)
                kb_size=$(printf "%.2f" $(echo "$size/1024" | bc -l 2>/dev/null))
                echo "       - $(basename "$file") (${kb_size}KB)"
            done
        done
    fi
    
    echo ""
    echo "��� 聊天数据位置总结:"
    echo "   1. $QODER_PATH/workspaceStorage/*/chatSessions/ - 聊天会话"
    echo "   2. $QODER_PATH/workspaceStorage/*/chatEditingSessions/ - 聊天编辑会话"
    echo "   3. $QODER_PATH/workspaceStorage/*/state.vscdb - SQLite数据库(需要SQLite工具查看)"
    echo "   4. $QODER_PATH/globalStorage/aicoding*/ - AI编码扩展数据(如果存在)"
else
    echo "❌ 未找到 Qoder 数据目录"
fi

echo ""
echo "��� 搜索完成!"

