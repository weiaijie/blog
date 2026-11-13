"""New evidence admission, immutable v1, concurrent profiles and causal replay."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import interactive_backtest as work
import model_replay
import recent_backtest as api
import recent_market_data as recent
import method_windows
from research_profile import FROZEN, RECENT, current, using, profile_cache


class RecentMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.audit = recent.admitted()

    def test_recent_quotes_and_halts_reconcile(self):
        self.assertEqual(self.data[0].sessions[-1],date(2026,11,12))
        self.assertEqual(len(self.audit['addedSessions']),9)
        self.assertEqual(len(self.audit['notices']),33)
        self.assertEqual(self.audit['officialRegisterRows'],95)
        self.assertEqual(self.audit['openingHalts'],['2026-11-03','2026-11-09','2026-11-10','2026-11-11','2026-11-12'])
        for d,s in self.data[3]:
            if d>work.END:
                self.assertEqual(s,'513500')
        self.assertFalse(self.audit['changesForwardAccount'])

    def test_seal_change_blocks_evidence(self):
        with patch.dict(recent.SEALS,{recent.MARKET:'0'*64}):
            with self.assertRaisesRegex(ValueError,'seal changed'):
                recent.checked_sources()

    def test_volume_extension_preserves_old_values(self):
        from technical_factors import volume_inputs
        old,_ = volume_inputs()
        new,_ = recent.volumes()
        for s,values in old.items():
            self.assertTrue(all(new[s][d]==v for d,v in values.items()))
            self.assertEqual(set(new[s]),set(self.data[0].sessions))

    def test_v1_rejects_extension_and_v2_rejects_unadmitted_date(self):
        p=dict(work.DEFAULTS,start='2026-10-30',end='2026-11-12')
        with self.assertRaises(work.InputError):work.backtest(p)
        self.assertEqual(api.calculate('account',p)['summary']['end'],date(2026,11,12))
        with self.assertRaises(work.InputError):api.calculate('account',dict(p,end='2026-11-13'))
        self.assertEqual(current.get(),FROZEN)

    def test_opening_halt_does_not_fill_or_synthesize_catchup(self):
        p=dict(work.DEFAULTS,start='2026-11-02',end='2026-11-12',weights='0,1,0,1',rebalance='hold')
        result=api.calculate('account',p)
        blocked=[r for r in result['orders'] if r['symbol']=='513500']
        self.assertEqual(len(blocked),1)
        self.assertEqual(blocked[0]['reason'],'opening_halt')
        self.assertEqual(blocked[0]['filled'],0)
        self.assertEqual(blocked[0]['fee'],D(0))

    def test_frozen_results_identical_through_original_end(self):
        for weights in ['1,0,0,1','0,1,0,1','0,0,1,1','1,1,1,3']:
            p=dict(work.DEFAULTS,start='2024-11-01',weights=weights)
            old=work.backtest(p)
            extended=api.calculate('account',p)
            self.assertEqual(old,{k:v for k,v in extended.items() if k not in ('dataVersion','admittedThrough')})

    def test_replay_prefix_is_identical_for_all_seven_models(self):
        for model in work.OPTIONS['replayModels']:
            factor=model.startswith('multifactor_')
            p=dict(work.DEFAULTS,start='2026-10-26',end='2026-11-12',weights='1,0,0,1',model=model,
                   rebalance='signal' if factor else 'monthly',step='all')
            if model=='installments':p['installments']='3'
            full=api.calculate('replay',p)
            prefix=api.calculate('replay',dict(p,step='4'))
            with self.subTest(model=model):
                self.assertEqual(prefix['frames'],full['frames'][:4])

    def test_profile_and_cache_are_thread_local_and_reset_on_failure(self):
        @profile_cache(2)
        def cached():return current.get()
        def check(profile):
            with using(profile):
                self.assertEqual(cached(),profile)
                self.assertEqual(work.inputs()[0].sessions[-1],work.END if profile==FROZEN else recent.THROUGH)
            return current.get()
        with ThreadPoolExecutor(4) as pool:
            self.assertEqual(list(pool.map(check,[FROZEN,RECENT]*8)),[FROZEN]*16)
        with self.assertRaises(RuntimeError),using(RECENT):raise RuntimeError('abort')
        self.assertEqual(current.get(),FROZEN)

    def test_extended_maturities_are_recomputed_not_served_from_old_archive(self):
        params=dict(method_windows.DEFAULTS,start='2025-11-03',end='2026-11-12')
        with patch.object(method_windows,'archived_entries',side_effect=AssertionError('old archive')):
            result=api.calculate('method-windows',params)
        self.assertGreater(result['periods'][1]['allocation']['count'],0)
        self.assertEqual(result['periods'][2]['allocation']['count'],0)
        self.assertEqual(result['lastSession'],recent.THROUGH)

    def test_exact_default_archive_is_versioned_and_hash_checked(self):
        params=dict(method_windows.DEFAULTS,end='2026-11-12')
        with patch.dict(api.OPERATIONS,{'method-windows':lambda p: self.fail('Default recomputed')}):
            result=api.calculate('method-windows',params)
        self.assertEqual(result['dataVersion'],RECENT)
        self.assertEqual(result['periods']['2']['allocation']['count'],1371)
        name,_=api.DEFAULT_ARCHIVES['method-windows']
        with patch.dict(api.DEFAULT_ARCHIVES,{'method-windows':(name,'0'*64)}):
            with self.assertRaisesRegex(ValueError,'comparison changed'):
                api.calculate('method-windows',params)


if __name__=='__main__':unittest.main()
