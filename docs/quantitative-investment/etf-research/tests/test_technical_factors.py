from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import interactive_backtest as work
from factor_lab import DEFAULTS, MODELS, REPORT, detail, replay_params
from model_replay import replay
from technical_factors import admit_volume, indicator_series, technical_schedule, volume_inputs


class TechnicalTests(unittest.TestCase):
    def test_volume_conflict_gap_duplicate_and_unit_rejected(self):
        day=date(2020,1,2)
        bars={s:{day:SimpleNamespace(open=D(10),high=D(11),low=D(9),close=D(10))} for s in ('510300','511010')}
        official={s:dict(code=s,total=1,kline=[[20200102,10,11,9,10,100,1000]]) for s in bars}
        sina={s:[dict(day=str(day),volume='100')] for s in bars}
        values,_=admit_volume([day],bars,official,sina)
        self.assertEqual(values['510300'][day],100)
        for field,value in [(5,0),(5,101),(6,100000)]:
            damaged=deepcopy(official);damaged['510300']['kline'][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                admit_volume([day],bars,damaged,sina)
        for variant in ([],sina['510300']*2):
            damaged=dict(sina,**{'510300':variant})
            with self.assertRaises((KeyError,ValueError)):
                admit_volume([day],bars,official,damaged)

    def test_declared_kdj_seed_and_dividend_neutrality(self):
        days=[date(2020,1,1)+timedelta(days=i) for i in range(150)]
        bars={'510300':{d:SimpleNamespace(open=D(100),high=D(101),low=D(99),close=D(100)) for d in days}}
        volume={'510300':dict.fromkeys(days,100)}
        out=indicator_series(days,bars,[],volume)
        np.testing.assert_allclose(out.k.dropna(),50)
        np.testing.assert_allclose(out.d.dropna(),50)
        # Neutral dividend with equal-price OHLC must not create a price jump.
        flat={'510300':{d:SimpleNamespace(open=D(100),high=D(100),low=D(100),close=D(100)) for d in days}}
        flat['510300'][days[-1]]=SimpleNamespace(open=D(99),high=D(99),low=D(99),close=D(99))
        event=SimpleNamespace(symbol='510300',announcement_date=days[-2],ex_date=days[-1],per_share=D(1))
        adjusted=indicator_series(days,flat,[event],volume)
        self.assertEqual(adjusted.iloc[-1]['return'],0)
        self.assertEqual(adjusted.iloc[-1].k,50)
        self.assertEqual(adjusted.iloc[-1].adx,0)
        event.announcement_date=days[-1]+timedelta(days=1)
        self.assertLess(indicator_series(days,flat,[event],volume).iloc[-1]['return'],0)

    def test_independent_wilder_adx_and_kdj_recurrence(self):
        base,_,bars,_=work.inputs()
        out=indicator_series(base.sessions,bars,base.dividends,volume_inputs()[0])
        k=d=50.
        for i in range(8,len(out)):
            x=out.iloc[i];window=out.iloc[i-8:i+1]
            span=window.high.max()-window.low.min()
            rsv=100*(x.close-window.low.min())/span if span else 50
            k=(2*k+rsv)/3;d=(2*d+k)/3
            self.assertAlmostEqual(x.k,k,places=10)
            self.assertAlmostEqual(x.d,d,places=10)
            self.assertAlmostEqual(x.j,3*k-2*d,places=10)
        plus=minus=tr=0.;dx=[];adx=None
        for i in range(1,len(out)):
            x,p=out.iloc[i],out.iloc[i-1]
            up=x.high-p.high;down=p.low-x.low
            pm=up if up>down and up>0 else 0.
            mm=down if down>up and down>0 else 0.
            true=max(x.high-x.low,abs(x.high-p.close),abs(x.low-p.close))
            if i<14:
                plus+=pm;minus+=mm;tr+=true;continue
            plus=plus-plus/14+pm;minus=minus-minus/14+mm;tr=tr-tr/14+true
            pdi=100*plus/tr if tr else 0.;mdi=100*minus/tr if tr else 0.
            self.assertAlmostEqual(x.plusDI,pdi,places=9)
            self.assertAlmostEqual(x.minusDI,mdi,places=9)
            val=100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else 0.
            dx.append(val)
            if i==27:adx=sum(dx)/14
            elif i>27:adx=(13*adx+val)/14
            if adx is not None:self.assertAlmostEqual(x.adx,adx,places=9)

    def test_clipped_future_prices_and_volumes_do_not_change_prefix(self):
        base,calendar,bars,halts=work.inputs()
        volumes,audit=volume_inputs()
        params=dict(DEFAULTS,start='2024-10-08',end='2025-03-03')
        for model in list(MODELS)[1:]:
            full=replay(replay_params(params,model))['frames']
            for count in (1,2,20,70):
                cutoff=full[count-1]['date']
                clipped={s:{d:b for d,b in rows.items() if d<=cutoff} for s,rows in bars.items()}
                known=replace(base,bars={s:clipped[s] for s in base.bars},dividends=tuple(e for e in base.dividends if e.announcement_date<=cutoff))
                v={s:{d:n for d,n in rows.items() if d<=cutoff} for s,rows in volumes.items()}
                with self.subTest(model=model,count=count),patch.object(work,'inputs',return_value=(known,calendar,clipped,halts)),patch('technical_factors.volume_inputs',return_value=(v,audit)):
                    actual=replay(dict(replay_params(params,model),step=str(count)))['frames']
                self.assertEqual(actual,full[:count])
            for prev,row in zip(full,full[1:]):
                for order in row['orders']:
                    self.assertEqual(order['signal'],prev['date'])
                    self.assertEqual(order['target'],prev['nextPlan']['target'][order['symbol']])
            for row in full:
                decision=row['decision']
                self.assertEqual(decision['regime']=='balanced',decision['votes']>=2 and decision['gate']['passed'])

    def test_all_published_worst_windows_match_replay(self):
        report=json.loads((REPORT/'comparison.json').read_text())
        for y,groups in report['periods'].items():
            for model,stats in groups.items():
                params=dict(DEFAULTS,start=stats['worstStart'],end=stats['worstEnd'])
                frames=replay(replay_params(params,model))['frames']
                self.assertEqual(frames[-1]['pnl'],D(str(stats['worstPnl'])))
                self.assertEqual(frames[0]['cash'],D(DEFAULTS['capital']))
                self.assertEqual(stats['profitable']+stats['losing']+stats['flat'],stats['count'])
                self.assertTrue(all(row['equity']-prev['equity']==row['dayPnl'] for prev,row in zip(frames,frames[1:])))

    def test_default_archive_rejects_corruption(self):
        import factor_lab
        factor_lab._compare.cache_clear()
        with tempfile.TemporaryDirectory() as folder:
            Path(folder,'comparison.json').write_text('{}')
            with patch.object(factor_lab,'REPORT',Path(folder)),self.assertRaisesRegex(ValueError,'Published technical'):
                factor_lab.compare(DEFAULTS)
        factor_lab._compare.cache_clear()

    def test_gate_models_reject_foreign_weights_or_wrong_schedule(self):
        for model in list(MODELS)[1:]:
            params=replay_params(DEFAULTS,model)
            for change in (dict(weights='0,1,0,1'),dict(rebalance='monthly'),dict(start=work.OPTIONS['domesticFirst'])):
                with self.assertRaises(work.InputError):
                    replay(params|change)
