# Qoder Web历史记录查看器 - 快速启动指南

## 一步到位启动

### Windows用户（最快方式）
1. 双击 `qoder/web_service/start.bat` 文件
2. 等待服务启动
3. 打开浏览器访问 `http://127.0.0.1:5000`

### 如果双击无效
1. 打开命令提示符（cmd）或PowerShell
2. 进入项目目录：
   ```cmd
   cd c:\Users\saber\Desktop\work\blog\qoder\web_service
   ```
3. 启动服务：
   ```cmd
   python app.py
   ```

### Git Bash用户（推荐解决乱码问题）
1. 打开Git Bash
2. 进入项目目录：
   ```bash
   cd /c/Users/saber/Desktop/work/blog/qoder/web_service
   ```
3. 启动服务：
   ```bash
   bash start_git_bash.sh
   ```

### 如果没有Python
1. 先安装Python 3.6+（官网：python.org）
2. 确保安装时勾选"Add Python to PATH"
3. 重启命令提示符
4. 安装Flask：`pip install Flask`
5. 再次尝试启动

## 功能一览

- 📊 **聊天会话** - 查看所有对话记录
- 🔍 **搜索功能** - 在历史记录中查找内容
- 📁 **文件浏览** - 查看历史文件内容
- 📈 **统计信息** - 数据概览
- 💬 **消息发送** - 预留发送功能

## 界面导航

1. **左侧菜单** - 切换不同数据类型
2. **顶部搜索** - 全局搜索
3. **主内容区** - 显示当前数据
4. **底部面板** - 消息发送区

## 常见问题

**Q: 打开浏览器后显示空白页面？**
A: 检查服务是否成功启动，看命令行是否有错误信息

**Q: 搜索功能没有结果？**
A: 确认Qoder数据目录存在且有内容

**Q: 访问不了127.0.0.1:5000？**
A: 检查防火墙设置，或尝试刷新页面

## 停止服务

在命令提示符窗口中按 `Ctrl+C` 停止服务。

## 成功标志

- 命令行显示 "Running on http://127.0.0.1:5000"
- 浏览器打开后显示 "Qoder 历史记录查看器" 标题
- 左侧菜单显示 "聊天会话"、"编辑会话" 等选项

现在就可以开始使用Web界面查看Qoder的历史记录了！