"""Summarize the frozen account ledger at registered calendar anniversaries."""
import argparse
from bisect import bisect_left
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D
from functools import lru_cache
import json
from pathlib import Path

from observation_price_inputs import admitted_operation, published_account_bundle
from review_recovery import episodes
from etf_research.admission import completed_date, sessions_between
from etf_research.baselines import SCENARIOS, STRATEGIES
from etf_research.exchange_calendar import calendar_at
from etf_research.forward import PROTOCOL, START, digest, engine_digest
from etf_research.policy_events import TZ, instant
from etf_research.publication import inside, read, sha, verify_bundle

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = (6,12,24)
COST_KEYS = ('commissions','sell_tax','slippage_cost')


def anniversary(start, months):
    year, month = divmod(start.month-1+months,12)
    year, month = start.year+year,month+1
    return date(year,month,min(start.day,monthrange(year,month)[1]))


@lru_cache(maxsize=2)
def load_active(root, payload):
    pointer=json.loads(payload)
    folder=inside(root,pointer['bundle'])
    checkpoint=inside(root,pointer['checkpoint'])
    if checkpoint!=folder/'forward_checkpoint.json':
        raise ValueError('Forward checkpoint is outside the active bundle')
    verify_bundle(folder)
    if sha(folder/'manifest.json')!=pointer['bundle_manifest_sha256']:
        raise ValueError('Forward bundle digest mismatch')
    state=read(checkpoint)
    if (pointer['checkpoint_sha256']!=state['checkpoint_sha256']
            or pointer['as_of']!=state['as_of']):
        raise ValueError('Active pointer differs from account checkpoint')
    return state


def amount(value, *, positive=False):
    result=D(value)
    if not result.is_finite() or result<0 or (positive and not result):
        raise ValueError('Invalid amount in forward ledger')
    return result


def metric(portfolio, days, *, annualized=False):
    ledger=portfolio['daily'][:len(days)]
    nav=[amount(row['equity'],positive=True) for row in ledger]
    if nav[0]!=amount(portfolio['summary']['initial_cash'],positive=True):
        raise ValueError('Initial cash does not match the first forward close')
    day_end=days[-1].isoformat()
    trades=[row for row in portfolio['journal'] if row['kind']=='trade' and row['day']<=day_end]
    commissions=sum((amount(row['commission']) for row in trades),D(0))
    tax=sum((amount(row['tax']) for row in trades),D(0))
    slippage=sum((abs(amount(row['fill_price'],positive=True)-amount(row['raw_price'],positive=True))
                  *amount(row['units'],positive=True) for row in trades),D(0))
    recovery=max(episodes(days,nav),key=lambda row:row['depth'],default=None)
    duration=(days[-1]-days[0]).days
    gain=nav[-1]/nav[0]-1
    rate=(nav[-1]/nav[0])**(D('365.25')/duration)-1 if annualized else None
    drawdown=None
    if recovery is not None:
        drawdown=dict(peakOn=recovery['peak'].isoformat(),troughOn=recovery['trough'].isoformat(),
                      recoveredOn=recovery['recovery'].isoformat() if recovery['recovery'] else None,
                      peakToTroughSessions=recovery['peak_to_trough'],
                      peakToRecoverySessions=recovery['peak_to_end'] if recovery['recovery'] else None,
                      troughToRecoverySessions=recovery['trough_to_recovery'],
                      underwaterCloses=recovery['underwater_closes'])
    return dict(initialCny=str(nav[0]),endingCny=str(nav[-1]),netPnlCny=str(nav[-1]-nav[0]),
                netReturn=float(gain),netAnnualized=float(rate) if rate is not None else None,
                atLeast4Pct=rate>=D('.04') if rate is not None else None,
                atLeast5Pct=rate>=D('.05') if rate is not None else None,
                maxCloseDrawdown=float(recovery['depth']) if recovery else 0.0,recovery=drawdown,
                trades=len(trades),commissionsCny=str(commissions),taxCny=str(tax),
                slippageCny=str(slippage),totalCostCny=str(commissions+tax+slippage))


