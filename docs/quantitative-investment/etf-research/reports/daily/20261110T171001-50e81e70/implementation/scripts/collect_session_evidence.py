"""Capture bounded public evidence; no admission or account updates."""
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.publication import read, create, seal
from etf_research.http_capture import HOSTS, fetch, load_policy, save_transport


def main():
    folder = ROOT/'data/snapshots'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-session-evidence-%H%M%S')
    folder.mkdir(exist_ok=False)
    policy = load_policy()
    save_transport(folder, policy)
    HOSTS.add('www.sseinfo.com')
    jobs = [('historical_product', 'https://www.sseinfo.com/services/assortment/historical/'),
            ('intraday_directory', 'https://www.sse.com.cn/disclosure/dealinstruc/intradaysuspension/')]
    for event in read(ROOT/'data/snapshots/2026-11-03-official-02/reconciliation.json')['dividends']:
        s = event['symbol']
        d = event['ex_date'].replace('-', '')
        jobs.append((f'sohu_{s}_{d}', f'https://q.stock.sohu.com/hisHq?code=cn_{s}&start={d}&end={d}&stat=1&order=D&period=d&rt=json'))
    def capture(job):
        name, url = job
        row = fetch(folder, name, url, policy)
        return row
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(capture, jobs))
    create(folder/'requests.json', rows)
    (folder/'collector.py').write_bytes(Path(__file__).read_bytes())
    seal(folder)
    print(folder.name, [(r['name'], r['status'], r['bytes']) for r in rows])


if __name__ == '__main__':
    main()
