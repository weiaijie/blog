# PowerShell 脚本：自动查找 Qoder 本地数据 (修复版 - 解决中文乱码)
# 设置输出编码为 UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔍 开始查找 Qoder 本地数据..." -ForegroundColor Green

# 获取当前用户的 AppData 路径
$appDataPath = $env:APPDATA
$qoderPath = Join-Path $appDataPath "Qoder\User"

Write-Host "📁 检查 Qoder 数据路径: $qoderPath" -ForegroundColor Yellow

if (Test-Path $qoderPath) {
    Write-Host "✅ 找到 Qoder 用户数据目录" -ForegroundColor Green
    
    # 列出主要子目录
    $subdirs = Get-ChildItem -Path $qoderPath -Directory | Select-Object Name
    Write-Host "`n📋 主要子目录:" -ForegroundColor Cyan
    foreach ($dir in $subdirs) {
        Write-Host "  - $($dir.Name)" -ForegroundColor White
    }
    
    # 检查 workspaceStorage
    $workspacePath = Join-Path $qoderPath "workspaceStorage"
    if (Test-Path $workspacePath) {
        Write-Host "`n📂 workspaceStorage 存在" -ForegroundColor Green
        $wsCount = (Get-ChildItem -Path $workspacePath -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "  包含 $wsCount 个工作区目录" -ForegroundColor White
        
        # 查找 state.vscdb 文件
        $stateFiles = Get-ChildItem -Path $workspacePath -Name "state.vscdb" -Recurse -ErrorAction SilentlyContinue
        if ($stateFiles) {
            Write-Host "  🗄️  找到 $($stateFiles.Count) 个 state.vscdb 文件" -ForegroundColor Green
        }
    }
    
    # 检查 globalStorage
    $globalPath = Join-Path $qoderPath "globalStorage"
    if (Test-Path $globalPath) {
        Write-Host "`n🌐 globalStorage 存在" -ForegroundColor Green
        $globalDirs = Get-ChildItem -Path $globalPath -Directory -ErrorAction SilentlyContinue
        Write-Host "  全局存储扩展数量: $($globalDirs.Count)" -ForegroundColor White
        
        # 查找可能的 aicoding 相关目录
        $aicodingDirs = $globalDirs | Where-Object { $_.Name -like "*aicoding*" }
        if ($aicodingDirs) {
            Write-Host "  🤖 找到 aicoding 相关扩展目录:" -ForegroundColor Green
            foreach ($dir in $aicodingDirs) {
                Write-Host "    - $($dir.Name)" -ForegroundColor White
            }
        }
    }
    
    # 显示目录大小
    $size = (Get-ChildItem $qoderPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "`n💾 Qoder 数据总大小: $sizeMB MB" -ForegroundColor Magenta
    
} else {
    Write-Host "❌ 未找到 Qoder 用户数据目录" -ForegroundColor Red
    Write-Host "💡 提示: Qoder 可能尚未创建数据目录，或者安装在其他位置" -ForegroundColor Yellow
}

Write-Host "`n🎯 脚本执行完成" -ForegroundColor Green