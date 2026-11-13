# 自主接续入口

先核对GitHub redesign-pc最新提交、Ubuntu活动指针及封存记录，不依赖旧聊天。仓库项目目录为docs/quantitative-investment/etf-research，独立Ubuntu运行副本为/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research。

## 当前事实

- [当前进度](docs/CURRENT_STATUS.md)集中维护完成与缺口；前瞻已至2026-11-12、18户6日，原版回测截至10-30，独立近期版及四只ETF报价截至11-12。
- [新版工作台](docs/WORKBENCH_PLAN.md)使用Vue/TypeScript/Vite，人工和Agent共用参数。服务根路径及/workbench/为新版，/market.html与/backtest.html保留旧入口。内网地址http://10.1.1.120:18766，未确认公网部署。
- [321个ADX落后窗口](reports/2026-11-12-adx-shortfall/README.md)已逐窗对账。270个短空档窗口只覆盖两次实际事件；事后取消诊断不能作为可执行规则。
- 多源行情、公告、日历、分红核验继续阻断不合格更新，不覆盖旧快照，不使用真实资金。

2026-11-13：[近期版准入报告](reports/2026-11-13-recent-data/README.md)固定数据版本verified-2026-11-12，v2 API与v1隔离，旧方案迁移保持冻结数据。后续扩展须新增证据版本、保留旧快照与接口复现边界；不原地改动此版日期或默默切换已保存方案。

## 接手顺序

1. 读取AGENTS、README、PROJECT_PLAN、DATA_SOURCES、docs/PLAN_ALIGNMENT、config/research.json、PROTOCOL_V1。核对远端和当前北京时间。
2. 执行verify_snapshot.py与scripts/verify_project.py。最新静态清单为reports/2026-11-13-recent-data/manifest.json；旧清单在相应提交验证。
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
