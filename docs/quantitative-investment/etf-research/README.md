# 个人量化投资研究系统

[2019～2021 年跨境历史准入](reports/2026-11-10-earlier-history/README.md)新增 730 个交易日。恒生配比可从 2019-01-02 连续运行；含标普的组合保留拆分前后两段独立账户。

[三种投资方式逐日起点与同区间成交对照](reports/2026-11-10-method-windows/README.md)提供沪深300与国债相同起点的 1 年、2 年满期窗口统计及交易原因。

[投资方式与买卖规则](reports/2026-11-10-investment-methods/README.md)包括一次建仓、按月分批和 120 日趋势的买卖条件、图上成交标记和 Agent 参数。

[逐日模型回放](reports/2026-11-10-model-replay/README.md)已接入工作台。可按日查看建仓与月度信号、开盘模拟订单、当日和累计盈亏，Agent 可按相同步数读取。


[2022 年跨境 ETF 事件与回测](reports/2026-11-10-markets-2022/README.md)：恒生可从 2022-01-04 起；标普可选 01-04 至 03-28，或从 03-30 起。03-29 为拆分停牌。

11 月 9 日 17:10 定时接续成功。[核验记录](reports/2026-11-10-forward-handoff/README.md)包含两个来源的行情、官方收盘对照和 18 个模拟账户的第 3 个前瞻交易日。

研究中国股票ETF 510300和债券ETF 511010，用1～2年评估长期年化净收益4%～5%可行性。仅研究模拟，不接实盘、不保证收益、不为目标调参。当前是重建后持续保存的项目，不能称找回旧系统。

## 当前事实（2026-11-10）

[行情覆盖与数据缺口](reports/2026-11-10-market-coverage/README.md)：行情页四只 ETF 均已核到 11 月 9 日。历史自定义回测截止 10 月 30 日，前瞻账户独立累计。

[历史行情与回测覆盖](reports/2026-11-09-history-coverage/README.md)：四只 ETF 的日 K 可追溯至 2018 年 9 月，含跨境 ETF 的共同回测从 2023-01-03 起，纯境内股债配比从 2018-09-14 起。

[同区间逐日盈亏差额](reports/2026-11-09-daily-gap/README.md)提供累计差额曲线、增加和减少最多的交易日与逐日 ETF 明细，看板和 Agent 共用同一份结果。

[同区间盈亏归因](reports/2026-11-09-overlay-attribution/README.md)已接入看板和 Agent，可核对整个持有期和所选组合前高至谷底的逐 ETF 价格、分红、佣金及滑点。示例 B 相对 A 分别少亏 935.13 元和 2,310.40 元。

[同区间净值与回撤叠图](reports/2026-11-08-same-window/README.md)可按所选组合最差一期的日期重放所有配比，对比到期盈亏、最大回撤和收复前高日期。

[两至三套自定义配比并排比较](reports/2026-11-08-compare-windows/README.md)支持共享参数、两个持有期的逐项对照与各自最差期回放。

[自定义配比逐日起点回测](reports/2026-11-08-custom-windows/README.md)支持在所选区间同时统计一年、两年满期结果，并查看最差一期的逐日回撤。

[自助回测及 Agent 调用说明](reports/2026-11-08-interactive-backtest/README.md)支持任意区间、本金、配比、调仓和费用，生成收盘回撤曲线。

