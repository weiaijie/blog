# 个人量化投资研究系统

仅研究中国股票ETF与债券ETF，用1～2年评估长期年化净收益4%～5%的可行性；不保证收益、不实盘、不用真实资金。沿用用户已授权公开的 weiaijie/blog / redesign-pc / docs/quantitative-investment/etf-research，不提交凭据或私人账户信息。

## 当前状态（2026-11-05，收盘前）

|对象|状态|
|---|---|
|冻结历史研究|1167日，2022-01-04～2026-10-30；162个预设场景。|
|账户已核验输入|1170日，截至2026-11-04；含新准入11月2/3/4日。|
|真正前瞻观察|0日；11月5日未取得合格收盘样本，收益为空。|
|最新代码验证|84项测试；离线研究、准入和检查点复现。|
|公开部署|静态看板代码已保存，不代表已配置域名托管。|

50/50基准费用场景年化在原640日为4.90%，扩样1167日后为0.51%、最大收盘回撤15.09%。起点敏感，当前不足支持长期目标；不挑有利区间或调参追到目标。

- [最新：官方历史、税费与停复牌证据](reports/2026-11-05-evidence/PROGRESS.md)
- [正式规则与公告审阅](reports/2026-11-05-notices/PROGRESS.md)
- [真实增量准入](reports/2026-11-05-admission/PROGRESS.md) · [1167日扩样研究](reports/2026-11-04-extension/PROGRESS.md) · [原640日研究](reports/2026-11-04-closure/PROGRESS.md)
- [冻结协议v1](PROTOCOL_V1.md) · [接续入口](CONTINUATION.md) · [完整计划与历史](PROJECT_PLAN.md) · [数据来源](DATA_SOURCES.md)
- [静态看板](site/index.html)

## 本地运行

研究只需Python3标准库；可选浏览器验收另需Playwright/Chromium。

```sh
python scripts/verify_project.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/reproduce.py
python -m http.server 8765 --bind 127.0.0.1
```

本地看板：http://127.0.0.1:8765/site/ 。离线复现不会抓新行情。候选采集用scripts/collect_update.py，准入及检查点用scripts/advance_forward.py，公告变化审阅用scripts/review_catalog.py；完整命令见对应报告。新快照/审阅包使用新目录，不覆盖历史。目录变化仍须核对原文，不自动批准分红或交易。

旧 /workspace/quant-research、旧策略/看板与旧10项测试没有恢复；当前是持续重建、保存在仓库的版本。原blog投资文章的业绩描述不构成研究证据。旧阶段清单需在对应历史提交核验，最新清单为reports/2026-11-05-evidence/manifest.json。新环境从固定提交取回后先读CONTINUATION.md再核验，不依赖聊天记忆。
