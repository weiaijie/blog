"""Replay real audited bars with endowed holdings, no trades or return claims."""
from pathlib import Path
from decimal import Decimal as D
import json,csv,argparse
from etf_research.data import load_dataset
from etf_research.accounting import Ledger,Costs,InstrumentRules
p=argparse.ArgumentParser();p.add_argument('--snapshots',type=Path,default=Path(__file__).resolve().parents[1]/'data/snapshots');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
data=load_dataset(args.snapshots)
initial={'510300':100,'511010':100};rules={'510300':InstrumentRules(100,D('.001'),False),'511010':InstrumentRules(100,D('.001'),True)}
l=Ledger(data.sessions,data.dividends,cash=0,holdings=initial,costs=Costs(D(0),D(0),D(0),D(0)),lot_size=100,instruments=rules)
rows=[]
for day in data.sessions:
 l.open_session(day);l.close_session()
 cash=sum((initial[e.symbol]*e.per_share for e in data.dividends if e.pay_date<=day),D(0))
 receivable=sum((initial[e.symbol]*e.per_share for e in data.dividends if e.ex_date<=day<e.pay_date),D(0))
 available=sum((initial[e.symbol]*e.per_share for e in data.dividends if e.pay_date<day),D(0))
 marks={s:data.bars[s][day].close for s in initial};equity=cash+receivable+sum(initial[s]*marks[s] for s in initial)
 checks=[l.cash==cash,sum(l.receivables.values(),D(0))==receivable,l.available_cash==available,l.equity(marks)==equity,l.holdings==initial]
 if not all(checks):raise AssertionError((day,checks))
 rows.append({'date':str(day),'close_510300':str(marks['510300']),'close_511010':str(marks['511010']),'units_510300':100,'units_511010':100,'cash':str(l.cash),'available_cash':str(l.available_cash),'receivables':str(receivable),'equity':str(l.equity(marks)),'independent_checks_passed':True})
args.output.mkdir(parents=True,exist_ok=True)
with (args.output/'daily_accounting.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(args.output/'journal.json').write_text(json.dumps(l.journal,default=str,ensure_ascii=False,indent=2))
summary={'purpose':'Accounting validation only; endowed starting shares, no trade strategy, not a net-return backtest','initial_state':{'cash':'0','holdings':initial,'holdings_assumption':'Already owned and settled; acquisition cost intentionally undefined'},'sessions':len(rows),'official_dividends':len(data.dividends),'trade_count':0,'independent_daily_checks':len(rows)*5,'all_checks_passed':True,'ending_dividend_cash':str(l.cash),'ending_receivables':str(sum(l.receivables.values(),D(0))),'acquisition_cost_fees_or_strategy_returns_computed':False,'provenance':data.provenance}
(args.output/'replay_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='provenance'},ensure_ascii=False,indent=2))
