from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from etf_research.evidence_archive import capture
from etf_research.publication import create, read, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import collect_sse_research_day as collector
from collect_sse_research_day import previous_session, verify
from observation_status import latest_source_evidence


class CollectSseResearchDayTests(unittest.TestCase):
    def test_calendar_and_cutoff(self):
        friday = date(2026, 11, 27)
        with self.assertRaisesRegex(ValueError, 'not complete'):
            previous_session(friday, datetime.fromisoformat('2026-11-27T15:59:59+08:00'))
        self.assertEqual(previous_session(friday, datetime.fromisoformat('2026-11-27T08:00:00+00:00')),
                         date(2026, 11, 26))
        with self.assertRaisesRegex(ValueError, 'Not an exchange session'):
            previous_session(date(2026, 11, 28), datetime.fromisoformat('2026-11-28T17:00:00+08:00'))

    def test_complete_response_keeps_financing_residual(self):
        sample = verify(ROOT / 'data/snapshots/20261127T084226Z-10828286-sse-research-day')
        self.assertEqual(sample['status'], 'full_capture')
        self.assertEqual(sample['margin']['balanceIdentity']['residualCny'], '43')
        self.assertIsNone(sample['margin']['reconciledFinancingNetCny'])

    def test_missing_summary_preserves_turnover_and_unknown_margin(self):
        sample = verify(ROOT / 'data/snapshots/20261127T084227Z-669d6f01-sse-research-day')
        self.assertEqual(sample['status'], 'partial_capture')
        self.assertEqual(sample['turnoverCny'], '930379000000.00')
        self.assertIsNone(sample['margin'])
        self.assertIsNone(sample['publishedAt'])
        self.assertFalse(sample['historicalPointInTime'])


    def test_capture_and_replay_follow_reported_detail_pages(self):
        day = date(2026,11,26)
        key = '20261126'
        fixture = ROOT/'data/snapshots/20261127T084226Z-10828286-sse-research-day'
        detail = [read(fixture/f'detail_{key}_{i}.body') for i in (1,2)]
        base_rows = detail[0]['result'] + detail[1]['result']
        occupied = {row['stockCode'] for row in base_rows}
        extra = (dict(stockCode=f'{i:06d}',opDate=key,rzmre=0)
                 for i in range(3000) if f'{i:06d}' not in occupied)
        extended = [*base_rows,*(next(extra) for _ in range(3001-len(base_rows)))]
        summary = read(fixture/'margin.body')
        summary['pageHelp']['data'] = summary['result']

        def mock_fetch(rows, page_count, unavailable_page=None):
            def fetch(folder,name,url,policy):
                response_path = folder/(name+'.body')
                status = 200
                if name.startswith('detail_'):
                    n = int(parse_qs(urlsplit(url).query)['pageHelp.pageNo'][0])
                    if n == unavailable_page:
                        status = 503
                        response_path.write_bytes(b'Service unavailable')
                    else:
                        batch = rows[(n-1)*collector.PAGE_SIZE:n*collector.PAGE_SIZE]
                        create(response_path,dict(detail[0],result=batch,
                            pageHelp=dict(detail[0]['pageHelp'],data=batch,total=len(rows),pageNo=n,
                                          pageCount=page_count)))
                elif name == 'margin':
                    current = next(row for row in summary['result'] if row['opDate']==key)
                    current['rzmre'] = sum(row['rzmre'] for row in rows)
                    create(response_path,summary)
                else:
                    response_path.write_bytes((fixture/(name+'.body')).read_bytes())
                return dict(name=name,url=url,final_url=url,status=status,curl_exit=0,
                            requested_at_utc=read(folder/'run.json')['startedAt'],sha256=sha(response_path),
                            bytes=response_path.stat().st_size,metrics={'ssl_verify_result':0})
            return fetch

        cases = ((base_rows[:1000],1,None,'full_capture',1),
                 (extended,3,None,'full_capture',3),
                 (extended,3,3,'partial_capture',3),
                 (extended,collector.MAX_DETAIL_PAGES+1,None,'partial_capture',1))
        for rows,pages,failed,state,requested in cases:
            with self.subTest(pages=pages,failed=failed), TemporaryDirectory() as directory:
                root = Path(directory)/'ledger'
                attempt = f'reports/research-observation/runs/{day}/fixture'
                with patch.object(collector,'fetch',side_effect=mock_fetch(rows,pages,failed)):
                    folder,sample = collector.collect(day,root/attempt/'inputs')
                self.assertEqual(read(folder/'run.json')['schemaVersion'],2)
                self.assertEqual([row['name'] for row in read(folder/'requests.json')],
                                 ['margin',f'market_{key}',*(f'detail_{key}_{i}' for i in range(1,requested+1))])
                self.assertEqual(sample['status'],state)
                self.assertEqual(verify(folder),sample)
                store = Path(directory)/'archive'
                archived = capture(root,store,[p.relative_to(root).as_posix() for p in folder.iterdir()])
                evidence = latest_source_evidence(store,dict(archive=archived['snapshot'],attempt=attempt,
                                                            session=str(day)))
                records = [r for r in evidence['requests'] if r['source']=='margin_detail']
                self.assertEqual(len(records),requested)
                if failed:
                    self.assertEqual(records[failed-1]['state'],'response_unavailable')
                    self.assertIn(f'detail_{key}_{failed}',sample['issues'])
                    self.assertIsNone(sample['margin'])
                if pages>collector.MAX_DETAIL_PAGES:
                    self.assertIn('pagination',sample['issues']['margin'])
