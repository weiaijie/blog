#!/bin/bash

# Qoder 历史记录查看器启动脚本 (Git Bash版)

echo ""
echo "=================================="
echo "Qoder 历史记录查看器 启动脚本 (Git Bash)"
echo "=================================="
echo ""

# 设置UTF-8编码
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=C.UTF-8

# 检查Python是否已安装
echo "检查Python环境..."

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✓ 检测到Python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "✓ 检测到Python"
else
    # 在Windows环境下，有时需要使用py命令
    if command -v py &> /dev/null; then
        PYTHON_CMD="py -3"
        echo "✓ 检测到Python (py -3)"
    else
        echo "错误: 未找到Python环境"
        echo "请先安装Python 3.6或更高版本"
        echo "下载地址: https://www.python.org/downloads/"
        echo ""
        read -n1 -r -p "按任意键退出..."
        exit 1
    fi
fi

# 检查pip是否可用
if command -v pip &> /dev/null || command -v pip3 &> /dev/null || command -v py &> /dev/null; then
    echo "✓ 检测到包管理器"
    
    # 安装依赖
    echo ""
    echo "正在安装依赖..."
    
    if [ "$PYTHON_CMD" = "py -3" ]; then
        PIP_CMD="py -3 -m pip"
    elif [ "$PYTHON_CMD" = "python3" ]; then
        PIP_CMD="pip3"
    else
        PIP_CMD="pip"
    fi
    
    if $PIP_CMD install -r requirements.txt; then
        echo "✓ 依赖安装完成"
    else
        echo "⚠ 警告: 依赖安装可能失败，尝试直接启动"
    fi
else
    echo "⚠ 警告: 未找到pip，跳过依赖安装"
fi

# 启动应用
echo ""
echo "正在启动Qoder历史记录查看器..."
echo "请在浏览器中访问: http://127.0.0.1:5000"
echo "按 Ctrl+C 停止服务器"
echo ""

# 进入脚本所在目录
cd "$(dirname "$0")"

# 启动Flask应用
if [ "$PYTHON_CMD" = "py -3" ]; then
    $PYTHON_CMD -m flask run --app app --host=127.0.0.1 --port=5000
else
    $PYTHON_CMD app.py
fi

echo ""
echo "服务器已停止"
read -n1 -r -p "按任意键退出..."