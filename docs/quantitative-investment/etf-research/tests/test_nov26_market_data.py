"""Verify the Thanksgiving redemption and opening halts against the sealed close data."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sys
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import nov26_market_data as data


class November26EvidenceTests(TestCase):
    def test_halts_distinct_from_primary_redemption(self):
        (base, calendar, bars, halts), audit, (volume, _) = data.admitted()
        (old, previous_calendar, old_bars, old_halts), previous, (old_volume, _) = data.previous.admitted()
        sessions = tuple(date(2026, 11, n) for n in (24, 25, 26))
        self.assertEqual(calendar, previous_calendar+sessions)
        self.assertEqual(base.sessions, old.sessions+sessions)
        self.assertEqual(base.dividends, old.dividends)
        self.assertEqual(halts, old_halts | {(d, '513500') for d in sessions[:2]})
        self.assertEqual(audit['openingHalts'], ['2026-11-24', '2026-11-25'])
        self.assertEqual(len(audit['notices']), 7)
        self.assertEqual(sum(n['kind']=='primary_redemption_suspended_2026-11-26' for n in audit['notices']), 1)
        old_audit = ROOT/'reports/2026-11-24-admission/admission.json'
        self.assertEqual(previous, json.loads(old_audit.read_bytes()))
        for symbol, last in {'510300':'3.959', '511010':'141.386', '513500':'2.489', '159920':'1.304'}.items():
            self.assertEqual(bars[symbol][sessions[-1]].close, Decimal(last))
            self.assertEqual({d:v for d,v in bars[symbol].items() if d not in sessions}, old_bars[symbol])
        for code, counts in [('510300',[1371750266,1983074614,860640082]), ('511010',[43170400,54681800,3447900])]:
            self.assertEqual([volume[code][d] for d in sessions], counts)
            self.assertEqual({d:v for d,v in volume[code].items() if d not in sessions}, old_volume[code])

    def test_digest_mismatch_blocks_new_version(self):
        corrupted = dict(data.SEALS)
        corrupted[data.MARKET] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Snapshot identity'):
            data.previous.extension_records(data.START, data.THROUGH, data.MARKET, data.CONTROL, corrupted)
