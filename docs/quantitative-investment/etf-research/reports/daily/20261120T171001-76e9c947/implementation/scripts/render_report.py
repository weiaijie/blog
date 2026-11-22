from pathlib import Path
import json,argparse,re
p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]
base=json.loads((a.results/'results.json').read_text());sensitivity=json.loads((a.results/'sensitivity.json').read_text());ev=json.loads((a.results/'evaluation.json').read_text());diag=json.loads((a.results/'execution_diagnostics.json').read_text());source=json.loads((root/'data/snapshots/2026-11-04-expansion-07/audit.json').read_text())
labels={'cash':'零息现金','equity_hold':'510300买入持有','bond_hold':'511010买入持有','monthly_20_80':'月度20/80','monthly_50_50':'月度50/50','trend_120':'固定120日趋势'}
lines=['# 第一版研究闭环验收（2026-11-04）','','## 当前结论','','研究流程已经连通：冻结协议 → 原始数据与准入 → 费用/成交场景 → 连续持仓时间评估 → 静态看板 → 可复现输出。长期年化净收益4%～5%的目标尚未证实。该目标需要未来1～2年观察，不可能在本次会话内完成时间验证。无实盘接入、无真实资金。',
'','## 本会话完成范围','','- 162组预先列明的策略×费用×本金×延迟场景，完整订单/分红审计；18组主场景逐日资产、连续持仓分折和滚动指标。未选择最优场景替换协议。',
'- 45项自动化测试通过；162组期末现金、持仓、费用和资产独立核对通过。前缀重跑、未来价格扰动、延迟信号保持、样本末未成交和整手约束均检查。',
'- 前瞻协议在新行情请求之前已提交：`'+base['protocol_commit']+'`。历史截止2026-10-30，真正前瞻期不早于2026-11-05；当前前瞻合格样本0，未计算前瞻收益。',
'- 新行情/规则请求24次，全部保留URL、UTC时间、原始响应、HTTP状态、错误和SHA256；新增历史未通过准入，真实研究区间仍为640日。',
'- 静态看板由保存结果生成，可切换费用、策略，查看本金/延迟、资产曲线、分折与原始来源。不需要外部行情API或账户。生成与仓库存储不等于已经公开部署到网站域名。',
'','## 主场景结果','','初始模拟现金100000元、信号后第1个交易日开盘、基准费用万3/最低5元/5bp滑点；期末不强制变现。完整原始价格、分红与制度口径沿用前轮报告。所有收益是明示假设下的历史场景，不是可兑现的实际净收益。','','|策略|场景年化|最大收盘回撤|交易笔数|','|---|---:|---:|---:|']
for r in base['results']:
 if r['scenario']=='base':lines.append(f"|{labels[r['strategy']]}|{r['annualized_scenario_return']:.2%}|{r['max_close_drawdown']:.2%}|{r['trades']}|")
lines+=['','## 本金与延迟敏感性','','|50/50基准费用：本金|延迟交易日|场景年化|最大收盘回撤|','|---:|---:|---:|---:|']
for r in sensitivity['results']:
 if r['strategy']=='monthly_50_50' and r['scenario']=='base':lines.append(f"|{r['initial_cash']}|{r['execution_delay_sessions']}|{r['annualized_scenario_return']:.2%}|{r['max_close_drawdown']:.2%}|")
