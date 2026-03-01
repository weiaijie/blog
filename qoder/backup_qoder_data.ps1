# PowerShell 脚本：备份 Qoder 数据
param(
    [string]$BackupDestination = "$env:USERPROFILE\Desktop\qoder_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

Write-Host "🔄 开始备份 Qoder 数据..." -ForegroundColor Green
Write-Host "📦 备份目标位置: $BackupDestination" -ForegroundColor Yellow

# 获取 Qoder 数据路径
$appDataPath = $env:APPDATA
$qoderPath = Join-Path $appDataPath "Qoder\User"

Write-Host "📁 源数据路径: $qoderPath" -ForegroundColor Yellow

if (Test-Path $qoderPath) {
    # 创建备份目录
    New-Item -ItemType Directory -Path $BackupDestination -Force | Out-Null
    
    Write-Host "✅ 开始复制数据..." -ForegroundColor Green
    
    # 复制整个 Qoder\User 目录
    try {
        Copy-Item -Path $qoderPath -Destination $BackupDestination -Recurse -Force
        Write-Host "✅ 数据备份完成!" -ForegroundColor Green
        
        # 计算备份大小
        $backupSize = (Get-ChildItem $BackupDestination -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $sizeMB = [math]::Round($backupSize / 1MB, 2)
        Write-Host "💾 备份大小: $sizeMB MB" -ForegroundColor Cyan
        
        Write-Host "📍 备份位置: $BackupDestination" -ForegroundColor Cyan
        
        # 列出备份的主要内容
        Write-Host "`n📋 备份内容概览:" -ForegroundColor Cyan
        $backupRoot = Join-Path $BackupDestination "User"
        if (Test-Path $backupRoot) {
            $subdirs = Get-ChildItem -Path $backupRoot -Directory | Select-Object Name
            foreach ($dir in $subdirs) {
                Write-Host "  - $($dir.Name)" -ForegroundColor White
            }
        } else {
            $subdirs = Get-ChildItem -Path $BackupDestination -Directory | Select-Object Name
            foreach ($dir in $subdirs) {
                Write-Host "  - $($dir.Name)" -ForegroundColor White
            }
        }
    }
    catch {
        Write-Host "❌ 备份过程中出现错误: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 未找到 Qoder 数据源路径，无法备份" -ForegroundColor Red
}

Write-Host "`n🎯 备份脚本执行完成" -ForegroundColor Green