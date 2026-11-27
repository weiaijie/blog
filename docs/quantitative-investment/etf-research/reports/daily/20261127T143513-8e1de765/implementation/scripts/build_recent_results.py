"""Rebuild the versioned default comparisons offline into a new output folder."""
import argparse
from pathlib import Path
import time

import recent_backtest as api
import method_windows
import factor_lab
from interactive_backtest import encode
from research_profile import RECENT, API_VERSIONS, data_module, using
from recent_market_data import THROUGH, admitted, volumes


def build(out, profile=RECENT):
    out.mkdir(parents=True,exist_ok=False)
    if profile != RECENT:
        provider = data_module(profile)
        end = provider.THROUGH
        _, audit, (_, volume_audit) = provider.admitted()
    else:
        end, audit, volume_audit = THROUGH, admitted()[1], volumes()[1]
    (out/'admission.json').write_bytes(encode(audit))
    (out/'volume.json').write_bytes(encode(volume_audit))
    timings = {}
    for operation, defaults, name in [('method-windows',method_windows.DEFAULTS,'default-methods.json'),
                                       ('technical-factors',factor_lab.DEFAULTS,'default-technical.json')]:
        params = dict(defaults,end=str(end))
        start = time.monotonic()
        # Bypass the versioned HTTP response archive: rebuild from admitted inputs.
        with using(profile):
            result = api.OPERATIONS[operation](params)
        result = dict(result,dataVersion=profile,admittedThrough=str(end))
        (out/name).write_bytes(encode(result))
        timings[operation] = round(time.monotonic()-start,3)
        print(operation,timings[operation],flush=True)
    (out/'default-timings.json').write_bytes(encode(timings))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--profile',choices=API_VERSIONS,default=RECENT)
    args = parser.parse_args()
    build(args.output,args.profile)
