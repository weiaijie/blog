# 沪深交易所年度休市公告自动发现

Ubuntu 在北京时间 08:05 和 21:35 检查待接入年度。上交所使用官方休市公告列表，深交所按官方通知公告页的方式提交标题检索。保留实际请求地址、检索参数、收报时间、原始响应和 SHA256。空查询、抓取失败和多份候选分开记录。两家各有唯一候选时，下载年度原文，再用已有日历核验器对照日期、星期和复市日。通过后生成可复核的候选包，仍按原流程登记、提交和同步两个生产工作副本。

11 月 28 日 01:07 实测取得两个结果。

| 查询年度 | 上交所 | 深交所 | 结果 |
| --- | --- | --- | --- |
| 2026 正对照 | 找到年度通知 | 找到年度通知 | 实际下载两份原文，解析结果一致 |
| 2027 | 官方列表未见年度通知 | 官方标题检索返回 HTTP 200、0 条 | 仍待两家交易所发布证据，未生成准入日历 |

[2026 发现结果与原文](../../data/snapshots/20261128T010713-exchange-calendar-discovery-2026/result.json) · [2027 查询原始参数及响应](../../data/snapshots/20261128T010751-exchange-calendar-discovery-2027/requests.json)

国办已发布 2027 年放假安排。交易所日历接入仍使用两家交易所的原文及实际登记时点。[国办通知](https://big5.www.gov.cn/gate/big5/www.gov.cn/zhengce/content/202611/content_7085101.htm) · [上交所休市公告目录](https://www.sse.com.cn/disclosure/dealinstruc/closed/list/) · [深交所通知公告](https://www.szse.cn/disclosure/notice/general/index.html)

定时结果会随夜间证据包导出。离线演练用真实零结果回执完成导出和隔离恢复，复算时 2027 年仍是未知。原有 2026 年交易日与已封存账户照原版本可重放。手工复核可用 `scripts/discover_exchange_calendar.py --year 2027 --output ...`，已有包使用 `--verify ...`。
