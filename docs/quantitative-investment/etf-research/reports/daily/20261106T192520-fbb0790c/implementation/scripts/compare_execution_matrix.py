"""Replay frozen targets through independent BackBroker; persist every mismatch."""
from pathlib import Path
from decimal import Decimal as D
import argparse,hashlib,json,sys,platform
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import backtrader as bt
from etf_research.long_history import load_long_history
from etf_research.baselines import run,STRATEGIES,SCENARIOS
from etf_research.backtrader_adapter import replay_targets

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--smoke',action='store_true');a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    implementation={}
    for name in ('src/etf_research/backtrader_adapter.py','scripts/compare_execution_matrix.py'):
        body=(ROOT/name).read_bytes();implementation[name]=hashlib.sha256(body).hexdigest()
        (a.output/(Path(name).stem+'_source.py')).write_bytes(body)
    data=load_long_history(ROOT/'data/snapshots')
    combinations=[(strategy,scenario,D(initial),delay) for strategy in STRATEGIES for scenario in SCENARIOS for initial in ('10000','100000','1000000') for delay in (1,2,3)]
    if a.smoke:combinations=[('monthly_50_50','base',D(100000),1)]
    cases=[];differences=[];native_fills=[];tolerance=D('0.0000001')
    for strategy,scenario,initial,delay in combinations:
        name=f'{strategy}_{scenario}_{initial}_{delay}'
        old=run(data,strategy,scenario,initial,execution_delay=delay)
        plans={}
        for d in old['decisions']:plans.setdefault(d['day'],[]).append((d['symbol'],d['target_units'],d['signal_date']))
        costs=SCENARIOS[scenario]
        new=replay_targets(data,plans,initial=initial,rate=costs.commission_rate,minimum=costs.minimum_commission,bps=costs.slippage_bps,sell_tax=costs.sell_tax_rate)
        native_fills.extend(dict(run=name,**x) for x in new['native_fills'])
        max_delta=D(0);checks=0;start=len(differences)
        for section in ('daily','decisions','journal'):
            if len(old[section])!=len(new[section]):differences.append(dict(run=name,section=section,error='length',old=len(old[section]),new=len(new[section])))
            for index,(left,right) in enumerate(zip(old[section],new[section])):
                for key in set(left)|set(right):
                    checks+=1;x=left.get(key);y=right.get(key)
                    if isinstance(x,D) and isinstance(y,D):
                        delta=abs(x-y)
                        if section=='daily':max_delta=max(max_delta,delta)
                        equal=delta<=tolerance if section=='daily' else delta==0
                    else:equal=x==y
                    if not equal:differences.append(dict(run=name,section=section,index=index,field=key,old=x,new=y))
        cases.append(dict(run=name,rows=len(new['daily']),field_checks=checks,max_daily_money_delta=str(max_delta),mismatches=len(differences)-start,reference_trades=sum(x['kind']=='trade' for x in old['journal']),native_trades=sum(x['kind']=='trade' for x in new['journal']),target_schedule_sha256=hashlib.sha256(json.dumps({str(k):v for k,v in plans.items()},default=str,sort_keys=True).encode()).hexdigest()))
        print(name,'mismatches',len(differences)-start,'max_money_delta',max_delta,flush=True)
    result=dict(scope='Independent execution/accounting with shared frozen target schedules; not independent strategy signal generation or proof of real fills.',python=platform.python_version(),backtrader=bt.__version__,sessions=len(data.sessions),cases=cases,case_count=len(cases),mismatch_count=len(differences),daily_money_tolerance=str(tolerance),trade_comparison_requires_exact_equality=True,source=data.provenance,implementation_sha256=implementation)
    for name,payload in [('matrix.json',result),('differences.json',differences),('native_fills.json',native_fills)]:
        (a.output/name).write_text(json.dumps(payload,default=str,ensure_ascii=False,indent=2)+'\n')
    if differences:raise SystemExit(2)

if __name__=='__main__':main()
