from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.admission import sessions_between
from etf_research.forward import START, digest
from etf_research.publication import atomic, read, seal
from forward_milestones import metric, prove_milestones, publication_report, report
from observation_price_inputs import admitted_operation, published_account_bundle

OBSERVED=datetime.fromisoformat('2026-11-27T21:20:00+08:00')
CHECKPOINT=ROOT/'reports/daily/20261127T170315-58f85234/forward_checkpoint.json'


class ForwardMilestonesTests(unittest.TestCase):
    def test_real_checkpoint_reconciles_all_accounts_and_excludes_anchor_interval(self):
        state=read(CHECKPOINT)
        result=report(ROOT,state,OBSERVED)
        self.assertEqual((result['valuationSessions'],result['returnIntervals']),(17,16))
        self.assertEqual(result['firstReturnSession'],'2026-11-06')
        self.assertEqual(len(result['progress']),18)
        row=result['progress']['monthly_50_50_base']
        self.assertEqual(Decimal(row['netPnlCny']),Decimal('475.28'))
        self.assertEqual(Decimal(row['commissionsCny']),Decimal('27.42'))
        self.assertEqual(Decimal(row['slippageCny']),Decimal('57.00'))
        self.assertAlmostEqual(row['netReturnVsBond'],row['netReturn']-result['progress']['bond_hold_base']['netReturn'])
        self.assertTrue(all(row['netAnnualized'] is None for row in result['progress'].values()))
        self.assertEqual([row['anniversary'] for row in result['milestones']],
                         ['2027-05-05','2027-11-05','2028-11-05'])
        self.assertTrue(all(row['accounts'] is None for row in result['milestones']))

    def test_checkpoints_before_cutoff_and_missing_calendar_row_rejected(self):
        state=read(CHECKPOINT)
        with self.assertRaisesRegex(ValueError,'Unverified frozen'):
            report(ROOT,state,datetime.fromisoformat('2026-11-27T15:59:00+08:00'))
        state['portfolios']['cash_base']['daily'].pop(1)
        state['checkpoint_sha256']=digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})
        with self.assertRaisesRegex(ValueError,'valuation or journal dates'):
            report(ROOT,state,OBSERVED)

    def test_anniversaries_use_next_admitted_session_and_only_full_years_annualize(self):
        # Unit-test series for calendar boundaries. Production reports use the real frozen ledger.
        state=read(CHECKPOINT)
        ranges={'2026': (), '2027': (('05-05','05-05'),), '2028': ()}
        end=date(2028,11,6)
        days=sessions_between(ranges,START,end)
        for portfolio in state['portfolios'].values():
            nav=[dict(date=day.isoformat(),equity='100000') for day in days]
            portfolio['daily']=nav
            portfolio['journal']=[]
            portfolio['summary'].update(ending_equity='100000',trades=0,commissions='0',sell_tax='0',
                                        slippage_cost='0',max_close_drawdown=0.0)
        state.update(as_of=end.isoformat(),forward_sessions=len(days))
        state['checkpoint_sha256']=digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})
        with patch('forward_milestones.calendar_at',return_value=SimpleNamespace(ranges=ranges,digest='test')):
            result=report(ROOT,state,datetime.fromisoformat('2028-11-06T17:00:00+08:00'))
        six,twelve,twenty_four=result['milestones']
        self.assertEqual(six['endSession'],'2027-05-06')
        self.assertEqual(twelve['endSession'],'2027-11-05')
        self.assertEqual(twenty_four['endSession'],'2028-11-06')
        self.assertIsNone(six['accounts']['cash_base']['netAnnualized'])
        self.assertEqual(twelve['accounts']['cash_base']['netAnnualized'],0.0)
        self.assertIs(twenty_four['accounts']['cash_base']['atLeast4Pct'],False)

    def test_timeline_uses_publication_time_instead_of_valuation_date(self):
        snapshots = (
            ('2026-11-26T22:00:00+08:00','2026-11-23'),
            ('2026-11-27T14:35:11.340388+08:00','2026-11-23'),
            ('2026-11-27T14:35:11.340389+08:00','2026-11-24'),
            ('2026-11-27T17:03:26.900449+08:00','2026-11-26'),
            ('2026-11-27T17:03:26.900450+08:00','2026-11-27'),
        )
        for clock,day in snapshots:
            with self.subTest(clock=clock):
                observed=datetime.fromisoformat(clock)
                version=publication_report(ROOT,observed)
                self.assertEqual(version['asOf'],day)
                self.assertLessEqual(datetime.fromisoformat(version['publication']['availableAt']),observed)
        exact=publication_report(ROOT,OBSERVED)
        self.assertEqual(exact['checkpointSha256'],read(CHECKPOINT)['checkpoint_sha256'])
        legacy=datetime.fromisoformat('2026-11-06T23:59:00+08:00')
        self.assertIsNone(publication_report(ROOT,legacy))

    def test_explicit_checkpoint_requires_actual_publication_and_untampered_receipt(self):
        state=read(CHECKPOINT)
        stamp=datetime.fromisoformat('2026-11-27T17:03:26.900450+08:00')
        self.assertIsNone(publication_report(ROOT,stamp-timedelta(microseconds=1),checkpoint=state))
        self.assertEqual(publication_report(ROOT,stamp,checkpoint=state)['checkpointSha256'],state['checkpoint_sha256'])
        state['forward_sessions']+=1
        with self.assertRaisesRegex(ValueError,'does not match the verified publication'):
            publication_report(ROOT,stamp,checkpoint=state)

        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            key='reports/operations/20261127T090314Z-5d902b22'
            target=shutil.copytree(ROOT/key,root/key)
            result=target/'result.json'
            result.write_bytes(result.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'Bundle hash mismatch'):
                publication_report(root,stamp)

    def test_recovery_and_costs_stop_at_end_of_requested_window(self):
        days=[date(2026,11,i) for i in (5,6,9,10,11)]
        portfolio={
            'summary':{'initial_cash':'100'},
            'daily':[dict(equity=str(value)) for value in (100,110,95,108,110)],
            'journal':[dict(kind='trade',day='2026-11-11',commission='1',tax='0.2',
                            raw_price='10',fill_price='10.1',units=3)],
        }
        unfinished=metric(portfolio,days[:-1])
        self.assertIsNone(unfinished['recovery']['recoveredOn'])
        self.assertEqual(unfinished['trades'],0)
        recovered=metric(portfolio,days)
        self.assertEqual(recovered['recovery']['recoveredOn'],'2026-11-11')
        self.assertEqual(recovered['recovery']['peakToRecoverySessions'],3)
        self.assertEqual(recovered['recovery']['troughToRecoverySessions'],2)
        self.assertEqual(Decimal(recovered['totalCostCny']),Decimal('1.5'))


    def test_milestone_uses_original_valuation_and_freezes_its_publication(self):
        day=date(2026,11,26)
        operation,folder=admitted_operation(ROOT,day,OBSERVED,require_account_binding=True,first=True)
        pointer,bundle,seen,_=published_account_bundle(ROOT,operation,OBSERVED)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            original_folder=shutil.copytree(folder,root/folder.relative_to(ROOT))
            retry=shutil.copytree(original_folder,original_folder.parent/'later-publish')
            relative=retry.relative_to(root).as_posix()
            atomic(retry/'started.json',dict(read(retry/'started.json'),operation=relative))
            atomic(retry/'result.json',dict(operation,operation=relative,
                                           finished_at_utc=(seen+timedelta(minutes=1)).isoformat()))
            (retry/'manifest.json').unlink()
            seal(retry)
            self.assertEqual(admitted_operation(root,day,OBSERVED)[1],retry)
            self.assertEqual(admitted_operation(root,day,OBSERVED,first=True)[1],original_folder)
        state=read(CHECKPOINT)
        original=read(bundle/'forward_checkpoint.json')
        with (patch('forward_milestones.WINDOWS',(6,)),
              patch('forward_milestones.anniversary',return_value=day)):
            early=publication_report(ROOT,seen-timedelta(microseconds=1))['milestones'][0]
            actual=publication_report(ROOT,OBSERVED)['milestones'][0]
            self.assertEqual(early['state'],'awaiting_valuation')
            self.assertIsNone(early['accounts'])
            self.assertEqual(actual['state'],'complete')
            self.assertEqual(actual['endSession'],str(day))
            self.assertEqual(actual['publication']['operation'],folder.relative_to(ROOT).as_posix())
            self.assertEqual(actual['publication']['checkpointSha256'],pointer['checkpoint_sha256'])
            old=report(ROOT,original,seen)
            self.assertEqual(actual['accounts'],old['milestones'][0]['accounts'])
            self.assertIsNone(actual['accounts']['monthly_50_50_base']['recovery']['recoveredOn'])
            self.assertEqual(report(ROOT,state,OBSERVED)['progress']['monthly_50_50_base']['recovery']['recoveredOn'],
                             '2026-11-27')

            with patch('forward_milestones.admitted_operation',return_value=None):
                missing=prove_milestones(ROOT,state,OBSERVED,report(ROOT,state,OBSERVED))['milestones'][0]
            self.assertEqual(missing['state'],'awaiting_publication')
            self.assertIsNone(missing['accounts'])

            raw=report(ROOT,state,OBSERVED)
            state['portfolios']['cash_base']['daily'][1]['equity']='100001'
            inconsistent=prove_milestones(ROOT,state,OBSERVED,raw)['milestones'][0]
            self.assertEqual(inconsistent['state'],'ledger_conflict')
            self.assertIsNone(inconsistent['accounts'])
