"""Evaluate sealed forecasts on the registered schedule and keep missing observations visible."""
import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from observation_decision_status import FIRST_DECISION, decision_counts, decision_row
from observation_forecast_status import forecast_row
from observation_label_status import label_counts, label_row
from observation_labels import EVIDENCE_ERRORS
from observation_status import archive_index, expected_days
from review_policy_observations import review_progress
from seal_observation_decision import first_archive
from etf_research.admission import sessions_between
from etf_research.baselines import SCENARIOS
from etf_research.exchange_calendar import calendar_at
from etf_research.observation_experiment import (
    CAPITAL, HORIZON, MIN_EVENTS, MIN_QUARTERS, MIN_TEST, VARIANTS, holdouts, label_floor,
    nonoverlap, paired_report, shadow_weight, shifted_month, windows,
)
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, read

ROOT=Path(__file__).resolve().parents[1]
ALLOCATION={'stock_bond_50_50':Decimal('.5'),'bond_100':Decimal(0)}
METRICS=('terminalReturn','maxDrawdown','commission','slippage','endingCash','availableCash','dividendReceivable')
VARIANT_NAMES=tuple(name for name in VARIANTS if name!='baseline')
UNVERIFIED_EVIDENCE={
    'decision_unverified','forecast_unverified','forecast_calendar_unverified',
    'label_unverified','label_calendar_unverified','label_outcome_unverified',
}
WAITING_LABELS={'label_holding_period_incomplete','label_mature_unsealed','label_pending_archive'}


def calendar_plan(root, started, observed=None):
    observed = observed if observed is not None else datetime.now(timezone.utc)
    ranges=calendar_at(root,observed).ranges
    schedules={}
    for start,end in holdouts(started):
        days,unknown=expected_days(root,start,end-timedelta(days=1),observed=observed)
        before=()
        if days:
            try:
                before=sessions_between(ranges,start-timedelta(days=31),start-timedelta(days=1))
            except ValueError:
                unknown=next((year for year in range(start.year-1,start.year+1) if str(year) not in ranges),unknown)
        candidates=tuple(windows((before[-1],*days))) if before else ()
        schedules[start]=dict(end=end,calendar=tuple(days),windows=candidates,
                              economic={window.entry for window in nonoverlap(candidates)},unknownYear=unknown)
    return schedules


def label_projection(label):
    if label['status']!='evidence_complete':
        return None
    result=label['latest']
    return dict(readyAt=label['readyAt'],archiveSha256=result['archiveSha256'],
                results=result['results'])


def observed_days(root,store,origin,schedules,as_of):
    chosen,models={},{}
    for start,phase in schedules.items():
        for window in phase['windows']:
            if window.cutoff>as_of:
                continue
            day=window.entry
            decision=decision_row(root,store,day,as_of,planned=True)
            forecast=forecast_row(root,store,day,as_of,origin,decision,details=True,models=models)
            label=label_row(root,store,day,as_of,decision,details=True)
            chosen[day]=dict(window=window,fold=start,decision=decision,forecast=forecast,label=label,
                             economic=day in phase['economic'])
    return chosen


def has_unverified(row):
    return row.get('status')=='unverified' or any(
        attempt['status']=='unverified' for attempt in row.get('attempts',()))


def label_gap(label):
    if has_unverified(label):
        return 'label_unverified'
    if any(attempt['status']=='pending_archive' for attempt in label.get('attempts',())):
        return 'label_pending_archive'
    return 'label_'+label['status']


