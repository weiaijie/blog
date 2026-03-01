# 中文乱码问题解决方案

## 问题描述
在Windows环境下运行PowerShell和批处理脚本时，中文字符显示出现乱码。

## 解决方案

### 1. PowerShell脚本修复
在脚本开头添加以下代码：
```powershell
# 设置输出编码为 UTF-8
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### 2. 批处理脚本修复
在脚本开头添加：
```batch
@echo off
chcp 65001 > nul
```

### 3. 手动设置命令行编码
在运行脚本前，可以手动设置：
```cmd
chcp 65001
```

## 已修复的脚本

- `find_qoder_data_fixed.ps1` - 修复版PowerShell脚本
- `find_qoder_data_fixed.bat` - 修复版批处理脚本

## 使用方法

### 运行修复版PowerShell脚本：
```powershell
powershell -ExecutionPolicy Bypass -File find_qoder_data_fixed.ps1
```

### 运行修复版批处理脚本：
```cmd
find_qoder_data_fixed.bat
```

## 验证效果
运行修复后的脚本，中文应该能正常显示，不再出现乱码问题。

## 如何永久解决乱码问题

如果在当前环境中仍然出现乱码，请尝试以下方法：

### 方法1：系统级设置（推荐）
1. 打开"控制面板" → "时钟和区域" → "区域"
2. 点击"管理"选项卡
3. 点击"更改系统区域设置"
4. 勾选"Beta版：使用Unicode UTF-8提供全球语言支持"
5. 重启计算机使设置生效

### 方法2：使用英文版脚本
如果中文显示仍有问题，可使用英文版脚本：
- `find_qoder_data_english.ps1` - 英文版查找脚本
- `find_qoder_data_fixed.ps1` - 修复版中文脚本（包含UTF-8编码设置）

### 方法3：运行PowerShell配置脚本
运行 `SETUP_UTF8_PERMANENT.ps1` 脚本来配置PowerShell以永久支持UTF-8编码。