from datetime import date, datetime, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.admission import sessions_between
from etf_research.exchange_calendar import BASE_PATH
from etf_research.observation_decision_receipt import DECISIONS
from etf_research.observation_experiment import BASE, VARIANTS
from etf_research.policy_events import TZ, instant
from etf_research.publication import create, read
from etf_research.evidence_archive import restore

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import train_observation_models as trainer
from observation_labels import label_window

ORIGIN=dict(date='2026-08-01',archiveVerifiedAt='2026-08-01T19:40:40+08:00',
            receiptPath='reports/research-observation/archives/2026-07-31/test.json',
            receiptSha256='1'*64,archiveSha256='2'*64)
START,END=date(2026,11,1),date(2027,2,1)
CUTOFF=trainer.fold_cutoff(START)
FIT_TIME=instant('2026-11-01T07:45:00+08:00')


def fixture_cohort():
    ranges=read(ROOT/trainer.CALENDAR)['holiday_ranges']
    days=sessions_between(ranges,date(2026,8,1),date(2026,10,23))[:42]
    rows=[]
    for index,entry in enumerate(days):
        window=label_window(ROOT,entry)
        base=[0.001*(index+column) for column in range(len(BASE))]
        policy=base+[1.0]
        etf=base+[0.0005*index,0.002]
        margin=base+[0.05+0.0001*index]
        combined=base+[1.0,0.0005*index,0.002,0.05+0.0001*index]
        vectors=dict(baseline=base,policy=policy if index<40 else None,etf=etf,
                     margin=margin if index<39 else None,combined=combined if index<39 else None)
        stamp=datetime.combine(window.last,datetime.min.time(),TZ)+timedelta(hours=20)
        rows.append(dict(entryDay=str(entry),lastSession=str(window.last),vectors=vectors,
                         inputSealedAt=(window.cutoff-timedelta(seconds=30)).isoformat(),
                         labelReadyAt=stamp.isoformat(),targets=[0.001*index,0.05-0.0001*index],
                         eventIds=[f'event-{index}']))
    return dict(studyOrigin=ORIGIN,fold=dict(start=str(START),end=str(END)),
                trainingCutoff=CUTOFF.isoformat(),observedAt=FIT_TIME.isoformat(),rows=rows)


class TrainObservationModelsTests(unittest.TestCase):
    def test_shared_complete_rows_minimum_and_stable_model(self):
        cohort=fixture_cohort()
        fitted=trainer.fit_comparisons(cohort)
        self.assertEqual({name:row['trainingDays'] for name,row in fitted.items()},
                         dict(policy=40,etf=42,margin=39,combined=39))
        self.assertEqual(fitted['policy']['status'],'fitted')
        self.assertEqual(fitted['margin']['status'],'insufficient_training')
        self.assertNotIn('models',fitted['combined'])
        self.assertEqual(len(fitted['policy']['trainingEventIds']),40)
        self.assertEqual(fitted['etf']['trainingEventIds'],[])
        outlier=cohort['rows'][-1]
        outlier['targets']=[-0.70,0.40]
        changed=trainer.fit_comparisons(cohort)
        self.assertEqual(fitted['policy']['modelSha256'],changed['policy']['modelSha256'])
        self.assertNotEqual(fitted['etf']['modelSha256'],changed['etf']['modelSha256'])

    def test_same_clock_late_label_and_cross_fold_rows_cannot_fit(self):
        cohort=fixture_cohort()
        row=cohort['rows'][-1]
        row['labelReadyAt']=CUTOFF.isoformat()
        with self.assertRaisesRegex(ValueError,'late or cross-fold'):
            trainer.fit_comparisons(cohort)
        cohort=fixture_cohort()
        cohort['rows'][-1]['lastSession']=str(START)
        with self.assertRaisesRegex(ValueError,'late or cross-fold'):
            trainer.fit_comparisons(cohort)

    def test_calendar_purges_windows_before_consulting_archives(self):
        with patch.object(trainer,'admitted_row',return_value=(None,{'reason':'decision_missing'})) as admit:
            cohort=trainer.build_cohort(ROOT,ROOT,ORIGIN,START,END,FIT_TIME)
        self.assertEqual(cohort['rows'],[])
        self.assertEqual(cohort['expectedTradingDays'],len(cohort['exclusions']))
        self.assertEqual(cohort['exclusions']['2026-10-30']['reason'],'holding_window_crosses_fold')
        self.assertEqual(cohort['exclusions']['2026-10-26']['reason'],'decision_missing')
        self.assertNotIn(date(2026,10,30),[call.args[2] for call in admit.call_args_list])

    def test_late_recovery_preserves_only_exclusion_metadata(self):
        entry=date(2026,10,26)
        window=label_window(ROOT,entry)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            attempt=root/DECISIONS/str(entry)/('a'*32)
            create(attempt/'records/decision.json',dict(studyOrigin=ORIGIN))
            decision=dict(status='eligible_inputs',latest=dict(id='a'*32,archivedAt=window.cutoff.isoformat()))
            prior=dict(status='mature_unsealed')
            late=dict(status='evidence_complete',readyAt=CUTOFF.isoformat(),
                      latest=dict(archiveSha256='b'*64))
            with patch.object(trainer,'decision_row',return_value=decision), patch.object(
                    trainer,'label_row',side_effect=[prior,late]):
                row,excluded=trainer.admitted_row(root,root,entry,window,ORIGIN,CUTOFF,FIT_TIME)
            self.assertIsNone(row)
            self.assertEqual(excluded['reason'],'label_ready_after_fold_cutoff')
            self.assertEqual(excluded['labelArchiveSha256'],'b'*64)

    def test_content_archive_recovers_actual_seal_clock_and_refits(self):
        with tempfile.TemporaryDirectory() as folder:
            root,store=Path(folder)/'root',Path(folder)/'archive'
            root.mkdir()
            calendar=root/BASE_PATH
            calendar.parent.mkdir(parents=True)
            calendar.write_bytes((ROOT/BASE_PATH).read_bytes())
            with (patch.object(trainer,'now',return_value=FIT_TIME),patch.object(trainer,'CODE',()),
                  patch('etf_research.evidence_archive.datetime') as clock):
                clock.now.return_value=FIT_TIME
                artifact,saved=trainer.archive_model(root,store,'d'*32,fixture_cohort())
            restored=Path(folder)/'restored'
            restore(store,artifact['archiveSha256'],restored)
            shutil.copyfile(root/artifact['path']/'receipt.json',restored/artifact['path']/'receipt.json')
            self.assertEqual(trainer.verify_model(restored,store,restored/artifact['path'],observed=FIT_TIME),(artifact,saved))
            with self.assertRaisesRegex(ValueError,'verification failed'):
                trainer.verify_model(restored,store,restored/artifact['path'],observed=FIT_TIME-timedelta(microseconds=1))
            (restored/artifact['path']/'records/training.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'Bundle hash mismatch'):
                trainer.verify_model(restored,store,restored/artifact['path'],observed=FIT_TIME)
