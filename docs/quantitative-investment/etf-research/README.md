# 个人量化投资研究系统

研究中国股票ETF 510300和债券ETF 511010，用1～2年评估长期年化净收益4%～5%可行性。仅研究模拟，不接实盘、不保证收益、不为目标调参。当前是重建后持续保存的项目，不能称找回旧系统。

## 当前事实（2026-11-07）

- [162 个场景的独立信号与目标审计](reports/2026-11-07-signal-audit/PROGRESS.md)核对 7,857 批目标及 11 月 6 日已封存的 18 个账户计划。

- [18 个历史账户的滚动风险预警](reports/2026-11-07-rolling-risk/PROGRESS.md)列出 7 条规则的首次越线、全部区间和期末未解除清单。

- [回撤恢复和披露变化](reports/2026-11-07-recovery/PROGRESS.md)覆盖18个历史账户及两次已公布的持仓。

- [主组合历史年报及季报](reports/2026-11-07-period-review/PERIODS.md)和[新增交易日验收说明](reports/2026-11-07-period-review/PROGRESS.md)已归档，覆盖18个历史账户774条期间记录。

- [本轮日报与13次除息证据](reports/2026-11-07-daily-evidence/PROGRESS.md)：日报合并同一期国债；18个历史与18个前瞻账户分别生成股债基准月报。13次正式除息价仍未知。

- [历史净收益与成交价核查](reports/2026-11-07-historical-pnl/PROGRESS.md)覆盖162个冻结场景、6,674笔模型成交和18个账户的逐日净值。
- 独立历史1967日，2018-09-14至2026-10-30，13次官方分红、162固定场景。50/50基准费用年化约4.02%、最大收盘回撤约19.73%；旧640日4.90%及1167日0.51%结果保留，起点敏感，未证明目标成立。
- 前瞻输入1172日，截至11月6日，真正前瞻2日。18组合21笔模型交易，主观察净值100067.48元、总收益0.06748%；8笔模型价超日线范围，不是实际成交证据。短样本不展示年化。
- 冻结Python引擎保留；Backtrader 162场景执行对照通过声明容差，但现金边界有拒单反例，暂不迁移。
- 风险监控、Beta、固定压力测试和官方季度披露代理已实现；完整当前持仓/集中度仍未知。
- Ubuntu每日采集已启用，16:10/16:40/17:10执行；IPv6路径TLS超时由采集器IPv4解决，证书及严格准入不变。此前5轮当日试验不能证明跨交易日长期稳定。

运行闭环阶段已完成：独立健康检查与每日归档已启用，201项基础测试、归档恢复和桌面/手机验收通过；公告审核记录仍不自动放行数据。

## 当前入口

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

可选框架对照另装requirements-backtrader.txt。历史报告和原始快照不覆盖；最新静态清单见reports/2026-11-07-signal-audit/manifest.json，动态状态另对照封存记录。旧阶段清单应在相应Git提交验证。历史建设记录见[历史计划](docs/history/PROJECT_PLAN-before-closure-20261106.md)。

最新研究证据审计见[报告](reports/2026-11-06-research-audit/PROGRESS.md)与[离线页面](site/research-audit.html)：57,726个一年/两年连续窗口、255个现金新账户；历史50/50两年窗口中位年化约3.71%，不支持稳定达标结论。完整中期股票339项及债券跨市场代码归并已核对，当前实时全持仓仍未知。新增复现：`python scripts/reproduce_research_audit.py`。
