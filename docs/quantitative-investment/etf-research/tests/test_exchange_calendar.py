from datetime import date, datetime, timedelta
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from capture_exchange_calendar import register
from collect_policy_etf_day import following_session
from collect_sse_research_day import previous_session
from observation_inputs import date_context
from observation_labels import label_window
from observation_status import expected_days
from etf_research.admission import sessions_between
from etf_research.exchange_calendar import BASE_PATH, BASE_SHA, REGISTRY, calendar_at, inspect_annual, parse_notice, verify_annual
from etf_research.publication import create, seal, sha

PROBE = ROOT/'data/snapshots/20261127T115806Z-calendar-annual-rehearsal'
CHECKED = datetime.fromisoformat('2026-12-22T16:50:00+08:00')
AVAILABLE = datetime.fromisoformat('2026-12-22T17:00:00+08:00')


class ExchangeCalendarTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        base = self.root/BASE_PATH
        base.parent.mkdir(parents=True)
        shutil.copyfile(ROOT/BASE_PATH,base)

    def synthetic_annual(self, *, conflict=False):
        folder = self.root/'data/snapshots/synthetic-year'
        folder.mkdir()
        suffix = '2027年部分节假日休市安排的通知'
        rows = []
        for name,title,url in (
            ('sse','关于上海证券交易所'+suffix,'https://www.sse.com.cn/disclosure/announcement/general/c/c_20261222_10000000.shtml'),
            ('szse','关于'+suffix,'https://www.szse.cn/disclosure/notice/general/t20261222_600000.html')):
            notices = []
            schedules = [(1,1),(2,8),(4,5),(5,3),(6,7),(9,20),(10,1)]
            if conflict and name=='szse':
                schedules[1] = (2,9)
            labels = ('元旦','春节','清明节','劳动节','端午节','中秋节','国庆节')
            for index,((month,day),label) in enumerate(zip(schedules,labels,strict=True)):
                close = date(2027,month,day)
                opening = close+timedelta(days=1)
                while opening.weekday()>=5:
                    opening += timedelta(days=1)
                notices.append(f"<p>（{'一二三四五六七'[index]}）{label}：{month}月{day}日休市，"
                               f"{opening.month}月{opening.day}日起照常开市。</p>")
            path = folder/(name+'.body')
            path.write_text('<h1>'+title+'</h1><p>一、休市安排</p>'+''.join(notices)+'<p>二、清算交收</p>',encoding='utf-8')
            rows.append(dict(name=name,url=url,final_url=url,status=200,curl_exit=0,bytes=path.stat().st_size,
                             certificate_verification_enabled=True,metrics=dict(ssl_verify_result=0),sha256=sha(path),
                             requested_at_utc=CHECKED.isoformat(),receivedAt=CHECKED.isoformat()))
        create(folder/'requests.json',rows)
        return folder

    def admit(self):
        folder = self.synthetic_annual()
        create(folder/'calendar.json',inspect_annual(folder,2027,CHECKED.isoformat()))
        seal(folder)
        with patch('capture_exchange_calendar.now',return_value=AVAILABLE):
            marker = register(folder,self.root)
            with self.assertRaisesRegex(ValueError,'out of sequence'):
                register(folder,self.root)
        return folder,marker

    def test_primary_notices_rebuild_every_2026_session(self):
        result = verify_annual(PROBE)
        scope = (date(2026,1,1),date(2026,12,31))
        original = calendar_at(self.root,AVAILABLE).ranges
        calculated = sessions_between({'2026':result['holidayRanges']},*scope)
        self.assertEqual(sessions_between(original,*scope),calculated)
        self.assertEqual(len(result['holidayRanges']),7)
        self.assertEqual(len(calculated),242)

    def test_annual_admission_is_point_in_time_and_legacy_hash_stays_pinned(self):
        folder,marker = self.admit()
        before = AVAILABLE-timedelta(microseconds=1)
        self.assertEqual(calendar_at(self.root,before).digest,BASE_SHA)
        after = calendar_at(self.root,AVAILABLE)
        self.assertNotEqual(after.digest,BASE_SHA)
        self.assertEqual(sha(folder/'manifest.json'),marker['manifestSha256'])
        self.assertIn(REGISTRY+'/2027.json',after.extensions)
        self.assertEqual(calendar_at(self.root,AVAILABLE,pinned=BASE_SHA).digest,BASE_SHA)
        self.assertNotIn('2027',calendar_at(self.root,AVAILABLE,pinned=BASE_SHA).ranges)
        self.assertEqual(calendar_at(self.root,AVAILABLE,pinned=after.digest),after)
        with self.assertRaisesRegex(ValueError,'pinned fingerprint'):
            calendar_at(self.root,before,pinned=after.digest)
        (folder/'sse.body').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            calendar_at(self.root,AVAILABLE)
        self.assertEqual(calendar_at(self.root,before).digest,BASE_SHA)

    def test_notice_disagreement_refuses_extension(self):
        folder = self.synthetic_annual(conflict=True)
        with self.assertRaisesRegex(ValueError,'ranges disagree'):
            inspect_annual(folder,2027,CHECKED.isoformat())
        self.assertFalse((self.root/REGISTRY/'2027.json').exists())

    def test_extra_weekday_closure_needs_review(self):
        folder = self.synthetic_annual()
        path = folder/'sse.body'
        original = path.read_text(encoding='utf-8')
        extra = original.replace('1月4日起照常开市。','1月4日起照常开市。另外，1月7日为周末休市。')
        self.assertNotEqual(extra,original)
        path.write_text(extra,encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'additional closure'):
            parse_notice('sse',path.read_bytes(),2027)

    def test_cross_year_snapshot_calendar_previous_next_and_five_session_label(self):
        self.admit()
        last = date(2026,12,31)
        next_day = date(2027,1,4)
        before = AVAILABLE-timedelta(seconds=1)
        self.assertEqual(expected_days(self.root,last,next_day,observed=before),((last,),2027))
        self.assertEqual(expected_days(self.root,last,next_day,observed=AVAILABLE),((last,next_day),None))
        with self.assertRaisesRegex(ValueError,'lacks independent evidence'):
            label_window(self.root,last,before)
        calendar = calendar_at(self.root,AVAILABLE)
        self.assertEqual(following_session(last,calendar),next_day)
        self.assertEqual(previous_session(next_day,datetime.fromisoformat('2027-01-04T19:00:00+08:00'),calendar),last)
        self.assertEqual(date_context(self.root,next_day,AVAILABLE)[-1],last)
        self.assertEqual(label_window(self.root,last,AVAILABLE).sessions,
                         (last,next_day,date(2027,1,5),date(2027,1,6),date(2027,1,7)))
