# 永久设置PowerShell UTF-8编码的脚本
# 该脚本将配置PowerShell以永久支持UTF-8编码

Write-Host "🔧 正在配置PowerShell UTF-8编码..." -ForegroundColor Green

# 1. 设置PowerShell配置以支持UTF-8
try {
    # 创建PowerShell配置目录（如果不存在）
    $profileDir = Split-Path $PROFILE -Parent
    if (!(Test-Path $profileDir)) {
        New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
        Write-Host "✅ 创建PowerShell配置目录: $profileDir" -ForegroundColor Green
    }

    # 添加UTF-8编码设置到PowerShell配置文件
    $encodingConfig = @'
# 设置PowerShell输出编码为UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# 设置默认参数以使用UTF-8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Import-Csv:Encoding'] = 'utf8'
$PSDefaultParameterValues['Export-Csv:Encoding'] = 'utf8'
'@

    # 检查配置文件是否已有编码设置
    if (Test-Path $PROFILE) {
        $profileContent = Get-Content $PROFILE -Raw
        if ($profileContent -match '\$OutputEncoding = \[System\.Text\.Encoding\]::UTF8') {
            Write-Host "⚠️  PowerShel配置文件中已存在UTF-8设置" -ForegroundColor Yellow
        } else {
            # 追加编码设置到现有配置
            Add-Content -Path $PROFILE -Value $encodingConfig
            Write-Host "✅ 已将UTF-8设置追加到现有PowerShell配置文件" -ForegroundColor Green
        }
    } else {
        # 创建新的配置文件
        Set-Content -Path $PROFILE -Value $encodingConfig
        Write-Host "✅ 已创建PowerShell配置文件: $PROFILE" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 设置PowerShell配置时出错: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. 提供系统级设置建议（需要管理员权限）
Write-Host "`n💡 系统级设置建议（需要管理员权限）:" -ForegroundColor Cyan
Write-Host "   1. 打开控制面板 -> 区域 -> 管理 -> 更改系统区域设置" -ForegroundColor White
Write-Host "   2. 勾选'使用Unicode UTF-8提供全球语言支持'" -ForegroundColor White
Write-Host "   3. 重启电脑使设置生效" -ForegroundColor White

# 3. 提供临时解决方案
Write-Host "`n🔄 临时解决方案（当前会话有效）:" -ForegroundColor Cyan
Write-Host "   在PowerShell中运行: chcp 65001" -ForegroundColor White
Write-Host "   然后运行: [Console]::OutputEncoding = [System.Text.Encoding]::UTF8" -ForegroundColor White

# 4. 验证当前设置
Write-Host "`n📋 当前编码设置:" -ForegroundColor Cyan
Write-Host "   控制台输出编码: $([Console]::OutputEncoding.EncodingName)" -ForegroundColor White
Write-Host "   控制台输入编码: $([Console]::InputEncoding.EncodingName)" -ForegroundColor White

Write-Host "`n✅ 配置完成！重启PowerShell后设置将生效。" -ForegroundColor Green