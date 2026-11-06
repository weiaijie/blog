"""Collect -> admit -> replay -> reconcile -> render -> seal -> atomic publish.

Ubuntu only. No broker, external notification, automatic Git push or strategy edit.
Failed partial runs are retained; retry creates a new run. Sealed runs can resume.
"""
from pathlib import Path
from datetime import date,datetime,timedelta
from decimal import Decimal as D
from zoneinfo import ZoneInfo
import argparse,html,json,os,re,shutil,subprocess,sys,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import read,sha,inside,create,lock,seal,promote,verify_bundle
from etf_research.admission import load_incremental,completed_date,sessions_between
from etf_research.forward import advance,digest,engine_digest
from etf_research.first_session_plan import check_execution
from audit_official_close import audit as official_audit
from collect_official_close import collect as collect_official
from build_risk_report import build as risk_build
from build_risk_extensions import build as extension_build

def reconcile(data,previous,state):
    """Independent daily cash/position/receivable arithmetic from event journal."""
    counts=dict(portfolios=0,daily_rows=0,trade_rows=0);outside=[]
    for name,p in state['portfolios'].items():
        cash=D(100000);receivable=D(0);units={s:0 for s in data.bars}
        journal=p['journal'];days={x['date'] for x in p['daily']}
        if any(t['day'] not in days for t in journal):raise ValueError('Journal outside account days')
        for row in p['daily']:
            day=date.fromisoformat(row['date'])
            for t in [t for t in journal if t['day']==row['date']]:
                if t['kind']=='trade':
                    n=t['units'];sign=1 if t['side']=='buy' else -1
                    if t['side'] not in ('buy','sell') or n<=0 or n%100 or t['signal_date']>=t['day']:raise ValueError('Invalid model trade')
                    if D(t['notional'])!=D(t['fill_price'])*n:raise ValueError('Trade notional mismatch')
                    cash-=sign*D(t['notional'])+D(t['commission'])+D(t['tax']);units[t['symbol']]+=sign*n
                    if cash<0 or units[t['symbol']]<0:raise ValueError('Negative cash/position')
                    bar=data.bars[t['symbol']][day]
                    if D(t['raw_price'])!=bar.open:raise ValueError('Raw execution price is not open')
                    if not bar.low<=D(t['fill_price'])<=bar.high:outside.append(dict(run=name,day=t['day'],symbol=t['symbol'],fill=t['fill_price']))
                    counts['trade_rows']+=1
                elif t['kind']=='dividend_receivable':receivable+=D(t['amount'])
                elif t['kind']=='dividend_paid':cash+=D(t['amount']);receivable-=D(t['amount'])
                elif t['kind']=='record_entitlement':
                    if t['units']!=units[t['symbol']]:raise ValueError('Entitlement/position mismatch')
                else:raise ValueError('Unknown journal event')
            equity=cash+receivable+sum(data.bars[s][day].close*n for s,n in units.items())
            if any(D(row[k])!=v for k,v in [('cash',cash),('receivables',receivable),('equity',equity)]) or any(row['units_'+s]!=n for s,n in units.items()):raise ValueError('Daily journal reconciliation failed')
            if not 0<=D(row['available_cash'])<=cash:raise ValueError('Invalid available cash')
            counts['daily_rows']+=1
        counts['portfolios']+=1
    return dict(**counts,model_fills_outside_daily_range=outside,scope='Independent journal arithmetic; not broker fill evidence. Frozen engine validates previous history and dividend availability; this check does not independently verify all dividend entitlements or fee rules.')

