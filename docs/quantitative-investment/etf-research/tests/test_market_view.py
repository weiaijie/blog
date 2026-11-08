import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from serve_market import payload


class MarketViewTests(unittest.TestCase):
    def test_archived_view_matches_published_account_and_market(self):
        folder=ROOT/'reports/daily/20261107T135033-e268ce3b'
        pointer=json.loads((folder/'ready.json').read_bytes())['pointer']
        pointer['bundle_manifest_sha256']=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest()
        result=payload(json.dumps(pointer).encode())
        self.assertEqual(result,(ROOT/'site/market-data.json').read_bytes())
        view=json.loads(result)
        self.assertEqual(view['curve'],[['2026-11-05',100000],['2026-11-06',100067.48]])
        self.assertEqual(view['nextSession'],'2026-11-09')
        self.assertEqual(set(view['candles']),{'510300','511010','513500','159920'})
        for symbol,bars in view['candles'].items():
            self.assertEqual([row[0] for row in bars],sorted({row[0] for row in bars}))
            self.assertEqual(bars[-1][0], '2026-10-30' if symbol in ('513500','159920') else view['asOf'])
            self.assertTrue(all(low<=min(op,cl)<=max(op,cl)<=high for _,op,high,low,cl in bars))

    def test_unbound_pointer_rejected(self):
        pointer=json.loads((ROOT/'config/active_run.json').read_bytes())
        pointer['checkpoint_sha256']='0'*64
        with self.assertRaises(ValueError):
            payload(json.dumps(pointer).encode())