[每个交易日起步的持有期研究](reports/2026-11-08-entry-windows/README.md)已核算四组独立建仓的一年、两年到期盈亏与年化达标次数，可在[回测看板](site/backtest.html#entries)切换查看。

[历史模型回测面板](site/backtest.html)支持四组股债组合近 1、2、3 年与六种境内策略完整区间。按历史快照独立起账，17,630 条收盘记录逐日对账。[回放命令与结果](reports/2026-11-08-model-backtest/README.md)。

- [标普 ETF 剩余价差的逐日损益与公告核查](reports/2026-11-08-residual-events/PROGRESS.md)逐日核算两套期货口径，核对申赎清单、清算份额、停复牌登记与带日期的公开提示。
- [标普 ETF 高溢价日与收盘时差核验](reports/2026-11-08-close-timing/PROGRESS.md)覆盖 257 个高溢价日，另附 2025 年 2 月逐日行情与全区间人民币损益分解。
- [跨境 ETF 净值、折溢价、汇率与标普账户回撤归因](reports/2026-11-08-nav-fx/PROGRESS.md)已对账 1,456 个基金日期和标普组 72 段每日损益。

- [三地股票 ETF 与同一国债 ETF 的四组人民币模拟](reports/2026-11-08-three-markets/PROGRESS.md)提供一年、两年收益和回撤恢复时间、滚动窗口及同期持仓。

- [目标仓位偏离与三档执行延迟](reports/2026-11-08-position-delay/PROGRESS.md)覆盖 162 个历史账户场景。

- [162 个场景的独立信号与目标审计](reports/2026-11-07-signal-audit/PROGRESS.md)核对 7,857 批目标及 11 月 6 日已封存的 18 个账户计划。

- [18 个历史账户的滚动风险预警](reports/2026-11-07-rolling-risk/PROGRESS.md)列出 7 条规则的首次越线、全部区间和期末未解除清单。

- [回撤恢复和披露变化](reports/2026-11-07-recovery/PROGRESS.md)覆盖18个历史账户及两次已公布的持仓。

- [主组合历史年报及季报](reports/2026-11-07-period-review/PERIODS.md)和[新增交易日验收说明](reports/2026-11-07-period-review/PROGRESS.md)已归档，覆盖18个历史账户774条期间记录。

- [本轮日报与13次除息证据](reports/2026-11-07-daily-evidence/PROGRESS.md)：日报合并同一期国债；18个历史与18个前瞻账户分别生成股债基准月报。13次正式除息价仍未知。

- [历史净收益与成交价核查](reports/2026-11-07-historical-pnl/PROGRESS.md)覆盖162个冻结场景、6,674笔模型成交和18个账户的逐日净值。
- 独立历史1967日，2018-09-14至2026-10-30，13次官方分红、162固定场景。50/50基准费用年化约4.02%、最大收盘回撤约19.73%；旧640日4.90%及1167日0.51%结果保留，起点敏感，未证明目标成立。
- 前瞻输入1173日，截至11月9日，真正前瞻3日。18组合累计21笔模型交易，主观察总资产100141.58元、总收益0.14158%；8笔模型价超日线范围，不是实际成交证据。短样本不展示年化。
- 冻结Python引擎保留；Backtrader 162场景执行对照通过声明容差，但现金边界有拒单反例，暂不迁移。
- 风险监控、Beta、固定压力测试和官方季度披露代理已实现；完整当前持仓/集中度仍未知。
- Ubuntu每日采集已启用，16:10/16:40/17:10执行；IPv6路径TLS超时由采集器IPv4解决，证书及严格准入不变。此前5轮当日试验不能证明跨交易日长期稳定。

运行闭环阶段已完成：独立健康检查与每日归档已启用，201项基础测试、归档恢复和桌面/手机验收通过；公告审核记录仍不自动放行数据。

## 当前入口

[行情与进度看板预览及使用说明](reports/2026-11-08-market-view/README.md)。可查看四只 ETF 的日 K、主账户净值和下一次核验。

- [每日账户与运行健康页面](site/daily.html) · [接续说明](CONTINUATION.md) · [当前计划](PROJECT_PLAN.md)
- [运行手册](docs/DAILY_PIPELINE.md) · [归档恢复与公告审阅](docs/OPERATIONS_CLOSURE.md)
- [本轮闭环验收](reports/2026-11-06-closure/PROGRESS.md) · [原规划对照](docs/PLAN_ALIGNMENT.md)
- [独立历史研究](site/index.html) · [数据来源](DATA_SOURCES.md) · [冻结协议](PROTOCOL_V1.md)

页面文件保存在GitHub，未验收公网实时托管。Ubuntu未来输出先存持久目录，无自动Git推送、外部消息或实盘。当前账户以config/active_run.json指向的整包为准；默认监控配置仍对应固定11月6日报告，不能混用。

## 验证

计算与管线使用独立Ubuntu，已验证Python3.12.16；不使用WSL。

```sh
python -m pip install -r requirements-lock.txt
python scripts/verify_project.py
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/check_health.py
python scripts/reproduce.py
```

可选框架对照另装requirements-backtrader.txt。历史报告和原始快照不覆盖；最新静态清单见reports/2026-11-10-method-windows/manifest.json，动态状态另对照封存记录。旧阶段清单应在相应Git提交验证。历史建设记录见[历史计划](docs/history/PROJECT_PLAN-before-closure-20261106.md)。

最新研究证据审计见[报告](reports/2026-11-06-research-audit/PROGRESS.md)与[离线页面](site/research-audit.html)：57,726个一年/两年连续窗口、255个现金新账户；历史50/50两年窗口中位年化约3.71%，不支持稳定达标结论。完整中期股票339项及债券跨市场代码归并已核对，当前实时全持仓仍未知。新增复现：`python scripts/reproduce_research_audit.py`。
