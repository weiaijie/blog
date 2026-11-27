"""Read admitted close inputs from the existing publication ledger."""
from decimal import Decimal as D
from hashlib import sha256

from audit_official_close import audit
from etf_research.admission import load_incremental
from etf_research.observation_experiment import sleeve_inputs, total_return_levels
from etf_research.official_history import parse_dayk
from etf_research.policy_events import instant
from etf_research.publication import encoded, inside, read, sha, verify_bundle

SYMBOLS = ('510300','511010')


def admitted_operation(root, anchor, ceiling):
    """Use the last same-session publication known at the cutoff."""
    candidates = []
    for path in (root/'reports/operations').glob('*/result.json'):
        try:
            recorded = read(path)
            output = recorded.get('result') or {}
            if (recorded['phase']=='success' and recorded['exit_code']==0
                    and output.get('status')=='published' and output.get('as_of')==str(anchor)):
                finished = instant(recorded['finished_at_utc'])
                if finished<=ceiling:
                    candidates.append((finished,path))
        except (OSError,ValueError,KeyError):
            continue
    if not candidates:
        return None
    _finished,path = max(candidates)
    verify_bundle(path.parent)
    record = read(path)
    started = read(path.parent/'started.json')
    if (inside(root,record['operation'])!=path.parent
            or any(record.get(key)!=value for key,value in started.items())):
        raise ValueError('Invalid archived publication operation')
    return record,path.parent


def establish_price_source(root, anchor, dates, ceiling):
    selected = admitted_operation(root,anchor,ceiling)
    if selected is None:
        return None
    record, operation = selected
    publication = record['result']
    bundle = inside(root,publication['bundle'])
    verify_bundle(bundle)
    ready = read(bundle/'ready.json')
    pointer = ready['pointer']
    after = dict(pointer,bundle_manifest_sha256=sha(bundle/'manifest.json'))
    started = read(bundle/'started.json')
    received = instant(record['finished_at_utc'])
    if (record.get('account_after')!=after or not record.get('account_before')
            or sha256(encoded(record['account_before'])).hexdigest()!=ready['previous_pointer_sha256']
            or inside(root,pointer['bundle'])!=bundle or pointer['as_of']!=str(anchor)
            or record['account_through']!=str(anchor)
            or record['checkpoint_sha256']!=pointer['checkpoint_sha256']
            or not instant(record['started_at_utc'])<=instant(started['created_at_shanghai'])<=received<=ceiling):
        raise ValueError('Published price bundle identity or time mismatch')

    snaps = root/'data/snapshots'
    intake = read(bundle/'admission.json')
    prices = inside(snaps,intake['snapshot'])
    official_audit = read(bundle/'official_close.json')
    matched = [m.parent for m in snaps.glob('*/manifest.json') if sha(m)==official_audit['source_manifest_sha256']]
    if prices.parent!=snaps or len(matched)!=1:
        raise ValueError('Missing or ambiguous price snapshots')
    official = matched[0]
    manifests = [folder/'manifest.json' for folder in (prices,official)]
    if any(ready['input_sha256'].get(p.relative_to(root).as_posix())!=sha(p) for p in manifests):
        raise ValueError('Price snapshot differs from sealed publication')
    data, computed = load_incremental(snaps,prices.name)
    if computed!=intake or data.sessions[-1]!=anchor:
        raise ValueError('Price admission did not reproduce')
    if audit(official.name,prices.name,anchor,snapshots=snaps)!=official_audit:
        raise ValueError('Exchange OHLC audit did not reproduce')

    values = {}
    for symbol in SYMBOLS:
        official_bars = parse_dayk((official/('sse_dayk_'+symbol+'.body')).read_text(),symbol)
        if not all(day in data.bars[symbol] and day in official_bars for day in dates):
            continue
        closes = [data.bars[symbol][day].close for day in dates]
        cash = [sum((e.per_share for e in data.dividends if e.symbol==symbol and e.ex_date==day
                     and e.announcement_date<=anchor),D(0)) for day in dates[1:]]
        series = total_return_levels(closes,cash)
        values[symbol] = sleeve_inputs(series)
    proofs = [operation/'manifest.json',bundle/'manifest.json',*manifests]
    return dict(values=values, availableAt=received.isoformat(),
                evidence=[dict(root='prices',path=p.relative_to(root).as_posix(),sha256=sha(p)) for p in proofs])
