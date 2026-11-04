"""Deterministic cash/receivable accounting using unadjusted fill prices.

No strategy, returns, market-data fetching, or broker connectivity is implemented.
Call open_session -> trade(s) -> close_session for every supplied trading session.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping

ZERO = Decimal('0')


def money(value, *, positive=False):
    if isinstance(value, (float, bool)):
        raise TypeError('Use Decimal, integer, or decimal string; floats are not accepted')
    amount = Decimal(value)
    if not amount.is_finite() or amount < ZERO or (positive and amount == ZERO):
        raise ValueError('Amount must be finite and nonnegative (positive for prices/dividends)')
    return amount


@dataclass(frozen=True)
class Dividend:
    symbol: str
    announcement_date: date
    record_date: date
    ex_date: date
    pay_date: date
    per_share: Decimal

    def __post_init__(self):
        if not self.symbol or not (self.announcement_date <= self.record_date < self.ex_date <= self.pay_date):
            raise ValueError('Invalid dividend dates or symbol')
        object.__setattr__(self, 'per_share', money(self.per_share, positive=True))

    @property
    def key(self):
        return self.symbol, self.ex_date


@dataclass(frozen=True)
class Costs:
    """Explicit scenario assumptions, not a verified broker tariff.

Fees are rounded neither here nor silently to cents; precise treatment can be
configured in a future broker-specific fee model before net-return research.
"""
    commission_rate: Decimal
    minimum_commission: Decimal
    slippage_bps: Decimal
    sell_tax_rate: Decimal

    def __post_init__(self):
        for field in self.__dataclass_fields__:
            object.__setattr__(self, field, money(getattr(self, field)))
        if self.slippage_bps >= 10000 or self.commission_rate >= 1 or self.sell_tax_rate >= 1:
            raise ValueError('Invalid cost rate')


class Ledger:
    def __init__(self, sessions, dividends, *, cash, holdings, costs, lot_size):
        self.sessions = tuple(sessions)
        if not self.sessions or list(self.sessions) != sorted(set(self.sessions)):
            raise ValueError('Sessions must be nonempty, unique and increasing')
        if not all(type(d) is date for d in self.sessions):
            raise TypeError('Sessions require datetime.date')
        if type(lot_size) is not int or lot_size <= 0:
            raise ValueError('Positive integer lot_size required')
        self.lot_size, self.costs = lot_size, costs
        self.cash = money(cash)
        self.holdings = dict(holdings)
        if any(type(n) is not int or n < 0 for n in self.holdings.values()):
            raise ValueError('Nonnegative integer initial units required')
        events = tuple(dividends)
        if len({e.key for e in events}) != len(events):
            raise ValueError('Duplicate dividend event')
        first, last = self.sessions[0], self.sessions[-1]
        # Opening holdings do not establish historical entitlement.
        if any(e.record_date < first <= e.pay_date for e in events):
            raise ValueError('Starting across a dividend requires explicit prior entitlement; unsupported')
        self.dividends = tuple(e for e in events if e.record_date >= first and e.record_date <= last)
        for e in self.dividends:
            for d in [e.record_date, e.ex_date]:
                if first <= d <= last and d not in self.sessions:
                    raise ValueError('Record/ex date missing from independent calendar')
        self.entitlements = {}
        self.receivables = {}
        self.blocked_cash = []
        self.bought_this_session = {}
        self.journal = []
        self.cursor = -1
        self.day = None
        self.is_open = False

    @property
    def available_cash(self):
        return self.cash - sum((a for _, a in self.blocked_cash), ZERO)

    def open_session(self, day):
        if self.is_open or self.cursor + 1 >= len(self.sessions) or day != self.sessions[self.cursor + 1]:
            raise ValueError('Must process each session exactly once and close it before advancing')
        self.cursor += 1
        self.day = day
        self.is_open = True
        self.bought_this_session = {}
        # Dividend cash is usable only on the first trading day strictly after payment.
        self.blocked_cash = [(p, a) for p, a in self.blocked_cash if day <= p]
        for event in self.dividends:
            if event.ex_date == day:
                amount = self.entitlements[event.key] * event.per_share
                self.receivables[event.key] = amount
                self.journal.append({'kind': 'dividend_receivable', 'day': day, 'symbol': event.symbol, 'amount': amount})
            if event.pay_date <= day and event.key in self.receivables:
                amount = self.receivables.pop(event.key)
                self.cash += amount
                if day == event.pay_date:
                    self.blocked_cash.append((event.pay_date, amount))
                self.journal.append({'kind': 'dividend_paid', 'day': day, 'symbol': event.symbol, 'amount': amount})

    def trade(self, symbol, side, units, raw_price, *, signal_date):
        if not self.is_open:
            raise ValueError('Open a session before trading')
        if signal_date not in self.sessions or signal_date >= self.day:
            raise ValueError('Signal must come from an earlier supplied trading session')
        if side not in ('buy', 'sell') or type(units) is not int or units <= 0 or units % self.lot_size:
            raise ValueError('Invalid side, units or lot multiple')
        price = money(raw_price, positive=True)
        direction = Decimal(1 if side == 'buy' else -1)
        fill_price = price * (1 + direction * self.costs.slippage_bps / 10000)
        notional = fill_price * units
        commission = max(self.costs.minimum_commission, notional * self.costs.commission_rate)
        tax = notional * self.costs.sell_tax_rate if side == 'sell' else ZERO
        fees = commission + tax
        if side == 'buy':
            if notional + fees > self.available_cash:
                raise ValueError('Insufficient available cash; receivables/payment-day cash cannot be spent')
            self.cash -= notional + fees
            self.holdings[symbol] = self.holdings.get(symbol, 0) + units
            self.bought_this_session[symbol] = self.bought_this_session.get(symbol, 0) + units
        else:
            # Conservative common rule: today's buys cannot be resold in this session.
            sellable = self.holdings.get(symbol, 0) - self.bought_this_session.get(symbol, 0)
            if units > sellable or self.available_cash + notional < fees:
                raise ValueError('Insufficient holdings or cash for fees')
            self.holdings[symbol] -= units
            self.cash += notional - fees
        record = {'kind': 'trade', 'day': self.day, 'symbol': symbol, 'side': side, 'units': units,
                  'signal_date': signal_date, 'raw_price': price, 'fill_price': fill_price,
                  'commission': commission, 'tax': tax, 'notional': notional}
        self.journal.append(record)
        return record.copy()

    def close_session(self):
        if not self.is_open:
            raise ValueError('No session open')
        for event in self.dividends:
            if event.record_date == self.day:
                units = self.holdings.get(event.symbol, 0)
                self.entitlements[event.key] = units
                self.journal.append({'kind': 'record_entitlement', 'day': self.day, 'symbol': event.symbol, 'units': units})
        self.is_open = False

    def equity(self, raw_marks: Mapping[str, Decimal]):
        return self.cash + sum(self.receivables.values(), ZERO) + sum(
            (money(raw_marks[s], positive=True) * n for s, n in self.holdings.items() if n), ZERO)
