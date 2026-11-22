"""The November 20 profile extends inputs without changing November 12 accounts."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import interactive_backtest as work
import november_market_data as data
import recent_backtest as api
from research_profile import LATEST, RECENT


class NovemberAdmissionTests(unittest.TestCase):
    def test_seals_and_sessions(self):
        with patch.dict(data.SEALS,{data.MARKET:'0'*64}):
            with self.assertRaisesRegex(ValueError,'Snapshot identity'): data.evidence()
        inputs, audit, (volumes, _) = data.admitted()
        self.assertEqual(len(audit['addedSessions']),6)
        self.assertEqual(len(audit['notices']),13)
        for values in volumes.values():
            self.assertEqual(set(values),set(inputs[0].sessions))

    def test_actual_opening_orders_blocked_only_for_halted_symbol(self):
        for start, end in [('2026-11-13','2026-11-16'),('2026-11-18','2026-11-19'),('2026-11-19','2026-11-20')]:
            p=dict(work.DEFAULTS,start=start,end=end,weights='0,1,0,1')
            orders=api.calculate('account',p,LATEST)['orders']
            self.assertEqual([(o['filled'],o['reason']) for o in orders if o['symbol']=='513500'],[(0,'opening_halt')])
            self.assertTrue(any(o['symbol']=='511010' and o['filled']>0 for o in orders))
            with self.assertRaises(work.InputError): api.calculate('account',p,RECENT)
        with self.assertRaises(work.InputError):
            api.calculate('account',dict(p,end='2026-11-23'),LATEST)

    def test_latest_default_archives_use_only_their_version(self):
        import method_windows
        import factor_lab
        for op, defaults in [('method-windows',method_windows.DEFAULTS), ('technical-factors',factor_lab.DEFAULTS)]:
            with patch.dict(api.OPERATIONS,{op: lambda p: self.fail('Default archive missed')}):
                latest=api.calculate(op,dict(defaults,end='2026-11-20'),LATEST)
                previous=api.calculate(op,dict(defaults,end='2026-11-12'),RECENT)
            self.assertEqual(latest['dataVersion'],LATEST)
            self.assertEqual(previous['dataVersion'],RECENT)
            for year, count in [('1',1620),('2',1377)]:
                for key, result in latest['periods'][year].items():
                    self.assertEqual(result['count'],count,key)
                    self.assertEqual(previous['periods'][year][key]['count'],count-6,key)

    def test_identical_old_replays_for_all_models(self):
        for model in work.OPTIONS['replayModels']:
            p=dict(work.DEFAULTS,start='2026-10-26',end='2026-11-12',weights='1,0,0,1',
                   model=model,step='all',rebalance='signal' if model.startswith('multifactor_') else 'monthly')
            if model=='installments': p['installments']='3'
            old=api.calculate('replay',p,RECENT)
            new=api.calculate('replay',p,LATEST)
            self.assertEqual(old['frames'],new['frames'],model)
