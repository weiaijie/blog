#!/bin/bash

# Qoder 聊天日志详细搜索脚本
echo "��� 详细搜索 Qoder 聊天日志..."

# 获取 Windows AppData 目录
APPDATA_DIR=$(cmd.exe /c "echo %APPDATA%" 2>/dev/null | tr -d "\r")

# 构建 Qoder 数据路径
QODER_PATH="$APPDATA_DIR/Qoder/User"

if [ -d "$QODER_PATH" ]; then
    echo "✅ 找到 Qoder 数据目录: $QODER_PATH"
    
    # 检查 workspaceStorage
    WORKSPACE_PATH="$QODER_PATH/workspaceStorage"
    if [ -d "$WORKSPACE_PATH" ]; then
        echo ""
        echo "��� 检查 workspaceStorage 中的数据库文件..."
        
        # 查找所有的 state.vscdb 文件并检查内容
        find "$WORKSPACE_PATH" -name "state.vscdb" 2>/dev/null | while read -r db_file; do
            dir_name=$(basename "$(dirname "$db_file")")
            echo "   检查数据库: $dir_name/$(basename "$db_file")"
            
            # 如果系统有 sqlite3，尝试查看表结构
            if command -v sqlite3 >/dev/null 2>&1; then
                table_count=$(sqlite3 "$db_file" "SELECT count(name) FROM sqlite_master WHERE type=\"table\";" 2>/dev/null)
                if [ $? -eq 0 ] && [ "$table_count" -gt 0 ]; then
                    echo "      数据库包含 $table_count 个表"
                    
                    # 获取表名并检查是否有与聊天相关的表
                    sqlite3 "$db_file" "SELECT name FROM sqlite_master WHERE type=\"table\";" 2>/dev/null | while read -r table_name; do
                        if [[ $table_name =~ chat|message|conversation|session|aicoding|ai ]]; then
                            record_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM \"$table_name\";" 2>/dev/null)
                            echo "         ���️ 发现聊天相关表: $table_name (包含 $record_count 条记录)"
                        fi
                    done
                fi
            else
                size=$(stat -c%s "$db_file" 2>/dev/null)
                kb_size=$(echo "scale=2; $size/1024" | bc 2>/dev/null)
                echo "      大小: ${kb_size}KB (需要安装 sqlite3 工具来查看内容)"
            fi
        done
    fi
    
    # 检查 globalStorage
    GLOBAL_PATH="$QODER_PATH/globalStorage"
    if [ -d "$GLOBAL_PATH" ]; then
        echo ""
        echo "��� 检查 globalStorage 中的扩展数据..."
        ls -la "$GLOBAL_PATH" 2>/dev/null | grep "^d" | awk "{print \$9}" | while read -r dir_name; do
            dir_path="$GLOBAL_PATH/$dir_name"
            if [ -d "$dir_path" ]; then
                # 检查是否是 AI 相关扩展
                if [[ $dir_name =~ aicoding|chat|ai|code ]]; then
                    echo "   ��� AI 相关扩展: $dir_name"
                    
                    # 搜索可能包含聊天记录的文件
                    json_files=$(find "$dir_path" -name "*.json" -type f 2>/dev/null | wc -l)
                    if [ "$json_files" -gt 0 ]; then
                        echo "      ��� 找到 $json_files 个 JSON 文件"
                        find "$dir_path" -name "*.json" -type f 2>/dev/null | head -n 3 | while read -r json_file; do
                            size=$(stat -c%s "$json_file" 2>/dev/null)
                            kb_size=$(echo "scale=2; $size/1024" | bc 2>/dev/null)
                            echo "         - $(basename "$json_file") (${kb_size}KB)"
                            
                            # 检查 JSON 文件内容是否包含聊天相关关键词
                            if grep -i -E "chat|message|role|content|prompt|response" "$json_file" 2>/dev/null | head -n 1; then
                                echo "            包含聊天数据"
                            fi
                        done
                    fi
                    
                    txt_files=$(find "$dir_path" -name "*.txt" -type f 2>/dev/null | wc -l)
                    if [ "$txt_files" -gt 0 ]; then
                        echo "      ��� 找到 $txt_files 个文本文件"
                    fi
                else
                    echo "   ��� 扩展: $dir_name"
                fi
            fi
        done
    fi
    
    echo ""
    echo "��� 总结:"
    echo "   - 聊天记录最有可能存储在 state.vscdb 数据库文件中"
    echo "   - 需要使用 SQLite 工具来查看数据库内容"
    echo "   - 如果安装了 sqlite3，可以使用以下命令查看数据:"
    echo "     sqlite3 \"path/to/state.vscdb\""
    echo "     .tables  # 查看所有表"
    echo "     SELECT * FROM table_name LIMIT 5;  # 查看表内容"
else
    echo "❌ 未找到 Qoder 数据目录"
fi

echo ""
echo "��� 详细搜索完成"

