from datetime import date, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

import run_research_observation as observation
from observation_inputs import archive_for_day, assemble
from etf_research.observation_experiment import BASE, Window, availability
from etf_research.policy_events import instant
from etf_research.publication import create, read, seal, sha

PROOF = ROOT/'reports/2026-11-27-observation-inputs'
STORE = PROOF/'archive-proofs'


class ObservationInputTests(unittest.TestCase):
    def probe(self, name, store=STORE):
        file = PROOF/name
        saved = read(file)
        actual = assemble(ROOT,ROOT,store,date.fromisoformat(saved['entryDay']),
                          instant(saved['observedAt']),computed=instant(saved['computedAt']))
        return saved,actual

    def test_real_published_close_and_turnover_reconstruct_seven_inputs(self):
        saved,actual = self.probe('2026-11-30-probe.json')
        self.assertEqual(saved,actual)
        self.assertEqual(actual['anchorDay'],'2026-11-27')
        self.assertEqual(len(actual['lookbackSessions']),21)
        self.assertEqual({k for k,v in actual['cells'].items() if v is not None},set(BASE))
        self.assertAlmostEqual(actual['cells']['turnover20']['value'],1.2362978819615829)
        self.assertIsNone(actual['cells']['policyActiveCount'])
        self.assertEqual(actual['gaps']['policyActiveCount']['capturedCandidateCount'],10)
        self.assertFalse(actual['inputSealedForForecast'])
        self.assertGreater(instant(actual['computedAt']),instant(actual['observedAt']))
        self.assertEqual(actual['cells']['turnover20']['readyAt'],actual['computedAt'])
        window = Window(date(2026,11,27),(date(2026,11,30),*(date(2026,12,d) for d in range(1,5))))
        self.assertTrue(all(availability(actual['cells'][name],window) is not None for name in BASE))

    def test_late_handoff_stays_out_even_when_raw_numbers_exist(self):
        saved,actual = self.probe('2026-11-27-late-probe.json')
        self.assertEqual(saved,actual)
        self.assertEqual(actual['evidenceCutoff'],'2026-11-27T08:55:00+08:00')
        self.assertTrue(all(value is None for value in actual['cells'].values()))
        self.assertEqual(actual['gaps']['stockShareFlow'],'archive_not_ready')
        evening = instant('2026-11-27T17:41:00+08:00')
        row,error = archive_for_day(ROOT,STORE,date(2026,11,26),evening,
                                   read(ROOT/'config/research_observation.json'))
        self.assertIsNone(error)
        self.assertEqual(len(row['policyEtf']['etf']),2)
        self.assertTrue(all(f['relativeIntensity'] is not None for f in row['policyEtf']['etf']))
        self.assertIsNotNone(row['sse']['margin']['financingBuyShare'])

    def test_bad_archive_seal_leaves_affected_fields_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_store = Path(directory)
            (temp_store/'snapshots').mkdir()
            for manifest in (STORE/'snapshots').glob('*.json'):
                content = manifest.read_bytes()
                if manifest.name.startswith('edfe0c5'):
                    content += b'x'
                (temp_store/'snapshots'/manifest.name).write_bytes(content)
            _,actual = self.probe('2026-11-30-probe.json',temp_store)
        self.assertIsNotNone(actual['cells']['stockReturn5'])
        self.assertIsNone(actual['cells']['turnover20'])
        self.assertEqual(actual['gaps']['stockShareFlow'],'archive_proof_invalid')
        self.assertIsNone(actual['cells']['policyActiveCount'])


    def test_only_empty_failed_attempt_preserves_earlier_verified_inputs(self):
        day = date(2026,11,26)
        before = instant('2026-11-27T17:41:00+08:00')
        later = before+timedelta(minutes=1)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root,store = base/'observations',base/'archive'
            ledger = root/'reports/research-observation'
            origin = ROOT/'reports/research-observation'
            for branch in ('runs','archives'):
                shutil.copytree(origin/branch/str(day),ledger/branch/str(day))
            shutil.copytree(STORE/'snapshots',store/'snapshots')
            config = read(ROOT/'config/research_observation.json')
            create(root/'config/research_observation.json',config)

            def add_failure(key, ready, *, raw=False, phase='failed'):
                folder = ledger/'runs'/str(day)/key
                record = dict(schemaVersion=1,date=str(day),startedAt=(ready-timedelta(seconds=2)).isoformat(),
                              trigger=None)
                create(folder/'started.json',record)
                create(folder/'result.json',dict(record,phase=phase,errors={'collect':'interrupted'},
                                                 finishedAt=(ready-timedelta(seconds=1)).isoformat(),coverage=None))
                if raw:
                    (folder/'source.body').write_bytes(b'partial official response')
                seal(folder)

                def files(path):
                    return [child.relative_to(root).as_posix() for child in path.iterdir()]

                with (patch.multiple(observation,ROOT=root,LOG=ledger,required_files=files),
                      patch.object(observation,'now',return_value=ready),
                      patch('etf_research.evidence_archive.datetime') as archive_clock):
                    archive_clock.now.return_value = ready
                    receipt = observation.archive_run(folder,store,config)
                    return receipt,observation.receipt_path(folder),folder

            original, issue = archive_for_day(root,store,day,before,config)
            self.assertIsNone(issue)
            receipt,path,folder = add_failure('empty-retry',later,phase='interrupted')
            after, issue = archive_for_day(root,store,day,later,config)
            self.assertIsNone(issue)
            ignored = after.pop('ignoredEmptyAttempts')
            self.assertEqual(after,original)
            self.assertEqual(ignored,[dict(attempt=receipt['attempt'],phase='interrupted',
                                            archiveVerifiedAt=later.isoformat(),archiveSha256=receipt['archive'],
                                            receiptSha256=sha(path))])
            inputs = assemble(ROOT,root,store,date(2026,11,30),later,computed=later)
            self.assertEqual(inputs['ignoredEmptyAttempts'],{str(day):ignored})

            with_response = later+timedelta(minutes=1)
            add_failure('retry-with-response',with_response,raw=True)
            self.assertEqual(archive_for_day(root,store,day,with_response,config),(None,'attempt_not_verified'))
            (folder/'result.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Archive receipt does not match'):
                archive_for_day(root,store,day,later,config)
