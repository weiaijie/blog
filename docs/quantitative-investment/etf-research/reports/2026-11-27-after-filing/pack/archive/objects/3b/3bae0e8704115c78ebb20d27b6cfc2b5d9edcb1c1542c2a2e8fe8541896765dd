"""Explicit ETF-proxy beta and fixed exposure shocks; never trading rules."""
from decimal import Decimal as D
import numpy as np
import pandas as pd

def benchmark_returns(dataset,symbol):
    """Gross fractional reinvestment proxy from raw close and verified cash events."""
    dates=dataset.sessions;events={}
    for e in dataset.dividends:
        if e.symbol==symbol:events[e.ex_date]=events.get(e.ex_date,D(0))+e.per_share
    values=[]
    for previous,day in zip(dates,dates[1:]):
        values.append(float((dataset.bars[symbol][day].close+events.get(day,D(0)))/dataset.bars[symbol][previous].close-1))
    return pd.Series(values,index=pd.to_datetime(dates[1:]),dtype=float)

def beta_metrics(dates,equity,benchmark,lookback=252):
    dates=pd.DatetimeIndex(pd.to_datetime(dates));v=np.asarray(equity,dtype=float)
    if len(dates)!=len(v) or not dates.is_monotonic_increasing or dates.has_duplicates:raise ValueError('Invalid NAV dates')
    if not np.isfinite(v).all() or (v<=0).any():raise ValueError('Invalid NAV')
    y=pd.Series(v,index=dates).pct_change(fill_method=None).iloc[1:]
    x=benchmark.reindex(y.index)
    if not np.isfinite(x.to_numpy()).all():raise ValueError('Benchmark dates missing')
    count=min(len(y),lookback)
    result=dict(observed_returns=len(y),window_returns=count,required_returns=lookback,beta=None,correlation=None,status='insufficient_sample')
    if len(y)<lookback:return result
    y=y.iloc[-lookback:].to_numpy();x=x.iloc[-lookback:].to_numpy()
    variance=float(np.var(x,ddof=1))
    if variance==0 or np.ptp(x)==0:result['status']='constant_benchmark';return result
    result.update(beta=float(np.cov(y,x,ddof=1)[0,1]/variance),status='computed')
    if np.std(y,ddof=1)>0:result['correlation']=float(np.corrcoef(y,x)[0,1])
    return result

def exposure_stress(equity,values,scenarios):
    equity=D(str(equity))
    if equity<=0:raise ValueError('Invalid equity')
    rows=[]
    for scenario in scenarios:
        shocks={s:D(str(scenario[s])) for s in ('510300','511010')}
        if any(not x.is_finite() or x<-1 for x in shocks.values()):raise ValueError('Invalid stress shock')
        pnl=sum(D(str(values[s]))*shocks[s] for s in shocks)
        rows.append(dict(name=scenario['name'],pnl=str(pnl),return_fraction=str(pnl/equity),ending_equity=str(equity+pnl)))
    return rows
