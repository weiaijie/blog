"""Build a dependency-free dashboard from saved result files, never invented series."""
from pathlib import Path
import json,csv,argparse

def main():
 p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]
 results=json.loads((a.results/'results.json').read_text());sensitivity=json.loads((a.results/'sensitivity.json').read_text());evaluation=json.loads((a.results/'evaluation.json').read_text())
 nav={};dates=None
 for r in results['results']:
  with (a.results/(r['run']+'_daily.csv')).open() as f:rows=list(csv.DictReader(f))
  current=[x['date'] for x in rows]
  if dates is None:dates=current
  if dates!=current:raise ValueError('NAV dates differ across scenarios')
  nav[r['run']]=[float(x['equity'])/float(r['initial_cash'])*100 for x in rows]
 simplified={name:{'folds':ev['folds'],'rolling_min':min(x['annualized_scenario_return'] for x in ev['rolling_252']),'rolling_max':max(x['annualized_scenario_return'] for x in ev['rolling_252']),'rolling_count':len(ev['rolling_252'])} for name,ev in evaluation.items()}
 snapshot='2026-11-05-costs-11' if results['sample'].get('long_history_extension') else '2026-11-04-calendar-08' if results['sample'].get('historical_extension') else '2026-11-04-expansion-07'
 snap=root/'data/snapshots'/snapshot;sources=[]
 for f in sorted(snap.glob('*requests.json')):sources+=json.loads(f.read_text())
 data={'source_snapshot':snapshot,'results':results['results'],'sensitivity':sensitivity['results'],'evaluation':simplified,'dates':dates,'nav':nav,'sources':sources}
 payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 main=next(r for r in results['results'] if r['strategy']=='monthly_50_50' and r['scenario']=='base')
 replacements={'__PAYLOAD__':payload,'__SAMPLE_COUNT__':str(len(dates)),'__START__':dates[0],'__END__':dates[-1],'__MAIN_ANNUAL__':format(main['annualized_scenario_return'],'.2%'),'__MAIN_DD__':format(abs(main['max_close_drawdown']),'.2%'),'__REPORT_NAME__':'2026-11-04-extension' if results['sample'].get('historical_extension') else '2026-11-04-closure','__SOURCE_NOTE__':'本轮13次请求：12次HTTP200，首次债券ETF大区间请求503；改为按年分段后返回成功。两只ETF在2022-01-04至2026-10-30共1167日的OHLC与新浪精确一致，期间10条分红有官方依据。2018～2021年度休市及2019劳动节、2020春节修订已归档，2018年末跨年休市已处理。2018起全历史仍有搜狐缺日及精度问题，不整体准入。' if snapshot.endswith('08') else '此前24次请求与640日冻结研究；完整事实见原报告。'}
 if results['sample'].get('long_history_extension'):
  replacements.update({'__REPORT_NAME__':'2026-11-05-long-history','__SOURCE_NOTE__':'上交所官方日线与新浪原价逐字段一致，独立日历核验通过；本页回顾样本为2018-09-14至2026-10-30，共1967日、13条官方分红。两次上市前份额折算未重复施加。28次证据请求27次200、1次404原样保存；今天收盘准入另见最新报告。'})
 status=json.loads((root/'reports/2026-11-06-close/site_status.json').read_text())
 replacements.update({'__UPDATE_DAY__':status['updated_on_shanghai'],'__ACCOUNT_THROUGH__':status['account_input_through'],'__ACCOUNT_SESSIONS__':str(status['account_input_sessions']),'__FORWARD_SESSIONS__':str(status['forward_sessions'])})
 html=(root/'site/template.html').read_text()
 for key,value in replacements.items():html=html.replace(key,value)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(html)
 print('Built dashboard from',len(nav),'saved NAV series and',len(sensitivity['results']),'sensitivity scenarios')
if __name__=='__main__':main()
