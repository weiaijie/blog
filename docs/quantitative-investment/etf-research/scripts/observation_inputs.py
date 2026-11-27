"""Assemble evidence-bound features in validation mode without creating forecasts."""
import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import collect_sse_research_day as sse
import market_state_pilot as pilot
from observation_price_inputs import establish_price_source
from observation_archive import archive_for_day
from observation_policy_inputs import load_policy_context
from etf_research.admission import sessions_between
from etf_research.observation_experiment import BASE, GROUPS, DECISION_TIME, relative_turnover
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, read, sha

ROOT = sse.ROOT
FEATURES = BASE + tuple(name for names in GROUPS.values() for name in names)
EVIDENCE_ERRORS = (OSError, ValueError, KeyError, TypeError, ArithmeticError)


def date_context(project, entry):
    path = project/'data/snapshots/2026-11-04-calendar-08/calendar.json'
    if sha(path)!=sse.CALENDAR_SHA:
        raise ValueError('Observation calendar digest mismatch')
    ranges = read(path)['holiday_ranges']
    rows = sessions_between(ranges,entry-timedelta(days=60),entry)
    if len(rows)<22 or rows[-1]!=entry:
        raise ValueError('Decision not on a verified trading session or insufficient calendar lookback')
    return rows[-22:-1]




def turnover_warmup(project, ceiling):
    stored = read(project/'reports/2026-11-27-policy-pilot/market-state.json')
    if instant(stored['featureReadyAt'])>ceiling:
        return {}
    if stored!=pilot.build(stored['featureReadyAt'], project=project):
        raise ValueError('Warm-up turnover audit did not reproduce')
    path = project/stored['snapshot']/'manifest.json'
    return {row['date']:dict(amount=row['turnoverCny'],readyAt=stored['featureReadyAt'],
                            receivedAt=stored['receivedAt'],
                            refs=[dict(root='prices',path=path.relative_to(project).as_posix(),
                                       sha256=stored['snapshotSha256'])]) for row in stored['rows']}


def feature(anchor, value, received, dependencies, proofs):
    """Record the source clocks before the actual calculation time is assigned."""
    if value is None:
        raise ValueError('Cannot construct a verified unknown observation')
    return dict(asOf=str(anchor),value=value,verified=True,receivedAt=received,
                dependencyReadyAt=sorted(set(dependencies)),evidence=proofs)


