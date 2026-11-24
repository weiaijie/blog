"""Independently reconcile the newly admitted session with the preceding sealed dataset."""
from decimal import Decimal
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import nov23_market_data as data


class November23EvidenceTests(TestCase):
    def test_previous_dates_prices_volumes_and_halts_survive_exactly(self):
        (old_base, old_calendar, old_bars, old_halts), _, (old_volume, _) = data.previous.admitted()
        (base, calendar, bars, halts), audit, (volumes, _) = data.admitted()
        self.assertEqual(calendar, old_calendar+(data.THROUGH,))
        self.assertEqual(base.sessions, old_base.sessions+(data.THROUGH,))
        self.assertEqual(base.dividends, old_base.dividends)
        self.assertEqual(halts, old_halts)
        self.assertEqual(audit['openingHalts'], [])
        self.assertEqual(len({n['sha256'] for n in audit['notices']}), 2)
        self.assertTrue(all(n['kind'] == 'premium_warning' for n in audit['notices']))
        closes = {'510300':'4.023', '511010':'141.401', '513500':'2.455', '159920':'1.309'}
        for code, close in closes.items():
            values = dict(bars[code])
            self.assertEqual(values.pop(data.THROUGH).close, Decimal(close))
            self.assertEqual(values, old_bars[code])
        for code, volume in [('510300', 1393990303), ('511010', 17616599)]:
            values = dict(volumes[code])
            self.assertEqual(values.pop(data.THROUGH), volume)
            self.assertEqual(values, old_volume[code])

    def test_unrecognised_snapshot_is_rejected(self):
        with patch.dict(data.SEALS, {data.MARKET:'0'*64}):
            with self.assertRaisesRegex(ValueError, 'Snapshot identity'):
                data.evidence()
