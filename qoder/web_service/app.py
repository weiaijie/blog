# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json
import sqlite3
from datetime import datetime
import glob
from pathlib import Path
import re
import sys
import locale

# 设置系统编码
if sys.platform.startswith('win'):
    # Windows平台设置控制台编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置locale为UTF-8
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass

app = Flask(__name__)

# 配置
APPDATA_PATH = os.path.expandvars('%APPDATA%')
QODER_PATH = os.path.join(APPDATA_PATH, 'Qoder', 'User')
WORKSPACE_PATH = os.path.join(QODER_PATH, 'workspaceStorage')
HISTORY_PATH = os.path.join(QODER_PATH, 'History')

class QoderDataService:
    def __init__(self):
        self.qoder_path = QODER_PATH
        self.workspace_path = WORKSPACE_PATH
        self.history_path = HISTORY_PATH
    
    def get_chat_sessions(self):
        """获取聊天会话数据"""
        sessions = []
        if os.path.exists(self.workspace_path):
            # 查找 chatSessions 目录
            chat_session_dirs = glob.glob(os.path.join(self.workspace_path, '*', 'chatSessions'))
            for session_dir in chat_session_dirs:
                if os.path.exists(session_dir):
                    json_files = glob.glob(os.path.join(session_dir, '*.json'))
                    for json_file in json_files:
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                sessions.append({
                                    'file': json_file,
                                    'data': data,
                                    'timestamp': os.path.getmtime(json_file)
                                })
                        except Exception as e:
                            print(f"Error reading {json_file}: {e}")
        return sessions
    
    def get_chat_editing_sessions(self):
        """获取聊天编辑会话数据"""
        editing_sessions = []
        if os.path.exists(self.workspace_path):
            # 查找 chatEditingSessions 目录
            editing_dirs = glob.glob(os.path.join(self.workspace_path, '*', 'chatEditingSessions'))
            for editing_dir in editing_dirs:
                if os.path.exists(editing_dir):
                    # 获取子目录（每个编辑会话）
                    session_dirs = [d for d in os.listdir(editing_dir) 
                                  if os.path.isdir(os.path.join(editing_dir, d))]
                    for session_dir in session_dirs:
                        session_path = os.path.join(editing_dir, session_dir)
                        state_file = os.path.join(session_path, 'state.json')
                        if os.path.exists(state_file):
                            try:
                                with open(state_file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    editing_sessions.append({
                                        'session_id': session_dir,
                                        'path': session_path,
                                        'data': data,
                                        'timestamp': os.path.getmtime(state_file)
                                    })
                            except Exception as e:
                                print(f"Error reading {state_file}: {e}")
        return editing_sessions
    
    def get_history_files(self, search_term=''):
        """获取历史文件"""
        files = []
        if os.path.exists(self.history_path):
            # 递归搜索所有文件
            for root, dirs, filenames in os.walk(self.history_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if search_term and search_term.lower() not in filename.lower():
                        continue
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        files.append({
                            'name': filename,
                            'path': file_path,
                            'size': file_size,
                            'modified': os.path.getmtime(file_path),
                            'relative_path': os.path.relpath(file_path, self.history_path)
                        })
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
        
        # 按修改时间排序
        files.sort(key=lambda x: x['modified'], reverse=True)
        return files
    
    def search_content(self, search_term):
        """在文件内容中搜索"""
        results = []
        if not search_term:
            return results
            
        # 搜索历史文件内容
        if os.path.exists(self.history_path):
            for root, dirs, filenames in os.walk(self.history_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if filename.endswith(('.php', '.json', '.txt', '.js', '.py', '.md')):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if search_term.lower() in content.lower():
                                    # 获取匹配行
                                    lines = content.split('\n')
                                    matching_lines = []
                                    for i, line in enumerate(lines):
                                        if search_term.lower() in line.lower():
                                            matching_lines.append({
                                                'line': i + 1,
                                                'content': line[:200]  # 限制显示长度
                                            })
                                            if len(matching_lines) >= 5:  # 限制匹配行数
                                                break
                                    
                                    results.append({
                                        'file': filename,
                                        'path': file_path,
                                        'matches': matching_lines,
                                        'total_matches': len([l for l in lines if search_term.lower() in l.lower()])
                                    })
                        except Exception as e:
                            print(f"Error searching {file_path}: {e}")
        
        return results

# 初始化服务
data_service = QoderDataService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat-sessions')
def get_chat_sessions():
    sessions = data_service.get_chat_sessions()
    return jsonify({
        'sessions': sessions,
        'count': len(sessions)
    })

@app.route('/api/chat-editing-sessions')
def get_chat_editing_sessions():
    sessions = data_service.get_chat_editing_sessions()
    return jsonify({
        'sessions': sessions,
        'count': len(sessions)
    })

@app.route('/api/history-files')
def get_history_files():
    search_term = request.args.get('search', '')
    files = data_service.get_history_files(search_term)
    return jsonify({
        'files': files,
        'count': len(files)
    })

@app.route('/api/search')
def search_content():
    search_term = request.args.get('q', '')
    results = data_service.search_content(search_term)
    return jsonify({
        'results': results,
        'count': len(results),
        'search_term': search_term
    })

@app.route('/api/file-content')
def get_file_content():
    file_path = request.args.get('path', '')
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return jsonify({
            'content': content,
            'file': os.path.basename(file_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get('message', '')
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # 这里可以实现实际的消息发送逻辑
    # 比如保存到数据库或调用Qoder API
    response = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'status': 'sent'
    }
    
    return jsonify(response)

@app.route('/api/stats')
def get_stats():
    """获取统计数据"""
    chat_sessions = data_service.get_chat_sessions()
    editing_sessions = data_service.get_chat_editing_sessions()
    history_files = data_service.get_history_files()
    
    stats = {
        'chat_sessions_count': len(chat_sessions),
        'editing_sessions_count': len(editing_sessions),
        'history_files_count': len(history_files),
        'total_size': sum(f['size'] for f in history_files)
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)