def comparison_rows(observations,variant):
    paired,staged,days=[],{},[]
    previous_events=set()
    fold_events=set()
    active_fold=None
    for day,state in sorted(observations.items()):
        window,fold=state['window'],state['fold']
        if active_fold != fold:
            previous_events.update(fold_events)
            fold_events.clear()
            active_fold=fold
        forecast,label = state['forecast'],state['label']
        last=forecast['latest'] or {}
        info=last.get('comparisons',{}).get(variant,{})
        record=dict(entryDay=str(day),lastSession=str(window.last),fold=str(fold),
                    forecastStatus=forecast['status'],labelStatus=label['status'],reason=None,
                    nonoverlapSelected=state['economic'])
        if forecast['status']!='sealed_predictions' or variant not in forecast['sealedVariants']:
            if has_unverified(forecast) or last.get('reason')=='evidence_unavailable':
                record['reason']='forecast_unverified'
            elif has_unverified(state['decision']):
                record['reason']='decision_unverified'
            else:
                record['reason']=(info.get('status') if info.get('status')!='predicted' else None) or (
                    last.get('reason') or 'forecast_'+forecast['status'])
        else:
            events=tuple(sorted(set(info['eventIds'])))
            if previous_events.intersection(events):
                record['reason']='policy_event_previously_seen'
            else:
                fold_events.update(events)
                archived=label_projection(label)
                record.update(forecastSealedAt=forecast['readyAt'],forecastArchiveSha256=last['archiveSha256'],
                              modelArchiveSha256=last['modelArchiveSha256'],eventIds=list(events))
                if archived:
                    record.update(labelReadyAt=archived['readyAt'],labelArchiveSha256=archived['archiveSha256'])
                    try:
                        actual=audit_outcome(archived['results']['stock_bond_50_50']['base'])
                    except EVIDENCE_ERRORS:
                        record['reason']='label_outcome_unverified'
                    else:
                        staged[day]=dict(value=actual,readyAt=archived['readyAt'])
                else:
                    record['reason']=label_gap(label)
                    missing_proof=label.get('latest') or {}
                    if label['status']=='evidence_missing' and missing_proof.get('archiveSha256'):
                        record['labelArchiveSha256']=missing_proof['archiveSha256']
                paired.append(dict(window=window,fold=fold,inputsSealedAt=state['decision']['latest']['archivedAt'],
                                   forecastSealedAt=forecast['readyAt'],eventIds=events,
                                   baseline=info['baseline'],expanded=info['expanded']))
        days.append(record)
    return paired,staged,days


def audit_outcome(outcome):
    for name in ('terminalReturn','maxDrawdown','commission','slippage'):
        value=Decimal(outcome[name])
        if not value.is_finite() or (name!='terminalReturn' and value<0) or (name=='maxDrawdown' and value>1):
            raise ValueError('Invalid sealed outcome metric')
    marks=[Decimal(value) for value in outcome['marks']]
    if (len(marks)!=HORIZON+1 or marks[0]!=CAPITAL or any(not mark.is_finite() or mark<0 for mark in marks)
            or marks[-1]/CAPITAL-1!=Decimal(outcome['terminalReturn'])):
        raise ValueError('Sealed return does not reconcile with the close marks')
    running=CAPITAL
    dips=[]
    for mark in marks:
        running=max(running,mark)
        dips.append(1-mark/running)
    if max(dips)!=Decimal(outcome['maxDrawdown']):
        raise ValueError('Sealed drawdown does not reconcile with the close marks')
    orders=outcome['orders']
    if any(type(row['requested']) is not int or type(row['filled']) is not int
           or not 0<=row['filled']<=row['requested'] or row['requested']%100 or row['filled']%100
           for row in orders.values()):
        raise ValueError('Invalid sealed entry order coverage')
    amounts={}
    for name in ('endingCash','availableCash','dividendReceivable'):
        value=outcome.get(name)
        if value is None:
            amounts[name]=None
        else:
            amount=Decimal(value)
            if not amount.is_finite() or amount<0:
                raise ValueError('Invalid sealed cash amount')
            amounts[name]=str(amount)
    if amounts['availableCash'] and amounts['endingCash'] and Decimal(amounts['availableCash'])>Decimal(amounts['endingCash']):
        raise ValueError('Available cash exceeds the ledger balance')
    return dict(**{name:str(outcome[name]) for name in METRICS[:4]},**amounts,
                unfilledOrders=sum(row['requested']>row['filled'] for row in orders.values()),orders=orders)


