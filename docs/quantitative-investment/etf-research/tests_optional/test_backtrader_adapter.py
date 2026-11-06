import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal as D
from etf_research.data import Dataset,RawBar
from etf_research.accounting import Dividend
from etf_research.backtrader_adapter import replay_targets

DAYS=tuple(date(2026,1,n) for n in (5,6,7,8,9,12,13))

def fixture(events=()):
    return Dataset(DAYS,{s:{d:RawBar(d,D(1),D('1.1'),D('.9'),D(1)) for d in DAYS} for s in ('510300','511010')},events,{})

class AdapterTests(unittest.TestCase):
    def test_native_fee_tick_cash(self):
        r=replay_targets(fixture(),{DAYS[1]:[('510300',100,DAYS[0])] },initial=D(1000))
        t=r['journal'][0];self.assertEqual((t['fill_price'],t['commission']),(D('1.001'),D(5)))
        self.assertAlmostEqual(float(r['daily'][1]['cash']),894.9,places=8)
    def test_dividend_paid_but_not_spendable(self):
        e=Dividend('510300',DAYS[0],DAYS[2],DAYS[3],DAYS[4],D(1))
        plan={DAYS[i]:[('510300',n,DAYS[i-1])] for i,n in [(1,100),(4,200),(5,200)]}
        r=replay_targets(fixture((e,)),plan,initial=D(100),rate=D(0),minimum=D(0),bps=D(0),enforce_guards=False)
        self.assertEqual(r['daily'][3]['receivables'],100)
        self.assertEqual((r['daily'][4]['cash'],r['daily'][4]['available_cash']),(100,0))
        self.assertEqual(r['daily'][4]['units_510300'],100)
        self.assertEqual(r['daily'][5]['units_510300'],200)
    def test_weekend_payment_available_next_session(self):
        e=Dividend('510300',DAYS[0],DAYS[2],DAYS[3],date(2026,1,10),D(1))
        r=replay_targets(fixture((e,)),{DAYS[1]:[('510300',100,DAYS[0])]},initial=D(100),rate=D(0),minimum=D(0),bps=D(0))
        self.assertEqual(r['daily'][4]['receivables'],100)
        self.assertEqual(r['daily'][5]['available_cash'],100)
    def test_same_session_resale(self):
        for symbol,sellable in [('510300',False),('511010',True)]:
            orders={DAYS[1]:[(symbol,'buy',100,DAYS[0]),(symbol,'sell',100,DAYS[0])]}
            r=replay_targets(fixture(),{},direct_orders=orders,initial=D(1000))
            self.assertEqual(r['decisions'][-1]['reason'],'filled' if sellable else 'insufficient_sellable_holdings')
    def test_odd_lot_and_short_rejected(self):
        for target,reason in [(101,'invalid_lot'),(-100,'insufficient_sellable_holdings')]:
            r=replay_targets(fixture(),{DAYS[1]:[('510300',target,DAYS[0])]})
            self.assertEqual(r['decisions'][0]['reason'],reason)
            self.assertEqual(r['daily'][1]['units_510300'],0)
    def test_cash_partial_no_late_remainder(self):
        r=replay_targets(fixture(),{DAYS[1]:[('510300',1000,DAYS[0])]},initial=D(250))
        self.assertEqual(r['decisions'][0]['filled_units'],200)
        self.assertEqual(r['daily'][-1]['units_510300'],200)
        self.assertEqual(len(r['decisions']),1)
    def test_same_day_signal_rejected(self):
        r=replay_targets(fixture(),{DAYS[1]:[('510300',100,DAYS[1])]})
        self.assertEqual(r['decisions'][0]['reason'],'invalid_signal_date')
    def test_known_ex_date_rejected(self):
        e=Dividend('510300',DAYS[0],DAYS[2],DAYS[3],DAYS[4],D('.1'))
        r=replay_targets(fixture((e,)),{DAYS[3]:[('510300',100,DAYS[2])]})
        self.assertEqual(r['decisions'][0]['reason'],'known_ex_dividend_day')
    def test_nine_percent_guard(self):
        d=fixture();bars={s:dict(v) for s,v in d.bars.items()};bars['510300'][DAYS[1]]=RawBar(DAYS[1],D('1.09'),D('1.1'),D(1),D('1.09'))
        r=replay_targets(replace(d,bars=bars),{DAYS[1]:[('510300',100,DAYS[0])]})
        self.assertEqual(r['decisions'][0]['reason'],'conservative_9pct_buffer')
    def test_missing_bar_rejected(self):
        d=fixture();bars={s:dict(v) for s,v in d.bars.items()};del bars['510300'][DAYS[1]]
        with self.assertRaisesRegex(ValueError,'Missing admitted'):replay_targets(replace(d,bars=bars),{})
    def test_sell_tax_and_sell_before_buy(self):
        plan={DAYS[1]:[('510300',100,DAYS[0])],DAYS[2]:[('510300',0,DAYS[1]),('511010',100,DAYS[1])]}
        r=replay_targets(fixture(),plan,initial=D(110),rate=D(0),minimum=D(0),bps=D(0),sell_tax=D('.001'))
        trades=[x for x in r['journal'] if x['kind']=='trade']
        self.assertEqual([x['side'] for x in trades],['buy','sell','buy'])
        self.assertEqual(trades[1]['tax'],D('.10'))
        self.assertAlmostEqual(float(r['daily'][2]['cash']),9.9,places=8)
    def test_target_execution_delay_is_preserved(self):
        for delay in (1,2,3):
            r=replay_targets(fixture(),{DAYS[delay]:[('510300',100,DAYS[0])]})
            self.assertEqual(r['journal'][0]['day'],DAYS[delay])
    def test_entitlement_survives_sale_after_record(self):
        e=Dividend('510300',DAYS[0],DAYS[2],DAYS[3],DAYS[4],D(1))
        r=replay_targets(fixture((e,)),{DAYS[1]:[('510300',100,DAYS[0])],DAYS[3]:[('510300',0,DAYS[2])]},initial=D(100),rate=D(0),minimum=D(0),bps=D(0),enforce_guards=False)
        self.assertEqual(r['daily'][3]['receivables'],100)
        self.assertEqual(r['daily'][4]['cash'],200)
        self.assertEqual(r['daily'][4]['available_cash'],100)
        self.assertEqual(r['daily'][5]['available_cash'],200)
    def test_buy_after_record_has_no_entitlement(self):
        e=Dividend('510300',DAYS[0],DAYS[2],DAYS[3],DAYS[4],D(1))
        r=replay_targets(fixture((e,)),{DAYS[3]:[('510300',100,DAYS[2])]},initial=D(100),rate=D(0),minimum=D(0),bps=D(0),enforce_guards=False)
        self.assertEqual(r['daily'][3]['receivables'],0)
        self.assertEqual(r['daily'][5]['cash'],0)
    def test_cent_half_up_rounding(self):
        r=replay_targets(fixture(),{DAYS[1]:[('510300',100,DAYS[0])]},rate=D('.00005'),minimum=D(0),bps=D(0))
        self.assertEqual(r['journal'][0]['commission'],D('.01'))
    def test_current_close_high_low_do_not_change_fill(self):
        d=fixture();plan={DAYS[1]:[('510300',100,DAYS[0])]};a=replay_targets(d,plan)
        bars={s:dict(v) for s,v in d.bars.items()};bars['510300'][DAYS[1]]=RawBar(DAYS[1],D(1),D(10),D('.001'),D(9))
        b=replay_targets(replace(d,bars=bars),plan)
        self.assertEqual(a['journal'],b['journal']);self.assertEqual(a['decisions'],b['decisions'])
    def test_adjusted_price_or_invalid_cost_rejected(self):
        d=fixture();bars={s:dict(v) for s,v in d.bars.items()};bars['510300'][DAYS[1]]=replace(bars['510300'][DAYS[1]],price_mode='adjusted')
        with self.assertRaisesRegex(ValueError,'mode'):replay_targets(replace(d,bars=bars),{})
        with self.assertRaisesRegex(ValueError,'cost'):replay_targets(d,{},bps=D(-1))
    def test_exact_cash_boundary_is_known_native_difference(self):
        from etf_research.accounting import Ledger,Costs,InstrumentRules
        d=fixture();bars={s:{day:RawBar(day,D('1.026'),D('1.026'),D('1.026'),D('1.026')) for day in DAYS} for s in d.bars};d=replace(d,bars=bars)
        r=replay_targets(d,{DAYS[1]:[('510300',100,DAYS[0])]},initial=D('107.6'),rate=D(0),minimum=D(5),bps=D(0))
        # Native float cash computes a tiny negative balance and rejects the order.
        self.assertEqual(r['decisions'][0]['reason'],'native_margin_rejection')
        old=Ledger(DAYS,[],cash=D('107.6'),holdings={},costs=Costs(D(0),D(5),D(0),D(0)),lot_size=100,instruments={'510300':InstrumentRules(100,D('.001'),False)})
        old.open_session(DAYS[0]);old.close_session();old.open_session(DAYS[1]);old.trade('510300','buy',100,D('1.026'),signal_date=DAYS[0])
        self.assertEqual(old.cash,0)
        self.assertEqual(old.holdings['510300'],100)
        self.assertEqual(r['daily'][1]['units_510300'],0)

if __name__=='__main__':unittest.main()
