# 独立前瞻研究首个合格归档

2026 年 11 月 28 日北京时间 **08:25:04.935958**，首个完整定时归档通过核验，样本对应 **11 月 27 日**交易。systemd 实际唤醒是 08:25:00.573230，调用编号与原始回执一致。样本在 11 月 30 日 08:55 截止前取得，首 20 日连续性台账已标为按时合格。目前有 1 个合格归档交易日。 [核验记录](verification.json) · [证据包索引](pack/index.json)

| 里程碑 | 北京时间日期 |
| --- | --- |
| 观察期起算 | 2026-11-28 |
| 6 个月中期复盘 | 2027-05-28 |
| 12 个月结题周年 | 2027-11-28 |

两只 ETF 的清算份额和同估值日净值、沪市同范围成交及政策原文均有归档。两融汇总返回 11 月 26、27 日，27 日明细两页分别有 1,500 和 519 行，融资买入加总与汇总一致。沪市主板 A 股和科创板融资买入约占同范围成交额 **7.5080%**。融资余额对账差额是 **26 元**，原因和对账净额继续留空。 [两融和市场核验](verification.json)

政策特征仍需五段有定时证据及审核的覆盖。正式成对日期还要有决策、预测与五交易日标签。最后所需标签核验完毕后生成结题报告。原 18 个模拟账户按[冻结协议](../../PROTOCOL_V1.md)观察至 24 个月。 [独立实验协议](../../PROTOCOL_OBSERVATION_V1.md)

在 Ubuntu 从本增量包恢复了起算回执、原始采集和日历巡检。起算登记与原回执逐字节一致，归档核验前一微秒查询为空，从核验时刻可复算相同起点。08:05 巡检中沪深两处来源均返回 HTTP 200，响应未列出 2027 年交易所休市公告。日历准入继续等待原文。 [恢复及日历证据](verification.json)

增量承接[此前复采包](../2026-11-28-predecision-retry/README.md)至 08:25:05，保留实际收报、核验和原始响应。夜间定时导出按其既有发布水位接续。

```bash
export PYTHONPATH=src
scratch=$(mktemp -d)
python scripts/pack_observation_evidence.py verify --pack reports/2026-11-28-first-qualified-observation/pack
python scripts/pack_observation_evidence.py restore-ledger --pack reports/2026-11-28-first-qualified-observation/pack --destination "$scratch/ledger"
```
