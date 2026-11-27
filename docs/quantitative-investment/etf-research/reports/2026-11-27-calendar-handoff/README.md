# 跨年交易日历的核验与接续

2026 年 11 月 27 日在 Ubuntu 实际取得沪深交易所的年度休市原文。独立解析得到相同的 7 段休市日期，逐日重建的 242 个交易日与原 2026 年日历全部一致。两份原文、HTTP 请求记录、收报时点、解析结果和哈希已封存。 [2026 年演练证据](../../data/snapshots/20261127T115806Z-calendar-annual-rehearsal/manifest.json) · [上交所年度公告](https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml) · [深交所年度公告](https://www.szse.cn/disclosure/notice/general/t20251222_618087.html)

到本次核查时，查阅的交易所入口仍展示 2026 年安排，2027 年暂未准入。缺年度证据时，系统保留已确认年份，涉及跨年交易日的决策、预测和月报等待核验。 [上交所休市安排](https://www.sse.com.cn/disclosure/dealinstruc/closed/) · [深交所公告目录](https://www.szse.cn/disclosure/notice/general/index.html)

## 正式公告发布后

在独立研究工作树先保存两家交易所针对 A 股全年的正式公告。下列变量分别填写研究年份、原文 URL 和新的证据目录。

```bash
python scripts/capture_exchange_calendar.py --year "$etf_calendar_year" \
  --sse "$etf_sse_annual_notice" --szse "$etf_szse_annual_notice" \
  --output "$etf_calendar_snapshot"
python scripts/capture_exchange_calendar.py --verify "$etf_calendar_snapshot"
python scripts/capture_exchange_calendar.py --register "$etf_calendar_snapshot"
```

校验两家公告的闭市区间、公告中的复市日、日期和星期。已支持的公告格式可重算，缺页、分歧、额外工作日休市或无法确认的格式保留错误。新年度以原始响应核验完成后的实际注册时间准入，逐年追加，原始包和登记文件不可覆盖。

提交已核验目录与新年度登记文件后，把同一版本同步至主项目和独立采集工作副本，使用 GitHub 字节与两处实际指纹复核部署。新形成的采集、决策、开盘、标签、训练、预测、评估及月报封存当次用到的年度证据。原有 18 户的行情准入按新候选自身时间绑定日历，原有历史候选仍按旧格式重算。临时闭市或正式公告更正需要保存新证据并核实影响后发布。

隔离测试专门检查注册前不可见、旧指纹复现、双源冲突、额外闭市注释、跨年上一个和下一个交易日以及连续五交易日标签。演练使用的未来日期仅属于测试。
