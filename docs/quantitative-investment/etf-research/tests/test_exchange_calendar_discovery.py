from datetime import timedelta
import json
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from etf_research.exchange_calendar import calendar_at
from etf_research.policy_events import instant
from etf_research.publication import atomic, read, seal, sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import discover_exchange_calendar as discovery
from observation_calendar_status import calendar_report
from pack_observation_evidence import export, restore_receipt

BASE=ROOT/'data/snapshots'
CONFIRMED=BASE/'20261128T010713-exchange-calendar-discovery-2026'
WAITING=BASE/'20261128T010751-exchange-calendar-discovery-2027'


class ExchangeCalendarDiscoveryTests(unittest.TestCase):
    def test_real_annual_positive_control_and_empty_search_replay(self):
        known=discovery.verify(CONFIRMED)
        self.assertEqual(known['status'],'annual_pair_verified')
        self.assertEqual(known['year'],2026)
        self.assertEqual(known['annualManifestSha256'],sha(CONFIRMED/'annual/manifest.json'))
        self.assertTrue(known['sources']['szse']['candidates'][0]['url'].startswith('https://www.szse.cn/'))

        waiting=discovery.verify(WAITING)
        self.assertEqual(waiting['status'],'waiting_for_both_exchanges')
        self.assertEqual(waiting['year'],2027)
        self.assertIsNone(waiting['annualManifestSha256'])
        self.assertEqual([row['status'] for row in waiting['sources'].values()],['not_listed','not_listed'])
        data=json.loads((WAITING/'szse.body').read_bytes())
        self.assertEqual(data['currentPage'],0)
        self.assertEqual(data['data'],[])

    def test_conflicting_annual_titles_and_incomplete_search_fail_closed(self):
        now=instant('2026-11-28T03:00:00+08:00')
        body=json.loads((CONFIRMED/'szse.body').read_bytes())
        entry=body['data'][0]
        next_url=entry['docpuburl'].replace('_618087.html','_618088.html')
        body['data'].append(dict(entry,docpuburl=next_url))
        body['totalSize']=2
        hits=discovery.candidates('szse',json.dumps(body).encode(),2026,now)
        self.assertEqual(len(hits),2)
        body['currentPage']=0
        with self.assertRaisesRegex(ValueError,'incomplete'):
            discovery.candidates('szse',json.dumps(body).encode(),2026,now)

    def test_watch_archive_round_trips_through_existing_nightly_format(self):
        tick=instant('2026-11-28T08:05:00+08:00')
        trigger=dict(unit=discovery.TIMER,invocationId='a'*32,timerRealtimeUsec=None)
        with TemporaryDirectory() as directory:
            prefix=Path(directory)
            root,store=prefix/'research',prefix/'store'
            for name in discovery.BINDINGS:
                target=root/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,target)

            def capture(folder,year,*,trigger):
                self.assertEqual(year,2027)
                shutil.copytree(WAITING,folder)
                (folder/'manifest.json').unlink()
                started=read(folder/'started.json')
                atomic(folder/'started.json',dict(started,trigger=trigger))
                seal(folder)
                return discovery.verify(folder)

            with (patch.object(discovery,'collect',side_effect=capture),
                  patch.object(discovery,'now',return_value=tick),
                  patch('etf_research.evidence_archive.datetime') as clock):
                clock.now.return_value=tick
                result=discovery.watch(root,store,trigger,tick)
            receipt=result['receipt']
            self.assertEqual(receipt['trigger'],trigger)
            self.assertEqual(result['status'],'waiting_for_both_exchanges')
            self.assertNotIn('2027',calendar_at(root,tick).ranges)
            pack=prefix/'nightly'
            self.assertEqual(export(root,store,pack,tick+timedelta(seconds=1))['receipts'],{'calendar-watch':1})
            restored=prefix/'restored'
            restore_receipt(pack,receipt['path']+'/receipt.json',restored)
            self.assertEqual(read(restored/receipt['path']/'receipt.json'),receipt)
            self.assertEqual(discovery.verify(restored/receipt['path']/'records'),discovery.verify(WAITING))

            earliest=instant('2026-11-28T01:07:50+08:00')
            self.assertIsNone(calendar_report(ROOT,root,store,earliest,year=2027)['latestManual'])
            pending=calendar_report(ROOT,root,store,tick-timedelta(microseconds=1),year=2027)
            self.assertIsNone(pending['latestScheduled'])
            self.assertEqual(pending['latestManual']['status'],'waiting_for_both_exchanges')
            self.assertEqual(pending['scheduledIssues'][0]['state'],'pending_archive')
            visible=calendar_report(ROOT,restored,pack/'archive',tick,year=2027)
            self.assertEqual(visible['admissionState'],'awaiting_exchange_evidence')
            self.assertEqual(visible['verifiedScheduledChecks'],1)
            self.assertEqual(visible['latestScheduled']['archiveSha256'],receipt['archiveSha256'])

            path=restored/receipt['path']/'receipt.json'
            atomic(path,dict(receipt,trigger=dict(trigger,invocationId='b'*32)))
            damaged=calendar_report(ROOT,restored,pack/'archive',tick,year=2027)
            self.assertEqual(damaged['scheduledIssues'][0]['state'],'unverified')
            self.assertIsNone(damaged['latestScheduled'])
            self.assertIsNotNone(damaged['latestManual'])
