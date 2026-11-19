"""Explicit chronological folds of a continuous portfolio, without parameter fit."""
from decimal import Decimal as D

def metrics(rows):
 if len(rows)<2:raise ValueError('At least two closing NAV observations required')
 first,last=rows[0],rows[-1];days=(last['date']-first['date']).days
 if days<=0 or any(r['equity']<=0 for r in rows):raise ValueError('Invalid dates or NAV')
 ratio=last['equity']/first['equity'];peak=first['equity'];dd=D(0)
 for r in rows:
  peak=max(peak,r['equity']);dd=min(dd,r['equity']/peak-1)
 return {'anchor_date':str(first['date']),'end_date':str(last['date']),'trading_intervals':len(rows)-1,'calendar_days':days,'starting_equity':str(first['equity']),'ending_equity':str(last['equity']),'total_return':float(ratio-1),'annualized_scenario_return':float(ratio**(D('365.25')/days)-1),'max_close_drawdown':float(dd)}

def chronological_folds(result, train_intervals=252, test_intervals=126):
 if type(train_intervals) is not int or type(test_intervals) is not int or min(train_intervals,test_intervals)<1:raise ValueError('Positive integer fold lengths required')
 rows=result['daily'];folds=[]
 for anchor in range(train_intervals,len(rows)-1,test_intervals):
  end=min(anchor+test_intervals,len(rows)-1)
  begin_day=rows[anchor]['date'];end_day=rows[end]['date']
  trades=[t for t in result['journal'] if t['kind']=='trade' and begin_day<t['day']<=end_day]
  folds.append({'fold':len(folds)+1,'information_window_start':str(rows[anchor-train_intervals]['date']),'information_window_end':str(begin_day),'test_first_session':str(rows[anchor+1]['date']),'test_last_session':str(end_day),'partial_fold':end-anchor<test_intervals,'parameters_fitted':False,'positions_carried':True,'fees_carried':True,'trade_count':len(trades),'commission':str(sum((t['commission'] for t in trades),D(0))),**metrics(rows[anchor:end+1])})
 rolling=[metrics(rows[i-252:i+1]) for i in range(252,len(rows))]
 return {'method':'Retrospective chronological evaluation of fixed rules; no fitting or pristine unseen-sample claim','train_intervals':train_intervals,'test_intervals':test_intervals,'folds':folds,'post_warmup_metrics':metrics(rows[train_intervals:]) if len(rows)>train_intervals+1 else None,'rolling_252':rolling}