def economic_report(selected, predictions, observations, *, publish):
    by_day={row['window'].entry:row for row in predictions}
    accepted=[]
    unresolved={}
    for day in sorted(selected):
        item=by_day.get(day)
        if item is None:
            unresolved[str(day)]='paired_forecast_missing'
            continue
        label=label_projection(observations[day]['label'])
        if label is None:
            unresolved[str(day)]=label_gap(observations[day]['label'])
            continue
        choices=dict(fixed_50_50='stock_bond_50_50',bond_only='bond_100')
        for name in ('baseline','expanded'):
            weight=shadow_weight(item[name])
            choices[name]=next(key for key,value in ALLOCATION.items() if value==weight)
        try:
            values={book:{scenario:audit_outcome(label['results'][allocation][scenario]) for scenario in SCENARIOS}
                    for book,allocation in choices.items()}
        except EVIDENCE_ERRORS:
            unresolved[str(day)]='economic_outcome_unverified'
            continue
        accepted.append(dict(entryDay=str(day),lastSession=str(item['window'].last),choices=choices,
                             labelArchiveSha256=label['archiveSha256'],outcomes=values))
    result=dict(selectedWindows=len(selected),matchedWindows=len(accepted),gaps=unresolved)
    if publish and 'economic_outcome_unverified' in unresolved.values():
        result['status']='economic_evidence_unverified'
    elif publish and accepted:
        result['windows']=accepted
        result['averages']={}
        for book in accepted[0]['outcomes']:
            result['averages'][book]={}
            for scenario in SCENARIOS:
                outcomes=[row['outcomes'][book][scenario] for row in accepted]
                totals={}
                for field in METRICS:
                    valid=[Decimal(row[field]) for row in outcomes if row[field] is not None]
                    totals[field]=str(sum(valid)/len(valid)) if valid else None
                    if field in ('endingCash','availableCash','dividendReceivable'):
                        totals[field+'KnownWindows']=len(valid)
                totals['windowsWithUnfilledOrders']=sum(row['unfilledOrders']>0 for row in outcomes)
                result['averages'][book][scenario]=totals
    return result


def evaluate(root,store,observed):
    origin=first_archive(root,store,observed)
    stamp=dict(schemaVersion=1,asOf=observed.isoformat(),studyOrigin=origin,
               thresholds=dict(pairs=MIN_TEST,folds=MIN_QUARTERS,policyEvents=MIN_EVENTS))
    if origin is None:
        return dict(stamp,status='observation_origin_pending',comparisons={},folds=[])
    start=date.fromisoformat(origin['date'])
    end=shifted_month(start,12)
    phase=calendar_plan(root,start,observed)
    observations=observed_days(root,store,origin,phase,observed)
    today=observed.astimezone(TZ).date()
    data_complete=all(row['unknownYear'] is None for row in phase.values())
    last_close=max((label_floor(w) for row in phase.values() for w in row['windows']),default=None)
    final_time=today>=end and (last_close is None or observed>=last_close)
    status='observation_in_progress' if not final_time else 'calendar_unverified' if not data_complete else 'evaluation_available'

    selected={key for key,item in observations.items() if item['economic'] and label_floor(item['window'])<=observed}
    comparisons={}
    for variant in VARIANT_NAMES:
        predictions,labels,days=comparison_rows(observations,variant)
        known=[p for p in predictions if p['window'].entry in labels]
        events={event for p in known for event in p['eventIds']}
        periods={p['fold'] for p in known}
        reasons={row['reason'] for row in days}
        group_status=status
        if status=='evaluation_available':
            if reasons & UNVERIFIED_EVIDENCE:
                group_status='final_evidence_unverified'
            elif reasons & WAITING_LABELS:
                group_status='final_labels_pending'
        publish=group_status=='evaluation_available'
        counts=dict(completedPairs=len(known),quarters=len(periods),independentEvents=len(events))
        missing=dict(pairs=max(0,MIN_TEST-len(known)),folds=max(0,MIN_QUARTERS-len(periods)),
                     policyEvents=max(0,MIN_EVENTS-len(events)) if 'policyActiveCount' in VARIANTS[variant] else 0)
        if publish:
            scores=paired_report(predictions,labels,{key:value['calendar'] for key,value in phase.items()},
                                 started_at=origin['archiveVerifiedAt'],observed=observed,variant=variant)
        else:
            scores=dict(**counts,status=group_status)
        fold_counts={str(fold):dict(sealedPairs=sum(item['fold']==fold for item in predictions),
                                    completedPairs=sum(item['fold']==fold for item in known),
                                    independentEvents=len({event for item in known if item['fold']==fold
                                                           for event in item['eventIds']}))
                     for fold in phase}
        comparisons[variant]=dict(score=scores,shortfall=missing,coverage=days,foldCoverage=fold_counts,
                                  economics=economic_report(selected,predictions,observations,publish=publish))
    if status=='evaluation_available':
        states={group['score']['status'] for group in comparisons.values()}
        status=next((blocker for blocker in ('final_evidence_unverified','final_labels_pending')
                     if blocker in states),status)
    folds=[dict(start=str(key),end=str(value['end']),eligibleCalendarDays=len(value['windows']),
                observedDecisionDays=sum(item['fold']==key for item in observations.values()),
                missingCalendarYear=value['unknownYear']) for key,value in phase.items()]
    return dict(stamp,status=status,midtermOn=str(shifted_month(start,6)),finalOn=str(end),folds=folds,comparisons=comparisons)


