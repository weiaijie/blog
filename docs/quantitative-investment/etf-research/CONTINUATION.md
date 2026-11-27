# 自主接续入口

[五交易日预登记](PROTOCOL_OBSERVATION_V1.md)已接上[真实归档特征组装](reports/2026-11-27-observation-inputs/README.md)和[政策候选审核与覆盖核验](reports/2026-11-27-policy-review/README.md)。首批 10 份中归并出 1 个独立事件，决策区间覆盖不足时政策输入留空。[08:55 前自动封存](reports/2026-11-27-decision-seal/README.md)已通过两次真实数据试跑和恢复。[看板与 Agent 决策覆盖](reports/2026-11-27-decision-coverage/README.md)已同源。[开盘取证与五交易日标签](reports/2026-11-27-five-session-labels/README.md)已接通定时任务。[标签覆盖](reports/2026-11-27-label-coverage/README.md)已接到看板和 Agent。[训练与预测封存](reports/2026-11-27-model-forecast/README.md)已接通并通过隔离演练。[训练和预测进度](reports/2026-11-27-forecast-coverage/README.md)已接到看板和 Agent。[样本外统计和经济对照](reports/2026-11-27-oos-evaluation/README.md)已接通。[评估覆盖](reports/2026-11-27-evaluation-coverage/README.md)可在看板和 Agent 同查。[月度覆盖与连续缺口](reports/2026-11-27-monthly-coverage/README.md)已接入。接续验收首份例行评估、首个合格日及 12 月 1 日的首次月度封存。

工作台 `/workbench/#/policy` 和 Agent `/api/v1/research/policy-pilot` 可核对政策事件与首批官方市场样本。两事件缺历史收报及处理时间，历史时点查询保留空结果。[首期验收、口径与后续](reports/2026-11-27-policy-pilot/README.md)

已核对模拟交易、前瞻、风控、回测与运维共 34 项。[功能清单与验收证据](reports/2026-11-27-system-audit/README.md)

11 月 24–26 日的 18 户前瞻账户已逐日重放并恢复，四只 ETF 的回测数据核验至 11 月 26 日。[审核、日报与回测准入](reports/2026-11-27-admission/README.md)

11 月 23 日的四只 ETF 已准入独立回测版本，18 个前瞻账户完成第 13 个交易日。[11 月 24 日核验报告](reports/2026-11-24-admission/README.md)

2026-11-23：[11月12日与20日版结果对比](reports/2026-11-23-six-session-change/README.md)覆盖七个模型、四组基准与132个新增到期结果。三次标普开盘停牌对满期结果影响为零，六笔未满期建仓拦单另列。看板入口为 `/workbench/#/changes/nov20`，Agent 使用 v3 对比接口。

2026-11-22：[六日回测准入](reports/2026-11-22-admission/README.md)已将四只 ETF 的独立数据版本及 K 线延至 11-20；11-12、10-30 版可复现。前瞻至 11-20，18 户共 12 个交易日。

2026-11-20 上午：[四只 ETF 收盘行情](reports/2026-11-20-quote-refresh/README.md)已三源核对至 11-19，固定回测仍至 11-12；后续补公告、停复牌、分红折算与成交量证据。

2026-11-19：新增[策略中心](reports/2026-11-19-strategy-catalog/README.md)，7 个模型与 4 个市场基准可搜索并按报告参数回放。[二维关系图](reports/2026-11-19-strategy-graph/README.md)现已接入，可按因子、模型和实验逐层查看并直接回放。

先核对GitHub redesign-pc最新提交、Ubuntu活动指针及封存记录，不依赖旧聊天。仓库项目目录为docs/quantitative-investment/etf-research，独立Ubuntu运行副本为/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research。

## 当前事实

