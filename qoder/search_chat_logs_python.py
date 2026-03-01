import os
import sqlite3
import json
from pathlib import Path
import re

def search_qoder_chat_logs():
    """搜索Qoder中的聊天日志"""
    print("🔍 开始搜索 Qoder 聊天日志...")
    
    # 获取Qoder数据目录
    appdata_path = Path(os.environ.get('APPDATA', ''))
    qoder_path = appdata_path / 'Qoder' / 'User'
    
    if not qoder_path.exists():
        print("❌ 未找到 Qoder 数据目录")
        return
    
    print(f"✅ 找到 Qoder 数据目录: {qoder_path}")
    
    # 搜索 workspaceStorage 中的数据库文件
    print("\n🔍 搜索 workspaceStorage 中的数据库文件...")
    workspace_path = qoder_path / 'workspaceStorage'
    
    if workspace_path.exists():
        # 查找所有 state.vscdb 文件
        state_files = list(workspace_path.rglob('state.vscdb'))
        print(f"📁 找到 {len(state_files)} 个 state.vscdb 数据库文件")
        
        # 尝试读取数据库内容
        for db_file in state_files:
            print(f"   检查数据库: {db_file.parent.name}/{db_file.name}")
            search_database_content(db_file)
    
    # 搜索 globalStorage 中的扩展数据
    print("\n🔍 搜索 globalStorage 中的扩展数据...")
    global_path = qoder_path / 'globalStorage'
    
    if global_path.exists():
        global_dirs = [d for d in global_path.iterdir() if d.is_dir()]
        print(f"📦 找到 {len(global_dirs)} 个全局存储扩展")
        
        for ext_dir in global_dirs:
            # 检查是否是 AI 相关扩展
            if any(keyword in ext_dir.name.lower() for keyword in ['aicoding', 'chat', 'ai', 'code']):
                print(f"   🤖 找到 AI 相关扩展目录: {ext_dir.name}")
                
                # 搜索可能包含聊天记录的文件
                search_extension_files(ext_dir)
    
    # 搜索 History 目录
    print("\n🔍 搜索 History 目录...")
    history_path = qoder_path / 'History'
    
    if history_path.exists():
        history_files = [f for f in history_path.iterdir() if f.is_file()]
        print(f"📅 找到 History 目录，包含 {len(history_files)} 个文件")
        for hist_file in history_files:
            print(f"   - {hist_file.name} ({hist_file.stat().st_size} bytes)")

def search_database_content(db_path):
    """搜索数据库中的聊天相关内容"""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table_name, in tables:
            # 检查表名是否与聊天相关
            if any(keyword in table_name.lower() for keyword in ['chat', 'message', 'conversation', 'session', 'aicoding']):
                print(f"      🗣️  发现可能的聊天相关表: {table_name}")
                
                # 获取表中的记录数
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]
                print(f"         记录数: {count}")
                
                # 尝试获取一些示例行
                if count > 0:
                    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                    rows = cursor.fetchall()
                    for i, row in enumerate(rows):
                        print(f"         示例 {i+1}: {str(row)[:100]}...")
                        
        # 即使表名不明显，也要检查列名和内容是否包含聊天关键词
        for table_name, in tables:
            try:
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                
                # 检查列名是否包含聊天相关关键词
                col_names = [col[1] for col in columns]
                if any(any(keyword in col_name.lower() for keyword in ['chat', 'message', 'role', 'content', 'prompt', 'response']) for col_name in col_names):
                    print(f"      🗣️  发现可能的聊天相关表 (通过列名): {table_name}")
                    print(f"         列名: {col_names}")
                    
                    # 获取表中的记录数
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    print(f"         记录数: {count}")
                    
            except sqlite3.Error:
                pass  # 如果无法查询表信息，则跳过
                
    except sqlite3.Error as e:
        print(f"      ⚠️  无法访问数据库: {e}")
    except Exception as e:
        print(f"      ⚠️  读取数据库时出错: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def search_extension_files(ext_dir):
    """搜索扩展目录中的聊天相关文件"""
    # 搜索 JSON、TXT 和其他可能包含数据的文件
    data_extensions = ['.json', '.txt', '.log', '.db', '.sqlite']
    
    for ext in data_extensions:
        files = list(ext_dir.rglob(f'*{ext}'))
        if files:
            print(f"      找到 {len(files)} 个 {ext.upper()} 文件:")
            for file_path in files[:10]:  # 只显示前10个
                size = file_path.stat().st_size
                print(f"         - {file_path.name} ({size} bytes)")
                
                # 尝试读取文件内容以查找聊天相关数据
                if ext == '.json':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 检查是否包含聊天相关关键词
                            if any(keyword in content.lower() for keyword in ['chat', 'message', 'role', 'content', 'prompt', 'response']):
                                print(f"            🗣️  包含聊天相关数据")
                    except Exception:
                        pass
                elif ext in ['.txt', '.log']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(1000)  # 读取前1000个字符
                            # 检查是否包含聊天相关关键词
                            if any(keyword in content.lower() for keyword in ['chat', 'message', 'role', 'content', 'prompt', 'response']):
                                print(f"            🗣️  包含聊天相关数据")
                    except Exception:
                        pass

def main():
    print("=" * 60)
    print("🤖 Qoder 聊天日志搜索工具")
    print("=" * 60)
    
    search_qoder_chat_logs()
    
    print("\n💡 搜索完成！")
    print("📋 聊天日志可能位于以下位置：")
    print("   1. workspaceStorage/*/*/state.vscdb (SQLite数据库)")
    print("   2. globalStorage/aicoding* 相关目录中的 JSON 文件")
    print("   3. History 目录中的历史记录文件")
    print("=" * 60)

if __name__ == "__main__":
    main()