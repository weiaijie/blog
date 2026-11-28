"""Build a verification-only day record and enforce an explicit read-time cutoff."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import collect_policy_etf_day as policy_etf
import collect_sse_research_day as sse
from etf_research.policy_events import instant
from etf_research.publication import create, inside, read, sha

ROOT = policy_etf.ROOT


def cover(policy_folder, sse_folder, decision_at):
    cutoff = instant(decision_at)
    policy_run = policy_etf.verify(policy_folder)
    market_run = sse.verify(sse_folder)
    if (policy_run['date'], policy_run['previousDate']) != (market_run['date'], market_run['previousDate']):
        raise ValueError('Research snapshots cover different exchange sessions')

    policy_visible = instant(policy_run['checkedAt']) <= cutoff
    market_visible = instant(market_run['checkedAt']) <= cutoff
    if policy_visible:
        snapshot = policy_run['policy']
        policy = dict(status=snapshot['status'], candidateCount=len(snapshot['candidates']),
                      uniqueRevisionKeys=sorted({row['revisionKey'] for row in snapshot['candidates']}),
                      signalEligibleCount=0, issues=snapshot['issues'])
        etfs = {row['symbol']:{k:row[k] for k in ('status','issues','estimatedNetSubscriptionCny',
                                                'featureReadyAt')} for row in policy_run['etf']}
    else:
        policy = dict(status='unknown_at_cutoff', candidateCount=None, signalEligibleCount=None)
        etfs = {code:dict(status='unknown_at_cutoff') for code in policy_etf.SYMBOLS}
    if market_visible:
        market = dict(status=market_run['status'], turnoverCny=market_run['turnoverCny'],
                      margin=market_run['margin'], featureReadyAt=market_run['featureReadyAt'],
                      issues=market_run['issues'])
    else:
        market = dict(status='unknown_at_cutoff')
    bound = {
        label:dict(path=folder.resolve().relative_to(ROOT).as_posix(),
                   manifestSha256=sha(folder/'manifest.json'))
        for label,folder in (('policyEtf',policy_folder),('sse',sse_folder))
    }
    return dict(schemaVersion=1, date=policy_run['date'], decisionAt=cutoff.isoformat(),
                runKind='validation', researchOnly=True, forwardEligible=False,
                policy=policy, etf=etfs, market=market, evidence=bound)


def verify(path):
    stored = read(path)
    proof = stored['evidence']
    folders = [inside(ROOT, proof[label]['path']) for label in ('policyEtf','sse')]
    if stored != cover(*folders,stored['decisionAt']):
        raise ValueError('Dated research coverage does not reproduce')
    return stored


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy-etf',type=Path)
    parser.add_argument('--sse',type=Path)
    parser.add_argument('--decision-at')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--verify',type=Path)
    args = parser.parse_args()
    if args.verify:
        if any((args.policy_etf,args.sse,args.decision_at,args.output)):
            parser.error('--verify cannot be combined with input or output options')
        result = verify(args.verify)
    else:
        if not args.policy_etf or not args.sse:
            parser.error('Both policy/ETF and SSE snapshot directories are required')
        result = cover(args.policy_etf,args.sse,args.decision_at or datetime.now(timezone.utc).isoformat())
        if args.output:
            create(args.output,result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
