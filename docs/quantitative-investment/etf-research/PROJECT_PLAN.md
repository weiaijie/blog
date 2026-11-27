# 项目计划与当前状态

[18 户按真实发布时点回看](reports/2026-11-27-forward-asof/README.md)已接入工作台和 Agent。晚到补发按原发布时间进入历史查询。

[结题证据分流](reports/2026-11-27-final-evidence-gate/README.md)已接入工作台与 Agent，区分未就绪、校验失败与已核验的样本不足。

[月结并入夜间归档](reports/2026-11-27-monthly-export/README.md)已完成隔离验收，首份生产月报及对应增量仍待按日历触发。

[空重试与盘前已有证据](reports/2026-11-27-retry-evidence/README.md)已验证。只有无新增取证的失败回执允许继续取用同日先前核验资料。

[11 月 27 日前瞻检查点与收盘输入复验](reports/2026-11-27-forward-publication/README.md)对齐了公开仓库的默认检查点，保留发布时点与 18 户逐日复算证据。

[前瞻起算定时归档核验](reports/2026-11-27-observation-origin/README.md)已接入。资料完整、systemd 计划时点及归档对象均须通过核对后，才以实际归档日作为观察起点。

[22:23 清算份额补齐与两融下载对照](reports/2026-11-27-cleared-shares/README.md)已封存。11 月 27 日份额与单位净值可核验，两融继续保留未知。

[证据增量定时导出](reports/2026-11-27-observation-export/README.md)以已验的 GitHub 证据包为起点，逐次封存真实水位与新增回执。[首次自动执行](reports/2026-11-27-automatic-portable-observation/README.md)已在 22:20 产生生产证据包。

[两融报送截止前后取证](reports/2026-11-27-after-filing/README.md)记录国债 ETF 单位净值首次有效收报、官方申赎清单对照与按时点回看。

[政策待审队列](reports/2026-11-27-policy-queue/README.md)按官方 URL 和原文 SHA256 识别重复与修订，保留审核前后的真实时点。

[首 20 个应采交易日连续性](reports/2026-11-27-observation-continuity/README.md)已接入。区分实际归档、已核验定时时点和截止前完整数据。当前开始跟踪 1 日，首个截止待 11 月 30 日 08:55。

[18 户前瞻复盘](reports/2026-11-27-forward-milestones/README.md)已按同一检查点接入工作台和 Agent。当前显示 17 个估值日、16 个收益区间以及 6、12、24 个月的到期进度。

[独立前瞻证据包](reports/2026-11-27-portable-observation/README.md)已首批导出并通过离线恢复。后续按实际封存时点持续增补，至少覆盖采集、政策审核、决定、开盘取证、标签、训练、预测、评估和月度回执。

独立前瞻的[单日原始响应与披露时点](reports/2026-11-27-source-availability/README.md)可从看板和 Agent 查看。同一时点的回执区分空表、少日期、未取得响应与归档对象不完整。继续核对交易所清算、管理人净值、两融的首次正式可用时点和第一份完整定时归档。

[12 个月模型研究](docs/LONG_TERM_RESEARCH.md)已完成[真实归档特征回算](reports/2026-11-27-observation-inputs/README.md)和[首批政策审核及覆盖判定](reports/2026-11-27-policy-review/README.md)。[08:55 前自动封存](reports/2026-11-27-decision-seal/README.md)已通过真实证据的试跑和恢复。[看板和 Agent 同查决策进度](reports/2026-11-27-decision-coverage/README.md)。[开盘取证与五交易日标签](reports/2026-11-27-five-session-labels/README.md)已实测真实行情缺口和会计复算。[标签进度](reports/2026-11-27-label-coverage/README.md)已接到看板和 Agent。[训练与预测封存](reports/2026-11-27-model-forecast/README.md)已验证可按原时点重放。[训练和预测进度](reports/2026-11-27-forecast-coverage/README.md)已接到看板和 Agent。[样本外误差统计和经济对照](reports/2026-11-27-oos-evaluation/README.md)已核对时间和样本门槛。[样本外评估进度](reports/2026-11-27-evaluation-coverage/README.md)已接入看板与 Agent。[月度覆盖](reports/2026-11-27-monthly-coverage/README.md)增加连续缺口和月结归档。[跨年日历接续](reports/2026-11-27-calendar-handoff/README.md)已接到独立生产链路及原模拟账户数据准入。[晚间政策审核与定时证据](reports/2026-11-27-policy-runtime/README.md)覆盖关联事件和首批标签例行检查。[晚间审核生产回读](reports/2026-11-27-policy-followup-verified/README.md)已核对审核前后两个时点。[盘前和开盘时点](reports/2026-11-27-morning-clock/README.md)已通过双触发取证与错过窗口演练。[首次例行评估](reports/2026-11-27-first-live-evaluation/README.md)已实际封存并复算，观察起点仍为空。下一步核对合格日、生产窗口、月结及 2027 年交易所原文。正式观察起点等首个独立生产合格归档。

