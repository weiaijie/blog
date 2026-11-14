"""Audit all published factor maturities using one chronological signal tape and fresh accounts."""
from decimal import Decimal as D

from build_entry_windows import entry_schedule
from method_windows import DEFAULTS, FACTOR_MODEL, archived_entries, prepare
from model_replay import replay


def verify():
    params, days, capital, simulate = prepare(DEFAULTS)
    params.pop('installments')
    frames = replay(dict(params,model=FACTOR_MODEL,rebalance='signal',step='all'))['frames']
    regimes = {f['date']: f['decision']['regime'] for f in frames}
    archive = archived_entries()
    checked = set()
    for sessions, endpoints in entry_schedule(days):
        previous = None
        schedule = {}
        for close, opening in zip(sessions, sessions[1:]):
            regime = regimes[close]
            if regime != previous:
                weights = {'510300':2, '511010':2} if regime == 'balanced' else {'511010':1}
                schedule[opening] = dict(denominators=weights)
            previous = regime
        ledger, _ = simulate(sessions,schedule=schedule)
        if ledger[0]['equity'] != capital or ledger[0]['available_cash'] != capital:
            raise ValueError('Window must start with all principal in cash')
        for years, offset in endpoints.items():
            key = (str(sessions[0]),years)
            entry = archive[key]
            if entry['end'] != str(sessions[offset]) or D(entry[FACTOR_MODEL]) != ledger[offset]['equity']:
                raise ValueError(f'Window differs from signal replay: {key}')
            checked.add(key)
    if checked != archive.keys():
        raise ValueError('Published window coverage mismatch')
    return len(checked)


if __name__ == '__main__':
    print('Factor maturities reconciled:',verify())
