# 12 个月目标首个工程里程碑

[长期目标与判定门槛](../../docs/LONG_TERM_RESEARCH.md)已登记。此处记录上交所数据的单日采集试跑，按目标日及上一个已核交易日查询，并保留 HTTP 响应、失败尝试、SHA256 和实际就绪时间。

| 目标交易日 | 结果 | 原始证据 |
| --- | --- | --- |
| 2026-11-26 | 四项响应完整。沪市主板 A 股与科创板成交额 6,136.50 亿元，按同范围计算的融资买入占比约 6.3850%。融资余额对账残差 43 元，对账净额继续留空。 | [封存清单](../../data/snapshots/20261127T084226Z-10828286-sse-research-day/manifest.json) |
| 2026-11-27 | 同范围成交额可复算为 9,303.79 亿元。相邻日融资汇总缺当日记录，两融结果留空。 | [封存清单](../../data/snapshots/20261127T084227Z-669d6f01-sse-research-day/manifest.json) |

两个快照均在 11 月 27 日 16:42 左右取回并校验，仅作为试跑证据。真实前瞻观察期等待独立管线正式运行后的首个合格归档日。本期入口处理日期、行情与融资样本的完整性，策略输入、原交易调度及账户的准入另有流程。

## 复算

```sh
python scripts/collect_sse_research_day.py --verify data/snapshots/20261127T084226Z-10828286-sse-research-day
python scripts/collect_sse_research_day.py --verify data/snapshots/20261127T084227Z-669d6f01-sse-research-day
```

运行 `python scripts/collect_sse_research_day.py --day YYYY-MM-DD` 会创建新快照。未到北京时间 16:00 的当天、非交易日或缺正式年份日历均拒绝采集。试跑期间未注册独立的定时任务。
