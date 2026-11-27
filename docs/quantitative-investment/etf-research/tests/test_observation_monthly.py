from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_monthly import LOG, month_report
from seal_observation_monthly import CODE, archive_month, month_view, run, verify_month
from pack_observation_evidence import export, merge_packs, restore_ledger, restore_receipt, verify
from run_observation_export import TIMER as EXPORT_TIMER, seal_export
from etf_research.evidence_archive import capture, restore
from etf_research.publication import create, read, seal, sha

A = '2026-11-27'
B = '2026-11-30'
OBSERVED = datetime.fromisoformat('2026-12-01T21:05:00+08:00')


class ObservationMonthlyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base/'root'
        self.store = self.base/'store'
        for name in CODE:
            target = self.root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
        self.log = self.root/'reports/research-observation'
        self.log.mkdir(parents=True)
        (self.store/'snapshots').mkdir(parents=True)
        self.index = 0

    def capture_at(self, names, when):
        with patch('etf_research.evidence_archive.datetime') as clock:
            clock.now.return_value = datetime.fromisoformat(when)
            return capture(self.root,self.store,names=names)['snapshot']

    def attempt(self, day, when, available, *, scheduled=True):
        self.index += 1
        token = f'{self.index:032x}'
        folder = self.log/'runs'/day/token
        folder.mkdir(parents=True)
        receipt_folder = self.log/'archives'/day
        receipt_folder.mkdir(parents=True,exist_ok=True)
        trigger = dict(unit='etf-research-observation.timer',invocationId=token) if scheduled else None
        complete = set(available)=={'policy','510300','511010','turnover','margin'}
        phase = 'complete' if complete else 'partial'
        started = dict(schemaVersion=1,date=day,startedAt=when,trigger=trigger)
        create(folder/'started.json',started)
        market = dict(turnoverCny='100.00' if 'turnover' in available else None,featureReadyAt=when,
                      margin=dict(balanceIdentity=dict(status='matched')) if 'margin' in available else None)
        policy = dict(status='archived' if 'policy' in available else 'coverage_incomplete',
                      candidateCount=1,signalEligibleCount=0)
        etf = {code:dict(status='verified_estimate' if code in available else 'unknown',
                         featureReadyAt=when if code in available else None) for code in ('510300','511010')}
        create(folder/'result.json',dict(**started,phase=phase,finishedAt=when,errors={},
                                       coverage=dict(policy=policy,etf=etf,market=market)))
        seal(folder)
        names = [path.relative_to(self.root).as_posix() for path in folder.iterdir()]
        identity = self.capture_at(names,when)
        create(receipt_folder/(token+'.json'),dict(schemaVersion=1,session=day,attempt=folder.relative_to(self.root).as_posix(),
                phase=phase,resultSha256=sha(folder/'result.json'),attemptManifestSha256=sha(folder/'manifest.json'),
                trigger=trigger,archive=identity,archiveCreatedAt=when,archiveVerifiedAt=when,
                files=len(names),forwardEligible=complete and scheduled))
        return identity

    def test_per_source_timeliness_and_consecutive_gaps(self):
        first = self.attempt(A,A+'T19:40:04+08:00',('policy','turnover'))
        late = self.attempt(A,B+'T09:03:00+08:00',('510300',))
        self.attempt(B,B+'T19:40:04+08:00',('policy','511010'))
        self.attempt(B,B+'T20:00:00+08:00',('policy','510300','511010','margin','turnover'),scheduled=False)
        detail = month_report(self.root,self.store,'2026-11',OBSERVED)
        self.assertEqual((detail['expected'],detail['archived'],detail['qualified']),(2,2,0))
        self.assertEqual(detail['qualificationGaps'],[dict(start=A,end=B,sessions=2)])
        self.assertEqual(detail['sealAfter'],'2026-12-01T08:55:00+08:00')
        self.assertEqual(detail['days'][0]['cutoffAt'], B+'T08:55:00+08:00')
        self.assertEqual(detail['days'][0]['sources']['policy']['archiveSha256'],first)
        self.assertEqual(detail['days'][0]['sources']['510300']['archiveSha256'],late)
        self.assertEqual(detail['sources']['510300']['late'],1)
        self.assertEqual(detail['sources']['margin']['gaps'],[dict(start=A,end=B,sessions=2)])
        self.assertEqual(len(detail['days'][1]['manualAttempts']),1)
        early = month_report(self.root,self.store,'2026-11',datetime.fromisoformat(B+'T08:55:00+08:00'))
        self.assertEqual((early['expected'],early['sources']['510300']['available']),(1,0))
        self.assertEqual(early['days'][0]['issues'],[])
        self.assertEqual(early['sealAfter'],'2026-12-01T08:55:00+08:00')

    def test_sealed_read_back_guards_old_clock_and_restores_evidence(self):
        self.attempt(A,A+'T19:40:04+08:00',('policy','turnover'))
        self.attempt(A,A+'T21:00:04+08:00',('margin',),scheduled=False)
        pending = self.log/'runs'/B/('b'*32)/'started.json'
        pending.parent.mkdir(parents=True)
        create(pending,dict(startedAt=B+'T19:40:00+08:00'))
        report = month_report(self.root,self.store,'2026-11',OBSERVED)
        with patch('seal_observation_monthly.now',return_value=OBSERVED), \
             patch('etf_research.evidence_archive.datetime') as archive_clock:
            archive_clock.now.return_value = OBSERVED
            sealed = archive_month(self.root,self.store,report,'a'*32)
        current = month_view(self.root,self.store,'2026-11',OBSERVED)
        self.assertEqual(current['archive']['archiveSha256'],sealed['archiveSha256'])
        self.assertEqual(current['report'],report)
        target = self.base/'restored-monthly'
        restore(self.store,sealed['archiveSha256'],target)
        folder = target/sealed['path']
        self.assertEqual(read(folder/'records/coverage.json')['report'],report)
        self.assertEqual(month_report(target,self.store,'2026-11',OBSERVED),report)
        records = self.root/sealed['path']/'records'/'coverage.json'
        records.write_text('{}',encoding='utf-8')
        self.assertEqual(month_view(self.root,self.store,'2026-11',OBSERVED)['archive']['state'],'unverified')

    def test_month_stays_unsealed_before_cutoff_and_when_calendar_is_unknown(self):
        before = datetime.fromisoformat('2026-12-01T08:54:59+08:00')
        self.assertEqual(month_report(self.root,self.store,'2026-11',before)['state'],'open')
        year_end = datetime.fromisoformat('2027-01-04T21:05:00+08:00')
        december = month_report(self.root,self.store,'2026-12',year_end)
        self.assertEqual((december['state'],december['calendarUnknownYear']),('calendar_unverified',2027))
        self.assertIsNone(december['sealAfter'])
        with patch.dict('os.environ',dict(TRIGGER_UNIT='manual-test',INVOCATION_ID='f'*32)):
            with self.assertRaisesRegex(ValueError,'requires its systemd timer'):
                run(self.root,self.store)
        self.assertFalse((self.root/LOG).exists())


    def test_monthly_seal_survives_scheduled_incremental_export_and_restore(self):
        self.attempt(A,A+'T19:40:04+08:00',('policy','turnover'))
        self.attempt(B,B+'T19:40:04+08:00',('policy','510300'))
        boundary = datetime.fromisoformat('2026-12-01T08:54:59+08:00')
        seed = self.base/'seed'
        seed_export = export(self.root,self.store,seed,boundary)
        self.assertEqual(seed_export['receipts'],{'observation':2})
        report = month_report(self.root,self.store,'2026-11',OBSERVED)
        with (patch('seal_observation_monthly.now',return_value=OBSERVED),
              patch('etf_research.evidence_archive.datetime') as clock):
            clock.now.return_value = OBSERVED
            receipt = archive_month(self.root,self.store,report,'a'*32)
        cutoff = OBSERVED+timedelta(hours=1,minutes=15)
        spool = self.base/'spool'
        trigger = dict(unit=EXPORT_TIMER,invocationId='c'*32,timerRealtimeUsec=None)
        with patch('run_observation_export.datetime') as clock:
            clock.now.return_value = cutoff
            batch = seal_export(self.root,self.store,seed,sha(seed/'manifest.json'),spool,cutoff,trigger)
        increment = spool/'batches'/batch['latest']['batchId']/'pack'
        self.assertEqual(verify(increment)['receipts'],{'monthly':1})
        self.assertEqual(verify(increment)['archives'],1)
        name = receipt['path']+'/receipt.json'
        self.assertEqual(read(increment/'index.json')['receipts'][0]['receipt'],name)

        standalone = self.base/'standalone-month'
        restore_receipt(increment,name,standalone)
        self.assertEqual(verify_month(standalone,increment/'archive',(standalone/name).parent,cutoff),
                         (receipt,report))
        self.assertTrue((standalone/'reports/research-observation/archives'/A/'00000000000000000000000000000001.json').is_file())

        merged,ledger = self.base/'merged',self.base/'restored-ledger'
        self.assertEqual(merge_packs([seed,increment],merged)['receipts'],{'monthly':1,'observation':2})
        restore_ledger(merged,ledger)
        self.assertEqual(month_view(ledger,merged/'archive','2026-11',cutoff),
                         month_view(self.root,self.store,'2026-11',cutoff))
        self.assertEqual(month_report(ledger,merged/'archive','2026-11',OBSERVED),report)
