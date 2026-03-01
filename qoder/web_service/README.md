# Qoder 历史记录查看器

一个用于查看和搜索 Qoder 历史记录的 Web 应用。

## 功能特性

- 📊 查看聊天会话记录
- ✏️ 查看编辑会话记录  
- 📁 查看历史文件
- 🔍 搜索功能
- 💬 消息发送窗口（预留功能）
- 📈 统计信息展示

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

或者直接安装 Flask：

```bash
pip install Flask
```

### 启动服务

**Windows (命令提示符):**
```cmd
python start_server.py
```

**Windows (Git Bash):**
```bash
bash start_git_bash.sh
```

**通用 Bash:**
```bash
bash start.sh
```

服务将在 `http://127.0.0.1:5000` 上运行

### 手动启动

```bash
cd web_service
python app.py
```

## 功能说明

### 1. 聊天会话
- 查看所有聊天会话记录
- 支持会话详情浏览

### 2. 编辑会话
- 查看聊天编辑会话记录
- 支持编辑会话详情浏览

### 3. 历史文件
- 浏览所有历史文件
- 查看文件内容

### 4. 搜索功能
- 在历史记录中搜索内容
- 高亮显示匹配项

### 5. 消息发送（预留）
- 预留消息发送窗口
- 可用于向 Qoder 发送消息

## 目录结构

```
web_service/
├── app.py              # 主应用文件
├── start_server.py     # 启动脚本
├── requirements.txt    # 依赖列表
├── templates/          # HTML 模板
│   └── index.html
├── static/             # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── README.md
```

## API 接口

- `GET /api/chat-sessions` - 获取聊天会话
- `GET /api/chat-editing-sessions` - 获取编辑会话
- `GET /api/history-files` - 获取历史文件
- `GET /api/search?q={query}` - 搜索内容
- `GET /api/file-content?path={filepath}` - 获取文件内容
- `POST /api/send-message` - 发送消息
- `GET /api/stats` - 获取统计信息

## 使用说明

1. 启动服务后，浏览器会自动打开主页
2. 使用左侧导航栏切换不同类型的记录
3. 在搜索框中输入关键词搜索内容
4. 点击项目查看详细信息
5. 使用底部消息面板发送消息（预留功能）

## 技术栈

- Python Flask - Web 框架
- HTML/CSS/JavaScript - 前端界面
- Font Awesome - 图标库
- AJAX - 异步请求

## 注意事项

- 需要 Python 3.6+ 环境
- 确保 Qoder 数据目录存在且有访问权限
- 搜索功能支持全文搜索
- 文件查看器支持代码高亮（待完善）