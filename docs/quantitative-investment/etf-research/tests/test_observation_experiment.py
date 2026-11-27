from datetime import date, datetime, time, timedelta
from decimal import Decimal as D
import unittest
from zoneinfo import ZoneInfo

from etf_research.accounting import Dividend
from etf_research.data import Dataset, RawBar
from etf_research.observation_experiment import (VARIANTS, availability, five_day_label,
    holdouts, label_floor, nonoverlap, paired_predictions, paired_report, relative_turnover, shadow_weight, sleeve_inputs, total_return_levels, windows)

TZ = ZoneInfo('Asia/Shanghai')
START = date(2027,1,4)
STARTED_AT = datetime.combine(START,time(19,45),TZ).isoformat()


def calendar(start, end):
    return tuple(day for i in range((end-start).days+1)
                 if (day:=start+timedelta(days=i)).weekday()<5)


def cell(window, value, **overrides):
    stamp = (window.cutoff-timedelta(minutes=2)).isoformat()
    return dict(asOf=str(window.anchor),verified=True,value=value,receivedAt=stamp,
                readyAt=stamp,dependencyReadyAt=[]) | overrides


def label():
    return dict(terminalReturn=D(0),maxDrawdown=D(0))


class ExperimentalGateTests(unittest.TestCase):
    def test_actual_timing_and_dependency_chain(self):
        window = next(windows(calendar(START,date(2027,1,12))))
        valid = cell(window,3)
        self.assertEqual(availability(valid,window),3)
        after = (window.cutoff+timedelta(microseconds=1)).isoformat()
        for bad in (cell(window,0,readyAt=after),cell(window,0,dependencyReadyAt=[after]),
                    cell(window,0,dependencyReadyAt=[None]),cell(window,0,asOf=str(window.entry)),
                    cell(window,0,receivedAt=after),cell(window,0,verified=False)):
            self.assertIsNone(availability(bad,window))
        self.assertIsNone(availability(valid,window,sealed=window.cutoff-timedelta(minutes=3)))
        before = (window.cutoff-timedelta(minutes=1)).isoformat()
        self.assertIsNone(availability(cell(window,0,dependencyReadyAt=[before]),window))
        self.assertEqual(relative_turnover([10]*20+[20]),2)
        self.assertEqual(sleeve_inputs([100]*21),(0,0,0))
        levels = total_return_levels([D(4)]*20+[D('3.90')],[D(0)]*19+[D('.10')])
        self.assertEqual(sleeve_inputs(levels),(0,0,0))
        self.assertIsNone(total_return_levels([D(4)]*21,[D(0)]*19+[None]))
        self.assertEqual(shadow_weight([.00001,.1]),D('.5'))
        self.assertEqual(shadow_weight([0,.1]),D(0))
        self.assertEqual(shadow_weight([-.00001,.1]),D(0))

    def test_five_closes_costs_and_dividend_entitlement(self):
        dates = calendar(START,date(2027,1,11))
        window = next(windows(dates))
        bars = {s:{d:RawBar(d,p,p+D('.50'),p-D('.50'),p) for d in dates}
                for s,p in (('510300',D(4)),('511010',D(100)))}
        dividend = Dividend('510300',dates[1],dates[2],dates[3],dates[4],D('.1'))
        data = Dataset(dates,bars,(dividend,),{})
        raw = Dataset(dates,bars,(),{})
        admission = {'510300':'tradable','511010':'tradable'}
        result = five_day_label(data,window,admission)
        no_cash = five_day_label(raw,window,admission)
        self.assertEqual(len(result['marks']),6)
        self.assertLess(result['marks'][1],D('100000'))
        self.assertGreater(result['commission'],0)
        self.assertGreater(result['slippage'],0)
        self.assertEqual(result['marks'][-1]-no_cash['marks'][-1],
                         D('.1')*result['orders']['510300']['filled'])
        self.assertEqual(result['marks'][3]-no_cash['marks'][3],result['marks'][4]-no_cash['marks'][4])
        self.assertIsNone(five_day_label(raw,window,{'510300':'tradable'}))
        ex_day = five_day_label(raw,window,dict(admission,**{'510300':'known_ex_dividend_day'}))
        self.assertEqual(ex_day['orders']['510300']['reason'],'known_ex_dividend_day')
        blocked = five_day_label(raw,window,dict(admission,**{'510300':'blocked'}))
        self.assertEqual(blocked['orders']['510300']['reason'],'opening_blocked')
        self.assertIsNone(five_day_label(Dataset(dates[:-1],bars,(),{}),window,admission))

    def test_expanding_fold_purges_crossing_labels_and_reused_policy(self):
        dates = calendar(START,date(2027,12,30))
        rows = []
        for window in windows(dates):
            values = {name:cell(window,(window.anchor.day%7)/100) for name in VARIANTS['combined']}
            entries = ['repeated'] if window.entry in (date(2027,1,12),date(2027,4,12)) else []
            rows.append(dict(window=window,cells=values,eventIds=entries,label=label(),
                             inputsSealedAt=window.cutoff.isoformat(),
                             labelReadyAt=label_floor(window).isoformat()))
        a,b = holdouts(START)[0]
        report = paired_predictions(rows,'policy',STARTED_AT,0)
        self.assertEqual(report['status'],'fitted')
        self.assertTrue(all(a<=p['window'].entry<=p['window'].last<b for p in report['predictions']))
        ids = {p['window'].entry for p in report['predictions']}
        self.assertNotIn(date(2027,4,12),ids)
        self.assertNotIn(date(2027,7,2),ids)
        self.assertEqual(report['trainingDays'],sum(row['window'].last<a for row in rows))
        late = rows[5]
        late['labelReadyAt']=datetime.combine(a,time(12),TZ).isoformat()
        self.assertEqual(paired_predictions(rows,'policy',STARTED_AT,0)['trainingDays'],
                         report['trainingDays']-1)
        late['labelReadyAt'] = label_floor(late['window']).isoformat()
        late['inputsSealedAt'] = (late['window'].cutoff+timedelta(minutes=1)).isoformat()
        self.assertEqual(paired_predictions(rows,'policy',STARTED_AT,0)['trainingDays'],
                         report['trainingDays']-1)
        picked = list(nonoverlap(p['window'] for p in report['predictions']))
        self.assertTrue(all(left.last<right.entry for left,right in zip(picked,picked[1:])))

    def test_confirmatory_gates_and_paired_block_intervals(self):
        dates = calendar(START,date(2028,1,10))
        folds = holdouts(START)
        fold_calendars = {a:tuple(d for d in dates if a<=d<b) for a,b in folds}
        predictions, labels = [], {}
        for window in windows(dates):
            for a,b in folds:
                if a<=window.entry<=window.last<b:
                    predictions.append(dict(fold=a,window=window,eventIds=(str(window.entry),),
                        baseline=[.1,.03],expanded=[0.,0.],inputsSealedAt=window.cutoff.isoformat(),
                        forecastSealedAt=window.cutoff.isoformat()))
                    labels[window.entry] = dict(readyAt=label_floor(window).isoformat(),value=label())
        reported = datetime(2028,1,5,17,tzinfo=TZ)
        def score(rows, at=reported):
            return paired_report(rows,labels,fold_calendars,started_at=STARTED_AT,
                                 observed=at,variant='combined')
        final = score(predictions)
        self.assertEqual(final['status'],'improved')
        self.assertEqual(final['quarters'],3)
        self.assertAlmostEqual(final['pairedImprovementInterval'][0][0],.1)
        self.assertEqual(final,score(predictions))
        self.assertEqual(score(predictions[:119])['status'],'insufficient_samples')
        labels[predictions[0]['window'].entry]['readyAt'] = None
        self.assertEqual(score(predictions[:120])['completedPairs'],119)
        self.assertEqual(score([dict(row,eventIds=('one',)) for row in predictions])['status'],
                         'insufficient_samples')
        self.assertEqual(score([dict(row,forecastSealedAt=None) for row in predictions])['completedPairs'],0)
        self.assertEqual(score(predictions,datetime(2027,12,20,17,tzinfo=TZ))['status'],'observation_in_progress')
