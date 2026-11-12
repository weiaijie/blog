from copy import deepcopy
from datetime import date,timedelta
from decimal import Decimal as D
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import adx_trades as trades
import adx_bond
from compare_three_markets import CODES,anniversary
from bisect import bisect_left


class AdxTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((trades.REPORT/'comparison.json').read_text())

    def test_closed_open_and_dividend_after_exit_reconcile(self):
        days=[date(2020,1,1)+timedelta(days=i) for i in range(6)]
        marks=[10,10,12,13,10,10]
        bars={s:{d:SimpleNamespace(open=D(marks[i] if s=='510300' else 10),close=D(marks[i] if s=='510300' else 10)) for i,d in enumerate(days)} for s in CODES}
        def row(i,stock,cash,receivable=0,bond=0):
            return dict(date=days[i],equity=D(cash)+D(receivable)+stock*marks[i]+bond*10,cash=D(cash),receivables=D(receivable),available_cash=D(cash),
                        **{'units_'+s:stock if s=='510300' else bond if s=='511010' else 0 for s in CODES})
        daily=[row(0,0,1000),row(1,5,950),row(2,5,950),row(3,0,1015),row(4,0,1015,5),row(5,2,995,5)]
        def order(i,side,n):return dict(day=days[i],symbol='510300',side=side,filled=n,open=D(marks[i]),modeled_price=D(marks[i]),fee=D(0))
        bond=[row(i,0,1000) for i in range(6)]
        events=[SimpleNamespace(symbol='510300',record_date=days[2],ex_date=days[4],pay_date=days[-1]+timedelta(days=3),per_share=D(1)),
                SimpleNamespace(symbol='510300',record_date=days[-1],ex_date=days[-1]+timedelta(days=1),pay_date=days[-1]+timedelta(days=3),per_share=D(1))]
        books={trades.audit.ADX:(daily,[order(1,'buy',5),order(3,'sell',5),order(5,'buy',2)]),'bonds':(bond,[])}
        r=trades.episodes(books,bars,events,{d:{} for d in days})
        self.assertEqual((r['closedCount'],r['openCount']),(1,1))
        closed,opened=r['episodes']
        self.assertEqual(closed['holdingSessions'],2)
        self.assertEqual(closed['dividendAfterExit'],5)
        self.assertEqual(closed['net'],20)
        self.assertEqual(closed['pairedGap'],15)
        self.assertEqual(opened['pendingDividend'],2)
        self.assertEqual(opened['net'],0)
        self.assertEqual(opened['reentryGapSessions'],2)
        self.assertEqual(r['episodeGap']+r['outsideEpisodeGap'],r['fullGap'])
        self.assertEqual(r['outsideEpisodeGap'],5)

    def test_every_fee_bridge_and_original_2967_endpoints(self):
        old=json.loads((adx_bond.REPORT/'comparison.json').read_text())
        expected={(r['start'],r['years']):r for r in old['windows']}
        self.assertEqual(len(self.report['windows']),2967)
        for r in self.report['windows']:
            oldrow=expected[r['start'],r['years']]
            for m in trades.MODELS:
                self.assertEqual(D(r['scenarios']['base']['accounts'][m]['equity']),D(oldrow['equities'][m]))
            for f,s in r['scenarios'].items():
                self.assertEqual(D(s['gap'])+D(s['extraCosts']),D(s['fixedFillGrossGap']))
                self.assertEqual(D(s['extraCosts'])+D(s['pathEffect']),D(s['zeroReplayImprovement']))
                self.assertEqual(D(s['gap'])+D(s['zeroReplayImprovement']),D(r['scenarios']['zero']['gap']))
                if f=='zero':self.assertEqual(D(s['extraCosts']),0)
        for y,groups in self.report['periods'].items():
            for f,s in groups.items():
                self.assertEqual(s['count'],s['beatBonds']+s['lagBonds']+s['tieBonds'])
                self.assertEqual(s['lagBonds'],s['costsReverse']+s['grossAlreadyBehind']+s['grossTied'])

    def test_all_episodes_and_bands_account_for_stock_ledger(self):
        for f,b in self.report['full'].items():
            total=D(0)
            for e in b['episodes']:
                net=D(e['price'])+D(e['dividend'])-D(e['commission'])-D(e['slippage'])
                self.assertEqual(net,D(e['net']));total+=net
                self.assertEqual(D(e['pairedGap']),D(e['accountAttribution']['differences'][trades.audit.ADX+'-bonds']['accountChange']))
            self.assertEqual(total,sum(map(D,b['stockTotals'].values())))
            self.assertEqual(b['closedCount'],sum(x['count'] for x in b['holdingBands']))
            self.assertEqual(D(b['episodeGap'])+D(b['outsideEpisodeGap']),D(b['fullGap']))
            self.assertEqual(D(b['fullGap']),D(self.report['fullCosts'][f]['gap']))

    def test_actual_episode_replay_keeps_original_capital_and_daily_sum(self):
        params=dict(trades.DEFAULTS,fees='base',episode='2025-10-10')
        r=trades.detail(params)
        self.assertEqual(r['mode'],'continuous_episode')
        self.assertNotEqual(r['curves'][trades.audit.ADX][0]['equity'],D(params['capital']))
        gap=r['attribution']['differences'][trades.audit.ADX+'-bonds']['accountChange']
        self.assertEqual(gap,r['episode']['pairedGap'])
        self.assertEqual(sum(d['change'] for d in r['daily']['days']),gap)
        for day in r['daily']['days']:
            self.assertEqual(sum(sum(day['byEtf'][s][k] for k in ('price','dividend','commission','slippage')) for s in CODES),day['change'])
            for a in day['accounts'].values():
                for o in a['orders']:self.assertLess(o['signal'],o['day'])

    def test_nonoverlap_anchors_and_immature_tails(self):
        days=tuple(d for d in adx_bond.work.inputs()[0].sessions if str(d)>=trades.DEFAULTS['start'])
        for y,chains in self.report['nonOverlapping'].items():
            self.assertEqual(len(chains),12)
            for c in chains:
                for i,r in enumerate(c['windows']):
                    self.assertEqual(r['start'],c['anchor'] if not i else c['windows'][i-1]['end'])
                    self.assertEqual(date.fromisoformat(r['end']),days[bisect_left(days,anniversary(date.fromisoformat(r['start']),int(y)))])
                if c['immatureTail']:
                    t=c['immatureTail'];self.assertLess(date.fromisoformat(t['end']),anniversary(date.fromisoformat(t['start']),int(y)))
                for s in c['summaries'].values():self.assertEqual(s['count'],len(c['windows']))

    def test_tiny_capital_no_fake_episode_and_fee_settings_unchanged(self):
        saved=deepcopy(trades.SCENARIOS)
        params=dict(start='2021-02-10',end='2022-02-10',capital='1')
        r=trades.calculate(params)
        self.assertEqual(saved,trades.SCENARIOS)
        for f,b in r['full'].items():
            self.assertEqual(b['episodes'],[])
            self.assertEqual(r['fullCosts'][f]['gap'],0)
            self.assertEqual(r['periods'][1][f]['tieBonds'],1)
        self.assertEqual(r['periods'][2]['base']['count'],0)

    def test_invalid_episode_fee_and_changed_archive_fail_closed(self):
        with self.assertRaises(trades.work.InputError):trades.detail(dict(trades.DEFAULTS,fees='bogus'))
        with self.assertRaises(trades.work.InputError):trades.detail(dict(trades.DEFAULTS,fees='base',episode='2000-01-01'))
        trades._compare.cache_clear()
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'comparison.json').write_text('{}')
            with patch.object(trades,'REPORT',Path(folder)):
                with self.assertRaisesRegex(ValueError,'archive changed'):trades.compare(trades.DEFAULTS)
        trades._compare.cache_clear()

    def test_runtime_failure_diagnosis_matches_original_bodies(self):
        from etf_research.admission import parse_prices
        import hashlib
        evidence=json.loads((trades.REPORT/'runtime-audit.json').read_text())
        self.assertTrue(evidence['transition']['timer_extension_verified'])
        self.assertEqual(len(evidence['sourceChecks']),7)
        target=date(2026,11,12)
        for i,row in enumerate(evidence['sourceChecks']):
            folder=ROOT/'data/snapshots'/row['snapshot']
            config=json.loads((folder/'config.json').read_text())
            for s in row['sources']:
                name=config['prices'][s['symbol']][s['provider']]
                body=(folder/(name+'.body')).read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(),s['sha256'])
                prices=parse_prices(body,s['provider'],target)
                self.assertEqual(str(max(prices)),s['through'])
                self.assertEqual(target not in prices,s['provider']=='sohu' and i<6)
                self.assertEqual(s['extra'],[])
if __name__=='__main__':unittest.main()
