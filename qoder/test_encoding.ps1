# 测试编码设置
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "测试中文显示：" -ForegroundColor Green
Write-Host "🔍 开始查找 Qoder 本地数据..." -ForegroundColor Yellow
Write-Host "✅ 找到 Qoder 用户数据目录" -ForegroundColor Green
Write-Host "📁 检查 Qoder 数据路径" -ForegroundColor Cyan
Write-Host "📂 workspaceStorage 存在" -ForegroundColor Magenta
Write-Host "🌐 globalStorage 存在" -ForegroundColor Blue
Write-Host "🤖 找到 aicoding 相关扩展目录" -ForegroundColor Red
Write-Host "💾 Qoder 数据总大小" -ForegroundColor White