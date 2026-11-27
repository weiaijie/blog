"""Synthetic, read-only comparison with Backtrader defaults; not a strategy backtest."""
from datetime import date
from decimal import Decimal as D, ROUND_HALF_UP
import json
from pathlib import Path
import sys
import tempfile

import backtrader as bt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from etf_research.accounting import Costs, Dividend, InstrumentRules, Ledger

DATES = [date(2026, 1, i) for i in (5, 6, 7, 8, 9)]
RULE = InstrumentRules(100, D('0.001'), False)
COST = Costs(D('0.0003'), D('5'), D('5'), D('0'))


def run_bt(size, cash=1000, slip=0, adapted=False, short=False):
    rows = []
    class Probe(bt.Strategy):
        def next(self):
            if len(self) == 1:
                (self.sell if short else self.buy)(size=size)
            rows.append({'date': self.data.datetime.date(0).isoformat(),
                         'cash': self.broker.getcash(), 'units': self.position.size})
        def notify_order(self, order):
            if order.status in (order.Completed, order.Margin, order.Rejected):
                rows.append({'status': order.getstatusname(),
                             'date': self.data.datetime.date(0).isoformat(),
                             'price': order.executed.price, 'commission': order.executed.comm})
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / 'data.csv'
        p.write_text('date,open,high,low,close,volume,openinterest\n' + ''.join(
            f'{d},1.000,1.100,0.900,1.000,100000,0\n' for d in DATES))
        c = bt.Cerebro(stdstats=False)
        c.adddata(bt.feeds.GenericCSVData(dataname=str(p), dtformat='%Y-%m-%d',
                 datetime=0, open=1, high=2, low=3, close=4, volume=5, openinterest=6))
        c.broker.setcash(cash)
        if adapted:
            class ScenarioCommission(bt.CommInfoBase):
                params = (('stocklike', True), ('commtype', bt.CommInfoBase.COMM_PERC))
                def _getcommission(self, size, price, pseudoexec):
                    value = D(str(abs(size))) * D(str(price)) * D('0.0003')
                    return float(max(D('5'), value).quantize(D('.01'), rounding=ROUND_HALF_UP))
            c.broker.addcommissioninfo(ScenarioCommission())
            # Fixture-specific one-tick slippage. General bps/tick rounding needs an adapter.
            c.broker.set_slippage_fixed(.001, slip_open=True)
        else:
            c.broker.setcommission(commission=0.0003)
            c.broker.set_slippage_perc(slip, slip_open=True)
        c.addstrategy(Probe)
        c.run()
    return rows


def ledger_trade(units, cash, side='buy'):
    ledger = Ledger(DATES, [], cash=D(str(cash)), holdings={}, costs=COST,
                    lot_size=100, instruments={'ETF': RULE})
    ledger.open_session(DATES[0]); ledger.close_session(); ledger.open_session(DATES[1])
    try:
        trade = ledger.trade('ETF', side, units, D('1'), signal_date=DATES[0])
        return {'status': 'filled', 'price': str(trade['fill_price']),
                'commission': str(trade['commission']), 'cash': str(ledger.cash)}
    except ValueError as exc:
        return {'status': 'rejected', 'reason': str(exc)}


def dividend_ledger():
    event = Dividend('ETF', DATES[0], DATES[1], DATES[2], DATES[3], D('0.1'))
    ledger = Ledger(DATES, [event], cash=D('0'), holdings={'ETF': 100}, costs=COST,
                    lot_size=100, instruments={'ETF': RULE})
    rows = []
    for day in DATES:
        ledger.open_session(day)
        ledger.close_session()
        rows.append({'date': day.isoformat(), 'cash': str(ledger.cash),
                     'available_cash': str(ledger.available_cash),
                     'receivable': str(sum(ledger.receivables.values(), D('0'))),
                     'entitlement': ledger.entitlements.get(event.key)})
    return rows


def resale_ledger(same_day_resale):
    rule = InstrumentRules(100, D('0.001'), same_day_resale)
    ledger = Ledger(DATES, [], cash=D('1000'), holdings={}, costs=COST,
                    lot_size=100, instruments={'ETF': rule})
    ledger.open_session(DATES[0]); ledger.close_session(); ledger.open_session(DATES[1])
    ledger.trade('ETF', 'buy', 100, D('1'), signal_date=DATES[0])
    try:
        ledger.trade('ETF', 'sell', 100, D('1'), signal_date=DATES[0])
        return 'filled'
    except ValueError as exc:
        return str(exc)


def main():
    result = {'backtrader_version': bt.__version__, 'fixture': 'synthetic only; daily OHLC 1/1.1/0.9/1',
              'normal_100': {'backtrader': run_bt(100, slip=.0005), 'ledger': ledger_trade(100, 1000)},
              'adapted_100': {'backtrader': run_bt(100, adapted=True), 'ledger': ledger_trade(100, 1000)},
              'odd_101': {'backtrader': run_bt(101), 'ledger': ledger_trade(101, 1000)},
              'insufficient_cash': {'backtrader': run_bt(100, cash=100), 'ledger': ledger_trade(100, 100)},
              'short_from_zero': {'backtrader': run_bt(100, short=True),
                                  'ledger': ledger_trade(100, 1000, side='sell')},
              'dividend_ledger': dividend_ledger(),
              'same_session_resale_ledger': {'t_plus_0': resale_ledger(True),
                                             't_plus_1': resale_ledger(False)}}
    def outcome(case):
        return next(x for x in result[case]['backtrader'] if 'status' in x)
    assert outcome('normal_100')['date'] == DATES[1].isoformat()
    assert outcome('odd_101')['status'] == 'Completed' and result['odd_101']['ledger']['status'] == 'rejected'
    assert outcome('insufficient_cash')['status'] == 'Margin' and result['insufficient_cash']['ledger']['status'] == 'rejected'
    assert result['short_from_zero']['backtrader'][-1]['units'] == -100 and result['short_from_zero']['ledger']['status'] == 'rejected'
    adapted = outcome('adapted_100')
    assert D(str(adapted['price'])) == D(result['adapted_100']['ledger']['price'])
    assert D(str(adapted['commission'])) == D(result['adapted_100']['ledger']['commission'])
    assert D(str(result['adapted_100']['backtrader'][-1]['cash'])) == D(result['adapted_100']['ledger']['cash'])
    assert [D(x['available_cash']) for x in result['dividend_ledger']] == [0, 0, 0, 0, 10]
    assert result['same_session_resale_ledger']['t_plus_0'] == 'filled'
    assert result['same_session_resale_ledger']['t_plus_1'] != 'filled'
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
