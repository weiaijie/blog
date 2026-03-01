# PowerShell 脚本：搜索 Qoder 中的聊天日志
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
        
        # 尝试连接数据库并搜索聊天相关的表
        foreach ($stateFile in $stateFiles) {
            $fullPath = Get-ChildItem -Path $workspacePath -Path $stateFile -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            
            Write-Host "   检查数据库: $($fullPath.FullName)" -ForegroundColor White
            
            try {
                # 使用 PowerShell 调用 SQLite 命令行工具查询数据库
                # 首先列出所有表
                $tablesResult = cmd /c "sqlite3.exe `"$($fullPath.FullName)`" `.tables 2>null""
                if ($tablesResult) {
                    $tables = $tablesResult -split '\s+' | Where-Object { $_.Trim() -ne "" }
                    foreach ($table in $tables) {
                        if ($table -match "chat|aicoding|message|conversation|session") {
                            Write-Host "      🗣️  发现可能的聊天相关表: $table" -ForegroundColor Magenta
                            
                            # 尝试获取表中的记录数
                            $countResult = cmd /c "sqlite3.exe `"$($fullPath.FullName)`" `"SELECT COUNT(*) FROM [$table];`""
                            Write-Host "         记录数: $countResult" -ForegroundColor Gray
                        }
                    }
                } else {
                    Write-Host "      💡 提示: 未安装 sqlite3 工具，跳过数据库内容检查" -ForegroundColor Gray
                }
            } catch {
                Write-Host "      ⚠️  无法访问数据库: $($_.Exception.Message)" -ForegroundColor Red
            }
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
                        Write-Host "         - $($jsonFile.Name) ($([math]::Round($jsonFile.Length/1KB, 2)) KB)" -ForegroundColor Gray
                    }
                }
                
                if ($txtFiles) {
                    Write-Host "      📝 找到 $($txtFiles.Count) 个文本文件" -ForegroundColor White
                    foreach ($txtFile in $txtFiles) {
                        Write-Host "         - $($txtFile.Name) ($([math]::Round($txtFile.Length/1KB, 2)) KB)" -ForegroundColor Gray
                    }
                }
                
                if ($logFiles) {
                    Write-Host "      📋 找到 $($logFiles.Count) 个日志文件" -ForegroundColor White
                    foreach ($logFile in $logFiles) {
                        Write-Host "         - $($logFile.Name) ($([math]::Round($logFile.Length/1KB, 2)) KB)" -ForegroundColor Gray
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
            Write-Host "   - $($file.Name) ($([math]::Round($file.Length/1KB, 2)) KB)" -ForegroundColor White
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