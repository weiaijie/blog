import sys
from pathlib import Path
import unittest
import subprocess
import os
import json
from decimal import Decimal as D
from datetime import date

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import new_window_attribution as subject
import interactive_backtest as work
import multifactor_strategy
from research_profile import RECENT, using


class NewWindowAttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=subject.report()

    def test_exact_parent_cohort_and_target(self):
        source=subject.selected()
        self.assertEqual(list(source),[w['start'] for w in self.report['windows']])
        self.assertEqual(self.report['counts']['multifactor_v1'],dict(profitable=9,reached=3,fixedFillGrossReached=6))
        self.assertEqual(self.report['counts']['allocation'],dict(profitable=9,reached=0,fixedFillGrossReached=0))
        for w in self.report['windows']:
            self.assertEqual(w['end'],source[w['start']]['allocation']['end'])
            for m,v in w['metrics'].items():
                self.assertEqual(D(v['pnl']),D(source[w['start']][m]['pnl']))
                self.assertEqual(v['reached'],D(v['annualized_return'])>=D('.04'))
                self.assertEqual(v['fixedFillGrossReached'],D(v['fixedFillGrossPnl'])>=D(w['thresholdPnl']))

    def test_all_daily_and_regime_components_reconcile(self):
        for w in self.report['windows']:
            detail=subject.detail({'case':w['start']})
            total=D(0)
            for i,day in enumerate(detail['dailyGap']['days']):
                frames={m:detail['replays'][m]['frames'][i] for m in subject.MODELS}
                self.assertEqual(D(day['change']),D(frames['multifactor_v1']['dayPnl'])-D(frames['allocation']['dayPnl']))
                total+=D(day['change'])
                self.assertEqual(total,D(day['cumulative']))
                self.assertEqual(total,D(frames['multifactor_v1']['equity'])-D(frames['allocation']['equity']))
                self.assertEqual(D(day['change']),sum(D(v[k]) for v in day['byEtf'].values() for k in subject.PARTS))
            self.assertEqual(total,D(w['difference']['accountChange']))
            for s in subject.SYMBOLS:
                for k in ('price','dividend'):
                    self.assertEqual(sum(D(p[s][k]) for p in w['regime']['parts'].values()),D(w['difference']['byEtf'][s][k]))
            self.assertGreater(total,0)

    def test_separate_direct_simulation_matches_every_account(self):
        # Rebuild schedules directly, independently of the UI replay-to-ledger adapter.
        with using(RECENT):
            base,_,bars,_=work.inputs()
            for w in self.report['windows']:
                days,_,simulate=work.configured_replay(dict(start=w['start'],end=w['end'],capital='100000',fees='base',weights='1,0,0,1',rebalance='hold'))
                index=base.sessions.index(days[0])
                _,schedule=multifactor_strategy.factor_schedule(base.sessions[index-120:index],days,days,bars,base.dividends)
                detail=subject.detail({'case':w['start']})
                for m in subject.MODELS:
                    ledger,orders=simulate(days,**({'schedule':schedule} if m=='multifactor_v1' else {}))
                    self.assertEqual([r['equity'] for r in ledger],[D(f['equity']) for f in detail['replays'][m]['frames']])
                    self.assertEqual(ledger[-1]['equity']-D('100000'),D(w['metrics'][m]['pnl']))

    def test_roundtrip_rebuild_is_identical(self):
        start=next(iter(subject.selected()))
        rebuilt=subject.calculate(start,subject.selected()[start])
        self.assertEqual(work.encode(rebuilt),(subject.REPORT/(start+'.json')).read_bytes())

    def test_unknown_and_path_injection_are_rejected(self):
        for key in ('../comparison','2024-10-30','2026-11-13',''):
            with self.assertRaises(work.InputError):subject.detail({'case':key})

    def test_agent_cli_runs_without_pythonpath_setup(self):
        env=dict(os.environ);env.pop('PYTHONPATH',None)
        output=subprocess.check_output([sys.executable,str(Path(subject.__file__)),'--case','2024-11-05'],env=env)
        self.assertEqual(json.loads(output),subject.detail({'case':'2024-11-05'}))


if __name__=='__main__':unittest.main()
