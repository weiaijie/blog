from datetime import date, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.policy_events import instant
from etf_research.publication import create, read, sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_forecast_status import forecast_row, forecast_counts
import observation_status
import seal_observation_decision as decision
import seal_observation_forecasts as forecast
import train_observation_models as trainer
from observation_labels import label_window
from test_train_observation_models import FIT_TIME, ORIGIN, fixture_cohort

DAY=date(2026,11,2)


def env_for(unit,invocation,stamp):
    return dict(TRIGGER_UNIT=unit,INVOCATION_ID=invocation,
                TRIGGER_TIMER_REALTIME_USEC=str(int(stamp.timestamp()*1_000_000)))


def source_clock(trigger, start, calendar):
    return dict(trigger,managerTimer=dict(lastTriggerUsec=int(start.timestamp()*1_000_000),
                                          calendar=[f'*-*-* {calendar} Asia/Shanghai']),
                managerTimerCheckedAt=start.isoformat(),managerTimerError=None)


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
                  patch.object(decision,'with_manager_clock',side_effect=lambda trigger:source_clock(trigger,before,'08:52:00')),
                  patch('etf_research.evidence_archive.datetime') as archive,
                  patch.dict(decision.os.environ,env_for(decision.TIMER,'c'*32,before-timedelta(days=1)),clear=True)):
                archive.now.return_value=before
                verified=decision.run(root,root,store)
            self.assertEqual(verified['status'],'eligible_inputs')

            at=instant('2026-11-02T08:53:03+08:00')
            with (patch.object(forecast,'now',return_value=at),patch.object(forecast,'CODE',()),
                  patch.object(trainer,'first_archive',return_value=ORIGIN),
                  patch.object(forecast,'with_manager_clock',side_effect=lambda trigger:source_clock(trigger,at,'08:53:00')),
                  patch('etf_research.evidence_archive.datetime') as archive,
                  patch.dict(forecast.os.environ,env_for(forecast.TIMER,'d'*32,at-timedelta(days=1)),clear=True)):
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

            create(root/'config/research_observation.json',{'observationEarliestDate':'2026-08-01'})
            (root/'reports/research-observation').mkdir(parents=True)
            observed=instant('2026-11-02T09:05:00+08:00')
            with (patch.object(observation_status,'FIRST_DECISION',DAY),
                  patch.object(observation_status,'first_archive',return_value=ORIGIN),
                  patch.object(trainer,'first_archive',return_value=ORIGIN)):
                overview=observation_status.report(root,store,observed=observed)
                detail=observation_status.report(root,store,day=str(DAY),observed=observed)['session']
                self.assertEqual(overview['forecastCounts']['due'],1)
                self.assertEqual(overview['forecastCounts']['sealedPairs'],dict(policy=0,etf=1,margin=0,combined=0))
                self.assertEqual(detail['modelProgress']['comparisons']['etf']['trainingDays'],42)
                self.assertEqual(detail['forecast']['readyAt'],at.isoformat())
                self.assertEqual(detail['forecast']['attempts'][0]['comparisons']['etf'],saved['comparisons']['etf'])
                model=root/saved['model']['path']/'records/training.json'
                model.write_bytes(b'{}')
                damaged=observation_status.report(root,store,observed=observed)
                self.assertEqual(damaged['modelProgress']['status'],'model_unverified')
                self.assertEqual(damaged['forecastCounts']['sealedDays'],0)
                self.assertEqual(damaged['sessions'][0]['forecast']['status'],'unverified')

    def test_late_scores_are_hidden_and_do_not_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root,store=Path(directory)/'research',Path(directory)/'archive'
            calendar=root/trainer.CALENDAR
            calendar.parent.mkdir(parents=True)
            shutil.copyfile(ROOT/trainer.CALENDAR,calendar)
            cutoff=forecast.deadline(DAY)
            start=cutoff-timedelta(minutes=1)
            ready=cutoff+timedelta(seconds=1)
            packet=dict(entryDay=str(DAY),startedAt=start.isoformat(),computedAt=cutoff.isoformat(),
                studyOrigin=ORIGIN,fold=dict(start='2026-11-01',end='2027-02-01'),
                trigger=forecast.trigger_from(env_for(forecast.TIMER,'1'*32,start)),sessions=[],
                model=None,decision=None,reason=None,
                comparisons=dict(etf=dict(status='predicted',baseline=[0.01,0.02],expanded=[0.02,0.01])))
            with (patch.object(forecast,'now',return_value=ready),patch.object(forecast,'CODE',()),
                  patch('etf_research.evidence_archive.datetime') as archive):
                archive.now.return_value=ready
                forecast.archive_forecast(root,store,packet)
            decision_row=dict(status='pending',scheduledAt=start.isoformat(),latest=None)
            view=forecast_row(root,store,DAY,ready,ORIGIN,decision_row,details=True)
            self.assertEqual(view['status'],'missed_deadline')
            self.assertNotIn('baseline',view['latest']['comparisons']['etf'])
            self.assertEqual(forecast_counts([view],ready)['gaps'],1)

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
