# 两融报送截止前后的独立取证

北京时间 11 月 27 日 21:57 复查，国泰基金返回下一交易日 11 月 30 日的申赎清单，其中 11 月 27 日估值日的 511010 单位净值为 141.339 元。当前最早留存的有效收报时间是 21:57。21:00 该请求仍返回 404。具体首次公开时点未知。 [21:57 净值证据](../../data/snapshots/20261127-disclosure-followup/pcf-1127/result.json) · [21:00 原始请求](../../data/snapshots/20261127-disclosure-availability/scheduled-input-probe-2100/requests.json)

上交所公开申赎清单栏目注明交易日上午 08:30 披露。实际提取了该页面所用的公开申赎清单接口，11 月 27 日估值日仍未在其中找到。同一接口与管理人清单对照，上一个估值日 11 月 26 日的单位净值均为 141.371 元，两份清单都标注 11 月 27 日生效。该路径保留为官方对照。 [上交所栏目](https://www.sse.com.cn/disclosure/fund/etflist/) · [原始页面](../../data/snapshots/20261127-disclosure-followup/exchange-publication/requests.json) · [同日期正对照](../../data/snapshots/20261127-disclosure-followup/pcf-positive-control/result.json)

21:57 的交易所份额请求仍是 HTTP 200 空表，两融汇总只返回 11 月 26 日，两页明细均为空。510300 两日单位净值与早一轮一致，分别为 11 月 26 日 3.9741 元与 11 月 27 日 4.1397 元。 [报送截止前原始请求](../../data/snapshots/20261127-disclosure-followup/before-2200/requests.json) · [上交所两融报送业务指南](https://www.sse.com.cn/lawandrules/guide2025/stock/jyglywznylc/zn/c/c_20230404_10797853.shtml)

## 22:05 单次复查

Ubuntu 的一次性复查在 22:05:00 启动，22:05:04 完成归档核验。来源结果为部分可用。两只 ETF 的单位净值都已取得，交易所清算份额仍是空表。上交所两融汇总只含 11 月 26 日，11 月 27 日两页明细均为空。两只 ETF 的当日份额净值资金估算与两融字段继续保留未知。 [单次复查回执](probe-receipt.json) · [六条来源响应](after.json)

此回执标记为手工核查。原定时采集已归档 1 个交易日，合格日仍为 0。下一次定时补采为北京时间 11 月 28 日 08:25。

## 从 GitHub 恢复并核验

日明细接口 `GET /api/v1/research/observation?day=2026-11-27&asOf=<含时区的时点>` 按指定时点读取实际可见的归档。尚未开始的尝试留在之后的时点。已开始、还未封存的尝试显示等待归档。可对比 [19:55 截至时点](before.json) 与 [复查后的时点](after.json)。

本批采用增量证据包。基础包和增量包须按留存的原时间边界依次合并。合并后可在新目录恢复台账并复算两个时点。时间不连续、回执冲突或归档字节不符时，合并报错。下面命令在项目目录执行。

```bash
export PYTHONPATH=src
scratch=$(mktemp -d)
python scripts/pack_observation_evidence.py merge --pack reports/2026-11-27-portable-observation/pack --pack reports/2026-11-27-after-filing/pack --output "$scratch/merged"
python scripts/pack_observation_evidence.py restore-ledger --pack "$scratch/merged" --destination "$scratch/ledger"
```

核对两个实际 PCF 样本可执行 `scripts/probe_exchange_etf_pcf.py --verify <快照目录>`。程序根据独立交易日历选择下一交易日，核对代码、估值日、清单日期、货币和申赎单位净值。行情收报和交易所公告口径保留在对应原始快照。
