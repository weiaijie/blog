# 11 月 27 日 ETF 清算份额补齐与两融下载核对

北京时间 22:05 取证时，11 月 27 日清算表仍返回零行。22:23:33，首次留存的有效完整表返回 938 行，包含 510300 和 511010。公开「ETF规模」页面也调用该接口并显示 11 月 27 日。具体首次公开时刻介于留存取证时点之间，仍未知。22:23:51 完成独立归档验证。 [早一轮证据](before.json) · [新一轮证据](after.json) · [上交所 ETF 规模栏目](https://www.sse.com.cn/market/funddata/volumn/etfvolumn/)

| 基金 | 11 月 26 日清算份额 | 11 月 27 日清算份额 | 份额变化 | 27 日单位净值（元） | 估算净申购金额（元） |
| --- | ---: | ---: | ---: | ---: | ---: |
| 510300 | 56,102,887,700 | 57,637,387,700 | +1,534,500,000 | 4.1397 | +6,352,369,650 |
| 511010 | 71,966,300 | 71,786,300 | -180,000 | 141.339 | -25,441,020 |

表内份额已从上交所万份转换为份。估算金额按份额变化乘本日单位净值计算。两只 ETF 均通过原有的份额、净值和折算依据校验。上表的输入、收报及归档时间可从原始文件重算。 [逐项对账](share-reconciliation.json) · [按日期取证与原始响应](../../data/snapshots/20261127-shares-and-margin/fresh/requests.json)

## 两融数据入口与口径

上交所「融资融券明细数据」页的下载入口已发现。22:25，11 月 26 日文件返回 HTTP 200 并可读取，11 月 27 日相同路径对应的文件返回 HTTP 404。按 11 月 27 日单独查询汇总接口为零行，联查两日仅返回 11 月 26 日，明细两页均为空。 [下载请求证据](../../data/snapshots/20261127-shares-and-margin/margin-download/requests.json) · [两融公开栏目](https://www.sse.com.cn/market/othersdata/margin/detail/index.shtml)

以 11 月 26 日对照，工作簿 6 个汇总字段与 API 一致。2,019 只证券代码一致，逐证券 6 个字段、共 12,114 项逐项相等。工作簿汇总表未列全市场融资偿还额，明细偿还合计为 61,675,320,065 元，当日 API 汇总偿还额为 61,724,016,978 元，差额为 -48,696,913 元。交易所说明汇总和明细的标的范围有差异，具体差额的逐证券归因仍未知。现行准入仍要求取得可核验的当日汇总和完整明细。 [工作簿与 JSON 对账](margin-download-reconciliation.json)

## 归档恢复

22:23 的取证记录为手工复查。独立研究仍为 1 个归档日、0 个合格日。增量包从 22:20 首批自动封存的水位起算，保留新增回执及其原始对象。11 月 28 日 08:25 继续正式定时采集。 [增量索引](pack/index.json) · [首批自动封存](../2026-11-27-automatic-portable-observation/README.md)

在 Ubuntu 的项目目录运行。

```bash
export PYTHONPATH=src
scratch=$(mktemp -d)
python scripts/pack_observation_evidence.py merge --pack reports/2026-11-27-portable-observation/pack --pack reports/2026-11-27-automatic-portable-observation/pack --pack reports/2026-11-27-cleared-shares/pack --output "$scratch/merged"
python scripts/pack_observation_evidence.py restore-ledger --pack "$scratch/merged" --destination "$scratch/ledger"
```

复算工作簿可在隔离环境安装 [xlrd 2.0.2](https://pypi.org/project/xlrd/2.0.2/#files)。验证所用官方 wheel 的 SHA256 为 `ea762c3d29f4cca48d82df517b6d89fbce4db3107f9d78713e48cd321d5c9aa9`。下载读取器用于可选对照。

```bash
python scripts/audit_sse_margin_workbook.py --snapshot data/snapshots/20261127-shares-and-margin/margin-download --archive-store reports/2026-11-27-portable-observation/pack/archive --archive 087b1492e77ab8721b55bfbda631293729ca09b4595ef3a5c9c3a77bf8052936 --day 2026-11-26
```
