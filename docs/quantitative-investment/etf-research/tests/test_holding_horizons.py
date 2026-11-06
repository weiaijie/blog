import unittest
from etf_research.holding_horizons import windows, summarize, disjoint


class HoldingHorizonTests(unittest.TestCase):
    def test_anniversary_holiday_and_partial_tail(self):
        rows = windows(['2020-01-01','2020-06-01','2021-01-04','2022-01-04'],[100,80,110,120],1)
        self.assertEqual(rows[0]['end'], '2021-01-04')
        self.assertEqual(rows[0]['calendar_days'],369)
        self.assertAlmostEqual(rows[0]['max_drawdown'],.2)
        self.assertEqual(len(rows),3)

    def test_leap_day(self):
        rows=windows(['2020-02-29','2021-02-28'],[100,104],1)
        self.assertEqual(rows[0]['anniversary'],'2021-02-28')
        self.assertEqual(rows[0]['calendar_days'],365)

    def test_window_peak_resets(self):
        rows=windows(['2019-01-01','2020-01-01','2021-01-01'],[200,100,110],1)
        self.assertEqual(rows[1]['max_drawdown'],0)

    def test_phase_does_not_overlap(self):
        rows=windows(['2018-01-01','2018-07-01','2019-01-01','2019-07-01','2020-01-01'],[100]*5,1)
        chosen=disjoint(rows,'2018-01-01',0)
        self.assertEqual([r['start'] for r in chosen],['2018-01-01','2019-01-01'])
        self.assertEqual(disjoint(rows,'2018-01-01',6)[0]['start'],'2018-07-01')

    def test_empty_is_not_low_risk(self):
        self.assertIsNone(summarize([])['losses'])
        self.assertEqual(windows(['2020-01-01','2020-02-01'],[100,99],2),[])

    def test_invalid_input_blocks(self):
        for dates,nav in [(['2020-01-01']*2,[100,101]),(['2021-01-01','2020-01-01'],[100,101]),(['2020-01-01','2021-01-01'],[100,0]),(['2020-01-01','2021-01-01'],[100,float('nan')])]:
            with self.assertRaises(ValueError):windows(dates,nav,1)
