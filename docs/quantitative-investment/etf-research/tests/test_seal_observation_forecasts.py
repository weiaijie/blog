from datetime import date, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.policy_events import instant
from etf_research.publication import read, sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import seal_observation_decision as decision
import seal_observation_forecasts as forecast
import train_observation_models as trainer
from observation_labels import label_window
from test_train_observation_models import FIT_TIME, ORIGIN, fixture_cohort

DAY=date(2026,11,2)


def env_for(unit,invocation,stamp):
    return dict(TRIGGER_UNIT=unit,INVOCATION_ID=invocation,
                TRIGGER_TIMER_REALTIME_USEC=str(int(stamp.timestamp()*1_000_000)))


class SealObservationForecastsTests(unittest.TestCase):
    def test_deadline_applies_to_archived_clock_and_not_only_calculation(self):
        begin=instant('2026-11-02T08:53:02+08:00')
        end=forecast.deadline(DAY)
        trigger=forecast.trigger_from(env_for(forecast.TIMER,'b'*32,begin))
        packet=dict(trigger=trigger,entryDay=str(DAY),startedAt=begin.isoformat(),
                    computedAt=(end-timedelta(seconds=5)).isoformat(),comparisons={'etf':{'status':'predicted'}})
        self.assertEqual(forecast.forecast_outcome(packet,end),'sealed_predictions')
        self.assertEqual(forecast.forecast_outcome(packet,end+timedelta(microseconds=1)),'missed_deadline')
        self.assertEqual(forecast.forecast_outcome(dict(packet,comparisons={}),end),'no_prediction')

    def test_full_timed_path_uses_frozen_inputs_and_reproduces_without_holdout_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root,store=Path(directory)/'research',Path(directory)/'archive'
            calendar=root/trainer.CALENDAR
            calendar.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/trainer.CALENDAR,calendar)
            with (patch.object(trainer,'now',return_value=FIT_TIME),patch.object(trainer,'CODE',()),
                  patch('etf_research.evidence_archive.datetime') as archive):
                archive.now.return_value=FIT_TIME
                trainer.archive_model(root,store,'a'*32,fixture_cohort())

            window=label_window(root,DAY)
            before=instant('2026-11-02T08:52:04+08:00')
            anchor=str(window.anchor)
            value=dict(value=0.01,verified=True,asOf=anchor,readyAt=before.isoformat(),
                       receivedAt=before.isoformat(),dependencyReadyAt=[before.isoformat()],
                       evidence=[dict(root='prices',path=trainer.CALENDAR,sha256=sha(calendar))])
            phases={name:value for name in decision.FEATURES}
            phases['policyActiveCount']=dict(value,value=1,eventIds=['event-0'])
            probe=dict(entryDay=str(DAY),anchorDay=anchor,computedAt=before.isoformat(),
                       evidenceCutoff=before.isoformat(),cells=phases,gaps={})
            with (patch.object(decision,'now',return_value=before),patch.object(decision,'CODE',()),
                  patch.object(decision,'first_archive',return_value=ORIGIN),
                  patch.object(decision,'assemble',return_value=probe),
                  patch('etf_research.evidence_archive.datetime') as archive,
                  patch.dict(decision.os.environ,env_for(decision.TIMER,'c'*32,before),clear=True)):
                archive.now.return_value=before
                verified=decision.run(root,root,store)
            self.assertEqual(verified['status'],'eligible_inputs')

            at=instant('2026-11-02T08:53:03+08:00')
            with (patch.object(forecast,'now',return_value=at),patch.object(forecast,'CODE',()),
                  patch.object(trainer,'first_archive',return_value=ORIGIN),
                  patch('etf_research.evidence_archive.datetime') as archive,
                  patch.dict(forecast.os.environ,env_for(forecast.TIMER,'d'*32,at),clear=True)):
                archive.now.return_value=at
                result=forecast.run(root,store)
            self.assertEqual(result['status'],'sealed_predictions')
            leaf=root/result['path']
            saved=read(leaf/'records/forecast.json')
            self.assertEqual(saved['comparisons']['etf']['status'],'predicted')
            self.assertEqual(saved['comparisons']['policy'],dict(status='policy_event_previously_seen',eventIds=['event-0']))
            self.assertEqual(saved['comparisons']['combined']['status'],'insufficient_training')
            self.assertEqual(forecast.reproduce_forecast(root,store,leaf),result)
            self.assertFalse((root/'reports/research-labels').exists())

    def test_prior_fold_events_are_variant_specific(self):
        cohort=trainer.fit_comparisons(fixture_cohort())
        window=label_window(ROOT,DAY)
        valid=dict(value=0.01,verified=True,asOf=str(window.anchor),
                   receivedAt=window.cutoff.isoformat(),readyAt=window.cutoff.isoformat())
        cells={name:valid for name in decision.FEATURES}
        cells['policyActiveCount']=dict(valid,value=1,eventIds=['new-but-seen-in-holdout'])
        prior={'policy':{'new-but-seen-in-holdout'}}
        output=forecast.forecast_comparisons(cohort,cells,window,window.cutoff,prior)
        self.assertEqual(output['policy']['status'],'policy_event_previously_seen')
        self.assertEqual(output['etf']['status'],'predicted')
