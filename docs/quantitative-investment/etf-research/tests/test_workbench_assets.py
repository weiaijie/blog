"""Built asset allowlist must not expose source, evidence, or arbitrary paths."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from serve_market import workbench_assets


class WorkbenchAssetTests(unittest.TestCase):
    def test_build_registers_entry_and_all_lazy_chunks_only(self):
        registered=workbench_assets(ROOT/'site')
        self.assertEqual(registered['/'],('workbench/index.html','text/html'))
        self.assertEqual(registered['/workbench/'],registered['/'])
        self.assertTrue(any('/Research-' in p for p in registered))
        self.assertFalse(any('manifest' in p or p.endswith('.ts') for p in registered))
        for name,_ in registered.values():self.assertTrue((ROOT/'site'/name).is_file())

    def test_traversal_and_unexpected_extensions_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp);folder=site/'workbench';(folder/'.vite').mkdir(parents=True)
            (folder/'index.html').write_text('test');(site/'private.json').write_text('{}')
            for name in ('../private.json','index.py'):
                (folder/'.vite/manifest.json').write_text(json.dumps({'src':{'file':name}}))
                with self.assertRaises((ValueError,OSError)):workbench_assets(site)

    def test_missing_chunk_does_not_get_registered(self):
        with tempfile.TemporaryDirectory() as tmp:
            site=Path(tmp);folder=site/'workbench';(folder/'.vite').mkdir(parents=True)
            (folder/'index.html').write_text('test')
            (folder/'.vite/manifest.json').write_text(json.dumps({'src':{'file':'missing.js'}}))
            with self.assertRaises(ValueError):workbench_assets(site)
