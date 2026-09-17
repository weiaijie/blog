import contextlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import reply_lab as lab


def row(sender, text, timestamp, kind="text"):
    return dict(sender_username=sender, clean_text=text, create_time=str(timestamp),
                local_id=str(timestamp), message_kind=kind, chat_username="chat",
                is_group="False", create_datetime="2026-03-01 10:00:00",
                db_file="message_0.db", table_name="Msg_" + "a" * 32)


def sample(index, chat):
    return dict(id=str(index), chat_id=chat, object_type="同事", context=[{"role":"对方","text":"现在怎么样"}],
                reference=["先看下再说"], intent="先检查", facts="无", approved=True,
                privacy_reviewed=True, identity_verified=True)


class LabTests(unittest.TestCase):
    def test_short_messages_stay_together_without_future(self):
        data = [row("other", "现在咋办", 1), row("me", "我先看下", 2), row("me", "等下再说", 3), row("other", "未来消息", 4)]
        result = lab.make_candidates(data, "me")
        self.assertEqual(result[0]["reference"], ["我先看下", "等下再说"])
        self.assertNotIn("未来消息", str(result[0]["context"]))

    def test_unknown_sender_and_media_are_barriers(self):
        for middle in (row("", "未知", 2), row("other", "图片", 2, "image")):
            self.assertEqual(lab.make_candidates([row("other", "问题", 1), middle, row("me", "这个我先看一下", 3)], "me"), [])

    def test_old_context_not_used(self):
        self.assertEqual(lab.make_candidates([row("other", "问题", 1), row("me", "这个我先看一下", 4000)], "me"), [])

    def test_redaction(self):
        text = lab.redact("张三 https://example.com/a 13812345678 a@b.com 10.2.3.4 password=abc", ["张三"])
        for secret in ("张三", "https://", "13812345678", "a@b.com", "10.2.3.4", "abc"):
            self.assertNotIn(secret, text)

    def test_whitespace_credentials_excluded_wholesale(self):
        for text in ("地址 example.invalid 密码 fake-secret", "密码是fake-secret", "password fake-secret"):
            self.assertEqual(lab.redact(text), "[含凭据信息，整条排除]")

    def test_identity_verifies_database_and_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            with contextlib.closing(sqlite3.connect(path / "message_0.db")) as conn:
                conn.execute("CREATE TABLE Name2Id (user_name TEXT)")
                conn.execute("INSERT INTO Name2Id VALUES ('me')")
                conn.execute('CREATE TABLE "Msg_' + 'a'*32 + '" (local_id INTEGER,real_sender_id INTEGER)')
                conn.execute('INSERT INTO "Msg_' + 'a'*32 + '" VALUES (1,1)')
                conn.commit()
            s = {"source":[row("me", "", 1)]}
            self.assertTrue(lab.verify_identity(s, path))
            s["source"][0]["sender_username"] = "other"
            self.assertFalse(lab.verify_identity(s, path))

    def test_split_rejects_pending_reviews(self):
        s=sample(1,"chat");s["privacy_reviewed"]=False
        with self.assertRaises(ValueError): lab.split_samples([s])

    def test_pipeline_keeps_contacts_and_answers_separate(self):
        data=[sample(i,"chat"+str(i//5)) for i in range(30)]
        dev,evaluation=lab.split_samples(data)
        self.assertEqual((len(dev),len(evaluation)),(10,20))
        self.assertFalse({s["chat_id"] for s in dev}&{s["chat_id"] for s in evaluation})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);lab.write_json(path/"source.json", data)
            lab.build(path/"source.json",path/"out")
            requests=(path/"out/requests.json").read_text(encoding="utf-8")
            self.assertNotIn("先看下再说",requests)
            self.assertNotIn('"reference"',requests)
            output=io.StringIO()
            with contextlib.redirect_stdout(output):lab.score(path/"out/ratings.json")
            self.assertEqual(json.loads(output.getvalue())["rated"],0)
            self.assertIsNone(json.loads(output.getvalue())["usable_rate"])

    def test_review_does_not_allow_embedded_script_breakout(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);lab.write_json(path/"source.json",[{"context":[{"role":"对方","text":"</script><script>bad</script>"}]}])
            lab.review(path/"source.json",path/"review.html")
            self.assertNotIn("</script><script>bad",(path/"review.html").read_text(encoding="utf-8"))

    def test_duplicate_sample_rejected(self):
        with self.assertRaisesRegex(ValueError,"ID 重复"):
            lab.split_samples([sample(1,"a"),sample(1,"b")])

    def test_scene_uses_current_topic_not_contact(self):
        s=sample(1,"same-chat")
        s['context']=[{'role':'对方','text':'接口字段改好了吗'}]
        self.assertEqual(lab.labels(s)['scene'],'工作')
        s['context']=[{'role':'对方','text':'哈哈这个电影好玩'}]
        self.assertEqual(lab.labels(s)['scene'],'闲聊')

    def test_state_does_not_copy_other_person_or_hidden_answer(self):
        s=sample(1,"chat");s['context']=[{'role':'对方','text':'我在忙，赶紧上线'}]
        s['reference']=['我也很着急']
        self.assertEqual(lab.labels(s)['reply_state'],'待判断')
        s['context'].append({'role':'我','text':'我在忙，晚点看'})
        self.assertEqual(lab.labels(s)['reply_state'],'暂时没空')

    def test_mixed_and_unknown_are_not_forced(self):
        s=sample(1,"chat");s['context']=[{'role':'对方','text':'下班再看看接口'}]
        self.assertEqual(lab.labels(s)['scene'],'混合场景')
        s['context']=[{'role':'对方','text':'好'}]
        self.assertEqual(lab.labels(s)['scene'],'待判断')
        s.update(scene='闲聊',reply_state='轻松玩笑',label_source='用户调整')
        self.assertEqual(lab.public_input(s)['scene'],'闲聊')

    def test_score_rejects_missing_or_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            lab.write_json(path/"manifest.json",{"eval_ids":["1","2"],"eval_types":{"同事":2}})
            for ratings in ([{"id":"1"}], [{"id":"1"},{"id":"1"}]):
                lab.write_json(path/"ratings.json",ratings)
                with self.assertRaisesRegex(ValueError,"评价 ID"):
                    lab.score(path/"ratings.json")

    def test_high_score_without_coverage_does_not_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            lab.write_json(path/"manifest.json",{"eval_ids":["1"],"eval_types":{"同事":1}})
            lab.write_json(path/"ratings.json",[{"id":"1","model":"synthetic-test","reply":["好"],"rating":"可直接用","factual_error":False,"extra_promise":False}])
            output=io.StringIO()
            with contextlib.redirect_stdout(output):lab.score(path/"ratings.json")
            result=json.loads(output.getvalue())
            self.assertEqual(result["usable_rate"],1)
            self.assertFalse(result["numeric_gate_met"])


if __name__ == "__main__":
    unittest.main()
