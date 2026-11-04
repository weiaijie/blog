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

## 会计组件（2026-11-04）

新增分红现金账本及13项合成会计测试：[说明与限制](reports/2026-11-04/PROGRESS.md)。在本项目目录运行 `PYTHONPATH=src python -m unittest discover -s tests -v`。尚未开展策略回测。

## 真实数据账本回放（2026-11-04）

[640日会计对账报告](reports/2026-11-04-replay/PROGRESS.md)：24项测试通过，7次分红、3200项每日核对一致。仅验证会计，未计算策略收益。在项目目录运行 `PYTHONPATH=src python scripts/replay_accounting.py --output /tmp/etf-accounting-replay`。

## 最新研究与自主接续

[目标、当前状态及下一任务](CONTINUATION.md) · [18组基准/趋势费用场景报告](reports/2026-11-04-baselines/PROGRESS.md)。35项测试通过；结果仅为明示假设下历史场景，不保证长期净收益。运行方式见报告。
