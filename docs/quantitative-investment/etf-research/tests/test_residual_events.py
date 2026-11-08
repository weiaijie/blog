import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_residual_events import rank_and_link
from capture_residual_press import extract


class ResidualEventTests(unittest.TestCase):
    def test_combined_holiday_is_not_a_ranked_day(self):
        observations={d:dict(close=v,expost_nav='1',es_3m_close=price,es_3m_us=price)
                      for d,v,price in [('a','2','1'),('b','2',''),('c','1','1'),('d','3','1')]}
        rows=[dict(previous='a',date='b',units=2,es_3m_remaining=None),
              dict(previous='b',date='c',units=2,es_3m_remaining=None),
              dict(previous='c',date='d',units=2,es_3m_remaining=D(4))]
        blocks,summary=rank_and_link(rows,observations,'es_3m')
        self.assertEqual(blocks[0]['combined_cny'],-2)
        self.assertEqual(summary['net'],2)
        self.assertTrue(all(r.get('es_3m_loss_rank') is None for r in rows))
        rows[1]['units']=3
        self.assertIsNone(rank_and_link(rows,observations,'es_3m')[1]['net'])

    def test_copy_date_does_not_change_signed_date(self):
        raw=('<meta property="article:published_time" content="2025-02-21T02:46:20+08:00">'
             '博时标普500交易型开放式指数证券投资基金溢价风险提示公告 近期，513500交易价格偏离。'
             '博时基金管理有限公司2025年2月20日').encode()
        self.assertEqual(set(extract(raw,'copy')['signed_notices']),{'2025-02-20'})
