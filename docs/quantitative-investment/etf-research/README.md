# 个人量化投资研究系统

已核对模拟交易、前瞻、风控、回测与运维共 34 项。[功能清单与验收证据](reports/2026-11-27-system-audit/README.md)

11 月 24–26 日的 18 户前瞻账户已逐日重放并恢复，四只 ETF 的回测数据核验至 11 月 26 日。[审核、日报与回测准入](reports/2026-11-27-admission/README.md)

11 月 23 日的四只 ETF 已准入独立回测版本，18 个前瞻账户完成第 13 个交易日。[11 月 24 日核验报告](reports/2026-11-24-admission/README.md)

2026-11-23：[11月12日与20日版结果对比](reports/2026-11-23-six-session-change/README.md)覆盖七个模型、四组基准与132个新增到期结果。三次标普开盘停牌对满期结果影响为零，六笔未满期建仓拦单另列。看板入口为 `/workbench/#/changes/nov20`，Agent 使用 v3 对比接口。

研究ETF配置与交易规则，以一至两年观察评估长期年化净收益4%～5%的可行性。仅研究模拟，不接实盘、不使用真实资金，不为达到目标调参。

## 从这里开始

- [新增9个两年窗口归因](reports/2026-11-14-new-window-attribution/README.md)：同起点比较多因子与一次建仓，逐日核对股票、国债、分红及费用。

- [新增9天前后的结果对比](http://10.1.1.120:18766/workbench/#/changes)：旧新赚钱/4%达标次数、最差盈亏及停牌条件影响。
- [当前进度与缺口](docs/CURRENT_STATUS.md)：数据、回测、模型、前瞻与原规划分别说明。
- [新版量化工作台](http://10.1.1.120:18766/workbench/)：总览、行情、模型回测、比较与报告；仅在可访问该Ubuntu内网地址的网络使用，未声明公网部署。
- [工作台操作与验收范围](docs/WORKBENCH_PLAN.md)：保存/恢复方案、逐日回放、最差期解释、Agent同参数请求。
- [自主接续](CONTINUATION.md)、[项目计划](PROJECT_PLAN.md)、[原规划逐项对照](docs/PLAN_ALIGNMENT.md)。
- [数据来源](DATA_SOURCES.md)、[冻结协议](PROTOCOL_V1.md)、[运行与恢复](docs/OPERATIONS_CLOSURE.md)。

截至本次交付，18 个前瞻账户已核验至 2026-11-26，共 16 个交易日。工作台可在研究设置中选择截至 10-30、11-12、11-20、11-23 或 11-26 的数据版本。最新运行状态见 Ubuntu 活动检查点及健康观察记录。

## 使用方式

在工作台右上角设置日期、本金、费用和配比。模型回放使用所选模型；配比比较与固定模型比较明确分开。方案默认只保存在当前浏览器，可导出JSON或生成链接，Agent请求清单由同一份参数生成并携带数据版本。旧方案恢复为原冻结样本；近期版含公告开盘停牌约束，见[近期数据准入与操作验收](reports/2026-11-13-recent-data/README.md)。

旧 [行情页](http://10.1.1.120:18766/market.html) 和 [完整研究页](http://10.1.1.120:18766/backtest.html) 保留。报告使用其自身归档参数，不能当作新方案运行结果。

## 本地验证

项目Python依赖见requirements-lock.txt；本次验证为Ubuntu Python 3.12.16。前端在frontend目录使用Node 22.12以上，执行npm ci、npm test、npm run build。

    python verify_snapshot.py
    python scripts/verify_project.py
    PYTHONPATH=src python -m unittest discover -s tests -v
    python scripts/reproduce.py

build_risk_report.py默认使用固定research.json，不会猜测最新前瞻目录；新检查点须显式指定输入。旧清单应在对应提交核验。

历史记录完整保留于 [整理前README](docs/history/20261112-before-workbench-README.md)。项目是重建后持续保存的版本，不声称恢复了最早旧项目。
