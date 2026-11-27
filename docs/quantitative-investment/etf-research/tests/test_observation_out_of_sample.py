from datetime import date
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.evidence_archive import restore
from etf_research.observation_experiment import label_floor, nonoverlap
from etf_research.policy_events import instant
from etf_research.publication import read

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import observation_out_of_sample as evaluation
import seal_observation_evaluation as publisher

ORIGIN=dict(date='2025-10-09',archiveVerifiedAt='2025-10-09T19:40:03+08:00')
FINAL=instant('2026-10-10T20:45:00+08:00')


def economic_case(stock):
    return dict(terminalReturn='0.01' if stock else '0',maxDrawdown='0',
        marks=['100000']+['101000' if stock else '100000']*5,commission='5.01',slippage='3.12',
        endingCash='70.47' if stock else '480.00',availableCash='70.47' if stock else '480.00',
        dividendReceivable='0',orders={'510300' if stock else '511010':dict(
            requested=200,filled=200 if stock else 100,reason='filled' if stock else 'cash_limited')})


def observations(as_of):
    result={}
    for fold,phase in evaluation.calendar_plan(ROOT,date.fromisoformat(ORIGIN['date'])).items():
        for w in phase['windows']:
            if w.cutoff>as_of:
                continue
            rows={kind:dict(status='predicted',baseline=[0,0.10],expanded=[0.01,0.001],
                            eventIds=[str(w.entry)] if kind in ('policy','combined') else [])
                  for kind in evaluation.VARIANT_NAMES}
            phase_label='evidence_complete' if label_floor(w)<=as_of else 'holding_period_incomplete'
            label=dict(status=phase_label,readyAt=label_floor(w).isoformat(),
                  latest=dict(archiveSha256='3'*64,results={
                      name:{scenario:economic_case(name=='stock_bond_50_50')
                            for scenario in evaluation.SCENARIOS} for name in evaluation.ALLOCATION}))
            result[w.entry]=dict(window=w,fold=fold,decision=dict(latest=dict(archivedAt=w.cutoff.isoformat())),
                economic=w.entry in phase['economic'],
                forecast=dict(status='sealed_predictions',readyAt=w.cutoff.isoformat(),
                              sealedVariants=list(rows),latest=dict(comparisons=rows,archiveSha256='2'*64,
                                                                 modelArchiveSha256='1'*64)),label=label)
    return result


