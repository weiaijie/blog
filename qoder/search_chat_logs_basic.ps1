# PowerShell 脚本：搜索 Qoder 中的聊天日志（基础版）
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Starting Qoder chat log search..." -ForegroundColor Green

# 获取 Qoder 数据路径
$appDataPath = $env:APPDATA
$qoderPath = Join-Path $appDataPath "Qoder\User"
$workspacePath = Join-Path $qoderPath "workspaceStorage"

if (Test-Path $qoderPath) {
    Write-Host "Found Qoder data directory: $qoderPath" -ForegroundColor Green
    
    # 搜索 workspaceStorage 中的 state.vscdb 数据库文件
    Write-Host ""
    Write-Host "Searching for database files in workspaceStorage..." -ForegroundColor Yellow
    
    $stateFiles = Get-ChildItem -Path $workspacePath -Name "state.vscdb" -Recurse -ErrorAction SilentlyContinue
    if ($stateFiles) {
        Write-Host "Found $($stateFiles.Count) state.vscdb database files" -ForegroundColor Cyan
        
        # 输出数据库文件的位置
        foreach ($stateFile in $stateFiles) {
            $fullPath = Get-ChildItem -Path $workspacePath -Path $stateFile -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            Write-Host "  Database location: $($fullPath.Directory.Name)/$($stateFile)" -ForegroundColor White
        }
    }
    
    # 搜索 globalStorage 中可能包含聊天数据的目录
    Write-Host ""
    Write-Host "Searching for chat data in globalStorage..." -ForegroundColor Yellow
    $globalPath = Join-Path $qoderPath "globalStorage"
    if (Test-Path $globalPath) {
        $globalDirs = Get-ChildItem -Path $globalPath -Directory -ErrorAction SilentlyContinue
        Write-Host "Found $($globalDirs.Count) global storage extensions" -ForegroundColor Cyan
        
        foreach ($dir in $globalDirs) {
            if ($dir.Name -match "aicoding|chat|ai|code") {
                Write-Host "  Found AI-related extension directory: $($dir.Name)" -ForegroundColor Green
                
                # 搜索可能包含聊天记录的文件
                $jsonFiles = Get-ChildItem -Path $dir.FullName -Filter "*.json" -Recurse -ErrorAction SilentlyContinue
                $txtFiles = Get-ChildItem -Path $dir.FullName -Filter "*.txt" -Recurse -ErrorAction SilentlyContinue
                $logFiles = Get-ChildItem -Path $dir.FullName -Filter "*.log" -Recurse -ErrorAction SilentlyContinue
                
                if ($jsonFiles) {
                    Write-Host "    Found $($jsonFiles.Count) JSON files" -ForegroundColor White
                    foreach ($jsonFile in $jsonFiles) {
                        $sizeKB = [math]::Round($jsonFile.Length/1KB, 2)
                        Write-Host "      - $($jsonFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
                
                if ($txtFiles) {
                    Write-Host "    Found $($txtFiles.Count) text files" -ForegroundColor White
                    foreach ($txtFile in $txtFiles) {
                        $sizeKB = [math]::Round($txtFile.Length/1KB, 2)
                        Write-Host "      - $($txtFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
                
                if ($logFiles) {
                    Write-Host "    Found $($logFiles.Count) log files" -ForegroundColor White
                    foreach ($logFile in $logFiles) {
                        $sizeKB = [math]::Round($logFile.Length/1KB, 2)
                        Write-Host "      - $($logFile.Name) ($sizeKB KB)" -ForegroundColor Gray
                    }
                }
            }
        }
    }
    
    # 搜索 History 目录
    Write-Host ""
    Write-Host "Searching History directory..." -ForegroundColor Yellow
    $historyPath = Join-Path $qoderPath "History"
    if (Test-Path $historyPath) {
        $historyFiles = Get-ChildItem -Path $historyPath -File -ErrorAction SilentlyContinue
        Write-Host "Found History directory with $($historyFiles.Count) files" -ForegroundColor Cyan
        foreach ($file in $historyFiles) {
            $sizeKB = [math]::Round($file.Length/1KB, 2)
            Write-Host "  - $($file.Name) ($sizeKB KB)" -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "Search completed!" -ForegroundColor Green
    Write-Host "Chat logs may be located at:" -ForegroundColor Cyan
    Write-Host "  1. workspaceStorage/*/*/state.vscdb (SQLite databases)" -ForegroundColor White
    Write-Host "  2. globalStorage/aicoding* related directories in JSON files" -ForegroundColor White
    Write-Host "  3. History directory files" -ForegroundColor White
} else {
    Write-Host "Qoder data directory not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "Script execution completed" -ForegroundColor Green