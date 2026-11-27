"""Evidence-bound cross-year checks, never generate a speculative calendar."""
from pathlib import Path
from datetime import datetime,date
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from etf_research.health import evaluate
from etf_research.admission import sessions_between
from etf_research.publication import verify_bundle


def build(output):
    calendar=ROOT/'data/snapshots/2026-11-04-calendar-08'
    source=ROOT/'data/snapshots/2026-11-06-research-evidence-234940'
    verify_bundle(calendar);verify_bundle(source)
    ranges=json.loads((calendar/'calendar.json').read_text())['holiday_ranges']
    if '2027' in ranges:raise ValueError('New calendar requires a new readiness audit')
    cases=[]
    for when in ('2026-12-31T15:59:59+08:00','2026-12-31T16:00:00+08:00','2027-01-01T00:00:00+08:00','2027-01-01T15:59:59+08:00','2027-01-04T16:30:00+08:00'):
        now=datetime.fromisoformat(when)
        result=evaluate(now,ranges,{'as_of':'2026-12-30'},dict(phase='success',started_at_utc='2026-12-30T09:10:00+00:00'),dict(timer_enabled='enabled',timer_active='active',linger='yes'))
        if (now.year==2027)!=(result['state']=='calendar_missing'):raise AssertionError('Year boundary failed closed')
        cases.append(dict(when=when,state=result['state'],issues=result['issues'],expected_through=result['expected_through']))
    try:sessions_between(ranges,date(2026,12,31),date(2027,1,4))
    except ValueError as exc:blocked=str(exc)
    else:raise AssertionError('Admission accepted unknown future year')
    body=(source/'calendar_index.body').read_bytes()
    report=dict(schema_version=1,synthetic_boundary_checks=True,not_actual_future_runs=True,
        evidence_status='No official 2027 calendar obtained in this collection; absence from this index snapshot is not proof of global nonpublication',
        calendar_years=sorted(ranges),index_mentions_2027=b'2027' in body,admission_block=blocked,cases=cases,
        sources_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (calendar/'calendar.json',source/'calendar_index.body',source/'calendar_index_request.json')},
        next_steps=['Obtain formal SSE 2027 holiday notice and retain raw response/URL/time/hash','Cross-check official dates, weekends and year boundaries independently','Add a new immutable calendar snapshot and versioned loader migration, regression-test all old admitted sessions','Review deployment separately; do not extend year coverage with guessed weekdays'])
    (output/'calendar_readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS 5 synthetic calendar boundary cases; missing 2027 blocks admission')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-research-audit');a=p.parse_args();build(a.output)