class ObservationEvaluationTests(unittest.TestCase):
    def test_nonoverlap_is_chosen_before_missing_predictions(self):
        data=observations(FINAL)
        selected=sorted(key for key,val in data.items() if val['economic'])
        first=selected[0]
        data[first]['forecast']=dict(status='missing',latest=None,sealedVariants=[])
        pairs,_,_=evaluation.comparison_rows(data,'combined')
        report=evaluation.economic_report(set(selected),pairs,data,publish=True)
        self.assertEqual(report['gaps'][str(first)],'paired_forecast_missing')
        self.assertEqual(report['matchedWindows'],len(selected)-1)
        self.assertEqual([row['entryDay'] for row in report['windows']],[str(day) for day in selected[1:]])
        example=report['windows'][0]
        self.assertEqual(example['choices']['baseline'],'bond_100')
        self.assertEqual(example['choices']['expanded'],'stock_bond_50_50')
        self.assertEqual(example['outcomes']['bond_only']['high']['unfilledOrders'],1)
        self.assertEqual(report['averages']['fixed_50_50']['low']['endingCash'],'70.47')
        phase=evaluation.calendar_plan(ROOT,date.fromisoformat(ORIGIN['date']))
        for row in phase.values():
            self.assertEqual(row['economic'],{w.entry for w in nonoverlap(row['windows'])})

    def test_midterm_has_coverage_only_and_final_respects_gates(self):
        review=instant('2026-04-09T20:45:00+08:00')
        with patch.object(evaluation,'first_archive',return_value=ORIGIN), patch.object(
                evaluation,'observed_days',return_value=observations(review)):
            midway=evaluation.evaluate(ROOT,ROOT,review)
        score=midway['comparisons']['combined']['score']
        self.assertEqual(score['status'],'observation_in_progress')
        self.assertGreater(score['completedPairs'],0)
        self.assertNotIn('baselineMae',score)
        self.assertNotIn('averages',midway['comparisons']['combined']['economics'])

        data=observations(FINAL)
        with patch.object(evaluation,'first_archive',return_value=ORIGIN), patch.object(
                evaluation,'observed_days',return_value=data):
            final=evaluation.evaluate(ROOT,ROOT,FINAL)
        outcome=final['comparisons']['combined']
        self.assertEqual(outcome['score']['status'],'improved')
        self.assertGreaterEqual(outcome['score']['completedPairs'],120)
        self.assertEqual(outcome['shortfall'],dict(pairs=0,folds=0,policyEvents=0))
        self.assertTrue(all(low>0 for low,_ in outcome['score']['pairedImprovementInterval']))
        self.assertEqual(final['comparisons']['etf']['score']['status'],'exploratory')

        limited={day:state for index,(day,state) in enumerate(data.items()) if index<25}
        with patch.object(evaluation,'first_archive',return_value=ORIGIN), patch.object(
                evaluation,'observed_days',return_value=limited):
            insufficient=evaluation.evaluate(ROOT,ROOT,FINAL)['comparisons']['combined']
        self.assertEqual(insufficient['score']['status'],'insufficient_samples')
        self.assertEqual(insufficient['shortfall']['pairs'],95)
        self.assertNotIn('baselineMae',insufficient['score'])

    def test_event_threshold_and_cash_verification_are_separate(self):
        data=observations(FINAL)
        for state in data.values():
            state['forecast']['latest']['comparisons']['combined']['eventIds']=[]
        for day,state in list(data.items())[:19]:
            state['forecast']['latest']['comparisons']['combined']['eventIds']=[str(day)]
        first=next(key for key,state in data.items() if state['economic'])
        cash=data[first]['label']['latest']['results']['bond_100']['high']
        cash['availableCash']='481'
        with (patch.object(evaluation,'first_archive',return_value=ORIGIN),
              patch.object(evaluation,'observed_days',return_value=data)):
            report=evaluation.evaluate(ROOT,ROOT,FINAL)
        group=report['comparisons']['combined']
        self.assertEqual(group['score']['status'],'insufficient_samples')
        self.assertEqual(group['shortfall'],dict(pairs=0,folds=0,policyEvents=1))
        self.assertEqual(group['economics']['gaps'][str(first)],'economic_outcome_unverified')
        self.assertEqual(report['comparisons']['etf']['score']['status'],'exploratory')

    def test_pending_label_and_policy_repeat_do_not_disappear(self):
        data=observations(FINAL)
        first=min(data)
        other=next(key for key,val in data.items() if val['fold']!=data[first]['fold'])
        data[other]['forecast']['latest']['comparisons']['combined']['eventIds']=[str(first)]
        data[first]['label']=dict(status='mature_unsealed',latest=None,readyAt=None)
        with patch.object(evaluation,'first_archive',return_value=ORIGIN), patch.object(
                evaluation,'observed_days',return_value=data):
            report=evaluation.evaluate(ROOT,ROOT,FINAL)
        combined=report['comparisons']['combined']
        self.assertEqual(combined['score']['status'],'final_labels_pending')
        self.assertEqual(report['status'],'final_labels_pending')
        self.assertTrue(any(row['entryDay']==str(other) and row['reason']=='policy_event_previously_seen'
                            for row in combined['coverage']))

    def test_live_no_origin_and_immutable_report_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            root,store=base/'observations',base/'archive'
            root.mkdir()
            with patch.object(evaluation,'first_archive',return_value=None):
                report=evaluation.evaluate(root,store,FINAL)
            self.assertEqual(report['status'],'observation_origin_pending')
            self.assertEqual(report['comparisons'],{})
            with (patch.object(publisher,'now',return_value=FINAL),patch.object(publisher,'CODE',()),
                  patch('etf_research.evidence_archive.datetime') as clock):
                clock.now.return_value=FINAL
                receipt=publisher.archive_evaluation(root,store,report,'a'*32)
            restored=base/'restored'
            restore(store,receipt['archiveSha256'],restored)
            shutil.copyfile(root/receipt['path']/'receipt.json',restored/receipt['path']/'receipt.json')
            self.assertEqual(publisher.verify_evaluation(restored,store,restored/receipt['path'],observed=FINAL),
                             (receipt,report))
            target=restored/receipt['path']/'records/evaluation.json'
            self.assertEqual(read(target)['report'],report)
            target.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'Bundle hash mismatch'):
                publisher.verify_evaluation(restored,store,restored/receipt['path'],observed=FINAL)
