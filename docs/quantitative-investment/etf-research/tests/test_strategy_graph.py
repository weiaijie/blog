"""Check the published human/agent graph against the strategy catalog and protocols."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_strategy_catalog import build


class StrategyGraphTests(unittest.TestCase):
    def test_published_index_and_evidence_links(self):
        catalog = json.loads((ROOT / 'site/strategy-catalog.json').read_bytes())
        self.assertEqual(build(), catalog)
        graph = catalog['graph']
        nodes = {n['id']: n for n in graph['nodes']}
        self.assertEqual(len(nodes), len(graph['nodes']))
        links = {(e['source'], e['target']): e['role'] for e in graph['edges']}
        self.assertEqual(len(links), len(graph['edges']))
        for source, target in links:
            self.assertIn((nodes[source]['kind'], nodes[target]['kind']),
                          [('factor', 'entry'), ('entry', 'experiment')])
        for entry in catalog['entries']:
            target = entry['id']
            self.assertEqual({nodes[end]['url'] for start, end in links if start == target},
                             {report['url'] for report in entry['reports']})
            model = entry['plan']['model']
            inputs = {start.removeprefix('factor:'): role for (start, end), role in links.items()
                      if end == target}
            if model.startswith('multifactor_'):
                expected = dict.fromkeys(('trend120', 'relative60', 'vol20'), '三票取二')
                parts = model.split('_')
                if len(parts) == 3:
                    expected[parts[1]] = '额外确认'
            else:
                expected = {'trend120': '月度择时'} if model == 'trend_120' else {}
            self.assertEqual(inputs, expected, target)
