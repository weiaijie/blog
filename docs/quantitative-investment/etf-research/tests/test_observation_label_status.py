from datetime import date
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.observation_decision_receipt import DECISIONS
from etf_research.policy_events import instant

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_label_status import label_counts, label_row
from observation_labels import CALENDAR, label_window
import seal_observation_labels as sealer

DAY=date(2026,11,30)
DUE='2026-12-04T16:00:00+08:00'


class LabelCoverageTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)/'observations'
        self.store=Path(directory.name)/'archive'
        path=self.root/CALENDAR
        path.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/CALENDAR,path)
        self.decision=dict(status='eligible_inputs',latest=dict(id='a'*32,archiveSha256='b'*64,receiptSha256='c'*64))

    def build(self, stamp, attempt, *, complete, binding=None):
        source=self.decision['latest']
        window=label_window(self.root,DAY)
        payload=dict(
            mode='scheduled_candidate',entryDay=str(DAY),status='evidence_complete' if complete else 'evidence_missing',
            notBefore=DUE,observedAt=stamp,anchorDay=str(window.anchor),lastSession=str(window.last),
            sessions=[str(day) for day in window.sessions],
            decision=binding or dict(path=f'{DECISIONS}/{DAY}/{source["id"]}',archiveSha256=source['archiveSha256'],
                                     receiptSha256=source['receiptSha256']),
            opening={'510300':'tradable'} if complete else {},
            labels={'stock_bond_50_50':{'base':{'terminalReturn':'0.01','maxDrawdown':'0.02'}}} if complete else None,
            gaps={} if complete else {'510300':'opening_evidence_missing'})
        clock=instant(stamp)
        with (patch.object(sealer,'now',return_value=clock),patch.object(sealer,'BINDINGS',()),
              patch('etf_research.evidence_archive.datetime') as archived):
            archived.now.return_value=clock
            return sealer.archive_label(self.root,self.store,attempt,payload)

    def row(self, observed, details=True):
        return label_row(self.root,self.store,DAY,instant(observed),self.decision,details=details)

    def test_holding_due_and_missing_evidence_are_separate(self):
        before='2026-12-04T15:59:59+08:00'
        holding=self.row(before)
        self.assertEqual(holding['status'],'holding_period_incomplete')
        self.assertEqual(label_counts([holding],instant(before)),dict(due=0,ready=0,gaps=0,holding=1,unknownCalendar=0))
        self.assertEqual(self.row(DUE)['status'],'mature_unsealed')
        self.build('2026-12-04T20:15:00+08:00','2'*32,complete=False)
        missing=self.row('2026-12-04T20:16:00+08:00')
        self.assertEqual(missing['latest']['gaps'],{'510300':'opening_evidence_missing'})
        self.assertIsNone(missing['readyAt'])

    def test_earliest_sealed_result_is_preserved_and_future_archive_is_excluded(self):
        later='2026-12-07T20:15:00+08:00'
        early='2026-12-04T20:15:00+08:00'
        self.build(later,'1'*32,complete=True)
        valid=self.build(early,'2'*32,complete=True)
        before='2026-12-04T20:14:59+08:00'
        self.assertEqual(self.row(before)['status'],'mature_unsealed')
        now='2026-12-08T09:00:00+08:00'
        full=self.row(now)
        brief=self.row(now,details=False)
        self.assertEqual(full['readyAt'],early)
        self.assertEqual(full['latest']['archiveSha256'],valid['archiveSha256'])
        self.assertEqual(full['latest']['results']['stock_bond_50_50']['base']['terminalReturn'],'0.01')
        self.assertNotIn('results',brief['latest'])
        self.assertEqual(label_counts([brief],instant(now))['ready'],1)
        self.decision['latest']['receiptSha256']='d'*64
        rejected=self.row(now)
        self.assertEqual(rejected['status'],'unverified')
        self.assertIsNone(rejected['readyAt'])
