import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

def find_qoder_data():
    """查找Qoder数据目录"""
    # Windows标准路径
    appdata_path = Path(os.environ.get('APPDATA', ''))
    qoder_path = appdata_path / 'Qoder' / 'User'
    
    print("🔍 开始查找 Qoder 本地数据...")
    print(f"📁 检查路径: {qoder_path}")
    
    if qoder_path.exists():
        print("✅ 找到 Qoder 用户数据目录")
        return qoder_path
    else:
        print("❌ 未找到 Qoder 用户数据目录")
        return None

def analyze_workspace_storage(qoder_path):
    """分析 workspaceStorage 目录"""
    workspace_path = qoder_path / 'workspaceStorage'
    
    if workspace_path.exists():
        print(f"\n📂 分析 workspaceStorage...")
        print(f"   路径: {workspace_path}")
        
        # 统计工作区数量
        workspace_dirs = [d for d in workspace_path.iterdir() if d.is_dir()]
        print(f"   工作区数量: {len(workspace_dirs)}")
        
        # 查找 state.vscdb 文件
        state_files = list(workspace_path.rglob('state.vscdb'))
        print(f"   state.vscdb 文件数量: {len(state_files)}")
        
        # 尝试读取数据库中的键值
        for state_file in state_files[:3]:  # 只检查前3个，避免过多输出
            analyze_state_db(state_file)
    else:
        print("\n📂 workspaceStorage 不存在")

def analyze_global_storage(qoder_path):
    """分析 globalStorage 目录"""
    global_path = qoder_path / 'globalStorage'
    
    if global_path.exists():
        print(f"\n🌐 分析 globalStorage...")
        print(f"   路径: {global_path}")
        
        # 统计扩展数量
        global_dirs = [d for d in global_path.iterdir() if d.is_dir()]
        print(f"   扩展数量: {len(global_dirs)}")
        
        # 查找 aicoding 相关目录
        aicoding_dirs = [d for d in global_dirs if 'aicoding' in d.name.lower()]
        if aicoding_dirs:
            print(f"   aicoding 相关扩展: {len(aicoding_dirs)} 个")
            for aicoding_dir in aicoding_dirs:
                print(f"     - {aicoding_dir.name}")
                
                # 查找 JSON 或其他可能包含聊天数据的文件
                find_chat_data_files(aicoding_dir)
    else:
        print("\n🌐 globalStorage 不存在")

def analyze_state_db(db_path):
    """分析 SQLite 数据库文件"""
    print(f"   \n      分析数据库: {db_path.name}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"      表数量: {len(tables)}")
            
            for table_name, in tables:
                print(f"         表名: {table_name}")
                
                # 获取该表的行数
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                print(f"            行数: {row_count}")
                
                # 如果是 StorageTable，尝试找出可能包含聊天数据的键
                if table_name.lower() == 'storagetable':
                    cursor.execute("SELECT key FROM StorageTable")
                    keys = cursor.fetchall()
                    
                    # 过滤出可能包含聊天数据的键
                    chat_keys = [key[0] for key in keys if any(term in key[0].lower() for term in ['chat', 'aicoding', 'session', 'message'])]
                    
                    if chat_keys:
                        print(f"            可能的聊天相关键: {len(chat_keys)} 个")
                        for key in chat_keys[:5]:  # 只显示前5个
                            print(f"               - {key}")
                            
                            # 尝试获取键对应的值的信息
                            cursor.execute("SELECT value FROM StorageTable WHERE key = ?", (key,))
                            value = cursor.fetchone()
                            if value and value[0]:
                                val_str = str(value[0])
                                print(f"                  值长度: {len(val_str)} 字符")
                                
                                # 尝试解析JSON
                                if val_str.startswith('{') or val_str.startswith('['):
                                    try:
                                        parsed = json.loads(value[0])
                                        if isinstance(parsed, dict) and 'messages' in str(parsed).lower():
                                            print(f"                  ⭐ 包含消息数据!")
                                    except json.JSONDecodeError:
                                        pass
                
    except sqlite3.Error as e:
        print(f"      数据库错误: {e}")
    except Exception as e:
        print(f"      错误: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def find_chat_data_files(directory):
    """在指定目录中查找可能包含聊天数据的文件"""
    print(f"      在 {directory.name} 中查找聊天数据文件...")
    
    # 查找 JSON、TXT 和其他可能包含数据的文件
    data_extensions = ['.json', '.txt', '.log', '.db']
    data_files = []
    
    for ext in data_extensions:
        data_files.extend(directory.rglob(f'*{ext}'))
    
    if data_files:
        print(f"         找到 {len(data_files)} 个数据文件:")
        for file_path in data_files[:10]:  # 只显示前10个
            size = file_path.stat().st_size
            print(f"            - {file_path.name} ({size} 字节)")
    else:
        print(f"         未找到常见数据格式文件")

def calculate_directory_size(path):
    """计算目录大小"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                pass  # 忽略无法访问的文件
    return total_size

def main():
    print("=" * 60)
    print("🤖 Qoder 数据分析工具")
    print("=" * 60)
    
    # 查找 Qoder 数据目录
    qoder_path = find_qoder_data()
    
    if qoder_path:
        # 分析目录结构
        print(f"\n📊 目录结构分析:")
        
        # 计算总大小
        total_size = calculate_directory_size(qoder_path)
        size_mb = total_size / (1024 * 1024)
        print(f"   总大小: {size_mb:.2f} MB")
        
        # 列出主要子目录
        subdirs = [d for d in qoder_path.iterdir() if d.is_dir()]
        print(f"   子目录数量: {len(subdirs)}")
        for subdir in subdirs:
            print(f"      - {subdir.name}")
        
        # 分析 workspaceStorage
        analyze_workspace_storage(qoder_path)
        
        # 分析 globalStorage
        analyze_global_storage(qoder_path)
        
        print(f"\n🎯 分析完成! 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n❌ 无法找到 Qoder 数据，无法进行进一步分析。")
    
    print("=" * 60)

if __name__ == "__main__":
    main()