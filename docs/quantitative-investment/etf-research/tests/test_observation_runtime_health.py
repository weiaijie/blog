from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from etf_research.publication import create, seal
from observation_runtime_health import JOBS, configuration, health_view, job_status, observe, parse_units

NOW=datetime.fromisoformat('2026-11-28T09:00:00+08:00')
UNIT='etf-research-observation'


def clock(local):
    return '@'+str(int(datetime.fromisoformat(local+'+08:00').timestamp()))


class ObservationRuntimeHealthTests(unittest.TestCase):
    def setUp(self):
        self.spec=configuration(ROOT,UNIT)
        self.timer=dict(LoadState='loaded',ActiveState='active',UnitFileState='enabled',
                        calendar=self.spec[0],Persistent='yes',
                        ActiveEnterTimestamp=clock('2026-11-27T08:00:00'),
                        LastTriggerUSec=clock('2026-11-28T08:34:00'),
                        NextElapseUSecRealtime=clock('2026-11-28T19:40:00'))
        self.service=dict(LoadState='loaded',ActiveState='inactive',Result='success',ExecMainStatus='0',
                          ExecMainStartTimestamp=clock('2026-11-28T08:34:00'),
                          ExecMainExitTimestamp=clock('2026-11-28T08:35:00'))

    def test_clock_and_actual_service_exit_never_conflate_missed_and_completed(self):
        def state(timer=None,service=None,observed=NOW):
            return job_status(dict(self.timer,**(timer or {})),dict(self.service,**(service or {})),self.spec,observed)['state']
        self.assertEqual(state(),'completed')
        early_timer = dict(LastTriggerUSec=clock('2026-11-28T08:25:00'),
                           NextElapseUSecRealtime=clock('2026-11-28T08:34:00'))
        early_run = dict(ExecMainStartTimestamp=clock('2026-11-28T08:25:00'),
                         ExecMainExitTimestamp=clock('2026-11-28T08:26:00'))
        self.assertEqual(state(early_timer,early_run,NOW.replace(hour=8,minute=30)),'completed')
        self.assertEqual(state(early_timer,early_run),'missed_schedule')
        self.assertEqual(state(dict(LastTriggerUSec=clock('2026-11-27T19:40:00'))),'missed_schedule')
        self.assertEqual(state(dict(LastTriggerUSec=clock('2026-11-28T08:45:00')),
                               dict(ExecMainStartTimestamp=clock('2026-11-28T08:45:00'),
                                    ExecMainExitTimestamp=clock('2026-11-28T08:46:00'))),'late_trigger')
        self.assertEqual(state(service=dict(ExecMainStatus='1',Result='exit-code')),'failed')
        self.assertEqual(state(service=dict(ExecMainStartTimestamp='')),'execution_unverified')
        self.assertEqual(state(service=dict(ActiveState='activating')),'stalled')
        self.assertEqual(state(dict(ActiveEnterTimestamp=clock('2026-11-28T08:45:00'))),'waiting')
        self.assertEqual(state(dict(UnitFileState='disabled')),'timer_inactive')
        self.assertEqual(state(dict(calendar=['changed'])),'timer_configuration_mismatch')

    def test_batch_parser_preserves_each_calendar_and_missing_units_are_visible(self):
        output=(
            'Id=etf-research-observation.timer\nLoadState=loaded\n'
            'TimersCalendar={ OnCalendar=*-*-* 19:40:00 Asia/Shanghai ; next_elapse=@1795866000 }\n'
            'TimersCalendar={ OnCalendar=*-*-* 08:34:00 Asia/Shanghai ; next_elapse=@1795826040 }\n'
            'TimersCalendar={ OnCalendar=*-*-* 08:25:00 Asia/Shanghai ; next_elapse=@1795825500 }\n\n'
            'Id=etf-research-observation.service\nResult=success\n'
        )
        parsed=parse_units(output)
        self.assertEqual(parsed[UNIT+'.timer']['calendar'],self.spec[0])
        self.assertEqual(parsed[UNIT+'.service']['Result'],'success')
        report=observe(ROOT,NOW,query=lambda:{UNIT+'.timer':self.timer,UNIT+'.service':self.service})
        self.assertEqual(set(report['jobs']),set(JOBS))
        self.assertEqual(report['jobs']['observation']['state'],'completed')
        self.assertEqual(report['jobs']['model']['state'],'unit_unavailable')
        self.assertIn('model',report['issues'])

    def test_agent_reads_exact_sealed_snapshot_and_marks_it_stale(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            self.assertEqual(health_view(root,NOW)['state'],'waiting')
            folder=root/'reports/health/example'
            payload=dict(observation='reports/health/example',
                        independent_study=observe(ROOT,NOW,query=lambda:{}))
            create(folder/'result.json',payload)
            seal(folder)
            pointer=root/'site/health_status.json'
            create(pointer,payload)
            self.assertEqual(health_view(root,NOW),payload['independent_study'])
            self.assertEqual(health_view(root,NOW+timedelta(minutes=31))['state'],'stale')
            pointer.write_text('{"observation":"reports/health/example"}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'differs from its seal'):
                health_view(root,NOW)
