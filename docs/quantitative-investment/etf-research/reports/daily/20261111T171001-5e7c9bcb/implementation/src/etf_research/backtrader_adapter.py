"""Independent native BackBroker execution of explicit, previously frozen targets.

No import of Ledger, baseline execution, guard, sizing or fee helpers. Backtrader
owns trade cash/positions; the extension owns ETF events and order restrictions.
This does not independently validate the strategy which produced the targets.
"""
from datetime import date
from decimal import Decimal as D, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
import backtrader as bt
import pandas as pd

SYMBOLS=('510300','511010')
TICK=D('.001')


class ETFCommission(bt.CommInfoBase):
    params=(('stocklike',True),('commtype',bt.CommInfoBase.COMM_PERC),
            ('rate',D('.0003')),('minimum',D(5)),('sell_tax',D(0)))

    def components(self, size, price):
        value=abs(size)*D(str(price))
        commission=max(self.p.minimum,value*self.p.rate).quantize(D('.01'),rounding=ROUND_HALF_UP)
        tax=(value*self.p.sell_tax).quantize(D('.01'),rounding=ROUND_HALF_UP) if size<0 else D(0)
        return commission,tax

    def _getcommission(self,size,price,pseudoexec):
        return float(sum(self.components(size,price)))


class ETFBroker(bt.brokers.BackBroker):
    params=(('dataset',None),('bps',D(5)),('enforce_guards',True),
            ('same_day_resale',None))

    def __init__(self):
        super().__init__()
        self.entitlements={};self.receivables={};self.blocked={}
        self.journal=[];self.decisions=[];self.bought={};self.native_fills=[]
        self.set_checksubmit(False)  # Validate sequentially at execution, after sells.
        self.set_filler(lambda order,price,ago: order.info.fill_units)

    def next(self):
        self.day=self.cerebro.datas[0].datetime.date(0);self.bought={}
        # Native broker cash is spendable. Payment-day cash is held separately.
        for key,(pay,amount) in list(self.blocked.items()):
            if pay<self.day:self.cash+=float(amount);del self.blocked[key]
        for event in self.p.dataset.dividends:
            key=(event.symbol,event.ex_date)
            if event.ex_date==self.day:
                if key not in self.entitlements:raise ValueError('Missing prior dividend entitlement')
                amount=self.entitlements[key]*event.per_share;self.receivables[key]=amount
                self.journal.append(dict(kind='dividend_receivable',day=self.day,symbol=event.symbol,amount=amount))
            if event.pay_date<=self.day and key in self.receivables:
                amount=self.receivables.pop(key)
                if event.pay_date==self.day:self.blocked[key]=(event.pay_date,amount)
                else:self.cash+=float(amount)
                self.journal.append(dict(kind='dividend_paid',day=self.day,symbol=event.symbol,amount=amount))
        super().next()
        for event in self.p.dataset.dividends:
            if event.record_date==self.day:
                feed=next(d for d in self.cerebro.datas if d._name==event.symbol)
                n=self.getposition(feed).size;self.entitlements[(event.symbol,event.ex_date)]=n
                self.journal.append(dict(kind='record_entitlement',day=self.day,symbol=event.symbol,units=n))

    def _reject(self,order,decision,reason):
        decision['reason']=reason;self.decisions.append(decision)
        order.reject(self);self.notify(order)

    def _try_exec_market(self,order,popen,phigh,plow):
        symbol=order.data._name;side='buy' if order.isbuy() else 'sell'
        wanted=abs(order.created.size);signal=order.info.signal_date
        decision=dict(day=self.day,signal_date=signal,symbol=symbol,side=side,
                      target_units=order.info.target_units,requested_units=wanted,filled_units=0,reason=None)
        if signal not in self.p.dataset.sessions or signal>=self.day:
            return self._reject(order,decision,'invalid_signal_date')
        if wanted<=0 or wanted%100:
            return self._reject(order,decision,'invalid_lot')
        raw=D(str(popen))
        if not raw.is_finite() or raw<=0 or raw%TICK:
            return self._reject(order,decision,'invalid_price')
        sign=1 if side=='buy' else -1
        fill=(raw*(1+sign*self.p.bps/D(10000))/TICK).to_integral_value(rounding=ROUND_CEILING if sign==1 else ROUND_FLOOR)*TICK
        if self.p.enforce_guards:
            known=[e for e in self.p.dataset.dividends if e.announcement_date<self.day]
            previous=D(str(order.data.close[-1]))
            if any(e.symbol==symbol and e.ex_date==self.day for e in known):
                return self._reject(order,decision,'known_ex_dividend_day')
            if max(abs(raw/previous-1),abs(fill/previous-1))>=D('.09'):
                return self._reject(order,decision,'conservative_9pct_buffer')
        n=wanted;scheme=self.getcommissioninfo(order.data)
        if side=='sell':
            same_day=self.p.same_day_resale or {'510300':False,'511010':True}
            locked=0 if same_day[symbol] else self.bought.get(symbol,0)
            if n>self.getposition(order.data).size-locked:
                return self._reject(order,decision,'insufficient_sellable_holdings')
            if D(str(self.cash))+fill*n<sum(scheme.components(-n,fill)):
                return self._reject(order,decision,'insufficient_cash_for_fees')
        else:
            n=min(n,int(D(str(self.cash))/fill/D(100))*100)
            while n>0 and fill*n+sum(scheme.components(n,fill))>D(str(self.cash)):n-=100
        if n:
            order.addinfo(fill_units=n)
            # Explicit frozen cost-model fill, possibly outside daily high/low.
            # Native _execute still calculates cash, position, commission and notification.
            super()._execute(order,ago=0,price=float(fill))
            actual=abs(order.executed.size);decision['filled_units']=actual
            if actual:
                native_price=D(str(order.executed.price));reported_price=native_price.quantize(TICK)
                # Backtrader recomputes the average fill (float * size / size).
                # Check then normalize reporting only; never alter its cash/position.
                if abs(native_price-reported_price)>D('1e-9') or reported_price!=fill:
                    raise ValueError('Native fill price differs beyond floating representation')
                commission,tax=scheme.components(sign*actual,reported_price)
                if abs(D(str(order.executed.comm))-commission-tax)>D('1e-9'):
                    raise ValueError('Native commission differs from the declared fee scheme')
                self.native_fills.append(dict(day=self.day,symbol=symbol,side=side,units=actual,
                    native_price=str(order.executed.price),reported_price=str(reported_price),
                    native_commission=str(order.executed.comm),price_representation_delta=str(native_price-reported_price)))
                self.journal.append(dict(kind='trade',day=self.day,symbol=symbol,side=side,
                    units=actual,signal_date=signal,raw_price=raw,fill_price=reported_price,
                    commission=commission,tax=tax,notional=reported_price*actual))
                if side=='buy':self.bought[symbol]=self.bought.get(symbol,0)+actual
        decision['reason']='filled' if decision['filled_units']==wanted else ('native_margin_rejection' if order.status==bt.Order.Margin else 'cash_limited_partial_or_zero')
        self.decisions.append(decision)
        if order.alive():order.cancel();self.notify(order)  # No deferred remainder.

    def snapshot(self):
        blocked=sum((a for _,a in self.blocked.values()),D(0))
        receivable=sum(self.receivables.values(),D(0))
        return dict(date=self.day,cash=D(str(self.cash))+blocked,available_cash=D(str(self.cash)),
                    receivables=receivable,equity=D(str(self.getvalue()))+blocked+receivable,
                    **{'units_'+d._name:self.getposition(d).size for d in self.cerebro.datas})


