from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import interactive_backtest as work
from etf_research.baselines import run
from model_replay import replay


class ModelReplayTests(unittest.TestCase):
    def config(self, model):
        return dict(work.DEFAULTS, start='2024-10-30', end='2025-02-13', model=model,
                    weights='1,0,0,1' if model in ('trend_120','multifactor_v1') else '1,1,1,3',
                    rebalance='signal' if model=='multifactor_v1' else 'monthly', step='all')

    def test_prefix_with_future_records_removed(self):
        base, calendar, bars, halts = work.inputs()
        for model in ('allocation','installments','trend_120','multifactor_v1'):
            params = self.config(model)
            full = replay(params)['frames']
            for count in (1,2,3,8,24,46,len(full)-1):
                cutoff = full[count-1]['date']
                clipped = {s:{d:q for d,q in records.items() if d <= cutoff} for s,records in bars.items()}
                known = replace(base, bars={s:clipped[s] for s in base.bars},
                                dividends=tuple(e for e in base.dividends if e.announcement_date<=cutoff))
                with self.subTest(model=model,count=count), patch.object(work,'inputs',return_value=(
                        known,calendar,clipped,{h for h in halts if h[0]<=cutoff})):
                    self.assertEqual(replay(dict(params,step=str(count)))['frames'], full[:count])

    def test_finished_accounts_and_targets_match(self):
        for model in ('allocation','trend_120'):
            params = self.config(model)
            frames = replay(params)['frames']
            base, _, _, _ = work.inputs()
            if model=='trend_120':
                dataset=replace(base,sessions=tuple(d for d in base.sessions if d<=frames[-1]['date']))
                reference=run(dataset,model,params['fees'],D(params['capital']),account_start=frames[0]['date'])['daily']
            else:
                reference=work.backtest({k:params[k] for k in work.DEFAULTS})['daily']
            self.assertEqual([r['equity'] for r in frames],[r['equity'] for r in reference])
            self.assertEqual(frames[0]['dayPnl'],0)
            self.assertIsNone(frames[-1]['nextPlan'])
            for prev,row in zip(frames,frames[1:]):
                for order in row['orders']:
                    self.assertEqual(order['signal'],prev['date'])
                    self.assertEqual(order['target'],prev['nextPlan']['target'][order['symbol']])
                self.assertEqual(row['equity']-prev['equity'],row['dayPnl'])

    def test_constraints(self):
        params = self.config('trend_120')
        for change in [dict(model='bad'),dict(step='0'),dict(step='9999'),dict(weights='0,1,0,1'),
                       dict(start=work.OPTIONS['domesticFirst'])]:
            with self.subTest(change=change), self.assertRaises(work.InputError):
                replay(dict(params,**change))
        hold = replay(dict(self.config('allocation'),rebalance='hold'))
        self.assertEqual(sum(f['nextPlan'] is not None for f in hold['frames']),1)
