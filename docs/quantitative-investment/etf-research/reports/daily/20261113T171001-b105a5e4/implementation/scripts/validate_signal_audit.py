"""Reproduce the sealed files, then exercise three corruptions in a disposable copy."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

from build_signal_audit import ROOT, build, read, save, write_csv
from check_signal_audit import records


def validate(published):
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)/'independent'
        build(out)
        command = [sys.executable, str(ROOT/'scripts/check_signal_audit.py'),'--folder',str(out),'--output']
        subprocess.run(command+[str(out/'verification.json')],check=True)
        for name in ('cases.csv','targets.csv','inputs.json','forward.json','verification.json'):
            if (published/name).read_bytes() != (out/name).read_bytes():
                raise ValueError('Different reproduction: '+name)
        rows = records(out/'targets.csv')
        # Cash target is deliberately a no-op in both instruments; simulate an erroneous lot and date.
        rows[0]['stock_target'] = str(int(rows[0]['stock_target'])+100)
        rows[0]['execution_day'] = rows[1]['execution_day']
        (out/'targets.csv').unlink()
        write_csv(out/'targets.csv',rows)
        item = read(out/'forward.json')
        item['portfolios']['monthly_50_50_base']['target_units']['510300'] += 100
        (out/'forward.json').unlink()
        save(out/'forward.json',item)
        negative = Path(temp)/'mutations.json'
        status = subprocess.run(command+[str(negative)]).returncode
        fields = {r['field'] for r in read(negative)['differences']}
        if status != 2 or not {'signal_inputs_and_targets','calendar','forward_target_units'} <= fields:
            raise ValueError('Corrupt target or date escaped detection')
        print('PASS: five artifacts byte-identical; wrong historical lot, date and forward target detected')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', required=True, type=Path)
    validate(p.parse_args().folder)