lines+=['','1万元买不起511010的100份整手，目标权重未必形成实际股债配置，大量债券目标会成为现金。延迟2/3日恰好提高该样本收益不证明延迟是改进；主观察保持延迟1日。买入目标份额在原信号日固定，成交时才检查实际开盘价、规则和可用现金；期间不重算目标，不使用当日高低收盘价决定是否交易。样本末尚未到执行日的订单保持未成交，不越界填单。',
'','## 成交可实现性的边界','','本轮上交所ETF常见问题与债券ETF指南HTTP200，两个旧技术PDF URL均404，因此未取得逐日正式除息参考价或停复牌/队列证据。仍保留已知除息日禁交易、开盘或模拟价偏离前收盘至少9%跳过的研究缓冲；不能冒称精确10%涨跌停模拟。',
f"162组场景累计发现{sum(r['fills_outside_daily_range'] for r in diag['runs'])}笔模拟滑点价格在当日高低范围外（同一历史交易在不同场景重复计数）。这是显式成本模型价格，不是实际成交。该检查在事后进行，不据此筛选或改变历史订单，避免用日内未来高低价产生选择偏差。详见 execution_diagnostics.json。实际成交能力仍未验证。",'','## 行情扩展的实际结果','','- 新浪两只ETF各1970行，2018-09-14至2026-11-04；与原快照1023日OHLC逐项一致。当前日和超出已验证范围的数据均未进入研究。',
'- 腾讯fqkline分年、先前成功URL及默认形式共14次HTTP501，响应是腾讯WAF引导页；保存错误，不将其解析为行情。腾讯旧2022接口2次HTTP200，各193行，仅到2022-10-24，OHLC两位小数；与新浪差值最大0.005元，510300/511010分别660/615个字段非精确一致。没有放宽阈值吸收它们。',
'- 东方财富未复权接口2次HTTP503；官方旧PDF2次404；上交所两个一般规则页面HTTP200。合计6次200、14次501、2次503、2次404。',
'- 新数据已存档，但双源精确核验和2018起独立日历均不完整，新增准入交易日为0。本项完成的是可追溯扩展尝试，不能称已完成真实历史扩容。',
'','## 时间评估与前瞻区别','','固定策略无模型拟合。初始252交易间隔之后，以126间隔逐折评估；信息窗结束日严格早于测试首日。前一日收盘NAV作为分折锚点，持仓、应收、到账和费用连续；末折9间隔单独标注。各折收益复合等于连续后段NAV收益，已测试。该方法具备时间隔离检查，但现有历史已被观察，不是无偏、真正未见样本外。需要调参时必须另立协议和训练期内选择规则，当前未做参数筛选。',
'','|50/50基准费用评估区间|间隔数|区间收益|年化场景收益|区间回撤|','|---|---:|---:|---:|---:|']
for f in ev['monthly_50_50_base_100000_d1']['folds']:lines.append(f"|{f['test_first_session']} → {f['test_last_session']}|{f['trading_intervals']}|{f['total_return']:.2%}|{f['annualized_scenario_return']:.2%}|{f['max_close_drawdown']:.2%}|")
lines+=['','短折年化数可能夸大观感，不据此认定目标。252间隔重叠滚动频率不是成功概率。未来评估日期见 PROTOCOL_V1.md；首次6个月、12个月和24个月观察不早于2027-05-05、2027-11-05、2028-11-05。',
'','## 复现','','标准研究脚本只需Python3标准库。可选浏览器验收额外需要Playwright及Chromium。已有原始快照禁止原地重跑抓取脚本。',
'','```sh','python scripts/verify_project.py','PYTHONPATH=src python -m unittest discover -s tests -v','PYTHONPATH=src python scripts/run_research.py --output /tmp/etf-reproduce','PYTHONPATH=src python scripts/check_execution_results.py --results /tmp/etf-reproduce','python scripts/build_site.py --results /tmp/etf-reproduce --output /tmp/etf-index.html','```',
'','site/index.html及app.js/style.css为静态文件，在项目目录运行 `python -m http.server 8765 --bind 127.0.0.1` 后访问 `/site/`。不必安装交易客户端。',
'','## 仍未完成的外部验证','','正式逐日参考价、停复牌/撮合证据、真实券商费率和更长精确交叉验证历史仍缺失。未来样本需等待真实时间。下一轮优先补这些证据，并按冻结协议加入合格新样本；现有结果和阈值不得为达目标而改写。原旧会话项目未恢复；当前交付是仓库中持续重建的可审计版本。']
(a.results/'PROGRESS.md').write_text('\n'.join(lines)+'\n')
