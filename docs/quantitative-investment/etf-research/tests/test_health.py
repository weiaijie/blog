from datetime import datetime
import unittest
from etf_research.health import evaluate

class HealthTests(unittest.TestCase):
    def check(self, when, account='2026-11-06', **kwargs):
        op=kwargs.pop('operation',dict(phase='success',started_at_utc='2026-11-06T11:25:25+00:00',mode='scheduled',operation='old'))
        return evaluate(datetime.fromisoformat(when+'+08:00'), {'2026':[['10-01','10-07']]}, {'as_of':account}, op,
                        kwargs.pop('scheduler',dict(timer_enabled='enabled',timer_active='active',linger='yes')), **kwargs)
    def test_weekend_is_not_stale(self):
        self.assertEqual(self.check('2026-11-08T20:00:00')['state'],'market_closed')
    def test_before_close_waits(self):
        self.assertEqual(self.check('2026-11-09T15:59:00')['state'],'before_collection_window')
    def test_collection_grace(self):
        self.assertEqual(self.check('2026-11-09T16:29:59')['state'],'awaiting_scheduled_collection')
    def test_old_success_cannot_hide_missed_run(self):
        r=self.check('2026-11-09T16:30:00');self.assertIn('missed_schedule',r['issues']);self.assertIn('account_stale',r['issues'])
    def test_weekend_does_not_hide_friday_backlog(self):
        self.assertIn('account_stale',self.check('2026-11-08T12:00:00',account='2026-11-05')['issues'])
    def test_second_slot_failure_not_hidden_by_current_account(self):
        op=dict(phase='failed',started_at_utc='2026-11-09T08:40:00+00:00',mode='scheduled')
        self.assertIn('run_failed',self.check('2026-11-09T16:50:00',account='2026-11-09',operation=op)['issues'])
    def test_missing_calendar_is_not_closed(self):
        self.assertEqual(self.check('2027-01-01T10:00:00')['state'],'calendar_missing')
    def test_disabled_timer_visible_on_weekend(self):
        self.assertTrue(self.check('2026-11-08T12:00:00',scheduler={})['actionable'])
    def test_stuck_running(self):
        op=dict(phase='running',started_at_utc='2026-11-06T08:10:00+00:00',mode='scheduled')
        self.assertIn('stalled_run',self.check('2026-11-06T16:27:00',operation=op)['issues'])
    def test_pending_and_reviewed_both_block(self):
        for pending,expected in [(1,'notice_review_required'),(0,'reviewed_but_admission_blocked')]:
            self.assertIn(expected,self.check('2026-11-08T12:00:00',reviews=[{'pending_changes':pending}])['issues'])
    def test_timezone_required(self):
        with self.assertRaises(ValueError):evaluate(datetime(2026,11,6),{}, {}, {}, {})
    def test_missing_operation_not_healthy(self):
        self.assertIn('no_runtime_observation',self.check('2026-11-08T12:00:00',operation=None)['issues'])
