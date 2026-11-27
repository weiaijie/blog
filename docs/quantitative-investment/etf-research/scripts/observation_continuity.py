"""Audit the initial 20 scheduled exchange sessions against archived evidence."""
import argparse
from datetime import datetime, time, timedelta, timezone
import json
from pathlib import Path

from observation_monthly import SOURCES, availability, gap_runs
from observation_policy_inputs import expected_slots
from observation_status import archive_index, expected_days, parse_day, production_paths, view_attempt
from etf_research.admission import completed_date
from etf_research.observation_decision_receipt import deadline
from etf_research.observation_slots import POLL_TIMES, scheduled_slot
from etf_research.policy_events import TZ, instant
from etf_research.publication import read

WINDOW = 20
SERVICE_TIMEOUT = timedelta(minutes=15)


def slot_status(slot, records, observed):
    matching=[]
    near=[]
    for receipt,record in records:
        if receipt['trigger'] is None:
            continue
        started=instant(record['startedAt'])
        if not slot<=started<slot+timedelta(minutes=1):
            continue
        attempt=dict(id=Path(receipt['attempt']).name,archiveSha256=receipt['archive'],
                     startedAt=record['startedAt'],archiveVerifiedAt=receipt['archiveVerifiedAt'],
                     phase=receipt['phase'])
        if scheduled_slot(record)==slot:
            matching.append(attempt)
        else:
            near.append(attempt)
    if matching:
        state='verified'
    elif near:
        state='unconfirmed_clock'
    elif observed<slot:
        state='upcoming'
    elif observed<slot+SERVICE_TIMEOUT:
        state='awaiting_archive'
    else:
        state='not_verified'
    return dict(at=slot.isoformat(),state=state,verified=matching,unconfirmed=near)


def session_row(day, next_day, records, issues, observed):
    cutoff=deadline(next_day) if next_day is not None else None
    first_poll=datetime.combine(day,POLL_TIMES[-1],TZ)
    expected=expected_slots(datetime.combine(day,time(16),TZ),cutoff) if cutoff else [first_poll]
    slots=[slot_status(slot,records,observed) for slot in expected]
    attempts=[view_attempt(receipt,record) for receipt,record in records if receipt['trigger'] is not None]
    manual_count=len(records)-len(attempts)
    qualified=[attempt for attempt in attempts if attempt['qualified']]
    on_time=bool(cutoff and any(instant(attempt['archivedAt'])<=cutoff for attempt in qualified))
    if on_time:
        state='on_time'
    elif cutoff is None:
        state='cutoff_unknown'
    elif observed<cutoff:
        state='awaiting_cutoff'
    elif qualified:
        state='qualified_late'
    else:
        state='incomplete' if attempts else 'no_scheduled_archive'
    return dict(day=day.isoformat(),cutoffAt=cutoff.isoformat() if cutoff else None,
                cutoffPassed=cutoff is not None and observed>=cutoff,qualification=state,
                scheduledAttempts=len(attempts),manualAttempts=manual_count,
                verifiedSlots=sum(slot['state']=='verified' for slot in slots),slots=slots,
                sources={key:availability(attempts,key,cutoff,observed) for key in SOURCES},
                archiveIssues=issues)


def audit(root,store,observed):
    config=read(root/'config/research_observation.json')
    start=parse_day(config['observationEarliestDate'])
    through=completed_date(observed)
    # Look beyond the latest completed session only to identify the next known cutoff.
    calendar,unknown=expected_days(root,start,through+timedelta(days=31),observed=observed)
    planned=tuple(day for day in calendar[:WINDOW] if day<=through)
    entries,errors=archive_index(root,store,config,observed,days=planned) if planned else ({},{})
    rows=[]
    for i,day in enumerate(planned):
        following=calendar[i+1] if i+1<len(calendar) else None
        key=day.isoformat()
        rows.append(session_row(day,following,entries.get(key,()),errors.get(key,[]),observed))
    closed=[row for row in rows if row['cutoffPassed']]
    return dict(schemaVersion=1,asOf=observed.astimezone(TZ).isoformat(),
                targetSessions=WINDOW,trackedSessions=len(rows),completedWindows=len(closed),
                collecting=len(closed)<WINDOW,
                calendarUnknownYear=unknown if len(calendar)<=WINDOW else None,
                daysWithScheduledArchive=sum(row['scheduledAttempts']>0 for row in rows),
                daysWithVerifiedTimer=sum(row['verifiedSlots']>0 for row in rows),
                qualifiedOnTime=sum(row['qualification']=='on_time' for row in rows),
                missedCutoffRuns=gap_runs(closed,lambda row:row['qualification']!='on_time'),
                notOnTimeBySource={key:sum(row['sources'][key]['status']!='on_time' for row in closed)
                                 for key in SOURCES},
                days=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root,store=production_paths()
    parser.add_argument('--observation-root',type=Path,default=root)
    parser.add_argument('--archive-store',type=Path,default=store)
    parser.add_argument('--as-of',type=instant)
    args=parser.parse_args()
    now=datetime.now(timezone.utc)
    observed=args.as_of or now
    if observed>now:
        parser.error('Audit cutoff cannot be in the future')
    result=audit(args.observation_root.resolve(),args.archive_store.resolve(),observed)
    print(json.dumps(result,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':
    main()
