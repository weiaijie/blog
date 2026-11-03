# 个人量化投资研究系统

仅研究中国股票 ETF 与债券 ETF，用 1～2 年评估长期年化净收益 4%～5% 的可行性；不保证收益，不接实盘，不使用真实资金。用户于2026-11-03确认：使用公开的 weiaijie/blog 仓库 redesign-pc 分支保存本研究资料；禁止提交凭据和私人资料。

## 当前保存范围

本仓库保存 2026-11-02 的真实行情诊断、数据源请求脚本、URL、原始响应、错误、分红与独立日历核验。旧项目的策略代码、测试和 site 尚未找到，本仓库不代表旧项目恢复。此前“10项测试通过”未在本次复验。

- `PROJECT_PLAN.md`：目标、已完成及下一步。
- `data/snapshots/2026-11-02/`：原始数据与逐文件 SHA256 清单；不得覆盖。
- `DATA_SOURCES.md`：数据源、实际限制和复核要求。
- `AGENTS.md`：续接与持久化规则。

## 离线验证

运行 `python verify_snapshot.py` 核验全部文件哈希；将快照复制到临时目录后运行 `python validate.py` 可重做数据核验。仅需 Python 3 标准库。采集脚本会覆盖输出，因此不得在原始快照内重跑采集。

GitHub 下载备份：登录仓库后选择 Code → Download ZIP。新云环境从仓库克隆后先读 PROJECT_PLAN.md，再校验文件。

保存位置：`weiaijie/blog` → `redesign-pc` → `docs/quantitative-investment/etf-research/`。历史快照 STATUS.txt 保留当时的私有存储约束，本文件记录的新授权优先。旧投资文档中的业绩描述不构成本ETF研究的验证结果。
