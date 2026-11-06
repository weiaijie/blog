# 个人量化投资研究系统

## 最新状态：2026-11-06三阶段工程验收

Backtrader独立执行矩阵、Beta/固定压力/官方披露代理、每日管线与故障恢复均已验收。145项基础测试+18项可选框架测试通过；保留冻结引擎，前瞻仍仅2日。当前日报入口为site/daily.html，状态与实际输入由config/active_run.json明确指向。Ubuntu定时方案已受控验证但未启用，公告TLS可靠性仍待解决；外部提醒、完整实时穿透和长期收益评估仍未完成。先读[当前接续说明](CONTINUATION.md)、[本轮验收](reports/2026-11-06-daily-pipeline/PROGRESS.md)与[操作说明](docs/DAILY_PIPELINE.md)。

以下保留历次建设过程与当时状态；有冲突时以当前接续说明及最新证据为准。

只研究中国股票ETF和债券ETF，用1～2年评估长期年化净收益4%～5%的可行性；不保证收益、不实盘、不使用真实资金。研究代码、行情与来源保存于用户授权公开的weiaijie/blog / redesign-pc / docs/quantitative-investment/etf-research，不保存凭据或私人账户资料。

## 当前状态（2026-11-06收盘后）

|对象|状态|
|---|---|
|最新独立历史研究|1967日，2018-09-14～2026-10-30；13次官方分红、162固定场景。|
|保留的旧历史|640日和1167日结果均保留，不覆盖、不拼接。|
|前瞻账户输入|1172日，截至2026-11-06；保持原2022起预热历史。|
|真正前瞻观察|2日；首日观察，第二日21笔成本模型交易；50/50基准费用净值100067.48元、总收益0.06748%，不展示年化。8笔模型价超日内范围，实际可成交性未证明。|
|验证|120项测试、162组独立期末核对、离线复现和浏览器验收。|
|看板部署|静态代码和页面已保存，未配置公开域名托管。|

50/50基准费用年化：原640日4.90%，1167日0.51%，新1967日4.02%（最大收盘回撤19.73%）。同策略、同历史终点对起点敏感；最新数字落入研究目标范围也不证明长期目标成立。

- [11月6日收盘准入与模拟对账](reports/2026-11-06-close/PROGRESS.md)
- [计划逐项对照](docs/PLAN_ALIGNMENT.md) · [风险监控页面](site/risk.html) · [统一监控配置](config/research.json)
- [Backtrader 固定样例初评](reports/2026-11-06-backtrader/PROGRESS.md) · [引擎对照页面](site/backtrader.html)：暂不替换冻结引擎，分红和交易制度仍需双引擎验证。
- [最新停复牌查询核验](reports/2026-11-06-suspension/PROGRESS.md)
- [11月6日模拟目标与时间说明](reports/2026-11-06-intent/PROGRESS.md)
- [最新规则时间线证据](reports/2026-11-05-rule-timeline/PROGRESS.md)
- [最新研究报告与来源限制](reports/2026-11-05-long-history/PROGRESS.md) · [三种历史区间比较](reports/2026-11-05-long-history/sample_comparison.json)
- [前瞻检查点](reports/2026-11-06-close/forward_checkpoint.json) · [官方收盘交叉验证](reports/2026-11-06-close/official_close.json)
- [原1167日报告](reports/2026-11-04-extension/PROGRESS.md) · [原640日报告](reports/2026-11-04-closure/PROGRESS.md)
- [冻结协议](PROTOCOL_V1.md) · [接续入口](CONTINUATION.md) · [计划](PROJECT_PLAN.md) · [数据来源](DATA_SOURCES.md) · [静态看板](site/index.html)

## 复现

```sh
python -m pip install -r requirements-lock.txt
python scripts/verify_project.py
python scripts/build_risk_report.py
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/audit_official_close.py --official-snapshot 2026-11-06-official-close-1650 --price-snapshot 2026-11-06-close-windows-1653 --day 2026-11-06 --output /tmp/etf-official-close-check.json
python scripts/reproduce.py
python -m http.server 8765 --bind 127.0.0.1
```

Python 3.11+；监控使用固定版本pandas、NumPy和matplotlib，完整依赖见requirements-lock.txt。旧冻结模拟引擎仍使用标准库；可选网页验收需Playwright/Chromium，PDF文本提取需pdftotext。已有原始快照不覆盖。最新清单reports/2026-11-06-engine-matrix-final/manifest.json；旧阶段清单在相应历史提交核验。新环境先读CONTINUATION.md，不依赖聊天记忆。

旧/workspace/quant-research、旧策略/看板和旧10项测试未恢复；当前是持续重建并已保存到仓库的版本。无实盘、无后台调度，未来收益不能在当前会话完成。

监控页面使用现有报告离线生成，浏览器无需安装框架或联网加载图表。可用上面的http.server打开/site/risk.html。配置仅控制分析输入和风险监控；策略权重/费用仍由冻结协议控制。原规划的剩余项见PLAN_ALIGNMENT，不以测试通过代替完整交付。

Windows 检出须保留快照原始字节（本项目 `.gitattributes` 已设定）；Linux 默认在独立 Ubuntu 执行。首次执行 `audit_official_close.py` 的输出必须为不存在的新文件，避免覆盖旧报告。

下一阶段大目标见[工程计划](docs/PHASE2_PLAN.md)。[独立执行矩阵](reports/2026-11-06-engine-matrix-final/PROGRESS.md)已完成162场景对照；存在精确现金边界反例，冻结引擎不迁移。风险扩展和每日流程仍在进行。

## 2026-11-06 风险扩展阶段

Beta、预设压力测试和官方2026Q3披露代理穿透已实现，见[验收报告](reports/2026-11-06-risk-expansion/PROGRESS.md)。当前完整持仓、完整集中度仍未知；前瞻样本不足的Beta为空。下一项为docs/PHASE2_PLAN.md阶段三每日管线，不能将本阶段通过视作整个规划完成。
