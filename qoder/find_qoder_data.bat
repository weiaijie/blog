@echo off
setlocal enabledelayedexpansion

echo 🔍 开始查找 Qoder 本地数据...
echo.

REM 获取当前用户的 AppData 路径
set "APPDATA_PATH=%APPDATA%"
set "QODER_PATH=%APPDATA_PATH%\Qoder\User"

echo 📁 检查 Qoder 数据路径: %QODER_PATH%
echo.

if exist "%QODER_PATH%" (
    echo ✅ 找到 Qoder 用户数据目录
    echo.
    
    REM 列出主要子目录
    echo 📋 主要子目录:
    for /d %%i in ("%QODER_PATH%\*") do (
        echo   - %%~ni
    )
    
    REM 检查 workspaceStorage
    set "WORKSPACE_PATH=%QODER_PATH%\workspaceStorage"
    if exist "!WORKSPACE_PATH!" (
        echo.
        echo 📂 workspaceStorage 存在
        REM 计算工作区目录数量
        set /a ws_count=0
        for /d %%j in ("!WORKSPACE_PATH!\*") do (
            set /a ws_count+=1
        )
        echo   包含 !ws_count! 个工作区目录
    )
    
    REM 检查 globalStorage
    set "GLOBAL_PATH=%QODER_PATH%\globalStorage"
    if exist "!GLOBAL_PATH!" (
        echo.
        echo 🌐 globalStorage 存在
        REM 计算全局存储扩展数量
        set /a global_count=0
        for /d %%k in ("!GLOBAL_PATH!\*") do (
            set /a global_count+=1
            REM 检查是否包含 aicoding
            if "%%~nk" gtr "" (
                set "temp_name=%%~nk"
                if "!temp_name!" == "!temp_name:aicoding=!" (
                    REM 不包含 aicoding
                ) else (
                    echo   🤖 找到 aicoding 相关扩展: %%~nk
                )
            )
        )
        echo   全局存储扩展数量: !global_count!
    )
    
    echo.
    echo 💾 正在计算 Qoder 数据大小...
    REM 使用 PowerShell 来计算目录大小
    powershell -Command "(Get-ChildItem '%QODER_PATH%' -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB" > temp_size.txt 2>nul
    set /p size_mb=<temp_size.txt
    del temp_size.txt 2>nul
    if defined size_mb (
        echo 💾 Qoder 数据总大小: !size_mb:~0,-2! MB
    )
    
) else (
    echo ❌ 未找到 Qoder 用户数据目录
    echo 💡 提示: Qoder 可能尚未创建数据目录，或者安装在其他位置
)

echo.
echo 🎯 脚本执行完成
pause