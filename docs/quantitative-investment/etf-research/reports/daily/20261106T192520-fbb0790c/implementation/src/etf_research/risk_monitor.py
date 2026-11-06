"""Read-only risk analysis using pandas/NumPy. Does not generate orders."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

RISK_KEYS = {'action','drawdown_warning','annual_drawdown_limit','annual_volatility_limit',
             'annual_volatility_warning','sharpe_target','daily_var_limit','daily_move_warning',
             'var_confidence','lookback_returns','annualization_sessions','annual_risk_free_assumption'}

def load_config(path, root):
    c=json.loads(Path(path).read_text());r=c['risk']
    if c['schema_version']!=1 or c['mode']!='research_only' or r.get('action')!='report_only':
        raise ValueError('Only research/report-only configuration is supported')
    if set(r)!=RISK_KEYS: raise ValueError('Unknown or missing risk setting')
    for k,v in r.items():
        if k!='action' and (isinstance(v,bool) or not isinstance(v,(float,int)) or not np.isfinite(v)):
            raise ValueError('Invalid numeric setting: '+k)
    for k in ('lookback_returns','annualization_sessions'):
        if type(r[k]) is not int or r[k]<2: raise ValueError('Invalid window')
    if not (0<r['drawdown_warning']<r['annual_drawdown_limit']<1 and
            0<r['annual_volatility_limit']<r['annual_volatility_warning'] and
            0<r['daily_var_limit']<1 and 0<r['daily_move_warning']<1 and
            0<r['var_confidence']<1 and r['annual_risk_free_assumption']>-1):
        raise ValueError('Invalid risk threshold ordering/range')
    for k in ('history_results','forward_checkpoint','protocol'):
        p=(Path(root)/c[k]).resolve()
        if not p.is_relative_to(Path(root).resolve()) or not p.is_file(): raise ValueError('Invalid input path: '+k)
    return c

def analyze(dates, equity, settings):
    index=pd.DatetimeIndex(pd.to_datetime(dates,errors='raise'))
    nav=pd.Series(np.asarray(equity,dtype=float),index=index,name='equity')
    if len(nav)<1 or index.hasnans or index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError('Dates must be nonempty, unique and sorted')
    if not np.isfinite(nav.to_numpy()).all() or (nav<=0).any(): raise ValueError('NAV must be finite and positive')
    ret=nav.pct_change(fill_method=None);dd=1-nav/nav.cummax();r=settings
    result={'sessions':len(nav),'as_of':index[-1].date().isoformat(),
            'total_return':float(nav.iloc[-1]/nav.iloc[0]-1),
            'max_close_drawdown':float(dd.max()),'current_drawdown':float(dd.iloc[-1]),
            'annualized_return':None,'rolling_volatility':None,'rolling_sharpe':None,'daily_var':None,
            'latest_daily_return':None if len(nav)<2 else float(ret.iloc[-1]),
            'risk_window_complete':len(nav)-1>=r['lookback_returns'],'years':[],'alerts':[]}
    days=(index[-1]-index[0]).days
    if days>=365: result['annualized_return']=float((nav.iloc[-1]/nav.iloc[0])**(365.25/days)-1)
    # Include previous year's last close as the next year's opening valuation anchor.
    for year in sorted(set(index.year)):
        positions=np.flatnonzero(index.year==year);first,last=int(positions[0]),int(positions[-1])
        values=nav.iloc[max(0,first-1):last+1];annual_dd=float((1-values/values.cummax()).max())
        result['years'].append({'year':int(year),'observed_start':index[first].date().isoformat(),
            'observed_end':index[last].date().isoformat(),'previous_close_anchor':first>0,
            'max_drawdown':annual_dd,'limit_breached':annual_dd>=r['annual_drawdown_limit']-1e-12,
            'coverage':'observed dates only; boundary years may be partial'})
    if result['risk_window_complete']:
        returns=ret.dropna().iloc[-r['lookback_returns']:];std=float(returns.std(ddof=1))
        result['rolling_volatility']=std*np.sqrt(r['annualization_sessions'])
        rf=(1+r['annual_risk_free_assumption'])**(1/r['annualization_sessions'])-1
        result['rolling_sharpe']=float((returns.mean()-rf)/std*np.sqrt(r['annualization_sessions'])) if std>0 else None
        result['daily_var']=max(0.,float(-np.quantile(returns.to_numpy(),1-r['var_confidence'],method='linear')))
    def alert(code, condition):
        if condition: result['alerts'].append(code)
    alert('current_drawdown_warning',result['current_drawdown']>r['drawdown_warning'])
    alert('observed_year_drawdown_limit',result['years'][-1]['limit_breached'])
    v=result['rolling_volatility'];var=result['daily_var'];sh=result['rolling_sharpe'];daily=result['latest_daily_return']
    alert('volatility_limit',v is not None and v>=r['annual_volatility_limit'])
    alert('volatility_warning',v is not None and v>r['annual_volatility_warning'])
    alert('var_limit',var is not None and var>=r['daily_var_limit'])
    alert('sharpe_below_or_equal_target',sh is not None and sh<=r['sharpe_target'])
    alert('daily_move_warning',daily is not None and abs(daily)>r['daily_move_warning'])
    return result
