````md
# DataClaw 导出 Codex 项目（yba-weapp）完整操作手册（最终稳定版）

## 🎯 目标

从 Codex CLI 日志中导出项目：

`codex:yba-weapp`

生成本地文件：

`yba_weapp_codex.jsonl`

仅本地导出，不上传到 HuggingFace。

---

# 🧱 前提条件

- 已安装 pipx
- 已安装 dataclaw
- 已成功运行 `dataclaw list`
- 当前环境为 WSL / Linux

---

# 🪜 标准执行步骤（按顺序执行）

## Step 1 — 扫描 Codex 数据

```bash
dataclaw prep --source codex
```

---

## Step 2 — 设置来源为 Codex

```bash
dataclaw config --source codex
```

---

## Step 3 — 排除不需要的项目

只保留 `codex:yba-weapp`，排除其他项目：

```bash
dataclaw config --exclude "codex:oh-my-opencode,codex:projects,codex:saber,codex:xyjl"
```

---

## Step 4 — 确认项目范围

```bash
dataclaw config --confirm-projects
```

---

## Step 5 — 导出到本地文件（不上传）

```bash
dataclaw export --no-push --repo "codex:yba-weapp" -o yba_weapp_codex.jsonl
```

---

# 📁 文件位置说明

默认导出到当前终端所在目录。

查看当前路径：

```bash
pwd
```

如果当前目录为：

```
/home/saber
```

则文件路径为：

```
/home/saber/yba_weapp_codex.jsonl
```

检查文件：

```bash
ls -lh yba_weapp_codex.jsonl
```

---

# 🪟 可选：导出到 Windows 桌面

```bash
dataclaw export \
  --no-push \
  --repo "codex:yba-weapp" \
  -o /mnt/c/Users/YourWindowsUser/Desktop/yba_weapp_codex.jsonl
```

替换 `YourWindowsUser` 为你的 Windows 用户名。

---

# 🔎 验证导出内容

查看前几行：

```bash
head -n 5 yba_weapp_codex.jsonl
```

统计条数：

```bash
wc -l yba_weapp_codex.jsonl
```

---

# 🔄 整体流程结构

```
prep
→ config --source
→ config --exclude
→ config --confirm-projects
→ export
```

---

# 🚀 完成说明

成功后，你将获得结构化 JSONL 文件，可用于：

- Prompt 分析
- Agent 行为复盘
- 微调数据准备
- 数据统计分析
- 构建个人 Coding 数据集

---

如需扩展：

- JSONL 数据分析脚本（Python）
- jq 分析命令合集
- 微调格式转换模板
- Prompt 质量筛选方案
- Token 统计脚本

可继续生成对应文档。
````
