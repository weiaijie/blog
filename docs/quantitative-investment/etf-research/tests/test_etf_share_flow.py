"""Clearance scaling, NAV date alignment, unknowns, and post-receipt timing."""
from decimal import Decimal as D
from datetime import datetime
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import etf_share_flow as flow


class ShareFlowTests(unittest.TestCase):
    def test_aligned_net_units_with_prior_assets(self):
        self.assertEqual(flow.estimate((D(100),D(2)),(D(120),D(3)),comparable=True,adjacent=True),
                         (D(60), D('.3')))
        self.assertEqual(flow.estimate((D(120),D(3)),(D(100),D(2)),comparable=True,adjacent=True)[0], D(-40))
        for kw in [dict(comparable=False,adjacent=True),dict(comparable=True,adjacent=False),
                   dict(comparable=True,adjacent=True,currency='USD')]:
            self.assertEqual(flow.estimate((D(100),D(2)),(D(120),D(3)),**kw),(None,None))
        self.assertEqual(flow.estimate((None,D(2)),(D(120),D(3)),comparable=True,adjacent=True),(None,None))

    def test_sealed_sources_pcf_day_and_unavailable_day(self):
        r=json.loads(flow.REPORT.read_bytes())
        self.assertEqual(r,flow.build(r['firstObservedCalculationAt']))
        self.assertEqual(r['clearingTableRows']['2026-11-27'],0)
        bonds={w['valuationDate']:w for w in r['rows'] if w['symbol']=='511010'}
        self.assertEqual(D(bonds['2026-11-26']['totalShares']),D('71966300'))
        self.assertEqual(D(bonds['2026-11-26']['unitNav']),D('141.371'))
        self.assertEqual(D(bonds['2026-11-26']['estimatedNetSubscriptionCny']),D('46652430'))
        self.assertEqual(sum(w['status']=='verified_estimate' for w in r['rows']),4)
        for w in r['rows']:
            self.assertIsNone(w['buyerIdentity'])
            self.assertIsNone(w['publishedAt'])
            if w['status']=='unknown':
                self.assertEqual(w['valuationDate'],'2026-11-27')
                self.assertTrue(all(w[k] is None for k in ['totalShares','unitNav','estimatedNetSubscriptionCny','availableAt','relativeIntensity']))
            else:
                self.assertTrue(all(datetime.fromisoformat(w['availableAt'])>=datetime.fromisoformat(r['sources'][k]['receivedAt']) for k in w['sourceKeys']))

    def test_ban_lookahead_from_historical_capture(self):
        with self.assertRaisesRegex(ValueError,'ready time'):
            flow.build('2026-11-27T12:24:37+08:00')
