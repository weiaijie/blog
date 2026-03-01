#!/bin/bash

# Qoder 聊天日志搜索脚本
echo "��� 开始搜索 Qoder 聊天日志..."

# 获取 Windows 用户目录
WIN_USER_DIR=$(cmd.exe /c "echo %USERPROFILE%" 2>/dev/null | tr -d "\r")
APPDATA_DIR=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d "\r")

# 构建 Qoder 数据路径
QODER_PATH="$APPDATA_DIR/Qoder/User"

if [ -d "$QODER_PATH" ]; then
    echo "✅ 找到 Qoder 数据目录: $QODER_PATH"
    
    # 检查 workspaceStorage
    WORKSPACE_PATH="$QODER_PATH/workspaceStorage"
    if [ -d "$WORKSPACE_PATH" ]; then
        echo ""
        echo "�� 搜索 workspaceStorage 中的数据库文件..."
        DB_FILES=$(find "$WORKSPACE_PATH" -name "state.vscdb" 2>/dev/null | wc -l)
        echo "��� 找到 $DB_FILES 个 state.vscdb 数据库文件"
        
        # 列出数据库文件
        find "$WORKSPACE_PATH" -name "state.vscdb" 2>/dev/null | while read -r db_file; do
            dir_name=$(basename "$(dirname "$db_file")")
            echo "   数据库位置: $dir_name/$(basename "$db_file")"
        done
    fi
    
    # 检查 globalStorage
    GLOBAL_PATH="$QODER_PATH/globalStorage"
    if [ -d "$GLOBAL_PATH" ]; then
        echo ""
        echo "��� 搜索 globalStorage 中的扩展数据..."
        EXT_DIRS=$(ls -la "$GLOBAL_PATH" 2>/dev/null | grep "^d" | wc -l)
        echo "��� 找到 $EXT_DIRS 个全局存储扩展"
        
        # 检查 AI 相关扩展目录
        for dir in "$GLOBAL_PATH"/*/; do
            if [ -d "$dir" ]; then
                dir_name=$(basename "$dir")
                if [[ $dir_name =~ aicoding|chat|ai|code ]]; then
                    echo "   ��� 找到 AI 相关扩展目录: $dir_name"
                    
                    # 搜索 JSON 文件
                    json_files=$(find "$dir" -name "*.json" 2>/dev/null | wc -l)
                    if [ "$json_files" -gt 0 ]; then
                        echo "      ��� 找到 $json_files 个 JSON 文件"
                        find "$dir" -name "*.json" 2>/dev/null | head -n 5 | while read -r file; do
                            size=$(stat -c%s "$file" 2>/dev/null)
                            kb_size=$(echo "scale=2; $size/1024" | bc 2>/dev/null)
                            echo "         - $(basename "$file") (${kb_size}KB)"
                        done
                    fi
                    
                    # 搜索文本文件
                    txt_files=$(find "$dir" -name "*.txt" 2>/dev/null | wc -l)
                    if [ "$txt_files" -gt 0 ]; then
                        echo "      ��� 找到 $txt_files 个文本文件"
                    fi
                fi
            fi
        done
    fi
    
    # 检查 History 目录
    HISTORY_PATH="$QODER_PATH/History"
    if [ -d "$HISTORY_PATH" ]; then
        echo ""
        echo "��� 搜索 History 目录..."
        hist_files=$(ls -la "$HISTORY_PATH" 2>/dev/null | grep "^-" | wc -l)
        echo "��� 找到 History 目录，包含 $hist_files 个文件"
        
        ls -lah "$HISTORY_PATH" 2>/dev/null | grep "^-" | while read -r perms links owner group size date time filename; do
            if [ -n "$filename" ]; then
                echo "   - $filename ($size)"
            fi
        done
    fi
    
    echo ""
    echo "��� 搜索完成！"
    echo "��� 聊天日志可能位于以下位置："
    echo "   1. workspaceStorage/*/*/state.vscdb (SQLite数据库)"
    echo "   2. globalStorage/aicoding* 相关目录中的 JSON 文件"
    echo "   3. History 目录中的历史记录文件"
else
    echo "❌ 未找到 Qoder 数据目录"
fi

echo ""
echo "��� 脚本执行完成"

