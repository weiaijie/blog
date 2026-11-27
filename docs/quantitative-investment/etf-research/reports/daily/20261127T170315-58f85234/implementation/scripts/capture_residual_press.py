"""Extract public notice evidence from newspaper pages without republishing unrelated articles."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

PREFIX = '2026-11-08-residual-events-0712'
TITLE = '博时标普500交易型开放式指数证券投资基金溢价风险提示'
SIGNATURE = re.compile(r'博时基金管理有限公司(20\d\d)年(\d{1,2})月(\d{1,2})日')


def extract(raw, name):
    try:
        markup = raw.decode('utf8')
    except UnicodeDecodeError:
        markup = raw.decode('gb18030')
    body = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', markup, flags=re.I|re.S)
    body = re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]*>', '', body)))
    clock = re.search(r'<meta property="article:published_time" content="([^"]+)"', markup)
    if name == 'copy_20250123':
        clock = re.search(r'(2025-01-23 \d\d:\d\d:\d\d)', markup)
    display = clock[1] if clock else None
    signatures = {}
    for m in re.finditer(TITLE + '(?:及停复牌)?公告', body):
        # A multi-notice edition may carry yesterday's signed notice.
        segment = body[m.end():m.end()+1100]
        signature = SIGNATURE.search(segment)
        if not signature:
            continue
        text = segment[:signature.start()]
        if '513500' not in text or '交易价格' not in text or TITLE in text:
            continue
        day = '%04d-%02d-%02d' % tuple(map(int, signature.groups()))
        signatures[day] = dict(signed_text=signature[0], fund_code='513500',
                               notice_text_sha256=hashlib.sha256(segment[:signature.end()].encode()).hexdigest())
    if name == 'copy_20250123' and not signatures:
        # This publisher's rendition omits the signature date; retain only the dated appearance.
        if not (display and TITLE in body and '交易所代码：513500' in body and '溢价风险' in body):
            raise ValueError('Unexpected Stockstar notice')
    return dict(title_and_code_present=TITLE in body and '513500' in body,
                publisher_clock=display, signed_notices=signatures)


def capture(source_root, out):
    records = []
    probes = []
    for suffix in 'bcdegijkloq':
        folder = source_root / (PREFIX + suffix)
        for req in json.loads((folder/'requests.json').read_bytes()):
            path = folder / (req['name'] + '.body')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != req['sha256']:
                raise ValueError('Response hash mismatch')
            key = req['name']
            if suffix in 'ijkl' and key.startswith(('copy_', 'article_')) and key != 'copy_2':
                records.append(dict(**req, **extract(raw, key)))
            else:
                probes.append(req)
    out.mkdir(parents=True,exist_ok=False)
    for filename, data in [('press.json', records), ('discovery_requests.json', probes)]:
        (out/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (out/'manifest.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                    for f in sorted(out.iterdir())},indent=2)+'\n',encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    capture(args.source_root,args.output)
