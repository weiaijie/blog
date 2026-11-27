# 11 月 27 日前瞻检查点与收盘输入复验

Ubuntu 定时采集于北京时间 17:03:26.900450 完成 11 月 27 日账本发布。GitHub 已保存[原始发布回执](../operations/20261127T090314Z-5d902b22/result.json)、[行情快照](../../data/snapshots/20261127T170315-58f85234-prices/requests.json)、[上交所交叉核验](../../data/snapshots/20261127T170315-58f85234-official/requests.json)和[当日日报](../daily/20261127T170315-58f85234/site/index.html)。本次对齐[公开仓库默认检查点](../../config/active_run.json)，同时封存[22:17 定时复查](../operations/20261127T141704Z-8fda72fd/result.json)。该次复查报告零网络请求、零账本变更。

从 11 月 26 日原检查点独立重放，18 户各追加一个估值日，账本日记录从 288 条增至 306 条。账户份额、现金和应收逐户核对，新增模拟成交 0 笔。用 510300 收盘 4.162 元、511010 收盘 141.301 元按持有份额复算权益，18 户与检查点逐项一致。基准费用月度 50/50 当日净盈亏为 +2,390.20 元，期末权益为 100,475.28 元。当前 17 个估值日、16 个收益区间。 [逐户复算](publication-replay.json) · [6、12、24 个月复盘](../2026-11-27-forward-milestones/README.md)

收盘输入以发布回执的实际完成时间为准。完成前 1 微秒查询，输入为空。到达该时点后，行情、交易所核对、发布回执及每日包的四份清单均能从 GitHub 恢复。该证据受五日实验自己的正式起算和决策时点约束。22:57 复查沪市两融，当日两页明细继续为空，汇总仅回 11 月 26 日。独立研究仍为 1 日归档、0 日合格。 [两融原始响应](../../data/snapshots/20261127-margin-2257/requests.json) · [独立研究起算核验](../2026-11-27-observation-origin/README.md)

用三份已公开证据包恢复 11 月 30 日盘前输入试算。22:05 的回看可复算 7 项量价输入，两只份额净值均为空。22:24 的回看可复算 9 项，新增股票 ETF 相对申购强度 +2.8491% 和国债 ETF -0.2501%。两个时点的政策事件数与同日融资买入占比均为空。两份结果均为按时点复算，属于验收证据。 [清算份额前](inputs-before-shares.json) · [清算份额后](inputs-after-shares.json) · [三份归档合并命令](../2026-11-27-cleared-shares/README.md)

```bash
export PYTHONPATH=src
python scripts/check_session_transition.py --bundle reports/daily/20261127T170315-58f85234
python scripts/forward_milestones.py --checkpoint reports/daily/20261127T170315-58f85234/forward_checkpoint.json --observed-at 2026-11-27T21:20:00+08:00
python -m unittest discover -s tests -p test_observation_inputs.py -v
```

从[清算份额报告](../2026-11-27-cleared-shares/README.md)先合并三份包并恢复台账，再在同一终端按原计算时点复算两个输入文件。

```bash
for stage in before after
do
  python scripts/observation_inputs.py --verify "reports/2026-11-27-forward-publication/inputs-$stage-shares.json" --observation-root "$scratch/ledger" --archive-store "$scratch/merged/archive"
done
```
