@echo off
echo.
echo ================================
echo Qoder 历史记录查看器 启动脚本
echo ================================
echo.

REM 检查是否安装了Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.6或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    goto :check_py
) else (
    goto :install_and_run
)

:check_py
REM 尝试使用py命令（Windows推荐方式）
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python和py命令
    echo 请先安装Python 3.6或更高版本
    echo.
    pause
    exit /b 1
) else (
    goto :install_and_run_py
)

:install_and_run
echo 检测到Python，正在安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 依赖安装失败，尝试直接启动
    goto :run_app
)
goto :run_app

:install_and_run_py
echo 检测到py命令，正在安装依赖...
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo 警告: 依赖安装失败，尝试直接启动
    goto :run_app_py
)
goto :run_app_py

:run_app
echo.
echo 正在启动Qoder历史记录查看器...
echo 请在浏览器中访问: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务器
echo.
python app.py
goto :end

:run_app_py
echo.
echo 正在启动Qoder历史记录查看器...
echo 请在浏览器中访问: http://127.0.0.1:5000
echo 按 Ctrl+C 停止服务器
echo.
py -m flask run --app app --host=127.0.0.1 --port=5000
goto :end

:end
echo.
echo 服务器已停止
pause