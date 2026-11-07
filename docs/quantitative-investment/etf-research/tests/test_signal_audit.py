from datetime import date, timedelta
from decimal import Decimal as D
from types import SimpleNamespace
import unittest

from etf_research.signal_audit import batches, close_book, lots, signal_weights


class SignalAuditTests(unittest.TestCase):
    def test_future_close_and_future_dividend_do_not_change_cutoff(self):
        days = [date(2020,1,1) + timedelta(days=n) for n in range(121)]
        prices = list(zip(days, [D(100)]*120+[D(250)]))
        def event(announce, ex):
            return SimpleNamespace(symbol='510300',announcement_date=announce,ex_date=ex,per_share=D(12))
        future = event(days[-2], days[-1])
        as_of = days[-2]
        off = (D(0),D(1))
        self.assertEqual(signal_weights('trend_120', prices, [future], as_of), (off,D(0)))
        prices[-1] = (days[-1],D(1))
        self.assertEqual(signal_weights('trend_120', prices, [future], as_of), (off,D(0)))
        past = event(days[-4], as_of)
        self.assertEqual(signal_weights('trend_120',prices,[past],as_of)[0], (D('.5'),D('.5')))
        with self.assertRaises(ValueError):
            signal_weights('trend_120',prices,[],days[118])

    def test_warmup_delay_and_pending_use_sessions_not_days(self):
        days = [date.fromisoformat(x) for x in ['2022-01-27','2022-01-28','2022-02-07','2022-02-08']]
        self.assertEqual(list(batches(days,'monthly_20_80',3)),[(0,3),(1,4)])
        self.assertFalse(list(batches(days,'trend_120',1)))
        self.assertEqual(list(batches(days,'equity_hold',1)),[(0,1)])

    def test_lot_boundary(self):
        self.assertEqual(lots(D('999.99'),(D(10), D(1)),(D(1), D(0))), (0,0))
        self.assertEqual(lots(D('1000'),(D(10), D(1)),(D(1), D(0))), (100,0))

    def test_record_date_rights_survive_sale_before_payment(self):
        days = [date(2020,1,n) for n in (2,3,6)]
        sym = '510300'
        e = SimpleNamespace(symbol=sym,record_date=days[0],ex_date=days[1],pay_date=days[2],
                            per_share=D('.5'),key=(sym,days[1]))
        bars = {s:{d:SimpleNamespace(close=D(10)) for d in days} for s in ('510300','511010')}
        dataset = SimpleNamespace(dividends=[e],sessions=days,bars=bars)
        def fill(side):
            return dict(symbol=sym,side=side,units=100,model_fill='10',commission='5',sell_tax='0')
        nav, held = close_book(dataset, 2000, {days[0]:[fill('buy')],days[1]:[fill('sell')]})
        self.assertEqual(nav,[D(1995),D(2040),D(2040)])
        self.assertEqual(held,[(100,0),(0,0),(0,0)])