def screen(portfolios, days, *, annualized=False, reconcile=False):
    rows={}
    for name,portfolio in portfolios.items():
        summary=portfolio['summary']
        row=metric(portfolio,days,annualized=annualized)
        if reconcile and (D(row['endingCny'])!=D(summary['ending_equity'])
                or row['trades']!=summary['trades']
                or any(D(row[key])!=D(summary[old]) for key,old in zip(
                    ('commissionsCny','taxCny','slippageCny'),COST_KEYS))
                or abs(row['maxCloseDrawdown']+summary['max_close_drawdown'])>1e-12):
            raise ValueError('Forward drawdown, trade costs or equity do not reconcile: '+name)
        rows[name]=dict(**row,strategy=summary['strategy'],scenario=summary['scenario'])
    for row in rows.values():
        scenario=row['scenario']
        row['netReturnVsBond']=row['netReturn']-rows['bond_hold_'+scenario]['netReturn']
        row['netReturnVsCash']=row['netReturn']-rows['cash_'+scenario]['netReturn']
    return rows


def report(root, state, observed):
    checksum=state['checkpoint_sha256']
    as_of=date.fromisoformat(state['as_of'])
    if (state['format']!=1 or state['real_money'] is not False or state['protocol_commit']!=PROTOCOL
            or state['engine_sha256']!=engine_digest() or state['forward_start']!=START.isoformat()
            or as_of>completed_date(observed)
            or digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})!=checksum):
        raise ValueError('Unverified frozen account checkpoint')
    portfolios=state['portfolios']
    expected={f'{strategy}_{scenario}' for strategy in STRATEGIES for scenario in SCENARIOS}
    if set(portfolios)!=expected:
        raise ValueError('Missing frozen accounts')
    calendar=calendar_at(root,observed)
    days=sessions_between(calendar.ranges,START,as_of)
    iso_days=[day.isoformat() for day in days]
    if not days or days[0]!=START or days[-1]!=as_of or len(days)!=state['forward_sessions']:
        raise ValueError('Forward dates do not match the verified calendar')
    known=set(iso_days)
    for name,portfolio in portfolios.items():
        summary=portfolio['summary']
        journal=portfolio['journal']
        if ([row['date'] for row in portfolio['daily']]!=iso_days
                or name!=summary['strategy']+'_'+summary['scenario']
                or any(row['day'] not in known for row in journal)):
            raise ValueError('Forward valuation or journal dates differ: '+name)
    windows=[]
    for months in WINDOWS:
        due=anniversary(START,months)
        end=bisect_left(days,due)
        complete=end<len(days)
        stats=screen(portfolios,days[:end+1],annualized=months>=12) if complete else None
        windows.append(dict(months=months,anniversary=due.isoformat(),state='complete' if complete else 'accumulating',
                            endSession=days[end].isoformat() if complete else None,
                            valuationSessions=end+1 if complete else None,accounts=stats))
    return dict(schemaVersion=1,asOf=as_of.isoformat(),anchorOn=START.isoformat(),
                valuationSessions=len(days),returnIntervals=len(days)-1,
                firstReturnSession=iso_days[1] if len(days)>1 else None,
                calendarDays=(as_of-START).days,calendarSha256=calendar.digest,checkpointSha256=checksum,
                protocolCommit=PROTOCOL,realMoney=False,terminalLiquidationIncluded=False,
                milestones=windows,progress=screen(portfolios,days,reconcile=True))


def reconcile_milestone(current, original):
    end = original['as_of']
    for name, portfolio in original['portfolios'].items():
        later = current['portfolios'][name]
        if (later['daily'][:len(portfolio['daily'])]!=portfolio['daily']
                or [entry for entry in later['journal'] if entry['day']<=end]!=portfolio['journal']):
            return False
    return True


