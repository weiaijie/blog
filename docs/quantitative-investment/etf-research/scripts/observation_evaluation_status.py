"""Read the current verified evaluation snapshot without running analyses in HTTP."""
from datetime import date
import re

from observation_labels import EVIDENCE_ERRORS
from seal_observation_evaluation import LOG, verify_evaluation
from etf_research.observation_experiment import MIN_EVENTS, MIN_QUARTERS, MIN_TEST, VARIANTS
from etf_research.policy_events import TZ, instant
from etf_research.publication import read

ARCHIVE_ID=re.compile('[a-f0-9]{64}')


def latest_evaluation(root,store,observed,*,archive=None):
    invalid,pending=0,0
    observed_day=observed.astimezone(TZ).date()
    for day in sorted((root/LOG).glob('*'),reverse=True):
        if not day.is_dir() or day.is_symlink():
            continue
        try:
            calendar_day=date.fromisoformat(day.name)
        except ValueError:
            continue
        if calendar_day>observed_day or day.name!=str(calendar_day):
            continue
        accepted=[]
        for folder in sorted(day.glob('*')):
            if not folder.is_dir() or folder.is_symlink():
                continue
            path=folder/'receipt.json'
            try:
                if not path.is_file():
                    if archive is None:
                        pending+=1
                    continue
                offered=read(path)
                if archive is not None and offered['archiveSha256']!=archive:
                    continue
                if instant(offered['archiveVerifiedAt'])>observed:
                    continue
                accepted.append(verify_evaluation(root,store,folder,observed=observed))
            except EVIDENCE_ERRORS:
                invalid+=1
        if accepted:
            latest=max(accepted,key=lambda pair:(instant(pair[1]['asOf']),instant(pair[0]['archiveVerifiedAt']),
                                                  pair[0]['archiveSha256']))
            return latest,dict(unverified=invalid,pending=pending)
    return None,dict(unverified=invalid,pending=pending)


def evaluation_view(root,store,observed,origin,*,details=False,archive=None):
    latest,issues=latest_evaluation(root,store,observed,archive=archive)
    receipt,report=latest or (None,None)
    state=report['status'] if report is not None else (
        'observation_origin_pending' if origin is None else 'awaiting_evaluation')
    thresholds=dict(pairs=MIN_TEST,folds=MIN_QUARTERS,policyEvents=MIN_EVENTS)
    if report is not None and report['thresholds']!=thresholds:
        raise ValueError('Evaluation thresholds differ from registration')
    summary={}
    for variant,columns in VARIANTS.items():
        if variant=='baseline':
            continue
        policy='policyActiveCount' in columns
        if report is not None and variant in report['comparisons']:
            comparison=report['comparisons'][variant]
            scoring=comparison['score']
            economic=comparison['economics']
            summary[variant]=dict(status=scoring['status'],completedPairs=scoring['completedPairs'],
                folds=scoring['quarters'],policyEvents=scoring['independentEvents'] if policy else None,
                shortfall=comparison['shortfall'],selectedWindows=economic['selectedWindows'],
                matchedWindows=economic['matchedWindows'])
        else:
            zero=0 if state=='observation_origin_pending' else None
            shortfall=dict(pairs=MIN_TEST,folds=MIN_QUARTERS,policyEvents=MIN_EVENTS if policy else 0) if zero==0 else None
            summary[variant]=dict(status=state,completedPairs=zero,folds=zero,policyEvents=zero if policy else None,
                                  shortfall=shortfall,selectedWindows=zero,matchedWindows=zero)
    view=dict(schemaVersion=1,reportedAt=observed.isoformat(),status=state,
              archiveState='verified' if receipt else 'unverified' if issues['unverified'] else 'waiting',
              assessedAt=report['asOf'] if report else None,
              verifiedAt=receipt['archiveVerifiedAt'] if receipt else None,
              archiveSha256=receipt['archiveSha256'] if receipt else None,
              archiveIssues=issues,originSinceArchive=bool(report and report['studyOrigin'] is None and origin),
              thresholds=thresholds,comparisons=summary)
    if details:
        view['report']=report
    return view
