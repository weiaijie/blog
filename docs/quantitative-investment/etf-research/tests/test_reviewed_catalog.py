"""Admission accepts only the two reviewed additions and retains the calendar gate."""
from pathlib import Path
import unittest
from unittest.mock import patch

from etf_research.admission import load_incremental
from etf_research.reviewed_catalog import (
    DECISION_FILE, REVIEWED_IDS, accepted_catalog_changes, reviewed_catalog_proof,
)
from etf_research.notice_workflow import review_queue

ROOT = Path(__file__).resolve().parents[1]


class ReviewedCatalogTests(unittest.TestCase):
    def test_exact_notice_fingerprints_require_sealed_full_text_proof(self):
        paths = reviewed_catalog_proof(ROOT)
        self.assertIn(ROOT / DECISION_FILE, paths)
        ids = sorted(REVIEWED_IDS)
        changes = [{'change_id': key} for key in [ids[0], 'f'*64, ids[1]]]
        self.assertEqual(accepted_catalog_changes(ROOT, changes), ids)
        with patch('etf_research.reviewed_catalog.DECISION_SHA256', '0'*64):
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                accepted_catalog_changes(ROOT, changes)
            self.assertEqual(accepted_catalog_changes(ROOT, [changes[1]]), [])

    def test_replay_uses_each_dated_announcement_and_retains_prior_snapshot(self):
        snapshots = ROOT / 'data/snapshots'
        for instant, count in [('20261124T171408-7f824d0c', 1), ('20261125T171409-c37ec299', 1),
                               ('20261126T171408-419cfdca', 2)]:
            data, audit = load_incremental(snapshots, instant + '-prices')
            self.assertEqual(data.sessions[-1].strftime('%Y%m%d'), instant[:8])
            self.assertEqual(audit['new_or_changed_notices'], count)
            self.assertTrue(set(audit['reviewed_notice_ids']).issubset(REVIEWED_IDS))
            self.assertFalse(audit['new_events_automatically_created'])
        _, old = load_incremental(snapshots, '20261123T171001-e77ea484-prices')
        self.assertEqual(old['new_or_changed_notices'], 0)
        self.assertNotIn('reviewed_notice_ids', old)

    def test_repeat_attempts_keep_evidence_but_no_longer_count_as_pending(self):
        self.assertTrue((ROOT / 'reports/daily/20261126T171408-419cfdca/notice_review/packet.json').is_file())
        self.assertFalse(any('20261124T' in row['packet_folder'] or '20261125T' in row['packet_folder']
                             or '20261126T' in row['packet_folder'] for row in review_queue(ROOT)))
