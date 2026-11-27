"""Freeze evidence for the independent ETF experiment at its actual decision time."""
import argparse
from datetime import date, datetime, timezone
from math import isfinite
import json
from pathlib import Path
import os
from uuid import uuid4

from observation_decision_status import SEALED_INPUT, decision_row
from observation_inputs import FEATURES, assemble
from run_research_observation import first_archive
from etf_research.admission import sessions_between
from etf_research.exchange_calendar import BASE_PATH as CALENDAR, LOADER, calendar_at
from etf_research.evidence_archive import capture, verify as verify_archive
from etf_research.observation_experiment import VARIANTS
from etf_research.observation_decision_receipt import (
    TIMER, DECISIONS, PROBES, current_slot, deadline, decision_status, verify_decision,
)
from etf_research.observation_slots import timer_identity, with_manager_clock
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, inside, lock, read, seal, sha, sync_dir

ROOT = Path(__file__).resolve().parents[1]
CODE = (
    LOADER, 'src/etf_research/observation_slots.py',
    'PROTOCOL_OBSERVATION_V1.md', 'config/research_observation.json', CALENDAR,
    'deploy/etf-research-decision.service', 'deploy/etf-research-decision.timer',
    'scripts/seal_observation_decision.py', 'scripts/observation_decision_status.py',
    'scripts/observation_inputs.py',
    'scripts/observation_archive.py', 'scripts/observation_policy_inputs.py',
    'scripts/observation_price_inputs.py', 'scripts/review_policy_observations.py',
    'scripts/run_research_observation.py', 'scripts/audit_official_close.py',
    'scripts/collect_policy_etf_day.py', 'scripts/collect_sse_research_day.py',
    'scripts/collect_market_state_pilot.py', 'scripts/market_state_pilot.py',
    'scripts/etf_share_flow.py', 'scripts/policy_source_watch.py', 'scripts/research_day_coverage.py',
    'src/etf_research/admission.py', 'src/etf_research/observation_experiment.py',
    'src/etf_research/data.py', 'src/etf_research/official_history.py',
    'src/etf_research/accounting.py', 'src/etf_research/baselines.py',
    'src/etf_research/forward.py', 'src/etf_research/http_capture.py',
    'src/etf_research/catalog_changes.py', 'src/etf_research/policy_events.py',
    'src/etf_research/observation_decision_receipt.py',
    'src/etf_research/evidence_archive.py', 'src/etf_research/publication.py',
)


def now():
    return datetime.now(timezone.utc)


def trigger_from(env):
    return timer_identity(env,TIMER)


def feature_state(inputs, roots):
    if set(inputs['cells']) != set(FEATURES):
        raise ValueError('Feature names differ from registered inputs')
    computed = instant(inputs['computedAt'])
    ceiling = instant(inputs['evidenceCutoff'])
    names = set()
    for name, cell in inputs['cells'].items():
        if cell is None:
            continue
        received, ready = instant(cell['receivedAt']), instant(cell['readyAt'])
        dependencies = [instant(value) for value in cell['dependencyReadyAt']]
        value = cell['value']
        if (type(value) is bool or not isfinite(float(value))
                or cell['verified'] is not True or cell['asOf']!=inputs['anchorDay']
                or not max([received,*dependencies])<=ceiling<=computed==ready or not cell['evidence']):
            raise ValueError('Feature clocks or evidence differ from decision snapshot')
        for proof in cell['evidence']:
            if sha(inside(roots[proof['root']],proof['path']))!=proof['sha256']:
                raise ValueError('Feature evidence has changed')
        names.add(name)
    return {variant: set(required)<=names for variant,required in VARIANTS.items()}


def run(root, prices, store, *, probe=None):
    trigger = None if probe else trigger_from(os.environ)
    if probe is None and trigger is None:
        raise ValueError('The production decision needs its scheduled systemd timer provenance')
    if trigger is not None:
        trigger = with_manager_clock(trigger)
    started = now()
    day = probe or started.astimezone(TZ).date()
    calendar = calendar_at(root,started)
    if not sessions_between(calendar.ranges,day,day):
        return dict(status='not_scheduled',entryDay=str(day),startedAt=started.isoformat(),trigger=trigger)
    log = root/(PROBES if probe else DECISIONS)/day.isoformat()
    roots = dict(prices=prices,observations=root,archive=store)
    with lock(root/'.runtime/research-decision.lock'):
        if probe is None:
            observed = now()
            prior = decision_row(root,store,day,observed,planned=True)
            if prior['status'] in SEALED_INPUT:
                return verify_decision(root,store,log/prior['latest']['id'],observed=observed)
        attempt = log/((started.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]) if probe else trigger['invocationId'])
        records = attempt/'records'
        records.mkdir(parents=True,exist_ok=False)
        input_file = records/'inputs.json'
        origin, failure = None, None
        available = dict.fromkeys(VARIANTS,False)
        code = {path:sha(root/path) for path in (*CODE,*calendar.extensions)}
        if probe or current_slot(trigger,day,started):
            try:
                origin = first_archive(root,store,started)
                inputs = assemble(prices,root,store,day,started,recover_transport=True)
                available = feature_state(inputs,roots)
                create(input_file,dict(inputs,runKind='validation' if probe else 'decision_input'))
            except (OSError,ValueError,KeyError,TypeError,ArithmeticError) as error:
                failure = dict(type=type(error).__name__,message=str(error)[:700])
                available = dict.fromkeys(VARIANTS,False)
        else:
            failure = dict(type='timer_provenance',message='Verified calendar timer did not activate within decision window')
        result = dict(schemaVersion=1,mode='probe' if probe else 'scheduled',entryDay=str(day),
                      startedAt=started.isoformat(),deadline=deadline(day).isoformat(),
                      finishedAt=now().isoformat(),trigger=trigger,studyOrigin=origin,
                      availableVariants=available,codeSha256=code,failure=failure,
                      inputSha256=sha(input_file) if input_file.is_file() else None,
                      forecastProduced=False)
        create(records/'decision.json',result)
        seal(records)
        names = [p.relative_to(root).as_posix() for p in records.iterdir()] + list(code)
        archive = capture(root,store,names)
        verify_archive(store,archive['snapshot'])
        ready = now()
        receipt = dict(schemaVersion=1,decisionPath=attempt.relative_to(root).as_posix(),
                       archiveSha256=archive['snapshot'],archiveVerifiedAt=ready.isoformat(),
                       recordManifestSha256=sha(records/'manifest.json'),status=decision_status(result,ready))
        create(attempt/'receipt.json',receipt)
        for folder in (attempt,log,log.parent):
            sync_dir(folder)
        return verify_decision(root,store,attempt,observed=now())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observation-root',type=Path,default=ROOT)
    parser.add_argument('--price-project',type=Path)
    parser.add_argument('--archive-store',type=Path,required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run',action='store_true')
    mode.add_argument('--probe',type=date.fromisoformat)
    mode.add_argument('--verify',type=Path)
    args = parser.parse_args()
    root,store = args.observation_root.resolve(),args.archive_store.resolve()
    if args.verify:
        result = verify_decision(root,store,args.verify)
    else:
        if args.price_project is None:
            parser.error('--price-project is required to assemble features')
        result = run(root,args.price_project.resolve(),store,probe=args.probe)
    print(json.dumps(result,ensure_ascii=False))
    return int(result['status']=='failed' or result.get('failure') is not None)


if __name__=='__main__':
    raise SystemExit(main())
