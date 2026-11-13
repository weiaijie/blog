"""Rebuild the versioned default comparisons offline into a new output folder."""
import argparse
from pathlib import Path
import time

import recent_backtest as api
import method_windows
import factor_lab
from interactive_backtest import encode
from research_profile import RECENT, using
from recent_market_data import THROUGH, admitted, volumes


def build(out):
    out.mkdir(parents=True,exist_ok=False)
    (out/'admission.json').write_bytes(encode(admitted()[1]))
    (out/'volume.json').write_bytes(encode(volumes()[1]))
    timings = {}
    for operation, defaults, name in [('method-windows',method_windows.DEFAULTS,'default-methods.json'),
                                       ('technical-factors',factor_lab.DEFAULTS,'default-technical.json')]:
        params = dict(defaults,end=str(THROUGH))
        start = time.monotonic()
        # Bypass the versioned HTTP response archive: rebuild from admitted inputs.
        with using(RECENT):
            result = api.OPERATIONS[operation](params)
        result = dict(result,dataVersion=RECENT,admittedThrough=str(THROUGH))
        (out/name).write_bytes(encode(result))
        timings[operation] = round(time.monotonic()-start,3)
        print(operation,timings[operation],flush=True)
    (out/'default-timings.json').write_bytes(encode(timings))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