- [当前进度](docs/CURRENT_STATUS.md)集中维护完成与缺口；前瞻已至 2026-11-26，18 户累计 16 个交易日。回测新增 11-26 版，四个先前版本可复现。
- [新版工作台](docs/WORKBENCH_PLAN.md)使用Vue/TypeScript/Vite，人工和Agent共用参数。服务根路径及/workbench/为新版，/market.html与/backtest.html保留旧入口。内网地址http://10.1.1.120:18766，未确认公网部署。
- [321个ADX落后窗口](reports/2026-11-12-adx-shortfall/README.md)已逐窗对账。270个短空档窗口只覆盖两次实际事件；事后取消诊断不能作为可执行规则。
- 多源行情、公告、日历、分红核验继续阻断不合格更新，不覆盖旧快照，不使用真实资金。

2026-11-13：[近期版准入报告](reports/2026-11-13-recent-data/README.md)固定数据版本verified-2026-11-12，v2 API与v1隔离，旧方案迁移保持冻结数据。后续扩展须新增证据版本、保留旧快照与接口复现边界；不原地改动此版日期或默默切换已保存方案。

2026-11-13补充：[新增9天的版本对比](reports/2026-11-13-data-change/README.md)已在/workbench/#/changes上线。七种境内模型与四组跨市场基准各增9个一年/两年窗口；旧到期结果与最差盈亏不变，新增停牌对这些满期统计影响0。另列短期拦单对照，严禁将其计入满期成绩或当作现实可成交收益。

2026-11-14补充：[新增9个两年窗口归因](reports/2026-11-14-new-window-attribution/README.md)固定上轮9个新增两年窗口，多因子3期达标、一次建仓0期；加回原成交成本为6期/0期。按ETF、全债状态和逐日账户拆分，看板/workbench/#/changes/attribution与Agent同源。前瞻已自动接续至11-13，不混入本次11-12版本分析。

## 接手顺序

1. 读取AGENTS、README、PROJECT_PLAN、DATA_SOURCES、docs/PLAN_ALIGNMENT、config/research.json、PROTOCOL_V1。核对远端和当前北京时间。
2. 执行verify_snapshot.py与scripts/verify_project.py。最新静态清单为reports/2026-11-27-monthly-coverage/manifest.json；旧清单在相应提交验证。
3. 核实三个用户定时器与site/health_status.json。静态Git文档不代表主机当前状态；未满252收益的风险指标留空，前瞻不借历史补齐。
4. 前端改动先在隔离目录/端口验证，npm ci、npm test、npm run build；维护frontend源码与site/workbench构建产物、归档清单和静态清单。只构建不运行测试不能称验收完成。
5. 研究下一步按PROJECT_PLAN执行：少量新规则先立协议、保留原版与失败区间。已观察历史不能重新标记成未见样本。
6. 若有新的完整交易日，北京时间16:00后采集新快照，多源价格、独立日历、分红与公告全部通过才续接旧检查点。执行check_session_transition.py --day YYYY-MM-DD --require-timer。时间到不等于来源已合格。

## 部署与持久化

- 独立Ubuntu，禁止回退WSL。运行Python为/home/ubuntu/projects/etf-research-py312/bin/python。
- 部署前按[运行闭环手册](docs/OPERATIONS_CLOSURE.md)暂停daily/health/archive三个timer，等服务结束，先取回新增公开证据。只部署本轮文件；config/active_run.json、site/operation_status.json、site/health_status.json不能用旧Git副本覆盖。
- 验证后重启本项目dashboard服务、恢复三个timer，检查enabled/active、页面/API和活动账户哈希。不得动其他服务。
- config/research.json控制固定监控输入，不是冻结策略总开关。新前瞻报告必须显式使用新检查点。
- 完成后中文提交到原分支、推送、远端读回核验。交付使用GitHub链接，不提供本地备份路径；不提交凭据和私人资料。

旧完整接续保留于 [历史接续](docs/history/20261112-before-workbench-CONTINUATION.md)；原计划归档位于docs/original-plan。此项目是重建后持续保存的版本。
