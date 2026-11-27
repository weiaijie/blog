# 五交易日标签与开盘取证

前瞻标签使用已核验交易日历固定五个交易日。每个窗口分别读取决定仓位的前收盘和五个持有日的三源日线发布记录，比较各版本的价格和分红，并校验前收盘版本与封存决定一致。第五日 16:00 后，所有依赖及归档核验通过才写入标签就绪时间。找不到所需证据时，保存缺口和回执。

## 开盘与计算口径

独立服务在北京时间 09:26 和 09:28 取上交所两只 ETF 快照，保存请求与响应、交易所时间、实际核验时间和归档哈希。已完成开盘集合竞价的行情须落在连续竞价前，并对上当日日线的开盘价。交易阶段明确显示停牌时记录拦单。冲突、迟到、开盘参考价异常以及无法确认的除息日期保留未知。交易时段及行情状态定义见[上交所交易规则](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml)和[上交所行情接口规范](https://big5.sse.com.cn/site/cht/www.sse.com.cn/services/tradingtech/development/c/10827383/files/4a5c0f16fef7493a81be3b5c420c1dab.pdf)。

标签复用已登记的模拟记账规则。输出 50/50 股债及 100% 国债在低、基准、高三档费用下的五个收盘净值、净收益、最大回撤、佣金、滑点和订单拦截原因。净值包含各日现金与应收分红。标签封存服务在 20:15 查已到期窗口，优先处理此前较少尝试的缺口。训练只能使用具备合格决策且已实际完成归档的结果。

## 真实历史证据验收

- 2026-11-23 入场的验证窗口，前收盘是 11 月 20 日，持有日为 11 月 23、24、25、26、27 日。六日行情全部验证。两只 ETF 均缺入场当日集合竞价快照，净收益与最大回撤留空。[价格时点与缺口](label-validation.json)
- 11 月 27 日 18:33 实际请求上交所快照，两只 ETF 均返回 HTTP 200。接口响应已封存并恢复复验，开盘条件因采集窗口已过保持未知。[试跑回执](../research-opening-probes/2026-11-27/20261127T103333Z-780ae021/receipt.json) · [归档清单](opening-probe-archive.json)
- 会计测试对同一批真实日线显式设定假设开盘条件，用现金、持仓、费用手工复算净值路径及回撤，并覆盖开盘阶段冲突、停牌、迟到、缺证和归档损坏。试跑均保存在验证范围，正式标签仍待首个窗口按期完成。

离线可在本提交的锁定 Python 环境复算验收窗口。

```bash
PYTHONPATH=src python scripts/observation_labels.py \
  --verify reports/2026-11-27-five-session-labels/label-validation.json \
  --price-project . --observation-root . \
  --archive-store reports/2026-11-27-observation-inputs/archive-proofs
PYTHONPATH=src python -m unittest discover -s tests -p test_observation_labels.py -v
```

后续核对首批例行开盘、首个独立合格归档和实际标签，接通标签进度、训练与预测封存。
