# 个人量化投资研究系统

仅研究中国股票ETF与债券ETF，用1～2年评估长期年化净收益4%～5%的可行性；不保证收益、不接实盘、不用真实资金。用户已允许将研究代码、行情和数据源公开保存在 weiaijie/blog 的 redesign-pc 分支本目录；禁止提交凭据和私人账户资料。

## 当前版本

- [本会话目标与验收](SESSION_GOAL.md) · [持续推进入口](CONTINUATION.md)
- [第一版研究闭环报告](reports/2026-11-04-closure/PROGRESS.md)：162个预设费用/本金/延迟场景、18组主场景的连续持仓分折及滚动评估。
- [静态看板文件](site/index.html)：原始数据截止2026-10-30，共640已核验日；可切换费用与策略。源码已生成，是否公开托管不能由文件存在推断。
- [前瞻协议v1](PROTOCOL_V1.md)：新行情请求前提交于0c797f5e；前瞻样本从2026-11-05起，目前无合格前瞻收益。
- [最新来源诊断](data/snapshots/2026-11-04-expansion-07/audit.json)：24次请求，新浪扩至1970行，但新增历史尚未获完整准入，研究区间未扩容。

45项自动化测试通过，另有162组期末独立核对、桌面/手机浏览器检查、完整离线重算验证。50/50基准费用场景年化约4.90%、最大收盘回撤10.10%，不代表长期目标成立；小本金整手限制、成交假设和未来样本仍重要。

## 本地复现

Python 3标准库即可运行研究，不需要券商客户端。可选页面浏览器验收才需要Playwright/Chromium。

```sh
python scripts/verify_project.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/reproduce.py
python -m http.server 8765 --bind 127.0.0.1
```

最后一行启动本地静态预览，打开 http://127.0.0.1:8765/site/ 。复现不会抓取新行情。采集脚本必须在新快照目录运行，不覆盖已冻结原始文件。

## 保存与历史

存储位置：weiaijie/blog → redesign-pc → docs/quantitative-investment/etf-research。新环境从固定提交取回本目录，先读 CONTINUATION.md，再做哈希验证。可下载整个仓库ZIP；项目单独备份与原始输入均可从已提交文件重建。

旧 /workspace/quant-research、旧策略和旧看板未恢复；当前是新建且逐步保存的研究，不冒称找回旧“10项测试”。历史会计/回放/基准报告位于reports目录；旧报告绑定当时提交的代码，不能要求旧代码哈希在最新实现上不变。当前版本以closure报告和清单为准。原有blog投资文章中的业绩描述不构成本研究证据。
