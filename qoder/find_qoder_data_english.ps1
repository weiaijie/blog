# PowerShell script: Find Qoder local data (English version to avoid encoding issues)
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Searching for Qoder local data..." -ForegroundColor Green

# Get current user's AppData path
$appDataPath = $env:APPDATA
$qoderPath = Join-Path $appDataPath "Qoder\User"

Write-Host "Checking Qoder data path: $qoderPath" -ForegroundColor Yellow

if (Test-Path $qoderPath) {
    Write-Host "Found Qoder user data directory" -ForegroundColor Green
    
    # List main subdirectories
    $subdirs = Get-ChildItem -Path $qoderPath -Directory | Select-Object Name
    Write-Host "`nMain subdirectories:" -ForegroundColor Cyan
    foreach ($dir in $subdirs) {
        Write-Host "  - $($dir.Name)" -ForegroundColor White
    }
    
    # Check workspaceStorage
    $workspacePath = Join-Path $qoderPath "workspaceStorage"
    if (Test-Path $workspacePath) {
        Write-Host "`nworkspaceStorage exists" -ForegroundColor Green
        $wsCount = (Get-ChildItem -Path $workspacePath -Directory -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "  Contains $wsCount workspace directories" -ForegroundColor White
        
        # Find state.vscdb files
        $stateFiles = Get-ChildItem -Path $workspacePath -Name "state.vscdb" -Recurse -ErrorAction SilentlyContinue
        if ($stateFiles) {
            Write-Host "  Found $($stateFiles.Count) state.vscdb files" -ForegroundColor Green
        }
    }
    
    # Check globalStorage
    $globalPath = Join-Path $qoderPath "globalStorage"
    if (Test-Path $globalPath) {
        Write-Host "`nglobalStorage exists" -ForegroundColor Green
        $globalDirs = Get-ChildItem -Path $globalPath -Directory -ErrorAction SilentlyContinue
        Write-Host "  Global storage extensions count: $($globalDirs.Count)" -ForegroundColor White
        
        # Find possible aicoding related directories
        $aicodingDirs = $globalDirs | Where-Object { $_.Name -like "*aicoding*" }
        if ($aicodingDirs) {
            Write-Host "  Found aicoding related extension directories:" -ForegroundColor Green
            foreach ($dir in $aicodingDirs) {
                Write-Host "    - $($dir.Name)" -ForegroundColor White
            }
        }
    }
    
    # Show directory size
    $size = (Get-ChildItem $qoderPath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "`nQoder data total size: $sizeMB MB" -ForegroundColor Magenta
    
} else {
    Write-Host "Qoder user data directory not found" -ForegroundColor Red
    Write-Host "Tip: Qoder may not have created data directory yet, or installed in different location" -ForegroundColor Yellow
}

Write-Host "`nScript execution completed" -ForegroundColor Green