def prove_milestones(root,state,observed,result):
    """Attach each completed window to the first exact-day account publication."""
    calendar = calendar_at(root,observed)
    as_of = date.fromisoformat(state['as_of'])
    local = observed.astimezone(TZ).date()
    for milestone in result['milestones']:
        due = date.fromisoformat(milestone['anniversary'])
        if str(due.year) not in calendar.ranges:
            if local>=due:
                milestone['state'] = 'calendar_unverified'
            continue
        horizon = min(date(due.year,12,31),due+timedelta(days=31))
        possible = sessions_between(calendar.ranges,due,horizon)
        if not possible:
            if local>=due:
                milestone['state'] = 'calendar_unverified'
            continue
        session = possible[0]
        milestone['expectedEndSession'] = session.isoformat()
        if session>as_of:
            if session<=completed_date(observed):
                milestone['state'] = 'awaiting_valuation'
            continue

        prior, milestone['accounts'] = milestone['accounts'],None
        milestone['state'] = 'publication_unverified'
        try:
            entry=admitted_operation(root,session,observed,require_account_binding=True,first=True)
            if entry is None:
                milestone['state'] = 'awaiting_publication'
                continue
            operation,folder = entry
            pointer,bundle,available,_ = published_account_bundle(root,operation,observed)
            original=read(bundle/'forward_checkpoint.json')
            if (original['as_of']!=session.isoformat() or original['as_of']!=pointer['as_of']
                    or original['checkpoint_sha256']!=pointer['checkpoint_sha256']):
                continue
            checked=report(root,original,available)
            exact=next(row for row in checked['milestones'] if row['months']==milestone['months'])
            if exact['state']!='complete' or exact['endSession']!=session.isoformat():
                continue
            milestone['publication'] = dict(availableAt=available.astimezone(TZ).isoformat(),
                checkpointSha256=original['checkpoint_sha256'],
                operation=folder.relative_to(root).as_posix(),operationManifestSha256=sha(folder/'manifest.json'),
                bundleManifestSha256=pointer['bundle_manifest_sha256'],calendarSha256=checked['calendarSha256'])
            if prior!=exact['accounts'] or not reconcile_milestone(state,original):
                milestone['state'] = 'ledger_conflict'
                continue
            milestone['state'] = 'complete'
            milestone['accounts'] = exact['accounts']
        except (OSError,ValueError,KeyError,TypeError,ArithmeticError):
            continue
    return result


def active_report(root=ROOT):
    state=load_active(root,(root/'config/active_run.json').read_bytes())
    observed=datetime.now(timezone.utc)
    return prove_milestones(root,state,observed,report(root,state,observed))


def publication_report(root, observed, *, checkpoint=None):
    anchor = date.fromisoformat(checkpoint['as_of']) if checkpoint is not None else None
    selected = admitted_operation(root,anchor,observed,require_account_binding=True)
    if selected is None:
        return None
    operation,folder = selected
    pointer,bundle,available,_ = published_account_bundle(root,operation,observed)
    state = read(bundle/'forward_checkpoint.json')
    if (state['as_of']!=pointer['as_of'] or state['checkpoint_sha256']!=pointer['checkpoint_sha256']
            or (checkpoint is not None and state!=checkpoint)):
        raise ValueError('Checkpoint does not match the verified publication')
    result = report(root,state,observed)
    result['publication'] = dict(observedAt=observed.astimezone(TZ).isoformat(),
                                 availableAt=available.astimezone(TZ).isoformat(),
                                 mode=operation['mode'],operation=folder.relative_to(root).as_posix(),
                                 operationManifestSha256=sha(folder/'manifest.json'),
                                 bundleManifestSha256=pointer['bundle_manifest_sha256'])
    return prove_milestones(root,state,observed,result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--observed-at',type=instant)
    options=parser.parse_args()
    state=read(options.checkpoint) if options.checkpoint else None
    now=datetime.now(timezone.utc)
    if options.observed_at is not None:
        if options.observed_at>now:
            parser.error('Publication cutoff cannot be in the future')
        result=publication_report(ROOT,options.observed_at,checkpoint=state)
        if result is None:
            parser.error('No verified account publication by the requested cutoff')
    elif state is not None:
        result=report(ROOT,state,now)
    else:
        result=active_report(ROOT)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
