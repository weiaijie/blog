"""Reproduce the registered five-session outcome from sealed daily and opening evidence."""
import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from observation_price_inputs import admitted_prices
from observe_opening_quotes import LOG as OPENING_LOG, verify_opening
from etf_research.admission import sessions_between
from etf_research.baselines import SCENARIOS, SYMBOLS
from etf_research.exchange_calendar import BASE_PATH as CALENDAR, calendar_at
from etf_research.observation_decision_receipt import DECISIONS, deadline, verify_decision
from etf_research.observation_experiment import HORIZON, Window, five_day_label, label_floor
from etf_research.policy_events import instant
from etf_research.publication import create, read, sha

EVIDENCE_ERRORS = (OSError, ValueError, KeyError, TypeError, ArithmeticError)


def label_window(project, entry, observed=None):
    ranges = calendar_at(project,observed if observed is not None else datetime.now(timezone.utc)).ranges
    previous = sessions_between(ranges,entry-timedelta(days=31),entry-timedelta(days=1))
    if not previous or not sessions_between(ranges,entry,entry):
        raise ValueError('Decision entry is not a verified exchange session')
    days = [entry]
    for offset in range(1,32):
        day = entry+timedelta(days=offset)
        days.extend(sessions_between(ranges,day,day))
        if len(days)==HORIZON:
            return Window(previous[-1],tuple(days))
    raise ValueError('Five consecutive exchange sessions are unavailable')


