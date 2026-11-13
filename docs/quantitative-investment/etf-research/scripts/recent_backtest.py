"""Versioned research API/Agent CLI. Calculations share request-local verified inputs."""
import argparse
import json
import hashlib
from pathlib import Path

import interactive_backtest as work
import model_replay
import method_windows
import factor_lab
from research_profile import RECENT, using
from recent_market_data import THROUGH, admitted

REPORT = Path(__file__).resolve().parents[1]/'reports/2026-11-13-recent-data'
DEFAULT_ARCHIVES = {
    'method-windows': ('default-methods.json','5beab53ecf29df44451520848b274e963e4a50a97940fd6c71fa846925af25f8'),
    'technical-factors': ('default-technical.json','4645a3d701c48f34bf5ff6ebb6cbacda318eea644bab5832a09dc60cab78ab7e'),
}

OPERATIONS = {'account':work.backtest, 'windows':work.entry_windows,
              'compare':work.compare_windows, 'overlay':work.same_window,
              'replay':model_replay.replay, 'method-windows':method_windows.compare,
              'method-detail':method_windows.detail, 'technical-factors':factor_lab.compare,
              'technical-detail':factor_lab.detail}


def options():
    # Eager verification: a date picker must not advertise data that fails admission.
    _, audit = admitted()
    result = dict(work.OPTIONS, last=str(THROUGH), dataVersion=RECENT,
                  defaults=dict(work.DEFAULTS,end=str(THROUGH)), evidence=audit,
                  methodWindowsDefaults=dict(method_windows.DEFAULTS,end=str(THROUGH)),
                  technicalFactorsDefaults=dict(factor_lab.DEFAULTS,end=str(THROUGH)))
    for key, value in list(result.items()):
        if isinstance(value,str) and value.startswith('/api/v1/'):
            result[key] = value.replace('/api/v1/','/api/v2/',1)
    return result


def parameters(operation, query):
    keys, optional = work.DEFAULTS, ()
    if operation in ('method-windows','method-detail'):
        keys = method_windows.DEFAULTS
    elif operation in ('technical-factors','technical-detail'):
        keys = factor_lab.DEFAULTS
    elif operation == 'replay':
        keys, optional = (*work.DEFAULTS,'model','step'), ('installments',)
    return work.request_params(query,keys,optional)


def calculate(operation, params):
    if operation not in OPERATIONS:
        raise work.InputError('不支持的研究操作。')
    defaults = {'method-windows':method_windows.DEFAULTS,'technical-factors':factor_lab.DEFAULTS}.get(operation)
    if defaults is not None and params == dict(defaults,end=str(THROUGH)):
        from recent_market_data import volumes
        admitted()
        volumes()
        name, expected = DEFAULT_ARCHIVES[operation]
        body = (REPORT/name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError('Versioned default comparison changed')
        result = json.loads(body)
        if result['parameters'] != params or result['dataVersion'] != RECENT or result['admittedThrough'] != str(THROUGH):
            raise ValueError('Versioned response identity differs')
        return result
    with using(RECENT):
        result = OPERATIONS[operation](params)
    return dict(result, dataVersion=RECENT, admittedThrough=str(THROUGH))


if __name__ == '__main__':
    from urllib.parse import urlencode
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation',required=True,choices=OPERATIONS)
    parser.add_argument('--params',required=True,help='JSON object; same string parameters as HTTP')
    args = parser.parse_args()
    params = json.loads(args.params)
    if not isinstance(params,dict) or any(not isinstance(v,str) for v in params.values()):
        parser.error('Parameters must be a JSON object with string values')
    print(work.encode(calculate(args.operation,parameters(args.operation,urlencode(params)))).decode())
