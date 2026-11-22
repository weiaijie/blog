"""Versioned research API/Agent CLI. Calculations share request-local verified inputs."""
import argparse
import json
import hashlib
from pathlib import Path

import interactive_backtest as work
import model_replay
import method_windows
import factor_lab
from research_profile import RECENT, LATEST, using
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


LATEST_REPORT = REPORT.parent/'2026-11-22-admission'
LATEST_ARCHIVES = {
    'method-windows': ('default-methods.json','f5968aad853905e79b34f154989c5cbd3df1597350fad2033c4514379ec983b7'),
    'technical-factors': ('default-technical.json','3e94b6cf9af759f9ffcd4b62d184469c7c8d1fa1888b7a6d205234838f10ebf2'),
}


def options(profile=RECENT):
    # Eager verification: a date picker must not advertise data that fails admission.
    end = THROUGH
    if profile == LATEST:
        from november_market_data import admitted as latest, THROUGH as end
        _, audit, _ = latest()
    elif profile == RECENT:
        _, audit = admitted()
    else:
        raise ValueError('Unknown data version')
    result = dict(work.OPTIONS, last=str(end), dataVersion=profile,
                  defaults=dict(work.DEFAULTS,end=str(end)), evidence=audit,
                  newWindowAttributionEndpoint='/api/v2/backtest/new-window-attribution', newWindowAttributionDetailEndpoint='/api/v2/backtest/new-window-attribution-detail',
                  dataChangeEndpoint='/api/v2/backtest/data-change', dataChangeDetailEndpoint='/api/v2/backtest/data-change-detail',
                  methodWindowsDefaults=dict(method_windows.DEFAULTS,end=str(end)),
                  technicalFactorsDefaults=dict(factor_lab.DEFAULTS,end=str(end)))
    if profile == LATEST:
        for key in ('newWindowAttributionEndpoint','newWindowAttributionDetailEndpoint','dataChangeEndpoint','dataChangeDetailEndpoint'):
            result.pop(key)
    for key, value in list(result.items()):
        if isinstance(value,str) and value.startswith('/api/v1/'):
            result[key] = value.replace('/api/v1/','/api/v3/' if profile == LATEST else '/api/v2/',1)
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


def calculate(operation, params, profile=RECENT):
    archive, folder, end = DEFAULT_ARCHIVES, REPORT, THROUGH
    if profile == LATEST:
        from november_market_data import THROUGH as end, admitted as latest
        latest()
        archive, folder = LATEST_ARCHIVES, LATEST_REPORT
    elif profile != RECENT:
        raise ValueError('Unknown data version')
    if operation not in OPERATIONS:
        raise work.InputError('不支持的研究操作。')
    defaults = {'method-windows':method_windows.DEFAULTS,'technical-factors':factor_lab.DEFAULTS}.get(operation)
    if operation in archive and defaults is not None and params == dict(defaults,end=str(end)):
        from recent_market_data import volumes
        if profile == RECENT:
            admitted()
            volumes()
        name, expected = archive[operation]
        body = (folder/name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError('Versioned default comparison changed')
        result = json.loads(body)
        if result['parameters'] != params or result['dataVersion'] != profile or result['admittedThrough'] != str(end):
            raise ValueError('Versioned response identity differs')
        return result
    with using(profile):
        result = OPERATIONS[operation](params)
    return dict(result, dataVersion=profile, admittedThrough=str(end))


if __name__ == '__main__':
    from urllib.parse import urlencode
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation',required=True,choices=OPERATIONS)
    parser.add_argument('--params',required=True,help='JSON object; same string parameters as HTTP')
    parser.add_argument('--profile',choices=(RECENT,LATEST),default=RECENT)
    args = parser.parse_args()
    params = json.loads(args.params)
    if not isinstance(params,dict) or any(not isinstance(v,str) for v in params.values()):
        parser.error('Parameters must be a JSON object with string values')
    print(work.encode(calculate(args.operation,parameters(args.operation,urlencode(params)),args.profile)).decode())