def dependencies(pointer):
    names=[ROOT/'config/research.json',ROOT/'config/risk_extensions.json',inside(ROOT,pointer['checkpoint']),ROOT/'PROTOCOL_V1.md',ROOT/'requirements-lock.txt',ROOT/'config/collection.json']
    names+=list((ROOT/'src/etf_research').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))
    names+=list((ROOT/'data/snapshots').glob('*/manifest.json'))+list((ROOT/'data/reference').glob('*.json'))
    # Include all immutable source bytes, not only a possibly unchanged manifest.
    for manifest in (ROOT/'data/snapshots').glob('*/manifest.json'):
        names += [inside(manifest.parent,n) for n in read(manifest)]
    names+=list((ROOT/'reports/2026-11-05-long-history').glob('*_daily.csv'))
    names+=[ROOT/'reports/2026-11-05-long-history/results.json',ROOT/'reports/2026-11-06-intent/plan.json',ROOT/'site/style.css']
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(names))}

def run(args):
    pointer_path=inside(ROOT,args.pointer)
    with lock(ROOT/'.runtime/daily.lock'):
        if args.resume:
            folder=inside(ROOT,args.resume)
            return dict(status=promote(ROOT,folder,pointer_path),bundle=str(folder.relative_to(ROOT)))
        current=read(pointer_path);previous=read(inside(ROOT,current['checkpoint']))
        if previous['checkpoint_sha256']!=digest({k:v for k,v in previous.items() if k!='checkpoint_sha256'}) or previous['engine_sha256']!=engine_digest() or current['checkpoint_sha256']!=previous['checkpoint_sha256'] or current['as_of']!=previous['as_of']:raise ValueError('Active checkpoint integrity failed')
        if current.get('bundle'):
            bundle=inside(ROOT,current['bundle']);verify_bundle(bundle)
            if sha(bundle/'manifest.json')!=current['bundle_manifest_sha256']:raise ValueError('Active bundle manifest changed')
        now=datetime.now(ZoneInfo('Asia/Shanghai'));cutoff=completed_date(now)
        calendar=read(ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json')
        days=sessions_between(calendar['holiday_ranges'],date(2026,11,5),cutoff)
        through=args.through or (days[-1] if days else None)
        if through not in days:raise ValueError('Target is not a completed verified exchange session')
        if str(through)<current['as_of']:raise ValueError('Refuse backward target')
        if str(through)==current['as_of'] and not args.rebuild:return dict(status='up_to_date',as_of=current['as_of'],network_requests=0,account_changes=0)
        if bool(args.candidate)!=bool(args.official):raise ValueError('Both candidate and official snapshot required for offline replay')
        if args.retry_of:
            failed=inside(ROOT,args.retry_of)
            if not (failed/'started.json').is_file() or (failed/'manifest.json').exists():raise ValueError('Retry must refer to an unsealed prior run')
        run_id=now.strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
        folder=ROOT/'reports/daily'/run_id;folder.mkdir(parents=True,exist_ok=False)
        rel=str(folder.relative_to(ROOT));pointer_sha=sha(pointer_path)
        create(folder/'started.json',dict(created_at_shanghai=now.isoformat(),through=str(through),previous_checkpoint=current['checkpoint'],retry_of=args.retry_of,offline_replay=bool(args.candidate)))
        try:
            candidate=args.candidate or run_id+'-prices';official=args.official or run_id+'-official'
            if not args.candidate:
                env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
                result=subprocess.run([sys.executable,str(ROOT/'scripts/collect_update.py'),'--through',str(through),'--output',str(ROOT/'data/snapshots'/candidate)],env=env,capture_output=True,text=True)
                create(folder/'collector_result.json',dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
                if result.returncode:raise ValueError('Price collector failed; see captured output')
                collect_official(ROOT/'data/snapshots'/official)
            data,admission=load_incremental(ROOT/'data/snapshots',candidate)
            if data.sessions[-1]!=through:raise ValueError('Candidate horizon mismatch')
            create(folder/'admission.json',admission)
            create(folder/'official_close.json',official_audit(official,candidate,through))
            inputs=dependencies(current)
            for name in inputs:
                if name.endswith('.py') and name.startswith(('src/','scripts/')):
                    saved=folder/'implementation'/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes((ROOT/name).read_bytes())
            state=advance(data,previous);create(folder/'forward_checkpoint.json',state)
            create(folder/'intent_check.json',check_execution(read(ROOT/'reports/2026-11-06-intent/plan.json'),state))
            create(folder/'reconciliation.json',reconcile(data,previous,state))
            config=read(ROOT/'config/research.json');config['forward_checkpoint']=rel+'/forward_checkpoint.json';create(folder/'research.json',config)
            extra=read(ROOT/'config/risk_extensions.json');extra.update(forward_price_snapshot=candidate,published_report=rel+'/risk_extensions.json');create(folder/'risk_extensions_config.json',extra)
            pages=folder/'site';pages.mkdir()
            risk_build(folder/'research.json',folder/'risk.json',pages/'risk.html')
            extension_build(folder/'risk_extensions.json',pages/'exposure.html',folder/'research.json',folder/'risk_extensions_config.json')
            # Existing page generators use paths relative to ROOT/site. Rebase for bundle/site.
            for p in pages.glob('*.html'):
                text=p.read_text().replace('href="../','href="../../../../')
                text=text.replace('href="../../../../config/research.json"','href="../research.json"').replace('href="../../../../reports/2026-11-06-close/risk.json"','href="../risk.json"').replace('href="../../../../reports/2026-11-06-close/PROGRESS.md"','href="index.html"')
                p.write_text(text,encoding='utf-8')
            shutil.copyfile(ROOT/'site/style.css',pages/'style.css')
            main=state['portfolios']['monthly_50_50_base']['daily'][-1]
            text='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>每日研究检查点</title><link rel="stylesheet" href="style.css"><main><h1>每日研究检查点 · '+state['as_of']+'</h1><p>前瞻 '+str(state['forward_sessions'])+' 个观察日；仅研究模拟。样本不足时年化和窗口风险为空。目标、模型成交、实际成交证据分别处理。</p><section><h2>50/50基准费用观察组合</h2><p>收盘净值 '+html.escape(main['equity'])+' 元；现金 '+html.escape(main['cash'])+' 元。完整对账见报告，不代表实际成交或未来收益。</p></section><nav><a href="risk.html">风险监控</a><a href="exposure.html">Beta与披露穿透</a><a href="../../../../site/index.html">独立历史研究</a><a href="../reconciliation.json">逐日会计核对</a><a href="../intent_check.json">11月6日冻结目标对账</a><a href="../admission.json">数据准入</a><a href="../official_close.json">官方价格复核</a><a href="../forward_checkpoint.json">检查点</a><a href="../manifest.json">完整性清单</a></nav><p>日报未接实盘；模拟成交价可能超出日线范围。公告变化会阻断更新，完整停复牌及实际成交证据仍有限。</p></main></html>'
            (pages/'index.html').write_text(text,encoding='utf-8')
            for name,value in inputs.items():
                if sha(ROOT/name)!=value:raise ValueError('Source changed during build')
            new=dict(schema_version=1,as_of=state['as_of'],checkpoint=rel+'/forward_checkpoint.json',checkpoint_sha256=state['checkpoint_sha256'],bundle=rel,dashboard=rel+'/site/index.html',research_config=rel+'/research.json',extensions_config=rel+'/risk_extensions_config.json')
            create(folder/'ready.json',dict(previous_pointer_sha256=pointer_sha,input_sha256=inputs,pointer=new))
            seal(folder)
        except Exception as e:
            if not (folder/'manifest.json').exists():create(folder/'failure.json',dict(error_type=type(e).__name__,error=str(e),account_published=False))
            raise
        status='prepared' if getattr(args,'prepare_only',False) else promote(ROOT,folder,pointer_path)
        return dict(status=status,bundle=rel,as_of=state['as_of'],forward_sessions=state['forward_sessions'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pointer',default='config/active_run.json');p.add_argument('--through',type=date.fromisoformat);p.add_argument('--candidate');p.add_argument('--official');p.add_argument('--rebuild',action='store_true');p.add_argument('--resume');p.add_argument('--retry-of');p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    print(json.dumps(run(a),ensure_ascii=False))
