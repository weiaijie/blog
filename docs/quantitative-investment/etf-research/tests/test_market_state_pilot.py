"""Unit and archive checks for the Shanghai market-state pilot."""
from decimal import Decimal
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import market_state_pilot as pilot


class ShanghaiPilotTests(unittest.TestCase):
    def test_preserve_exact_residual(self):
        prior={'rzye':100}
        row={'rzye':105,'rzmre':9,'rzche':5}
        self.assertEqual(pilot.equation(row,prior),dict(status='mismatch',expectedBalanceCny='104',residualCny='1'))
        self.assertEqual(pilot.equation(dict(row,rzye=104),prior)['status'],'matched')
        self.assertIsNone(pilot.equation(row,None)['residualCny'])

    def test_baseline_excludes_current_and_requires_twenty_prior(self):
        self.assertIsNone(pilot.prior_ratio([Decimal(4)]*19,Decimal(8)))
        self.assertEqual(pilot.prior_ratio([Decimal(10000)]+[Decimal(4)]*20,Decimal(8)),Decimal(2))

    def test_detail_must_cover_every_declared_security_once(self):
        def fake(snapshot,name,sql):
            page=int(name[-1])
            rows=[dict(stockCode='600111',opDate='20261126') for _ in range(2 if page==1 else 1)]
            return dict(result=rows,pageHelp=dict(pageNo=page,pageCount=2,pageSize=2,total=3,data=rows))
        with patch.object(pilot,'PAGE_SIZE',2),patch.object(pilot,'result',fake):
            with self.assertRaisesRegex(ValueError,'Duplicate'):
                pilot.financing_detail(None,'20261126')

    def test_archive_roundtrips_with_retrospective_availability(self):
        archive=pilot.read(pilot.REPORT)
        self.assertEqual(pilot.build(archive['featureReadyAt']),archive)
        self.assertFalse(archive['historicalPointInTime'])
        self.assertIsNone(archive['publishedAt'])
        self.assertEqual(archive['balanceCounts'],{'missing_previous':1,'mismatch':27})
        self.assertTrue(all(r['combinedBalanceMatched'] and r['reconciledFinancingNetCny'] is None
                            and r['breadth'] is None for r in archive['rows']))
        latest=archive['rows'][-1]
        self.assertEqual(latest['balanceIdentity']['residualCny'],'43')
        self.assertEqual(latest['financingBuyShare'],
                         str(Decimal(latest['stockFinancingBuyCny'])/Decimal(latest['turnoverCny'])))
