"""Does the public SSE snapshot endpoint actually honor a historical date?"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.http_capture import fetch, load_policy, save_transport, HOSTS
from etf_research.publication import read, create, seal


def main():
    folder = ROOT/'data/snapshots'/datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d-exdate-quotes-%H%M%S')
    folder.mkdir(exist_ok=False)
    policy = load_policy()
    save_transport(folder, policy)
    HOSTS.add('www.sseinfo.com')
    jobs = [('interface_manual','https://www.sseinfo.com/services/assortment/market/hqywwd/wdzsjk/c/10800481/files/43b75567ae224148bd576acf11d30bd3.pdf')]
    for e in read(ROOT/'data/snapshots/2026-11-03-official-02/reconciliation.json')['dividends']:
        if '2018-09-14' <= e['ex_date'] <= '2026-10-30':
            s, d = e['symbol'], e['ex_date'].replace('-', '')
            jobs.append((f'snap_{s}_{d}', f'https://yunhq.sse.com.cn:32042/v1/sh1/snap/{s}?select=name,prev_close,open,high,low,last&date={d}'))
    rows = [fetch(folder, name, url, policy) for name, url in jobs]
    create(folder/'requests.json', rows)
    (folder/'collector.py').write_bytes(Path(__file__).read_bytes())
    seal(folder)
    print(folder.name, [(r['name'], r['status'], r['bytes']) for r in rows])


if __name__=='__main__':
    main()
