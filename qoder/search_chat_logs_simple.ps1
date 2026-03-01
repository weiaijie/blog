# PowerShell 脚本：搜索 Qoder 中的聊天日志（简化版）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔍 开始搜索 Qoder 聊天日志..." -ForegroundColor Green

# 获取 Qoder 数据路径
$appDataPath = $env:APPDATA
$qoderPath = Join-Path $appDataPath "Qoder\User"
$workspacePath = Join-Path $qoderPath "workspaceStorage"

if (Test-Path $qoderPath) {
    Write-Host "✅ 找到 Qoder 数据目录: $qoderPath" -ForegroundColor Green
    
    # 搜索 workspaceStorage 中的 state.vscdb 数据库文件
    Write-Host "`n🔍 搜索 workspaceStorage 中的数据库文件..." -ForegroundColor Yellow
    
    $stateFiles = Get-ChildItem -Path $workspacePath -Name "state.vscdb" -Recurse -ErrorAction SilentlyContinue
    if ($stateFiles) {
        Write-Host "📁 找到 $($stateFiles.Count) 个 state.vscdb 数据库文件" -ForegroundColor Cyan
        
        # 输出数据库文件的位置
        foreach ($stateFile in $stateFiles) {
            $fullPath = Get-ChildItem -Path $workspacePath -Path $stateFile -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            Write-Host "   数据库位置: $($fullPath.Directory.Name)/$($stateFile)" -ForegroundColor White
        }
    }
    
    # 搜索 globalStorage 中可能包含聊天数据的目录
    Write-Host "`n🔍 搜索 globalStorage 中的扩展数据..." -ForegroundColor Yellow
    $globalPath = Join-Path $qoderPath "globalStorage"
    if (Test-Path $globalPath) {
        $globalDirs = Get-ChildItem -Path $globalPath -Directory -ErrorAction SilentlyContinue
        Write-Host "📦 找到 $($globalDirs.Count) 个全局存储扩展" -ForegroundColor Cyan
        
        foreach ($dir in $globalDirs) {
            if ($dir.Name -match "aicoding|chat|ai|code") {
                Write-Host "   🤖 找到 AI 相关扩展目录: $($dir.Name)" -ForegroundColor Green
                
                # 搜索可能包含聊天记录的文件
                $jsonFiles = Get-ChildItem -Path $dir.FullName -Filter "*.json" -Recurse -ErrorAction SilentlyContinue
                $txtFiles = Get-ChildItem -Path $dir.FullName -Filter "*.txt" -Recurse -ErrorAction SilentlyContinue
                $logFiles = Get-ChildItem -Path $dir.FullName -Filter "*.log" -Recurse -ErrorAction SilentlyContinue
                
                if ($jsonFiles) {
                    Write-Host "      📄 找到 $($jsonFiles.Count) 个 JSON 文件" -ForegroundColor White
                    foreach ($jsonFile in $jsonFiles) {
                        $sizeKB = [math]::Round($jsonFile.Length/1KB, 2)
                        Write-Host "         - $($jsonFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
                
                if ($txtFiles) {
                    Write-Host "      📝 找到 $($txtFiles.Count) 个文本文件" -ForegroundColor White
                    foreach ($txtFile in $txtFiles) {
                        $sizeKB = [math]::Round($txtFile.Length/1KB, 2)
                        Write-Host "         - $($txtFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
                
                if ($logFiles) {
                    Write-Host "      📋 找到 $($logFiles.Count) 个日志文件" -ForegroundColor White
                    foreach ($logFile in $logFiles) {
                        $sizeKB = [math]::Round($logFile.Length/1KB, 2)
                        Write-Host "         - $($logFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
            }
        }
    }
    
    # 搜索 History 目录
    Write-Host "`n🔍 搜索 History 目录..." -ForegroundColor Yellow
    $historyPath = Join-Path $qoderPath "History"
    if (Test-Path $historyPath) {
        $historyFiles = Get-ChildItem -Path $historyPath -File -ErrorAction SilentlyContinue
        Write-Host "📅 找到 History 目录，包含 $($historyFiles.Count) 个文件" -ForegroundColor Cyan
        foreach ($file in $historyFiles) {
            $sizeKB = [math]::Round($file.Length/1KB, 2)
            Write-Host "   - $($file.Name) ($sizeKB KB)" -ForegroundColor White
        }
    }
    
    Write-Host "`n💡 搜索完成！" -ForegroundColor Green
    Write-Host "📋 聊天日志可能位于以下位置：" -ForegroundColor Cyan
    Write-Host "   1. workspaceStorage/*/*/state.vscdb (SQLite数据库)" -ForegroundColor White
    Write-Host "   2. globalStorage/aicoding* 相关目录中的 JSON 文件" -ForegroundColor White
    Write-Host "   3. History 目录中的历史记录文件" -ForegroundColor White
} else {
    Write-Host "❌ 未找到 Qoder 数据目录" -ForegroundColor Red
}

Write-Host "`n🎯 脚本执行完成" -ForegroundColor Green