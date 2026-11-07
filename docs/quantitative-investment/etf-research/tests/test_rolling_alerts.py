import json
from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from etf_research.rolling_alerts import episodes, metrics, states

RISK = json.loads((Path(__file__).resolve().parents[1]/'config/research.json').read_text())['risk']


class RollingRiskTests(unittest.TestCase):
    def test_threshold_equality(self):
        for rule, key, expected in [
            ('current_drawdown_warning','drawdown_warning','clear'),
            ('observed_year_drawdown_limit','annual_drawdown_limit','active'),
            ('volatility_limit','annual_volatility_limit','active'),
            ('volatility_warning','annual_volatility_warning','clear'),
            ('var_limit','daily_var_limit','active'),
            ('sharpe_below_or_equal_target','sharpe_target','active'),
            ('daily_move_warning','daily_move_warning','clear')]:
            with self.subTest(rule=rule):
                self.assertEqual(states(pd.Series([np.nan,RISK[key]]),rule,RISK).tolist(), ['unknown',expected])
        self.assertEqual(states(pd.Series([-.06]),'daily_move_warning',RISK)[0], 'active')

    def test_calendar_year_anchor_latch_and_clear(self):
        days = ['2020-12-31','2021-01-04','2021-01-05','2022-01-04']
        field = 'observed_year_drawdown_limit'
        path = metrics([100,80,100,100], days, RISK)
        flags = states(path.year_drawdown, field, RISK)
        self.assertEqual(flags.tolist(), ['clear','active','active','clear'])
        row, = episodes('a',field,days,flags)
        self.assertEqual((row['sessions'],row['cleared'],row['clearance_reason']), (2,days[-1],'year_reset'))

    def test_unknown_separates_runs_without_claiming_clearance(self):
        days = ['2020-01-02','2020-01-03','2020-01-06','2020-01-07','2020-01-08']
        rows = episodes('a','rolling',days,['active','active','unknown','active','active'])
        self.assertEqual([(x['sessions'],x['status'],x['cleared']) for x in rows],
                         [(2,'interrupted_unknown',''),(2,'open','')])
        self.assertEqual(rows[1]['start'],days[3])

    def test_window_needs_returns_and_constant_nav_has_no_sharpe(self):
        days = ['2020-01-02','2020-01-03','2020-01-06','2020-01-07']
        path = metrics([100]*len(days), days, {**RISK,'lookback_returns':3})
        self.assertTrue(path.rolling_volatility.iloc[:3].isna().all())
        self.assertEqual(path.rolling_volatility.iloc[-1], 0)
        self.assertTrue(path.rolling_sharpe.isna().all())
