# Qoder 历史记录查看器启动脚本 (PowerShell版)

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "Qoder 历史记录查看器 启动脚本" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""

# 检查Python是否已安装
Write-Host "检查Python环境..." -ForegroundColor Yellow

$pythonInstalled = $false
$usePyCommand = $false

# 尝试直接运行python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ 检测到Python: $pythonVersion" -ForegroundColor Green
        $pythonInstalled = $true
    }
} catch {
    Write-Host "✗ 未找到 'python' 命令" -ForegroundColor Red
}

# 如果直接python不可用，尝试py命令
if (-not $pythonInstalled) {
    try {
        $pyVersion = py -3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 检测到Python (py): $pyVersion" -ForegroundColor Green
            $pythonInstalled = $true
            $usePyCommand = $true
        }
    } catch {
        Write-Host "✗ 未找到 'py' 命令" -ForegroundColor Red
    }
}

if (-not $pythonInstalled) {
    Write-Host ""
    Write-Host "错误: 未找到Python环境" -ForegroundColor Red
    Write-Host "请先安装Python 3.6或更高版本" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

# 安装依赖
Write-Host ""
Write-Host "正在安装依赖..." -ForegroundColor Yellow

if ($usePyCommand) {
    $installResult = py -m pip install -r requirements.txt 2>&1
} else {
    $installResult = pip install -r requirements.txt 2>&1
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: 依赖安装可能失败，尝试直接启动" -ForegroundColor Yellow
} else {
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
}

# 启动应用
Write-Host ""
Write-Host "正在启动Qoder历史记录查看器..." -ForegroundColor Green
Write-Host "请在浏览器中访问: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

try {
    if ($usePyCommand) {
        py -m flask run --app app --host=127.0.0.1 --port=5000
    } else {
        python app.py
    }
} catch {
    Write-Host "服务器启动失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "服务器已停止" -ForegroundColor Yellow
Read-Host "按任意键退出"