第 35–39、41 项已完成首批样本验证，详见[政策与市场数据首期验收](reports/2026-11-27-policy-pilot/README.md)。两条官方政策事件可做按时点准入核对，ETF 份额净值和沪市融资成交已有首批只读样本。接下来补连续取证、历史可用时间和市场广度，达到可比条件再验证第 40 项。第 42 项单独评估。

已核对模拟交易、前瞻、风控、回测与运维共 34 项。[功能清单与验收证据](reports/2026-11-27-system-audit/README.md)

11 月 24–26 日的 18 户前瞻账户已逐日重放并恢复，四只 ETF 的回测数据核验至 11 月 26 日。[审核、日报与回测准入](reports/2026-11-27-admission/README.md)

11 月 23 日的四只 ETF 已准入独立回测版本，18 个前瞻账户完成第 13 个交易日。[11 月 24 日核验报告](reports/2026-11-24-admission/README.md)

2026-11-23：[11月12日与20日版结果对比](reports/2026-11-23-six-session-change/README.md)覆盖七个模型、四组基准与132个新增到期结果。三次标普开盘停牌对满期结果影响为零，六笔未满期建仓拦单另列。看板入口为 `/workbench/#/changes/nov20`，Agent 使用 v3 对比接口。

2026-11-22：[六日回测准入](reports/2026-11-22-admission/README.md)已将四只 ETF 的独立数据版本及 K 线延至 11-20；11-12、10-30 版可复现。前瞻至 11-20，18 户共 12 个交易日。

2026-11-20 上午：[四只 ETF 收盘行情](reports/2026-11-20-quote-refresh/README.md)已三源核对至 11-19，固定回测仍至 11-12；后续补公告、停复牌、分红折算与成交量证据。

2026-11-19：新增[策略中心](reports/2026-11-19-strategy-catalog/README.md)，7 个模型与 4 个市场基准可搜索并按报告参数回放。[二维关系图](reports/2026-11-19-strategy-graph/README.md)现已接入，可按因子、模型和实验逐层查看并直接回放。

当前状态统一维护于 [CURRENT_STATUS](docs/CURRENT_STATUS.md)。本页列工作顺序，旧进度不再反复插入顶部。

## 当前交付：新增两年窗口的配对归因

[新增9个两年窗口归因](reports/2026-11-14-new-window-attribution/README.md)已逐窗核对9期、18个账户及每日差额，区分股票/国债价格与分红、全债阶段和交易成本；看板与Agent同源，不调整模型或冻结数据。

## 上轮交付：新旧数据版本结果对比

本轮新增[9天前后对比](reports/2026-11-13-data-change/README.md)：七种境内模型、四组跨市场基准的一年/两年旧新统计、198个新满期结果与停牌条件诊断，看板与Agent同源。最差盈亏均未刷新；本批满期统计没有新增停牌影响，不据此宣称停牌永远无影响。

工作台初版范围见[WORKBENCH_PLAN](docs/WORKBENCH_PLAN.md)；本轮结果见[近期数据与操作验收](reports/2026-11-13-recent-data/README.md)。

- 四只ETF新增9日三源核对，33份公告、6条标普开盘停牌登记核对；新增5天开盘成交限制，未知保留。
- 独立近期数据版本与v2接口，旧方案仍使用原版样本；桌面/手机与Agent同参数验收通过。

- 六个主页面与新增窗口归因子页面；版本对比采用明确固定参数，其余研究页面共享草稿参数；保存恢复、导入导出、复现链接及Agent请求。
- 原接口驱动逐日回放、投资方式及配比窗口比较、最差期交易因子和配比盈亏归因。
- 冻结引擎、旧策略、原始证据及18户前瞻账户不修改；旧专题仍可访问。

## 后续优先级

1. 连续留存政策事件的实际收报与处理时间，补齐 ETF 份额净值、两融及同口径市场成交，核对修订和冲突原因。符合时间覆盖率及样本要求后，再验证五交易日增量预测。
2. 实际方案使用反馈与工作台异常处理，保持新旧参数与账目一致。
3. 先立新协议，再研究少量信号连续确认/分档仓位；原ADX与2021等失败样本保留。已见历史不算新前瞻验证。
4. 持续推进正式除息参考价、独立停复牌完整性及已公布时点的估值/基本面/持仓证据。查不到保持未知，不放宽准入。
5. 每日合格数据接续、健康及归档观察；外部提醒与2027正式日历仍待完成。
6. Backtrader精确现金边界差异继续隔离验证，不因162场景或测试通过就迁移。
7. 前瞻满6/12/24个月分别观察，最早2027-05-05、2027-11-05、2028-11-05。

## 与最初计划对照

[13份原规划与状态](docs/PLAN_ALIGNMENT.md)保留已实现、部分实现、不适用及缺项。工具真实使用、界面可用、模型有效与前瞻目标是四个不同验收层次，不合并成一个完成百分比。

完整旧阶段计划保留于 [整理前项目计划](docs/history/20261112-before-workbench-PROJECT_PLAN.md)。
