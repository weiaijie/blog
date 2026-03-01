# Qoder Web历史记录查看器 - Bash启动指南

## 为什么使用Bash启动？

如果您遇到CMD终端乱码或访问问题，使用Bash（特别是Git Bash）可以解决这些问题：

1. 更好的字符编码支持
2. 更稳定的终端环境
3. 更好的跨平台兼容性

## 启动方式

### Git Bash（推荐）

如果您安装了Git for Windows，通常会自带Git Bash：

1. 右键点击项目文件夹，选择 "Git Bash Here"
2. 或者单独启动Git Bash程序
3. 运行以下命令：

```bash
cd /c/Users/saber/Desktop/work/blog/qoder/web_service
bash start_git_bash.sh
```

### 通用Bash

如果您使用的是WSL、Cygwin或其他Bash环境：

```bash
cd /c/Users/saber/Desktop/work/blog/qoder/web_service
bash start.sh
```

## 解决常见问题

### 如果遇到权限问题

在Linux/Mac或Git Bash中，您可能需要给脚本添加执行权限：

```bash
chmod +x start_git_bash.sh
chmod +x start.sh
```

### Python路径问题

如果脚本无法找到Python，可能是由于PATH设置问题。start_git_bash.sh脚本会尝试多种方式找到Python：

1. `python3`
2. `python`
3. `py -3` (Windows)

### 端口被占用

如果看到"端口已被占用"的错误，可以：

1. 查找占用端口的进程并结束它
2. 或者修改app.py中的端口号

## 脚本特性

### start_git_bash.sh 特性

- 自动检测Python环境（支持python3, python, py -3）
- 自动设置UTF-8编码避免乱码
- 自动安装依赖包
- 兼容Windows和Unix路径

### 编码处理

脚本设置了以下环境变量来处理编码问题：

```bash
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=C.UTF-8
```

## 访问Web界面

启动成功后，在浏览器中访问：

```
http://127.0.0.1:5000
```

## 停止服务

在Bash终端中按 `Ctrl+C` 停止服务。

## 故障排除

### 1. 如果找不到python命令

确保Python已正确安装并添加到PATH：

```bash
python --version
```

### 2. 如果遇到编码错误

确保在Git Bash中运行，而不是Windows CMD。

### 3. 如果依赖安装失败

尝试手动安装Flask：

```bash
pip install Flask
```

### 4. 如果无法访问网页

- 检查防火墙设置
- 确保没有其他程序占用了5000端口
- 确认服务已成功启动

## 优势

相比Windows CMD，使用Bash启动有以下优势：

- 更好的Unicode字符支持
- 更一致的路径处理
- 更丰富的shell功能
- 更好的错误信息显示
- 更稳定的运行环境