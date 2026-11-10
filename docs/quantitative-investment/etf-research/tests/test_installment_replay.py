import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import interactive_backtest as work
from model_replay import replay


class InstallmentTests(unittest.TestCase):
    params = dict(work.DEFAULTS, start='2024-10-30', end='2025-02-13', weights='1,0,0,1',
                  model='installments', installments='3', rebalance='hold', step='all')

    def test_tranches_and_accounting(self):
        frames=replay(self.params)['frames']
        plans=[r['nextPlan'] for r in frames if r['nextPlan']]
        self.assertEqual([str(p['execution']) for p in plans],['2024-10-31','2024-11-01','2024-12-02'])
        self.assertEqual([p['batch'] for p in plans],[1,2,3])
        for r in frames:
            plan=r['nextPlan']
            if plan:
                for s,n in plan['target'].items():
                    expected=int((r['equity']*plan['batch'])//(D(6)*r['bars'][s]['close']*100))*100
                    self.assertEqual(n,expected)
                    self.assertEqual(plan['change'][s],n-r['holdings'][s])
            self.assertEqual(r['equity'],r['cash']+r['receivables']+sum(
                n*r['bars'][s]['close'] for s,n in r['holdings'].items()))
        for prev,row in zip(frames,frames[1:]):
            for order in row['orders']:
                self.assertEqual(order['target'],prev['nextPlan']['target'][order['symbol']])
        for step in (1,2,3,22,28):
            self.assertEqual(replay(dict(self.params,step=str(step)))['frames'],frames[:step])

    def test_month_boundary_and_followup(self):
        params=dict(self.params,start='2024-10-31',rebalance='monthly',installments='2')
        plans=[r['nextPlan'] for r in replay(params)['frames'] if r['nextPlan']]
        self.assertEqual([(str(p['execution']),p['reason']) for p in plans],
            [('2024-11-01','installment'),('2024-12-02','installment'),('2025-01-02','monthly'),('2025-02-05','monthly')])
        tiny=replay(dict(params,capital='1',step='3'))['frames']
        self.assertTrue(all(not r['orders'] and r['equity']==1 for r in tiny))
        for n in ('0','1','13','2.5',''):
            with self.assertRaises(work.InputError):
                replay(dict(params,installments=n))
        self.assertEqual(replay({k:v for k,v in params.items() if k!='installments'})['parameters']['installments'],'3')
