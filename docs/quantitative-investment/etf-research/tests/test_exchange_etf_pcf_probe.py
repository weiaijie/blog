from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.policy_events import instant
from etf_research.publication import read, verify_bundle
from probe_exchange_etf_pcf import analyze

SOURCE=ROOT/'data/snapshots/20261127-disclosure-followup'


class ExchangePcfProbeTests(unittest.TestCase):
    def replay(self,name):
        sample=SOURCE/name
        verify_bundle(sample)
        saved=read(sample/'result.json')
        self.assertEqual(analyze(sample,instant(saved['checkedAt'])),saved)
        return saved

    def test_sse_and_manager_match_for_the_same_two_dates(self):
        control=self.replay('pcf-positive-control')
        self.assertEqual((control['valuationOn'],control['effectiveOn']),('2026-11-26','2026-11-27'))
        self.assertEqual(control['exchange']['navCny'],'141.3710')
        self.assertEqual(control['manager']['navCny'],'141.371')
        self.assertTrue(control['matched'])

    def test_public_prior_valuation_does_not_match_current_manager_nav(self):
        today=self.replay('pcf-1127')
        self.assertEqual((today['valuationOn'],today['effectiveOn']),('2026-11-27','2026-11-30'))
        self.assertEqual(today['exchange']['state'],'different_dates')
        self.assertEqual(today['exchange']['valuationOn'],'2026-11-26')
        self.assertEqual(today['manager']['state'],'exact_dates')
        self.assertEqual(today['manager']['navCny'],'141.339')
        self.assertIsNone(today['matched'])