def check_opens(root, store, entry, observed):
    by_symbol = {symbol:[] for symbol in SYMBOLS}
    evidence, issues = [], []
    for folder in sorted((root/OPENING_LOG/str(entry)).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        path = folder/'receipt.json'
        try:
            if instant(read(path)['archiveVerifiedAt'])>observed:
                continue
            row = verify_opening(root,store,folder)
            if not row['scheduled']:
                raise ValueError('Opening quote was not captured in a scheduled live slot')
            for symbol, quote in row['quotes'].items():
                if quote['status'] in ('tradable','blocked'):
                    by_symbol[symbol].append(quote)
                else:
                    issues.append(dict(instrument=symbol,reason=quote['reason'],attempt=folder.name))
            digest=row['archiveSha256']
            evidence.append(dict(readyAt=row['archiveVerifiedAt'],receipt=path.relative_to(root).as_posix(),
                                 receiptSha256=sha(path),archiveSha256=digest))
        except EVIDENCE_ERRORS as error:
            issues.append(dict(attempt=folder.name,reason=str(error)[:240]))
    return by_symbol,evidence,issues


def match_opening(quotes, latest, window):
    eligible, gaps = {}, {}
    entry = window.entry
    for symbol, rows in quotes.items():
        observations = {(row['status'],row.get('openingPrice'),row.get('reference')) for row in rows}
        if not observations:
            gaps[symbol] = 'opening_evidence_missing'
            continue
        if len(observations)!=1:
            gaps[symbol] = 'opening_sources_conflict'
            continue
        status, price, reference = observations.pop()
        if status=='blocked':
            eligible[symbol] = status
            continue
        bars = latest.bars[symbol]
        if Decimal(price)!=bars[entry].open:
            gaps[symbol] = 'opening_quote_differs_from_admitted_ohlc'
            continue
        events = [event for event in latest.dividends if event.symbol==symbol and event.ex_date==entry]
        if events and any(event.announcement_date>=entry for event in events):
            gaps[symbol] = 'ex_dividend_timing_unverified'
        elif events:
            eligible[symbol] = 'known_ex_dividend_day'
        elif Decimal(reference)!=bars[window.anchor].close:
            gaps[symbol] = 'opening_reference_change_unexplained'
        else:
            eligible[symbol] = status
    return eligible,gaps


def serial_results(data, window, opening):
    comparisons = {}
    for allocation, weight in (('stock_bond_50_50',Decimal('.5')),('bond_100',Decimal(0))):
        comparisons[allocation] = {}
        for scenario in SCENARIOS:
            raw = five_day_label(data,window,opening,weight=weight,scenario=scenario)
            if raw is None:
                raise ValueError('Verified label inputs did not replay')
            comparisons[allocation][scenario] = dict(
                terminalReturn=str(raw['terminalReturn']),maxDrawdown=str(raw['maxDrawdown']),
                marks=[str(value) for value in raw['marks']],commission=str(raw['commission']),
                slippage=str(raw['slippage']),orders=raw['orders'],
                endingCash=str(raw['endingCash']),availableCash=str(raw['availableCash']),
                dividendReceivable=str(raw['dividendReceivable']))
    return comparisons


def assemble_label(project, observations, store, entry, observed, *, decision_folder=None):
    window = label_window(project,entry,observed)
    base = dict(schemaVersion=1,mode='scheduled_candidate' if decision_folder else 'validation',
                entryDay=str(entry),anchorDay=str(window.anchor),
                sessions=[str(day) for day in window.sessions],lastSession=str(window.last),
                observedAt=observed.isoformat(),notBefore=label_floor(window).isoformat(),
                decision=None,prices={},openingEvidence=[],openingIssues=[],opening={},gaps={},labels=None)
    data_ceiling = deadline(entry)
    anchor_refs = None
    if decision_folder:
        decision = verify_decision(observations,store,decision_folder,observed=observed)
        if decision['status']!='eligible_inputs' or decision['entryDay']!=str(entry):
            raise ValueError('Label requires an eligible sealed decision for the same entry day')
        record = read(decision_folder/'records/decision.json')
        data_ceiling = instant(record['startedAt'])
        cells = read(decision_folder/'records/inputs.json')['cells']
        anchor_refs = [cells[name]['evidence'] for name in ('stockReturn5','bondReturn5')]
        base['decision'] = dict(path=decision['decisionPath'],archiveSha256=decision['archiveSha256'],
                                receiptSha256=sha(decision_folder/'receipt.json'),
                                availableVariants=decision['availableVariants'])
    if observed<label_floor(window):
        return dict(base,status='holding_period_incomplete')
    checked = {}
    gaps = base['gaps']
    for day in (window.anchor,*window.sessions):
        try:
            found = admitted_prices(project,day,data_ceiling if day==window.anchor else observed)
        except EVIDENCE_ERRORS as error:
            gaps[str(day)] = dict(reason='price_evidence_invalid',error=str(error)[:240])
            continue
        if found is None:
            gaps[str(day)] = dict(reason='price_evidence_not_ready')
            continue
        if day==window.anchor and anchor_refs is not None and any(
                sources!=found['evidence'] for sources in anchor_refs):
            gaps[str(day)] = dict(reason='anchor_price_version_differs_from_sealed_decision')
            continue
        checked[day] = found['data']
        base['prices'][str(day)] = dict(readyAt=found['availableAt'],evidence=found['evidence'])
    quotes,base['openingEvidence'],base['openingIssues'] = check_opens(observations,store,entry,observed)
    if not gaps:
        last = checked[window.last]
        for day, published in checked.items():
            if day not in last.sessions or any(
                    published.bars[symbol].get(day) is None or published.bars[symbol][day]!=last.bars[symbol].get(day)
                    for symbol in SYMBOLS):
                gaps[str(day)] = dict(reason='published_price_revision_or_missing_day')
        def known_dividends(dataset, day):
            return {event for event in dataset.dividends if event.announcement_date<=day and
                    (window.entry<=event.record_date<=window.last or event.ex_date==window.entry)}

        for day, published in checked.items():
            if known_dividends(last,day)!=known_dividends(published,day):
                gaps[str(day)] = dict(reason='published_dividend_version_conflict')
        if not gaps:
            base['opening'],open_gaps = match_opening(quotes,last,window)
            gaps.update(open_gaps)
    if gaps:
        return dict(base,status='evidence_missing')
    base['labels'] = serial_results(last,window,base['opening'])
    return dict(base,status='evidence_complete')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--price-project',type=Path,required=True)
    parser.add_argument('--observation-root',type=Path,required=True)
    parser.add_argument('--archive-store',type=Path,required=True)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--entry',type=date.fromisoformat)
    action.add_argument('--verify',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    project,observations,store=(path.resolve() for path in (args.price_project,args.observation_root,args.archive_store))
    if args.verify:
        expected=read(args.verify)
        if expected['mode']!='validation':
            parser.error('Use the scheduled label archive verifier for formal labels')
        result=assemble_label(project,observations,store,date.fromisoformat(expected['entryDay']),instant(expected['observedAt']))
        if expected!=result:
            raise ValueError('Stored label probe does not reproduce')
    else:
        if not args.output:
            parser.error('--entry requires a new --output file')
        result=assemble_label(project,observations,store,args.entry,datetime.now(timezone.utc))
        create(args.output,result)
    print(result['status'],result['entryDay'],len(result['prices']),'verified price dates',list(result['gaps']))
