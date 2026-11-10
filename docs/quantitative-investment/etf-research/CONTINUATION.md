# 自主接续入口

更新于 2026-11-10 收盘前，北京时间。每次接手先核实 GitHub redesign-pc 分支、Ubuntu 活动检查点和最近一次已封存操作。

## 当前进度

[多因子 514 个两年低收益窗口](reports/2026-11-10-multifactor-shortfall/README.md)按相同起点对照一次建仓，核对退出股票、费用和滑点的贡献，并回放最大差距期间的翻票。

[四种方式逐日起点对比](reports/2026-11-10-multifactor-windows/README.md)提供相同本金和费用下的一年、两年结果。点开最差一期，可核对多因子哪些票改变、股票和国债次日成交多少。

[多因子 v1 历史回放](reports/2026-11-10-multifactor/README.md)每日按趋势、股债强弱和波动表决；看板及 Agent 可查询收盘投票、次日目标与模拟成交。

[三批为何多亏 821.26 元](reports/2026-11-10-method-gap/README.md)逐日核对 244 个收盘、两只 ETF 和两套账户。看板可按日期点开持仓、价格与费用，Agent 同参数可查。

[三种投资方式逐日起点与同区间成交对照](reports/2026-11-10-method-windows/README.md)提供沪深300与国债相同起点的 1 年、2 年满期窗口统计及交易原因。

[投资方式与买卖规则](reports/2026-11-10-investment-methods/README.md)包括一次建仓、按月分批和 120 日趋势的买卖条件、图上成交标记和 Agent 参数。

[逐日模型回放](reports/2026-11-10-model-replay/README.md)已接入工作台。可按日查看建仓与月度信号、开盘模拟订单、当日和累计盈亏，Agent 可按相同步数读取。


| 用途 | 已核验范围 | 入口 |
|---|---|---|
| 前瞻账户 | 11-05 至 11-09，3 个收盘，18 户，1,173 个行情输入日。月度 50/50 基准账户 100,141.58 元，11-09 当日 +74.10 元 | [活动检查点](config/active_run.json)、[远端复算](reports/2026-11-10-forward-handoff/README.md) |
| 场内人民币日 K | 四只 ETF 均核至 2026-11-09。两只跨境 ETF 在 10-30 后各补入 6 个交易日 | [逐只覆盖与缺口](reports/2026-11-10-market-coverage/README.md) |
| 自定义历史回测 | 收益结算上限 2026-10-30。仅沪深300、国债可从 2018-09-14 起；恒生可从 2019-01-02 起；含标普的组合可选 2019-01-02～2022-03-28 或 2022-03-30 起。[早期行情与证据](reports/2026-11-10-earlier-history/README.md) | [适用区间](reports/2026-11-10-markets-2022/README.md)、[逐日归因](reports/2026-11-09-daily-gap/README.md) |

范围为研究模拟，不使用真实资金。用 1～2 年评估长期年化净收益 4%～5% 的可行性，不为达到目标调参。保留冻结协议、旧目标和原始证据。1,967 日历史样本、162 个固定场景及旧 640/1,167 日结果分别可查。前瞻从真实观察日起算。11 月 6 日目标生成于 09:15；模拟成交与实际成交证据分开记录。

## 下一步顺序

1. 先读 AGENTS、README、PROJECT_PLAN、DATA_SOURCES、[原规划对照](docs/PLAN_ALIGNMENT.md)、PROTOCOL_V1 及研究、风险扩展配置。检查远端最新提交，执行 `python verify_snapshot.py` 和 `python scripts/verify_project.py`。最新静态清单在 `reports/2026-11-10-multifactor-shortfall/manifest.json`，旧清单在相应提交核验。
2. 依据活动检查点、独立日历和北京时间确定下一完整交易日。11 月 9 日的定时接续已验收，前六次日期不齐的尝试均留证，17:10 的新快照通过。后续交易日 16:00 后核验多源行情、日历、分红和公告。按实际日期运行 `python scripts/check_session_transition.py --day YYYY-MM-DD --require-timer`，核对运行来源、旧前缀、18 户权益及新增交易。
3. 推进跨境收益回测前先补齐相应日期的公告与执行约束。继续寻 13 次分红的正式逐日除息参考价、独立盘中停复牌与有披露日期的持仓证据，缺项保留未知。外部提醒、ETF 估值因子及 2027 年正式交易日历仍待完成。
4. 按 6、12、24 个月观察点累计前瞻结果（最早 2027-05-05、2027-11-05、2028-11-05）。风险阈值仅用于报告。Backtrader 对照覆盖 162 场景，精确现金边界仍有差异，继续保留冻结引擎。

## 运行、失败与交接

- 使用独立 Ubuntu。每日、健康、归档三个用户定时器以实际运行记录为准。每日入口在北京时间 16:10、16:40、17:10 检查。境内行情接已核验账户更新，跨境行情按单独快照核验。内网看板与 GitHub 静态文件的日期分别核实。
- `config/active_run.json` 指向同一封存包内的账户、页面和分析配置。基础 `config/research.json` 默认对应固定研究报告，新增前瞻输入必须显式指定。
- 来源失败或公告变化保留新快照并阻断准入。运行 review_catalog.py 生成审阅包。未封存中断与已封存未发布的恢复方法见[每日运行手册](docs/DAILY_PIPELINE.md)。保留证书校验和有界 IPv4 重试。
- 先增量取回 Ubuntu 新证据和对应活动指针。运行目录切换按[闭环手册](docs/OPERATIONS_CLOSURE.md)协调定时器。恢复到新目录并核对 SHA256 和账本，避免旧归档覆盖活动数据。仅提交本轮授权的公开产物，推送原分支并从远端读回，不提交凭据和私人资料。项目是重建后持续保存的版本。

[项目计划](PROJECT_PLAN.md) · [数据来源](DATA_SOURCES.md) · [13 份上层规划](docs/original-plan/sources.json) · [整理前的完整阶段记录](https://github.com/weiaijie/blog/blob/8ebb6b51c6510308fa0b4da81dd7afd07fb420b3/docs/quantitative-investment/etf-research/CONTINUATION.md)