def midterm_review(root, store, current, *, reuse_archive=False):
    if current['studyOrigin'] is None:
        return None
    due = date.fromisoformat(current['midtermOn'])
    cutoff = datetime.combine(due,time.min,TZ)
    if instant(current['asOf']) < cutoff:
        return None

    origin = current['studyOrigin']
    if reuse_archive:
        from observation_evaluation_status import latest_evaluation
        previous,_ = latest_evaluation(root,store,instant(current['asOf']))
        checkpoint = previous[1].get('midtermReview') if previous else None
        if checkpoint is not None:
            if checkpoint['studyOrigin'] != origin or instant(checkpoint['cutoffAt']) != cutoff:
                raise ValueError('Sealed midterm review is bound to a different origin or cutoff')
            return checkpoint

    origin_time = instant(origin['archiveVerifiedAt'])
    start = date.fromisoformat(origin['date'])
    frozen = evaluate(root,store,cutoff)
    if frozen['studyOrigin'] != origin:
        raise ValueError('Midterm cutoff is bound to a different observation origin')

    sessions,missing_year = expected_days(root,start,due-timedelta(days=1),observed=cutoff)
    config = read(root/'config/research_observation.json')
    archives,issues = archive_index(root,store,config,cutoff,days=sessions)
    states = Counter()
    for day in sessions:
        key = str(day)
        attempts = [receipt for receipt,_ in archives.get(key,()) if instant(receipt['archiveVerifiedAt'])>=origin_time]
        if any(row['forwardEligible'] for row in attempts):
            states['qualified'] += 1
        elif attempts:
            states[attempts[-1]['phase']] += 1
        elif issues.get(key):
            states['unverified' if any(item['status']=='unverified' for item in issues[key]) else 'pending_archive'] += 1
        else:
            states['missing'] += 1

    decisions = {day:decision_row(root,store,day,cutoff,planned=True) for day in sessions if day>=FIRST_DECISION}
    labels = [label_row(root,store,day,cutoff,decision) for day,decision in decisions.items()
              if decision['status']=='eligible_inputs']
    comparisons = {}
    for variant,group in frozen['comparisons'].items():
        score = group['score']
        reasons = Counter(row['reason'] for row in group['coverage'] if row['reason'] is not None)
        comparisons[variant] = dict(completedPairs=score['completedPairs'],quarters=score['quarters'],
                                    independentEvents=score['independentEvents'],exclusions=dict(reasons))
    try:
        before = review_progress(root,store,origin_time-timedelta(microseconds=1))
        through = review_progress(root,store,cutoff)
        events = sorted(set(through['independentEventIds'])-set(before['independentEventIds']))
        policy = dict(status='verified',independentEventIds=events)
    except EVIDENCE_ERRORS:
        policy = dict(status='unverified',independentEventIds=None)
    return dict(schemaVersion=1,cutoffAt=cutoff.isoformat(),studyOrigin=origin,
                acquisition=dict(expected=len(sessions),qualified=states['qualified'],
                                 statuses=dict(states),missingCalendarYear=missing_year),
                decisions=decision_counts(decisions.values(),cutoff),
                decisionStatuses=dict(Counter(row['status'] for row in decisions.values())),
                labels=label_counts(labels,cutoff),policy=policy,comparisons=comparisons)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--archive-store',type=Path,required=True)
    method=parser.add_mutually_exclusive_group(required=True)
    method.add_argument('--output',type=Path)
    method.add_argument('--verify',type=Path)
    args=parser.parse_args()
    expected=read(args.verify) if args.verify else None
    clock=instant(expected['asOf']) if expected else datetime.now(timezone.utc)
    if clock>datetime.now(timezone.utc):
        parser.error('Evaluation cannot use a future as-of time')
    root,store=args.observation_root.resolve(),args.archive_store.resolve()
    result=evaluate(root,store,clock)
    if expected is None or 'midtermReview' in expected:
        checkpoint=midterm_review(root,store,result)
        if checkpoint is not None:
            result['midtermReview']=checkpoint
    if expected is not None:
        if result!=expected:
            raise ValueError('Evaluation as-of result does not reproduce')
    else:
        create(args.output,result)
    print(result['status'])
