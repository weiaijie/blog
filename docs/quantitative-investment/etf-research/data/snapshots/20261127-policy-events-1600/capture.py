"""Capture the four reviewed official pages, using new files only."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PAGES = {
    'xinhua_1106': 'https://www.news.cn/20261106/84f141de4c884bf6b250edcbb5b32952/c.html',
    'mofcom_1107': 'https://www.mofcom.gov.cn/syxwfb/art/2026/art_12d65a0ba98a436b8c6b046863e591e7.html',
    'xinhua_1127': 'https://www.news.cn/politics/leaders/20261127/a7c52bc55082444da343d42d738f28b8/c.html',
    'csrc_1127': 'https://www.csrc.gov.cn/csrc/c100028/c7673432/content.shtml',
}


def capture():
    folder = Path(__file__).resolve().parent
    if any(p.name != 'capture.py' for p in folder.iterdir()):
        raise FileExistsError('Use a new snapshot directory')
    requests = []
    for name, url in PAGES.items():
        path = folder/(name+'.body')
        started = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(['curl', '--silent', '--show-error', '--proto', '=https',
                                 '--connect-timeout', '8', '--max-time', '20', '--output', str(path),
                                 '--write-out', '%{http_code} %{url_effective}', url],
                                capture_output=True, text=True, check=False)
        finished = datetime.now(timezone.utc).isoformat()
        status, _, final_url = result.stdout.partition(' ')
        requests.append(dict(name=name, url=url, final_url=final_url, status=int(status or 0),
                             curl_exit=result.returncode, error=result.stderr.strip() or None,
                             requested_at_utc=started, completed_at_utc=finished,
                             sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None))
    (folder/'requests.json').write_text(json.dumps(requests, ensure_ascii=False, indent=2)+'\n')
    manifest = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


if __name__ == '__main__':
    capture()
