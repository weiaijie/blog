from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from etf_research.policy_events import instant
from etf_research.exchange_calendar import BASE_PATH
from etf_research.publication import create, read, sha

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from observation_labels import assemble_label, check_opens, label_window, match_opening, serial_results
from observation_price_inputs import admitted_prices
import observe_opening_quotes as opening
import seal_observation_labels as sealer

DAY=date(2026,11,23)
PROOF=ROOT/'reports/2026-11-27-five-session-labels/label-validation.json'


class OpeningAndLabelTests(unittest.TestCase):
    def test_manager_slot_and_missed_opening_leave_verified_no_request_evidence(self):
        friday = date(2026,11,27)
        started = instant('2026-11-27T09:26:02+08:00')
        actual = started-timedelta(seconds=2)
        stale = actual-timedelta(days=1)
        environment = dict(TRIGGER_UNIT=opening.TIMER,INVOCATION_ID='f'*32,
                           TRIGGER_TIMER_REALTIME_USEC=str(int(stale.timestamp()*1_000_000)))
        identity = opening.trigger_event(environment)
        calendar = ['*-*-* 09:26:00 Asia/Shanghai','*-*-* 09:28:00 Asia/Shanghai']
        clock = dict(identity,managerTimer=dict(lastTriggerUsec=int(actual.timestamp()*1_000_000),calendar=calendar),
                     managerTimerCheckedAt=started.isoformat(),managerTimerError=None)
        self.assertFalse(opening.scheduled_opening(identity,started))
        self.assertTrue(opening.scheduled_opening(clock,started))
        self.assertFalse(opening.scheduled_opening(clock,actual+timedelta(minutes=1)))
        missing = dict(identity,realtimeUsec=int(actual.timestamp()*1_000_000),managerTimer=None,
                       managerTimerCheckedAt=started.isoformat(),managerTimerError='TimeoutExpired')
        self.assertFalse(opening.scheduled_opening(missing,started))

        with tempfile.TemporaryDirectory() as directory:
            root,store = Path(directory)/'project',Path(directory)/'store'
            for name in ('scripts/observe_opening_quotes.py',opening.CALENDAR,opening.LOADER,
                         'src/etf_research/observation_slots.py','config/collection.json'):
                local = root/name
                local.parent.mkdir(parents=True,exist_ok=True)
                local.write_bytes((ROOT/name).read_bytes())
            with (patch.dict(opening.os.environ,environment,clear=True),
                  patch.object(opening,'now',return_value=started),
                  patch.object(opening,'with_manager_clock',return_value=missing),
                  patch.object(opening,'fetch') as fetch,
                  patch('etf_research.evidence_archive.datetime') as archive_clock):
                archive_clock.now.return_value=started
                result = opening.collect(root,store,probe=False)
                self.assertEqual(result['status'],'missed_opening_slot')
                self.assertFalse(result['scheduled'])
                self.assertEqual(read(root/result['path']/'records/requests.json'),[])
                fetch.assert_not_called()
                quotes,evidence,issues = check_opens(root,store,friday,started)
                self.assertTrue(all(not rows for rows in quotes.values()))
                self.assertEqual(evidence[0]['archiveSha256'],result['archiveSha256'])
                self.assertEqual(len(issues),2)

    def test_open_is_supported_only_by_timed_auction_or_explicit_halt(self):
        day=date(2026,11,27)
        start=instant('2026-11-27T09:26:00+08:00')
        finish=instant('2026-11-27T09:26:08+08:00')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/'510300.body'
            source=opening.request_url('510300')
            meta=dict(url=source,final_url=source,status=200,curl_exit=0,
                      requested_at_utc=start.isoformat(),certificate_verification_enabled=True)
            quote=dict(code='510300',date=20261127,time=92600,
                       snap=['300ETF',4.021,4.035,4.035,4.035,4.035,4.425,3.619,'T110    ',''])
            def inspect(changes):
                path.write_text(opening.json.dumps(dict(quote,**changes)),encoding='utf-8')
                return opening.quote_state(root,dict(meta,sha256=sha(path)),'510300',day,start,finish)
            self.assertEqual(inspect({})['openingPrice'],'4.035')
            halted=quote['snap'][:]
            halted[8]='P010    '
            self.assertEqual(inspect({'snap':halted})['status'],'blocked')
            for change in ({'time':92459},{'time':93000},{'date':20261126},{'code':'511010'}):
                with self.assertRaisesRegex(ValueError,'outside opening'):
                    inspect(change)
            halt_flag=quote['snap'][:]
            halt_flag[9]='P'
            with self.assertRaisesRegex(ValueError,'completed auction'):
                inspect({'snap':halt_flag})

    def test_horizon_preserves_weekend_and_waits_for_last_close(self):
        window=label_window(ROOT,date(2026,11,26))
        self.assertEqual([str(day) for day in window.sessions],
                         ['2026-11-26','2026-11-27','2026-11-30','2026-12-01','2026-12-02'])
        incomplete=assemble_label(ROOT,ROOT,ROOT,DAY,instant('2026-11-27T15:59:59+08:00'))
        self.assertEqual(incomplete['status'],'holding_period_incomplete')
        self.assertEqual(incomplete['prices'],{})
        self.assertIsNone(incomplete['labels'])

    def test_real_published_dates_replay_but_opening_remains_unknown(self):
        saved=read(PROOF)
        with tempfile.TemporaryDirectory() as empty:
            actual=assemble_label(ROOT,Path(empty),Path(empty),DAY,instant(saved['observedAt']))
        self.assertEqual(actual,saved)
        self.assertEqual(len(actual['prices']),6)
        self.assertEqual(actual['gaps'],{'510300':'opening_evidence_missing','511010':'opening_evidence_missing'})
        self.assertIsNone(actual['labels'])

    def test_price_match_conflict_and_accounting_use_exact_compared_dates(self):
        # This test supplies explicit hypothetical opening states for real, admitted daily bars.
        window=label_window(ROOT,DAY)
        data=admitted_prices(ROOT,window.last,instant(read(PROOF)['observedAt']))['data']
        quotes={symbol:[dict(status='tradable',openingPrice=str(bars[DAY].open),
                             reference=str(bars[window.anchor].close))] for symbol,bars in data.bars.items()}
        accepted,gaps=match_opening(quotes,data,window)
        self.assertEqual(gaps,{})
        self.assertEqual(accepted,{'510300':'tradable','511010':'tradable'})
        alternative=dict(quotes,**{'510300':[*quotes['510300'],{'status':'blocked'}]})
        _,gaps=match_opening(alternative,data,window)
        self.assertEqual(gaps,{'510300':'opening_sources_conflict'})
        curves=serial_results(data,window,accepted)
        base=curves['stock_bond_50_50']['base']
        positions={symbol:order['filled'] for symbol,order in base['orders'].items()}
        cash=D('100000')-D(base['commission'])-D(base['slippage'])-sum(
            D(units)*data.bars[symbol][DAY].open for symbol,units in positions.items())
        marks=[D('100000'),*(cash+sum(D(units)*data.bars[symbol][day].close
                    for symbol,units in positions.items()) for day in window.sessions)]
        self.assertEqual(list(map(D,base['marks'])),marks)
        self.assertEqual(D(base['endingCash']),cash)
        self.assertEqual(D(base['availableCash']),cash)
        self.assertEqual(D(base['dividendReceivable']),0)
        self.assertEqual(D(base['terminalReturn']),marks[-1]/marks[0]-1)
        self.assertEqual(D(base['maxDrawdown']),max(1-mark/max(marks[:i+1]) for i,mark in enumerate(marks)))
        self.assertTrue(all(set(variants)=={'low','base','high'} for variants in curves.values()))

    def test_scheduled_archive_retains_actual_ready_clock_and_rejects_damage(self):
        with tempfile.TemporaryDirectory() as directory:
            root,store=Path(directory)/'research',Path(directory)/'store'
            root.mkdir()
            calendar=root/BASE_PATH
            calendar.parent.mkdir(parents=True)
            calendar.write_bytes((ROOT/BASE_PATH).read_bytes())
            stamp=instant(read(PROOF)['observedAt'])
            good=dict(mode='scheduled_candidate',entryDay=str(DAY),status='evidence_complete',
                      notBefore='2026-11-27T16:00:00+08:00',observedAt=stamp.isoformat(),
                      decision={'path':'sealed eligible sample in this isolated test'},labels={'synthetic':True},gaps={})
            clock=instant('2026-11-27T21:00:00+08:00')
            with (patch.object(sealer,'now',return_value=clock),patch.object(sealer,'BINDINGS',()),
                  patch('etf_research.evidence_archive.datetime') as archive_clock):
                archive_clock.now.return_value=clock
                receipt=sealer.archive_label(root,store,'a'*32,good)
                self.assertEqual(receipt['labelReadyAt'],clock.isoformat())
                path=root/receipt['path']
                self.assertEqual(sealer.check_label(root,store,path),receipt)
                (path/'records/label.json').write_bytes(b'{}')
                with self.assertRaisesRegex(ValueError,'Bundle hash mismatch'):
                    sealer.check_label(root,store,path)
