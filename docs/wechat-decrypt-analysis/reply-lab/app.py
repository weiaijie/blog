"""Loopback-only reply draft UI. New conversations are in memory unless saved."""
import argparse
import datetime as dt
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import uuid

import reply_engine as engine
import reply_lab as lab
from codex_provider import ProviderError

HERE=Path(__file__).resolve().parent
DEFAULT_RUN=HERE/'private/review-20260917-next-sample-check'
REPLAY=HERE/'private/replay-20260918/inputs.json'


class ReplyServer(ThreadingHTTPServer):
    daemon_threads=True

    def __init__(self,address,run,provider=None):
        super().__init__(address,Handler)
        self.run=run
        self.provider=provider
        self.token=secrets.token_urlsafe(32)
        self.busy=threading.Lock()
        self.responses={}
        self.replays=lab.read_json(REPLAY) if REPLAY.exists() else []
        if self.replays and engine.auto.sha(self.replays)!=lab.read_json(REPLAY.parent/'manifest.json')['inputs_sha256']:
            self.server_close()
            raise ValueError('历史回放资料已改变')


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):
        pass

    def trusted_host(self):
        return self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port)

    def send(self,status,value,kind='application/json; charset=utf-8'):
        body=(json.dumps(value,ensure_ascii=False) if kind.startswith('application/json') else value).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; connect-src 'self'")
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass

    def do_GET(self):
        if not self.trusted_host() or self.headers.get('Sec-Fetch-Site')=='cross-site':
            self.send(403,{'error':'仅允许本机页面访问'});return
        if self.path=='/':
            self.send(200,(HERE/'app.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token),'text/html; charset=utf-8')
        elif self.path=='/api/examples' and self.headers.get('X-Reply-Token')==self.server.token:
            self.send(200,[{'id':s['id'],'title':s.get('title','历史片段 '+str(i+1)),
                           'text':'\n'.join(m['role']+'：'+m['text'] for m in s['messages']),
                           'as_of':s['as_of']} for i,s in enumerate(self.server.replays)])
        else:self.send(404,{'error':'页面不存在'})

    def do_POST(self):
        origin='http://127.0.0.1:'+str(self.server.server_port)
        if (not self.trusted_host() or self.headers.get('Origin')!=origin
                or not secrets.compare_digest(self.headers.get('X-Reply-Token',''),self.server.token)):
            self.send(403,{'error':'请从本机页面发起操作'});return
        if self.path not in ('/api/reply','/api/feedback'):
            self.send(404,{'error':'接口不存在'});return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>48000 or not self.headers.get('Content-Type','').startswith('application/json'):
                self.send(400,{'error':'请输入不超过 12000 字的对话'});return
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):raise ValueError('请求格式无效')
            if self.path=='/api/feedback':
                self.feedback(body);return
            if not self.server.busy.acquire(blocking=False):
                self.send(409,{'error':'上一条还在生成，请稍等'});return
            try:
                replay_id=body.get('replay_id')
                options={'provider':self.server.provider} if self.server.provider else {}
                if replay_id:
                    replay=next((s for s in self.server.replays if s['id']==replay_id),None)
                    if not replay:raise ValueError('历史片段不存在')
                    response=engine.reply(self.server.run,replay['messages'],as_of=replay['as_of'],history=replay.get('history',[]),**options)
                else:
                    text=body.get('text','')
                    if not isinstance(text,str) or len(text)>12000:raise ValueError('对话不能超过 12000 字')
                    response=engine.reply(self.server.run,engine.parse_chat(text),**options)
                identifier=uuid.uuid4().hex
                response['id']=identifier
                self.server.responses[identifier]=response
                # Bound in-memory retention; never persists on ordinary generation.
                while len(self.server.responses)>20:self.server.responses.pop(next(iter(self.server.responses)))
                self.send(200,response)
            finally:self.server.busy.release()
        except (ValueError,KeyError) as exc:self.send(400,{'error':str(exc) if isinstance(exc,ValueError) else '资料不完整'})
        except ProviderError as exc:self.send(502,{'error':str(exc)})
        except Exception:self.send(500,{'error':'本地资料读取或生成失败，请检查服务运行状态'})

    def feedback(self,body):
        response=self.server.responses.get(body.get('id',''))
        edited=body.get('edited','')
        if not response or not isinstance(edited,str) or not edited.strip() or len(edited)>1200:
            raise ValueError('请先生成，再填写希望保留的回复')
        edited=engine.auto.mask(edited,())
        if '[含凭据信息' in edited:raise ValueError('不能保存凭据内容')
        folder=HERE/'private/feedback'
        folder.mkdir(parents=True,exist_ok=True)
        record={'saved_at':dt.datetime.now(engine.TZ).isoformat(),'generated':response,
                'edited':edited,'purpose':'用户主动保存的本地修改反馈；不会自动写入风格档案'}
        lab.write_json(folder/(uuid.uuid4().hex+'.json'),record)
        self.send(200,{'saved':True})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--run',type=Path,default=DEFAULT_RUN)
    args=parser.parse_args()
    # Refuse startup when the reference bundle has drifted.
    engine.prepare_request(args.run,[{'role':'对方','text':'启动检查'}])
    server=ReplyServer(('127.0.0.1',args.port),args.run)
    print('回复草稿台：http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
