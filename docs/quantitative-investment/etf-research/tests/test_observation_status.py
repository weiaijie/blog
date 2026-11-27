from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_status import report
from etf_research.evidence_archive import object_path
from etf_research.publication import read
from pack_observation_evidence import restore_ledger

PROOF = ROOT/'reports/2026-11-27-observation-launch'
OBSERVED = datetime.fromisoformat('2026-11-27T17:10:00+08:00')


class ObservationStatusTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = Path(folder.name)
        (self.store/'snapshots').mkdir()
        for manifest in PROOF.glob('archive-*.json'):
            (self.store/'snapshots'/manifest.name.removeprefix('archive-')).write_bytes(manifest.read_bytes())

    def test_live_shape_compares_attempts_and_excludes_manual_complete(self):
        status = report(ROOT,self.store,observed=OBSERVED)
        self.assertEqual(status['counts'],dict(expected=1,archived=1,qualified=0,missing=0))
        self.assertIsNone(status['firstQualifiedArchive'])
        self.assertEqual([day['day'] for day in status['sessions']],['2026-11-27','2026-11-26'])
        detail = report(ROOT,self.store,day='2026-11-27',observed=OBSERVED)['session']
        self.assertEqual(detail['archivedAttempts'],2)
        self.assertEqual(detail['status'],'partial')
        self.assertTrue(all(row['scheduled'] for row in detail['attempts']))
        fields = detail['latest']['sources']
        self.assertEqual(fields['market']['turnover']['cny'],'930379000000.00')
        self.assertEqual(fields['market']['margin']['status'],'unknown')
        self.assertIsNone(fields['etf']['511010']['featureReadyAt'])

    def test_source_gaps_are_classified_from_archived_objects(self):
        day = '2026-11-27'
        head = '20261127T115450Z-c4c154d1'
        ledger = ROOT/'reports/research-observation'
        identity = read(ledger/'archives'/day/(head+'.json'))['archive']
        proof = ROOT/'reports/2026-11-27-policy-runtime/archive-proofs/snapshots'/(identity+'.json')
        snapshot = self.store/'snapshots'/(identity+'.json')
        snapshot.write_bytes(proof.read_bytes())
        prefix = f'reports/research-observation/runs/{day}/{head}/inputs/'
        for name,entry in read(snapshot)['files'].items():
            if name.startswith(prefix):
                obj = object_path(self.store,entry['sha256'])
                obj.parent.mkdir(parents=True,exist_ok=True)
                obj.write_bytes((ROOT/name).read_bytes())
        def evidence():
            row = report(ROOT,self.store,day=day,observed=datetime.fromisoformat(day+'T20:00:00+08:00'))['session']
            self.assertEqual(row['status'],'partial')
            self.assertEqual(row['latestSourceEvidence']['archiveSha256'],identity)
            return {e['request']:e for e in row['latestSourceEvidence']['requests']}

        rows = evidence()
        self.assertEqual(rows['shares_20261127']['state'],'empty_response')
        self.assertEqual(rows['shares_20261127']['httpStatus'],200)
        self.assertEqual(rows['nav_510300']['returnedDates'],['2026-11-26',day])
        self.assertEqual(rows['nav_511010_20261130']['httpStatus'],404)
        self.assertEqual(rows['nav_511010_20261130']['state'],'response_unavailable')
        self.assertEqual(rows['nav_511010_20261130']['expectedDates'],[day])
        self.assertEqual(rows['margin']['state'],'date_mismatch')
        self.assertEqual(rows['margin']['returnedDates'],['2026-11-26'])
        self.assertEqual(rows['detail_20261127_1']['rowCount'],0)
        self.assertEqual(rows['detail_20261127_2']['rowCount'],0)
        object_path(self.store,rows['margin']['sha256']).write_bytes(b'bad hash')
        self.assertEqual(evidence()['margin']['state'],'unverified')

    def test_as_of_distinguishes_future_running_and_archived_attempts(self):
        pack=ROOT/'reports/2026-11-27-portable-observation/pack'
        day='2026-11-27'
        latest='20261127T115450Z-c4c154d1'
        ledger=self.store/'restored'
        restore_ledger(pack,ledger)
        folder=ledger/'reports/research-observation/runs'/day/latest
        started=datetime.fromisoformat(read(folder/'started.json')['startedAt'])
        archive=read(ledger/'reports/research-observation/archives'/day/(latest+'.json'))
        ready=datetime.fromisoformat(archive['archiveVerifiedAt'])
        before=report(ledger,pack/'archive',day=day,observed=started-timedelta(seconds=1))['session']
        self.assertEqual(before['latest']['id'],'20261127T114000Z-18f4f01f')
        self.assertEqual(before['archivedAttempts'],8)
        self.assertEqual(before['issues'],[])
        running=report(ledger,pack/'archive',day=day,observed=started)['session']
        self.assertEqual(running['issues'],[dict(id=latest,status='pending_archive')])
        self.assertEqual(running['latestSourceEvidence']['archiveSha256'],before['latest']['archiveSha256'])
        verified=report(ledger,pack/'archive',day=day,observed=ready)['session']
        self.assertEqual(verified['archivedAttempts'],9)
        self.assertEqual(verified['latest']['id'],latest)
        self.assertEqual(verified['latestSourceEvidence']['archiveSha256'],archive['archive'])
        self.assertEqual(verified['issues'],[])

    def test_missing_record_separate_from_unverified_archive(self):
        path = ROOT/'reports/research-observation/archives/2026-11-27'
        for receipt in path.glob('*.json'):
            identity = read(receipt)['archive']
            (self.store/'snapshots'/(identity+'.json')).write_text('bad digest',encoding='utf-8')
        detail = report(ROOT,self.store,day='2026-11-27',observed=OBSERVED)['session']
        self.assertEqual(detail['status'],'unverified')
        self.assertEqual(detail['attempts'],[])
        missing = report(ROOT,self.store,day='2026-11-30',
                        observed=datetime.fromisoformat('2026-11-30T18:00:00+08:00'))['session']
        self.assertEqual(missing['status'],'missing')

    def test_qualification_uses_first_archive_completion(self):
        stamp = '2026-12-01T02:30:00+00:00'
        rec = dict(id='first',forwardEligible=True,session='2026-11-27',
                   archiveVerifiedAt=stamp,archive='a'*64,phase='complete',
                   trigger=None,attempt='x/first',resultSha256='b'*64)
        body = dict(startedAt=stamp,finishedAt=stamp,coverage=None,errors={})
        with patch('observation_status.archive_index',return_value=({'2026-11-27':[(rec,body)]},{})):
            result = report(ROOT,self.store,observed=datetime.fromisoformat('2026-12-01T17:00:00+08:00'))
        self.assertEqual(result['counts']['qualified'],1)
        self.assertEqual(result['firstQualifiedArchive']['date'],'2026-12-01')
        self.assertEqual(result['firstQualifiedArchive']['midtermOn'],'2027-06-01')
        self.assertEqual(result['firstQualifiedArchive']['finalOn'],'2027-12-01')

    def test_unconfirmed_year_preserves_known_previous_days(self):
        observed = datetime.fromisoformat('2027-01-05T18:00:00+08:00')
        overview = report(ROOT,self.store,observed=observed)
        self.assertEqual(overview['calendarUnknownYear'],2027)
        self.assertTrue(overview['calendarThrough'].startswith('2026-12-'))
        self.assertEqual(report(ROOT,self.store,day='2027-01-05',observed=observed)['session']['status'],
                         'calendar_unknown')
