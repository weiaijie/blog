"""Independent Decimal arithmetic for the first execution day; no order generation."""
from pathlib import Path
from decimal import Decimal as D, ROUND_CEILING, ROUND_HALF_UP
import json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.admission import load_incremental

def audit():
    data,_=load_incremental(ROOT/'data/snapshots','2026-11-06-close-windows-1653')
    state=json.loads((ROOT/'reports/2026-11-06-close/forward_checkpoint.json').read_text())
    prior=json.loads((ROOT/'reports/2026-11-05-long-history/forward_checkpoint.json').read_text())
    assert state['as_of']=='2026-11-06' and state['forward_sessions']==2
    assert len(state['portfolios'])==18
    results=[];outside=[];trades=0
    for name,p in state['portfolios'].items():
        old=prior['portfolios'][name];assert p['daily'][:1]==old['daily']
        assert len(p['daily'])==2 and old['daily'][0]['equity']=='100000'
        assert old['journal']==[] and old['daily'][0]['units_510300']==old['daily'][0]['units_511010']==0
        cash=D('100000');units={'510300':0,'511010':0};fees=D(0);slippage=D(0)
        rate,bps={'low':(D('.0001'),D(1)),'base':(D('.0003'),D(5)),'high':(D('.001'),D(10))}[p['summary']['scenario']]
        for t in p['journal']:
            assert t['kind']=='trade' and t['day']=='2026-11-06' and t['signal_date']=='2026-11-05' and t['side']=='buy'
            symbol=t['symbol'];bar=data.bars[symbol][data.sessions[-1]];n=t['units']
            assert n>0 and n%100==0 and D(t['raw_price'])==bar.open
            fill=(bar.open*(1+bps/10000)/D('.001')).to_integral_value(rounding=ROUND_CEILING)*D('.001')
            notional=fill*n;fee=max(D(5),notional*rate).quantize(D('.01'),rounding=ROUND_HALF_UP)
            assert (D(t['fill_price']),D(t['notional']),D(t['commission']),D(t['tax']))==(fill,notional,fee,D(0))
            assert cash>=notional+fee
            cash-=notional+fee;units[symbol]+=n;fees+=fee;slippage+=(fill-bar.open)*n;trades+=1
            if not bar.low<=fill<=bar.high:outside.append({'run':name,'symbol':symbol,'model_fill':str(fill),'low':str(bar.low),'high':str(bar.high)})
        end=p['daily'][-1];equity=cash+sum(data.bars[s][data.sessions[-1]].close*n for s,n in units.items())
        assert end['date']=='2026-11-06' and D(end['cash'])==D(end['available_cash'])==cash and D(end['receivables'])==0
        assert D(end['equity'])==equity and all(end['units_'+s]==n for s,n in units.items())
        assert D(p['summary']['commissions'])==fees and D(p['summary']['slippage_cost'])==slippage
        assert abs(D(str(p['summary']['total_return']))-(equity/D(100000)-1))<D('1e-12')
        results.append({'run':name,'equity':str(equity),'cash':str(cash),'holdings':units,'commissions':str(fees),'slippage_cost':str(slippage),'total_return':str(equity/D(100000)-1),'annualized_return':None,'trades':len(p['journal'])})
    return {'as_of':state['as_of'],'portfolios_checked':len(results),'trades_checked':trades,'independent_arithmetic_passed':True,'model_fills_outside_daily_range':outside,'portfolios':results,'scope':'Cost-model simulation only. Out-of-range fills are not proven executable. Annualization suppressed for this two-session sample; frozen engine raw summary is retained unchanged.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=audit()
    with a.output.open('x') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'portfolios':result['portfolios_checked'],'trades':result['trades_checked'],'outside_daily_range':len(result['model_fills_outside_daily_range'])}))
