# 个人量化投资研究系统

只研究中国股票ETF和债券ETF，用1～2年评估长期年化净收益4%～5%的可行性；不保证收益、不实盘、不使用真实资金。研究代码、行情与来源保存于用户授权公开的weiaijie/blog / redesign-pc / docs/quantitative-investment/etf-research，不保存凭据或私人账户资料。

## 当前状态（2026-11-05收盘后）

|对象|状态|
|---|---|
|最新独立历史研究|1967日，2018-09-14～2026-10-30；13次官方分红、162固定场景。|
|保留的旧历史|640日和1167日结果均保留，不覆盖、不拼接。|
|前瞻账户输入|1171日，截至2026-11-05；保持原2022起预热历史。|
|真正前瞻观察|1日；首日只观察，18组合各持现金10万元，零交易、总收益0、年化空。|
|验证|108项测试、162组独立期末核对、离线复现和浏览器验收。|
|看板部署|静态代码和页面已保存，未配置公开域名托管。|

50/50基准费用年化：原640日4.90%，1167日0.51%，新1967日4.02%（最大收盘回撤19.73%）。同策略、同历史终点对起点敏感；最新数字落入研究目标范围也不证明长期目标成立。

- [最新停复牌查询核验](reports/2026-11-06-suspension/PROGRESS.md)
- [11月6日模拟目标与时间说明](reports/2026-11-06-intent/PROGRESS.md)
- [最新规则时间线证据](reports/2026-11-05-rule-timeline/PROGRESS.md)
- [最新研究报告与来源限制](reports/2026-11-05-long-history/PROGRESS.md) · [三种历史区间比较](reports/2026-11-05-long-history/sample_comparison.json)
- [前瞻检查点](reports/2026-11-05-long-history/forward_checkpoint.json) · [官方收盘交叉验证](reports/2026-11-05-long-history/official_close.json)
- [原1167日报告](reports/2026-11-04-extension/PROGRESS.md) · [原640日报告](reports/2026-11-04-closure/PROGRESS.md)
- [冻结协议](PROTOCOL_V1.md) · [接续入口](CONTINUATION.md) · [计划](PROJECT_PLAN.md) · [数据来源](DATA_SOURCES.md) · [静态看板](site/index.html)

## 复现

```sh
python scripts/verify_project.py
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/audit_official_close.py
python scripts/reproduce.py
python -m http.server 8765 --bind 127.0.0.1
```

依赖Python3标准库；可选网页验收需Playwright/Chromium，PDF文本提取需pdftotext。已有原始快照不覆盖。最新清单reports/2026-11-06-suspension/manifest.json；旧阶段清单在相应历史提交核验。新环境先读CONTINUATION.md，不依赖聊天记忆。

旧/workspace/quant-research、旧策略/看板和旧10项测试未恢复；当前是持续重建并已保存到仓库的版本。无实盘、无后台调度，未来收益不能在当前会话完成。
