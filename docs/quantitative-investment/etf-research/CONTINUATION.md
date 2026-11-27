# 自主接续入口

[原 18 户凌晨归档恢复](reports/2026-11-28-forward-archive-readback/README.md)已实际恢复 11 月 28 日 01:16 生产快照，检查点与 Ubuntu 和 GitHub 一致。

[盘前封存特征复算](reports/2026-11-28-decision-replay/README.md)补齐了按原始截止和计算时间核对输入、证据与各版准入状态的入口。已用生产隔离副本和公开证据分别复算 9 个已就绪字段。

[GitHub 证据链核验与恢复](reports/2026-11-28-observation-publication-catalog/README.md)已核对基础包和首批定时增量，可逐批比较 Ubuntu 与公开发布，并从 GitHub 复算原时点报告。

[政策事件去重复验](reports/2026-11-28-policy-event-identity/README.md)已核对原文修订、转载与审核时点。工作台和 Agent 同查事件原文。首批 11 个已审核版本归为 1 个独立事件与 1 条关联公告，政策覆盖仍为 0/5 个区间。

[18 户到期检查点与回执](reports/2026-11-28-forward-milestone-publication/README.md)按首次正式发布的到期原件核算，并逐项核对后来账本的同一时期。工作台和 Agent 同查。

[工作台与 Agent 的跨年日历证据](reports/2026-11-28-exchange-calendar-evidence-view/README.md)展示定时归档、手工复核和正式登记状态。2027 年仍待两家交易所原文。

[年度休市公告自动发现](reports/2026-11-28-exchange-calendar-discovery/README.md)接上沪深交易所两条正式渠道。2026 正对照复算一致，2027 保留待核验状态。

[五日标签统一绑定盘前决策](reports/2026-11-28-observation-label-decision-binding/README.md)按实际封存时间同步标签调度、覆盖接口和工作台。错版标签保留并等待正确的核验结果。

[盘前输入对无响应重试的处理](reports/2026-11-28-observation-transport-recovery/README.md)按两次归档校验依据，展示可安全沿用的单项和失败来源。真实盘前探查当前有 9 项可核验。

[夜间导出水位保护](reports/2026-11-28-observation-export-watermark/README.md)可识别最新批次目录整批丢失。已用首批生产数据和 GitHub 原件验证按原水位恢复。

[夜间证据包全链核验](reports/2026-11-28-observation-export-audit/README.md)在每次增量前检查所有旧包对象，出现损坏时保留失败记录。首个生产包已隔离恢复，单日与来源响应按原时点复算一致。

[沪市两融明细按实际分页采集](reports/2026-11-28-sse-margin-pagination/README.md)保留所有必需明细页及失败响应。11 月 28 日 00:16 复核，11 月 27 日两融仍缺，11 月 26 日完成两页及汇总核验。

[首个合格归档的起算登记](reports/2026-11-28-observation-origin-pin/README.md)保存首份回执的原始字节，并纳入夜间证据包。回执缺失或变化须先恢复原证据。