def assemble(project, observations, store, entry, observed, *, computed=None):
    project,observations,store = (path.resolve() for path in (project,observations,store))
    dates = date_context(project,entry)
    anchor = dates[-1]
    deadline = datetime.combine(entry,DECISION_TIME,TZ)
    ceiling = min(deadline,observed)
    cells = dict.fromkeys(FEATURES)
    gaps = {}
    price_gap = 'price_publication_or_matching_closes_not_ready'
    try:
        closes = establish_price_source(project,anchor,dates,ceiling)
    except EVIDENCE_ERRORS:
        closes = None
        price_gap = 'price_publication_proof_invalid'
    for symbol,names in zip(('510300','511010'),(BASE[:3],BASE[3:6]),strict=True):
        if closes and symbol in closes['values']:
            for name,value in zip(names,closes['values'][symbol],strict=True):
                available = closes['availableAt']
                cells[name] = feature(anchor,value,available,[available],closes['evidence'])
        else:
            gaps.update(dict.fromkeys(names,price_gap))

    config = read(observations/'config/research_observation.json')
    selected,issues = {},{}
    for day in dates:
        try:
            result,issue = archive_for_day(observations,store,day,ceiling,config)
        except EVIDENCE_ERRORS:
            result,issue = None,'archive_proof_invalid'
        if result is not None:
            selected[day] = result
        else:
            issues[str(day)] = issue
    warm_status = 'required_turnover_not_ready'
    try:
        warm = turnover_warmup(project,ceiling)
    except EVIDENCE_ERRORS:
        warm = {}
        warm_status = 'warmup_proof_invalid'
    amounts, amount_sources, missing = [], [], []
    for day in dates:
        current = selected.get(day)
        if current and current['sse']['turnoverCny'] is not None:
            source = dict(amount=current['sse']['turnoverCny'],receivedAt=current['sse']['receivedAt'],
                          readyAt=current['readyAt'],refs=current['refs'])
        else:
            source = warm.get(str(day)) if day!=anchor and issues.get(str(day))!='archive_proof_invalid' else None
        if source is not None:
            amounts.append(float(source['amount']))
            amount_sources.append(source)
        else:
            missing.append(str(day))
    if not missing:
        refs = {tuple(ref.items()):ref for source in amount_sources for ref in source['refs']}
        cells['turnover20'] = feature(anchor,relative_turnover(amounts),
            max((p['receivedAt'] for p in amount_sources),key=instant),
            [p['readyAt'] for p in amount_sources],list(refs.values()))
    else:
        gaps['turnover20'] = dict(missingSessions=missing,reason=warm_status)

    current = selected.get(anchor)
    candidate_count = None
    if current:
        fund_snapshot,market,ready,refs = (current[k] for k in ('policyEtf','sse','readyAt','refs'))
        if fund_snapshot['policy']['status']=='archived':
            candidate_count = len(fund_snapshot['policy']['candidates'])
        for symbol,name in zip(('510300','511010'),GROUPS['etf'],strict=True):
            row = next(item for item in fund_snapshot['etf'] if item['symbol']==symbol)
            if row['status']=='verified_estimate' and row['relativeIntensity'] is not None:
                cells[name] = feature(anchor,row['relativeIntensity'],
                            fund_snapshot['receivedAt'],[ready,row['featureReadyAt']],refs)
            else:
                gaps[name] = dict(reason='same_valuation_day_basis_missing',sourceIssues=row['issues'])
        if market['margin'] is not None and market['margin']['financingBuyShare'] is not None:
            cells['stockFinancingBuyShare'] = feature(anchor,market['margin']['financingBuyShare'],
                market['receivedAt'],[ready,market['featureReadyAt']],refs)
        else:
            gaps['stockFinancingBuyShare'] = dict(reason='matched_margin_basis_missing',sourceIssues=market['issues'])
    else:
        gaps.update(dict.fromkeys((*GROUPS['etf'],*GROUPS['margin']),issues[str(anchor)]))
    # The unreviewed candidate stream contains repeated and older URLs. No count is implied.
    gaps['policyActiveCount'] = dict(reason='five_decision_intervals_without_certified_review',
                                    capturedCandidateCount=candidate_count,
                                    evidence=current['refs'] if current else [])
    policy = None
    try:
        policy = load_policy_context(observations,store,dates,entry,ceiling)
    except EVIDENCE_ERRORS:
        gaps['policyActiveCount']['reason'] = 'policy_review_proof_invalid'
    if policy is not None:
        if policy['count'] is None:
            gaps['policyActiveCount']['reviewedScope'] = policy
        else:
            references = {tuple(ref.items()):ref for ref in [*policy['reviewEvidence'],*policy['pollEvidence']]}
            cells['policyActiveCount'] = feature(anchor,policy['count'],policy['reviewReadyAt'],
                                                  policy['dependencyReadyAt'],list(references.values()))
            cells['policyActiveCount']['eventIds'] = policy['eventIds']
            del gaps['policyActiveCount']
    complete = datetime.now(timezone.utc) if computed is None else computed
    if observed>complete:
        raise ValueError('Calculation time precedes observation start')
    for cell in cells.values():
        if cell is not None:
            cell['readyAt'] = complete.isoformat()
    return dict(schemaVersion=1,runKind='validation',inputSealedForForecast=False,
                entryDay=str(entry),anchorDay=str(anchor),observedAt=observed.isoformat(),
                computedAt=complete.isoformat(),deadline=deadline.isoformat(),evidenceCutoff=ceiling.isoformat(),
                lookbackSessions=list(map(str,dates)),cells=cells,gaps=gaps)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--entry',type=date.fromisoformat)
    action.add_argument('--verify',type=Path)
    parser.add_argument('--price-project',type=Path,default=ROOT)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.verify:
        saved = read(args.verify)
        result = assemble(args.price_project,args.observation_root,args.archive_store,
                          date.fromisoformat(saved['entryDay']),instant(saved['observedAt']),
                          computed=instant(saved['computedAt']))
        if saved != result:
            raise ValueError('Stored input probe does not reproduce')
    else:
        if args.output is None:
            parser.error('--entry requires --output')
        result = assemble(args.price_project,args.observation_root,args.archive_store,
                          args.entry,datetime.now(timezone.utc))
        create(args.output,result)
    print('PASS',result['entryDay'],sum(value is not None for value in result['cells'].values()),
          'verified feature values; remaining',','.join(result['gaps']))
