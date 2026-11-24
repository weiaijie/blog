"""Versioned research API/Agent CLI. Calculations share request-local verified inputs."""
import argparse
import json
import hashlib
from pathlib import Path

import interactive_backtest as work
import model_replay
import method_windows
import factor_lab
from research_profile import RECENT, LATEST, NOV23, API_VERSIONS, data_module, using

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


NOV23_REPORT = REPORT.parent/'2026-11-24-admission'
NOV23_ARCHIVES = {
    'method-windows': ('default-methods.json', 'c2eeb580fdc045cea91096fd17d1322703b96d6b70553b608aaa54fbb94f3893'),
    'technical-factors': ('default-technical.json', '31a73e50960ca989562ad5c58a9af291b7858e088635ef4745a84a0c73d77e6e'),
}


def options(profile=RECENT):
    provider = data_module(profile)
    end = str(provider.THROUGH)
    # Eager verification: the UI should only offer approved sessions.
    result = dict(work.OPTIONS, last=end, dataVersion=profile, evidence=provider.admitted()[1],
                  defaults=dict(work.DEFAULTS,end=end),
                  methodWindowsDefaults=dict(method_windows.DEFAULTS,end=end),
                  technicalFactorsDefaults=dict(factor_lab.DEFAULTS,end=end))
    prefix = '/api/'+API_VERSIONS[profile]+'/backtest'
    for key, value in list(result.items()):
        if isinstance(value,str) and value.startswith('/api/v1/backtest'):
            result[key] = value.replace('/api/v1/backtest',prefix,1)
    if profile in (RECENT, LATEST):
        result.update(dataChangeEndpoint=prefix+'/data-change',dataChangeDetailEndpoint=prefix+'/data-change-detail')
    if profile == RECENT:
        result.update(newWindowAttributionEndpoint=prefix+'/new-window-attribution',
                      newWindowAttributionDetailEndpoint=prefix+'/new-window-attribution-detail')
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
    provider = data_module(profile)
    end = provider.THROUGH
    archive, folder = {
        RECENT: (DEFAULT_ARCHIVES, REPORT),
        LATEST: (LATEST_ARCHIVES, LATEST_REPORT),
        NOV23: (NOV23_ARCHIVES, NOV23_REPORT),
    }[profile]
    if profile != RECENT:
        provider.admitted()
    if operation not in OPERATIONS:
        raise work.InputError('不支持的研究操作。')
    defaults = {'method-windows':method_windows.DEFAULTS,'technical-factors':factor_lab.DEFAULTS}.get(operation)
    if operation in archive and defaults is not None and params == dict(defaults,end=str(end)):
        if profile == RECENT:
            provider.admitted()
            provider.volumes()
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
    parser.add_argument('--profile',choices=API_VERSIONS,default=RECENT)
    args = parser.parse_args()
    params = json.loads(args.params)
    if not isinstance(params,dict) or any(not isinstance(v,str) for v in params.values()):
        parser.error('Parameters must be a JSON object with string values')
    print(work.encode(calculate(args.operation,parameters(args.operation,urlencode(params)),args.profile)).decode())
