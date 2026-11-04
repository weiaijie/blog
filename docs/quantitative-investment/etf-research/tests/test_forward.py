"""Synthetic fixtures only: future dates here are unit tests, never market data."""
import unittest,copy
from datetime import date,datetime,timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal as D
from dataclasses import replace
from etf_research.data import Dataset,RawBar
from etf_research.accounting import Dividend
from etf_research.forward import advance,START,digest
from etf_research.baselines import run

def fixture():
 days=[];day=date(2026,4,1)
 while day<=date(2026,11,13):
  if day.weekday()<5:days.append(day)
  day+=timedelta(days=1)
 bars={s:{d:RawBar(d,p,p,p,p) for d in days} for s,p in [('510300',D(4)),('511010',D(140))]}
 event=Dividend('511010',date(2026,11,4),date(2026,11,6),date(2026,11,9),date(2026,11,10),D(1))
 return Dataset(tuple(days),bars,(event,),{'synthetic_unit_test':True})
def now(day,hour=16):return datetime(2026,11,day,hour,tzinfo=ZoneInfo('Asia/Shanghai'))
class ForwardTests(unittest.TestCase):
 def test_pending_contains_no_invented_return(self):
  c=advance(fixture(),now=now(4));self.assertEqual(c['forward_sessions'],0);self.assertEqual(c['portfolios'],{});self.assertEqual(c['status'],'pending_future_observations')
 def test_first_session_only_observes_and_warmup_never_trades(self):
  c=advance(fixture(),now=now(5))
  for r in c['portfolios'].values():self.assertEqual(len(r['daily']),1);self.assertEqual(r['summary']['trades'],0);self.assertEqual(D(r['summary']['ending_equity']),100000)
 def test_completion_gate_uses_shanghai_time(self):
  self.assertEqual(advance(fixture(),now=now(6,15))['as_of'],'2026-11-05')
  self.assertEqual(advance(fixture(),now=now(6))['as_of'],'2026-11-06')
  with self.assertRaises(ValueError):advance(fixture(),now=datetime(2026,11,6))
 def test_resume_across_ex_and_pay_matches_single_run(self):
  d=fixture();checkpoint=advance(d,now=now(9));r=advance(d,checkpoint,now=now(11));full=advance(d,now=now(11));self.assertEqual(r,full)
  bond=r['portfolios']['bond_hold_base'];paid=[x for x in bond['journal'] if x['kind']=='dividend_paid'];self.assertEqual(len(paid),1);self.assertGreater(D(paid[0]['amount']),0)
  self.assertTrue(all(t['day']>='2026-11-06' for t in bond['journal'] if t['kind']=='trade'))
 def test_same_input_retry_is_idempotent(self):
  d=fixture();a=advance(d,now=now(10));self.assertEqual(advance(d,a,now=now(10)),a)
 def test_prior_price_revision_and_rollback_rejected(self):
  d=fixture();c=advance(d,now=now(9));bars={s:dict(v) for s,v in d.bars.items()};day=d.sessions[1];bars['510300'][day]=replace(bars['510300'][day],close=D('4.001'))
  with self.assertRaisesRegex(ValueError,'revision'):advance(replace(d,bars=bars),c,now=now(10))
  with self.assertRaisesRegex(ValueError,'backward'):advance(d,c,now=now(6))
 def test_checkpoint_corruption_and_modified_history_rejected(self):
  d=fixture();c=advance(d,now=now(9));bad=copy.deepcopy(c);bad['as_of']='2026-11-10'
  with self.assertRaisesRegex(ValueError,'checksum'):advance(d,bad,now=now(11))
  bad=copy.deepcopy(c);bad['portfolios']['cash_base']['daily'][0]['cash']='1';bad['checkpoint_sha256']=digest({k:v for k,v in bad.items() if k!='checkpoint_sha256'})
  with self.assertRaisesRegex(ValueError,'history changed'):advance(d,bad,now=now(11))
 def test_trend_requires_past_warmup(self):
  d=fixture();short=replace(d,sessions=tuple(day for day in d.sessions if day>=date(2026,11,2)))
  with self.assertRaisesRegex(ValueError,'120 prior'):advance(short,now=now(6))
 def test_zero_start_has_no_pre_start_dividend_entitlement(self):
  d=fixture();e=Dividend('511010',date(2026,11,2),date(2026,11,4),date(2026,11,5),date(2026,11,6),D(1));r=run(replace(d,dividends=(e,)),'bond_hold','base',account_start=START)
  self.assertFalse(any(x['kind']=='dividend_paid' for x in r['journal']))