[五交易日预登记](PROTOCOL_OBSERVATION_V1.md)已接上[真实归档特征组装](reports/2026-11-27-observation-inputs/README.md)和[政策候选审核与覆盖核验](reports/2026-11-27-policy-review/README.md)。首批 10 份中归并出 1 个独立事件，决策区间覆盖不足时政策输入留空。[08:55 前自动封存](reports/2026-11-27-decision-seal/README.md)已通过两次真实数据试跑和恢复。[看板与 Agent 决策覆盖](reports/2026-11-27-decision-coverage/README.md)已同源。[开盘取证与五交易日标签](reports/2026-11-27-five-session-labels/README.md)已接通定时任务。[标签覆盖](reports/2026-11-27-label-coverage/README.md)已接到看板和 Agent。[训练与预测封存](reports/2026-11-27-model-forecast/README.md)已接通并通过隔离演练。[训练和预测进度](reports/2026-11-27-forecast-coverage/README.md)已接到看板和 Agent。[样本外统计和经济对照](reports/2026-11-27-oos-evaluation/README.md)已接通。[评估覆盖](reports/2026-11-27-evaluation-coverage/README.md)可在看板和 Agent 同查。[月度覆盖与连续缺口](reports/2026-11-27-monthly-coverage/README.md)已接入。[跨年日历接续](reports/2026-11-27-calendar-handoff/README.md)已完成双源解析及新年度准入演练，等待 2027 年正式证据。[晚间政策审核、定时证据与首次标签检查](reports/2026-11-27-policy-runtime/README.md)记录了关联公告及实际定时证据。[晚间审核生产回读](reports/2026-11-27-policy-followup-verified/README.md)确认 11 个已审版本、1 个独立事件及 1 条关联公告。[盘前和开盘时点](reports/2026-11-27-morning-clock/README.md)已完成双触发隔离验收。[首次例行评估](reports/2026-11-27-first-live-evaluation/README.md)已通过回读、按时点重算及恢复。首日[单日原始响应与披露时点](reports/2026-11-27-source-availability/README.md)在看板与 Agent 同查。[独立前瞻证据包](reports/2026-11-27-portable-observation/README.md)已导出，可从 GitHub 恢复同一截至时点的采集、审核和评估台账。21:05 首次月度检查已由 systemd 实际触发并成功退出，11 月尚待封存。[首 20 个应采交易日连续性](reports/2026-11-27-observation-continuity/README.md)已可按实际回执核查。[政策待审队列](reports/2026-11-27-policy-queue/README.md)已按原文版本连通看板和 Agent。[报送截止前后取证](reports/2026-11-27-after-filing/README.md)取得 11 月 27 日国债 ETF 单位净值，并保存按时点复核证据。[证据增量定时导出](reports/2026-11-27-observation-export/README.md)已启用，每日 22:20。[首批自动封存](reports/2026-11-27-automatic-portable-observation/README.md)已在 Ubuntu 运行并完成证据复算。[22:23 清算份额补齐与两融下载对照](reports/2026-11-27-cleared-shares/README.md)已归档。[前瞻起算定时归档核验](reports/2026-11-27-observation-origin/README.md)已接入。资料完整、systemd 计划时点及归档对象均须通过核对后，才以实际归档日作为观察起点。 [11 月 27 日前瞻检查点与收盘输入复验](reports/2026-11-27-forward-publication/README.md)已对齐 GitHub 默认检查点并核对盘前研究可引用的收盘证据。[空重试与盘前已有证据](reports/2026-11-27-retry-evidence/README.md)已验证空失败后仍能按原时点使用同日资料。[月结并入夜间归档](reports/2026-11-27-monthly-export/README.md)已用真实采集证据完成隔离恢复。[结题证据分流](reports/2026-11-27-final-evidence-gate/README.md)已补上损坏归档与有效缺证样本的区分。[18 户按真实发布时点回看](reports/2026-11-27-forward-asof/README.md)已用实际补发和当天发布回执核验。[独立研究运行健康](reports/2026-11-27-independent-runtime-health/README.md)可查看九项计划及实际运行。[政策部分缺证时的原文待审](reports/2026-11-27-policy-partial-review/README.md)可在工作台与 Agent 同查。继续核对 08:25 两融、首个合格日、12 月 1 日首份月结及其夜间增量与首个交易日的盘前窗口。

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

- [当前进度](docs/CURRENT_STATUS.md)集中维护完成与缺口；[前瞻已至 2026-11-27](reports/daily/20261127T170315-58f85234/forward_checkpoint.json)，18 户共有 17 个收盘估值和 16 个收益区间。[6、12、24 个月复盘口径](reports/2026-11-27-forward-milestones/README.md)可在总览与 Agent 查看。回测新增 11-26 版，四个先前版本可复现。
- [新版工作台](docs/WORKBENCH_PLAN.md)使用Vue/TypeScript/Vite，人工和Agent共用参数。服务根路径及/workbench/为新版，/market.html与/backtest.html保留旧入口。内网地址http://10.1.1.120:18766，未确认公网部署。
- [321个ADX落后窗口](reports/2026-11-12-adx-shortfall/README.md)已逐窗对账。270个短空档窗口只覆盖两次实际事件；事后取消诊断不能作为可执行规则。
- 多源行情、公告、日历、分红核验继续阻断不合格更新，不覆盖旧快照，不使用真实资金。

2026-11-13：[近期版准入报告](reports/2026-11-13-recent-data/README.md)固定数据版本verified-2026-11-12，v2 API与v1隔离，旧方案迁移保持冻结数据。后续扩展须新增证据版本、保留旧快照与接口复现边界；不原地改动此版日期或默默切换已保存方案。

2026-11-13补充：[新增9天的版本对比](reports/2026-11-13-data-change/README.md)已在/workbench/#/changes上线。七种境内模型与四组跨市场基准各增9个一年/两年窗口；旧到期结果与最差盈亏不变，新增停牌对这些满期统计影响0。另列短期拦单对照，严禁将其计入满期成绩或当作现实可成交收益。

2026-11-14补充：[新增9个两年窗口归因](reports/2026-11-14-new-window-attribution/README.md)固定上轮9个新增两年窗口，多因子3期达标、一次建仓0期；加回原成交成本为6期/0期。按ETF、全债状态和逐日账户拆分，看板/workbench/#/changes/attribution与Agent同源。前瞻已自动接续至11-13，不混入本次11-12版本分析。

## 接手顺序

1. 读取AGENTS、README、PROJECT_PLAN、DATA_SOURCES、docs/PLAN_ALIGNMENT、config/research.json、PROTOCOL_V1。核对远端和当前北京时间。
2. 执行verify_snapshot.py与scripts/verify_project.py。最新静态清单为reports/2026-11-27-policy-partial-review/manifest.json；旧清单在相应提交验证。
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
