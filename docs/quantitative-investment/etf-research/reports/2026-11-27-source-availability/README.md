# 首日采集的原始响应与披露时点

在工作台「政策研究 → 前瞻数据覆盖」点开交易日，展开「最近一次归档的原始响应」。Agent 从 `GET /api/v1/research/observation?day=YYYY-MM-DD` 读取同一份 `session.latestSourceEvidence`，可按原始 URL、收报时刻、请求日期、返回日期和 SHA256 复核。只在单日详情读取最近一次通过回执核验的归档。内容缺失或校验不符时对应响应标为待核验。HTTP 状态及返回日期用于定位问题，特征准入仍走原有的份额、净值、两融对账和时间门槛。

## 2026-11-27 实证

北京时间 19:54 的生产归档已有上交所股票成交、510300 两个估值日管理人净值和政策原文索引。剩余响应如下，可从[单日 Agent 证据](original-responses.json)逐条核对。

| 来源 | 19:54 生产归档 | 21:00 手工复查 |
| --- | --- | --- |
| 上交所 ETF 清算份额 | HTTP 200，11 月 27 日零行 | 相同原始响应 |
| 511010 管理人 PCF | 11 月 30 日清单返回 HTTP 404，无法由此核验 11 月 27 日单位净值 | 相同原始响应 |
| 沪市两融汇总 | HTTP 200，仅返回 11 月 26 日 | 相同原始响应 |
| 沪市两融明细 | HTTP 200，两页均零行 | 相同原始响应 |
| 510300 管理人净值 | HTTP 200，11 月 26 日与 27 日均有 | 三次请求均未收到 HTTP 响应（curl 52），已取得的生产归档可继续复核 |

21:00 取证保留实际连接失败和原始响应，未进入生产准入台账。上交所有效业务指南规定会员可在交易日 22:00 前覆盖报送，交易所于各交易日开市前公布相关数据。该条款提供核对时段，首报时刻仍以系统实际抓取为准。[21:00 原始请求](../../data/snapshots/20261127-disclosure-availability/scheduled-input-probe-2100/requests.json) · [上交所业务指南](https://www.sse.com.cn/lawandrules/guide2025/stock/jyglywznylc/zn/c/c_20230404_10797853.shtml)

国泰基金公开产品页实测可读。该页面所用 JavaScript 中 511010 净值日期只有 `07/27`，缺少年份及对应估值日证据，官网净值查询内嵌表返回 HTTP 404。继续由原 PCF 确认 511010 同估值日单位净值，首次确定时间以生产归档为准。[国泰产品页证据](../../data/snapshots/20261127-disclosure-availability/fund-product-links/requests.json) · [净值配置响应](../../data/snapshots/20261127-disclosure-availability/fund-nav-page/requests.json) · [内嵌表响应](../../data/snapshots/20261127-disclosure-availability/fund-nav-table/requests.json)

[11 月 26 日完整手工归档](complete-control.json)作为正对照。6 条响应都含所需日期，其中清算 938 行、两融明细两页合计 2,019 行。手工采集的资格仍为否。

1366 px 与 390 px 均打开单日响应面板，核对了六条记录、日期与 HTTP 状态。页面与 Agent 指向同一归档。归档对象被篡改的测试确认能识别为待核验，单个对象失败仍保留其余响应。

## 首次月度任务

北京时间 21:05 定时器首次触发，服务退出码 0，月报接口同时显示开放状态，1 个应采日期、0 个完整合格日。任务本次未生成定稿。待 11 月 30 日对应的下一交易日 08:55 取证截止，按现有调度最早在 12 月 1 日 21:05 封存。[实际运行回执](monthly-first-invocation.json)