def replay_targets(dataset, targets, *, initial=D(100000), rate=D('.0003'), minimum=D(5),
                   bps=D(5), sell_tax=D(0), enforce_guards=True, direct_orders=None):
    """Targets: {execution_date: [(symbol, target_units, signal_date), ...]}.

    Feeds contain admitted unadjusted prices only. next_open reads fixed targets,
    never computes a signal from the current OHLC. Orders use native execution.
    """
    for value in (initial,rate,minimum,bps,sell_tax):
        if not isinstance(value,D) or not value.is_finite() or value<0:raise ValueError('Invalid decimal cost/cash')
    if initial<=0 or rate>=1 or sell_tax>=1 or bps>=10000:raise ValueError('Invalid cost/cash range')
    if not dataset.sessions or any(s not in dataset.bars for s in SYMBOLS):raise ValueError('Missing sessions/instruments')
    if tuple(sorted(set(dataset.sessions)))!=dataset.sessions:raise ValueError('Unordered/duplicate sessions')
    if len({(e.symbol,e.ex_date) for e in dataset.dividends})!=len(dataset.dividends):raise ValueError('Duplicate dividend')
    for e in dataset.dividends:
        if e.record_date<dataset.sessions[0]<=e.pay_date:raise ValueError('Missing prior dividend entitlement')
        for day in (e.record_date,e.ex_date):
            if dataset.sessions[0]<=day<=dataset.sessions[-1] and day not in dataset.sessions:raise ValueError('Missing event session')
    for s in SYMBOLS:
        if set(dataset.sessions)-set(dataset.bars[s]):raise ValueError('Missing admitted daily bar')
        for day in dataset.sessions:
            bar=dataset.bars[s][day];prices=[bar.open,bar.high,bar.low,bar.close]
            if bar.day!=day or bar.price_mode!='unadjusted':raise ValueError('Wrong raw price identity/mode')
            if any(not isinstance(v,D) or not v.is_finite() or v<=0 or v%TICK for v in prices):raise ValueError('Invalid raw price/tick')
            if not bar.low<=min(bar.open,bar.close)<=max(bar.open,bar.close)<=bar.high:raise ValueError('Invalid OHLC bounds')
    for day,orders in targets.items():
        if day not in dataset.sessions:raise ValueError('Target execution day absent')
        for symbol,n,signal in orders:
            if symbol not in SYMBOLS or type(n) is not int:raise ValueError('Invalid target')
    for day,orders in (direct_orders or {}).items():
        if day not in dataset.sessions:raise ValueError('Order execution day absent')
        for symbol,side,n,signal in orders:
            if symbol not in SYMBOLS or side not in ('buy','sell') or type(n) is not int or n<=0:raise ValueError('Invalid direct order')
    class TargetReplay(bt.Strategy):
        def __init__(self):self.rows=[]
        def next_open(self):
            day=self.datas[0].datetime.date(0)
            for symbol,side,n,signal in (direct_orders or {}).get(day,[]):
                feed=self.getdatabyname(symbol)
                (self.buy if side=='buy' else self.sell)(data=feed,size=n,signal_date=signal,
                    target_units=self.getposition(feed).size+(n if side=='buy' else -n))
            planned=targets.get(day,[])
            # Position-dependent delta is independently evaluated; never consume old fill sizes.
            for side in ('sell','buy'):
                for symbol,target,signal in planned:
                    feed=self.getdatabyname(symbol);delta=target-self.getposition(feed).size
                    if (side=='buy' and delta<=0) or (side=='sell' and delta>=0):continue
                    (self.buy if side=='buy' else self.sell)(data=feed,size=abs(delta),
                        signal_date=signal,target_units=target)
        def prenext_open(self):self.next_open()
        def next(self):self.rows.append(self.broker.snapshot())
    cerebro=bt.Cerebro(stdstats=False,cheat_on_open=True)
    broker=ETFBroker(dataset=dataset,bps=bps,enforce_guards=enforce_guards)
    cerebro.setbroker(broker);broker.setcash(float(initial));broker.set_coo(True)
    broker.addcommissioninfo(ETFCommission(rate=rate,minimum=minimum,sell_tax=sell_tax))
    for symbol in SYMBOLS:
        frame=pd.DataFrame([{'datetime':pd.Timestamp(d),**{k:float(getattr(dataset.bars[symbol][d],k)) for k in ('open','high','low','close')},'volume':0} for d in dataset.sessions]).set_index('datetime')
        cerebro.adddata(bt.feeds.PandasData(dataname=frame),name=symbol)
    cerebro.addstrategy(TargetReplay);strategy=cerebro.run(runonce=False)[0]
    return {'daily':strategy.rows,'journal':broker.journal,'decisions':broker.decisions,'native_fills':broker.native_fills}
