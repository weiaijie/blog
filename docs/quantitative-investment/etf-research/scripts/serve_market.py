"""Serve the read-only research dashboard, or export its verified data for static viewing."""
import argparse
from datetime import date, timedelta
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Lock
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import load_incremental, sessions_between
from etf_research.forward import digest, prefix_digest
from etf_research.publication import inside, read, sha, verify_bundle
import interactive_backtest as interactive
from market_evidence import SNAPS

SITE = ROOT/'site'
ASSETS = {'/': ('market.html','text/html'), '/market.html': ('market.html','text/html'),
          '/market.css': ('market.css','text/css'), '/market.js': ('market.js','text/javascript'),
          '/vendor-charts/lightweight-charts-5.0.9.js': ('vendor-charts/lightweight-charts-5.0.9.js','text/javascript'),
          '/backtest.html': ('backtest.html','text/html'), '/backtest.css': ('backtest.css','text/css'),
          '/backtest.js': ('backtest.js','text/javascript'), '/backtest-data.json': ('backtest-data.json','application/json'),
          '/interactive.js': ('interactive.js','text/javascript'), '/interactive.css': ('interactive.css','text/css'),
          '/overlay.js': ('overlay.js','text/javascript'),
          '/entry-windows.json': ('entry-windows.json','application/json'),
          '/vendor-charts/LICENSE.txt': ('vendor-charts/LICENSE.txt','text/plain')}
guard = Lock()


@lru_cache(maxsize=1)
def history():
    _, _, bars, _ = interactive.inputs()
    return bars


@lru_cache(maxsize=1)
def payload(pointer_bytes):
    pointer = json.loads(pointer_bytes)
    folder = inside(ROOT,pointer['bundle'])
    verify_bundle(folder)
    if sha(folder/'manifest.json') != pointer['bundle_manifest_sha256']:
        raise ValueError('Bundle digest mismatch')
    checkpoint = folder/'forward_checkpoint.json'
    if inside(ROOT,pointer['checkpoint']) != checkpoint:
        raise ValueError('Checkpoint outside active bundle')
    state = read(checkpoint)
    checksum = digest({k:v for k,v in state.items() if k!='checkpoint_sha256'})
    if (state['real_money'] is not False or checksum != state['checkpoint_sha256'] or
            checksum != pointer['checkpoint_sha256'] or state['as_of']!=pointer['as_of']):
        raise ValueError('Checkpoint identity mismatch')
    audit = read(folder/'admission.json')
    data, rebuilt = load_incremental(SNAPS, audit['snapshot'])
    as_of = date.fromisoformat(state['as_of'])
    if rebuilt!=audit or data.sessions[-1]!=as_of or prefix_digest(data,as_of)!=state['admitted_prefix_sha256']:
        raise ValueError('Account and market data differ')
    candles = {}
    for symbol,old in history().items():
        prices = dict(old)
        if symbol in data.bars:
            current = data.bars[symbol]
            if any(prices[d]!=current[d] for d in prices.keys() & current.keys()):
                raise ValueError('Revised OHLC on overlap: '+symbol)
            cutoff = max(old)
            prices.update({d:v for d,v in current.items() if d>cutoff})
        candles[symbol] = [[d.isoformat(),float(b.open),float(b.high),float(b.low),float(b.close)]
                           for d,b in sorted(prices.items())]
    portfolio=state['portfolios']['monthly_50_50_base']
    curve=[[r['date'],float(r['equity'])] for r in portfolio['daily']]
    if len(curve)!=state['forward_sessions'] or curve[-1][0]!=state['as_of']:
        raise ValueError('Forward observations incomplete')
    calendar=read(SNAPS/'2026-11-04-calendar-08/calendar.json')['holiday_ranges']
    end=date(as_of.year,12,31)
    following=sessions_between(calendar,as_of+timedelta(days=1),end) if as_of<end else []
    view=dict(asOf=state['as_of'],start=state['forward_start'],sessions=state['forward_sessions'],
              initial=float(portfolio['summary']['initial_cash']),curve=curve,candles=candles,
              nextSession=str(following[0]) if following else None)
    return json.dumps(view,ensure_ascii=False,separators=(',',':')).encode()


def latest():
    with guard:
        return payload((ROOT/'config/active_run.json').read_bytes())


CALCULATIONS = {'/api/v1/backtest': interactive.backtest,
                '/api/v1/backtest/windows': interactive.entry_windows,
                '/api/v1/backtest/compare': interactive.compare_windows,
                '/api/v1/backtest/overlay': interactive.same_window}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.reply(True)

    def do_HEAD(self):
        self.reply(False)

    def reply(self, send_body):
        url = urlsplit(self.path)
        path = url.path
        status = 200
        if path == '/api/v1/backtest/options':
            body, kind = interactive.encode(interactive.OPTIONS), 'application/json'
        elif path in CALCULATIONS:
            kind = 'application/json'
            try:
                calculate = CALCULATIONS[path]
                body = interactive.encode(calculate(interactive.request_params(url.query)))
            except interactive.InputError as exc:
                status, body = 400, interactive.encode({'error': str(exc)})
            except (OSError, ValueError, KeyError, IndexError) as exc:
                self.log_error('Historical replay unavailable: %s', exc)
                status, body = 503, interactive.encode({'error': '已核验的历史数据暂时不可用。'})
        elif path=='/market-data.json':
            try:
                body,kind=latest(),'application/json'
            except (OSError,ValueError,KeyError,IndexError) as exc:
                self.log_error('Research verification failed: %s', exc)
                self.send_error(503,'Verified research unavailable')
                return
        elif path in ASSETS:
            name,kind=ASSETS[path]
            body=(SITE/name).read_bytes()
        else:
            self.send_error(404)
            return
        self.send_response(status)
        self.send_header('Content-Type',kind+'; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--bind',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=18766)
    parser.add_argument('--export',type=Path)
    args=parser.parse_args()
    if args.export:
        args.export.write_bytes(latest())
    else:
        latest()
        ThreadingHTTPServer((args.bind,args.port),Handler).serve_forever()
