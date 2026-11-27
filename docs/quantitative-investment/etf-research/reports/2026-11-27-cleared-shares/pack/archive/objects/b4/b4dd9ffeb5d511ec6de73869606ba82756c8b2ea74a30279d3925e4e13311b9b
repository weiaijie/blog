"""Strict discovery and receipt of public policy candidates for review."""
from datetime import date, timedelta
import hashlib
from html.parser import HTMLParser
import json
import re
from urllib.parse import urljoin, urlsplit

from etf_research.policy_events import TZ, instant, publication_bound

GOV_LIST = 'https://www.gov.cn/yaowen/liebiao/YAOWENLIEBIAO.json'
CSRC_HOME = 'https://www.csrc.gov.cn/csrc/index.shtml'
INDEXES = {'gov_list': GOV_LIST, 'csrc_home': CSRC_HOME}
GOV_PATH = re.compile(r'/yaowen/(?:liebiao/)?\d{6}/content_\d+\.htm')
CSRC_PATH = re.compile(r'/csrc/c\d+/c\d+/content\.shtml')
TITLE = re.compile(r'国务院常务会议|资本市场|证券投资基金|交易型开放式|ETF|融资融券|中长期资金', re.I)


def normalized(text):
    return ' '.join(text.split())


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.meta = {}
        self.links = []
        self.title = ''
        self.href = None
        self.title_open = False
        self.link_text = []
        self.feed(body.decode('utf-8-sig'))
        self.close()

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == 'meta' and fields.get('name') and fields.get('content'):
            self.meta.setdefault(fields['name'].lower(), fields['content'])
        elif tag == 'a':
            self.href = fields.get('href')
            self.link_text = []
        elif tag == 'title':
            self.title_open = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.href:
            self.links.append((self.href, normalized(''.join(self.link_text))))
            self.href = None
        elif tag == 'title':
            self.title_open = False

    def handle_data(self, data):
        if self.href:
            self.link_text.append(data)
        if self.title_open:
            self.title += data


def article_url(source, link):
    full = urljoin(INDEXES[source], link)
    u = urlsplit(full)
    host, pattern = (('www.gov.cn', GOV_PATH) if source == 'gov_list' else ('www.csrc.gov.cn', CSRC_PATH))
    if u.scheme == 'https' and u.netloc == host and not (u.query or u.fragment) and pattern.fullmatch(u.path):
        return full
    return None


def index_candidates(source, body, observed_date):
    """A stale catalogue is missing coverage, including when the response is HTTP 200."""
    oldest = observed_date - timedelta(days=7)
    if source == 'gov_list':
        records = json.loads(body)
        dates = [date.fromisoformat(row['DOCRELPUBTIME']) for row in records]
        if not dates or max(dates) < oldest or max(dates) > observed_date:
            raise ValueError('Government news list is stale or has future dates')
        rows = ((row['URL'], row['TITLE'], str(d)) for row, d in zip(records, dates, strict=True) if d >= oldest)
    else:
        page = Page(body)
        raw = page.meta.get('others','')
        match = re.search(r'页面生成时间 (\d{4}-\d{2}-\d{2})', raw)
        if not match or not oldest <= date.fromisoformat(match[1]) <= observed_date:
            raise ValueError('CSRC homepage date is absent, stale or in the future')
        rows = [(path, title, None) for path, title in page.links if article_url(source, path)]
        if not rows:
            raise ValueError('CSRC homepage contains no recognized article links')
    result = {}
    for link, title, date_text in rows:
        url = article_url(source, link)
        if url and TITLE.search(title):
            previous = result.get(url)
            if previous and normalized(previous['title']) != normalized(title):
                raise ValueError('Conflicting titles for one official URL')
            result[url] = dict(index=source, url=url, title=normalized(title), indexDate=date_text)
    return result


def candidate(body, discovered, receipt, checked):
    page = Page(body)
    from_government = discovered['index'] == 'gov_list'
    title = normalized(page.title.split('__')[0] if from_government else page.meta.get('articletitle',''))
    if title != discovered['title']:
        raise ValueError('Index and article titles differ')
    raw = page.meta.get('firstpublishedtime' if from_government else 'pubdate')
    if not raw:
        raise ValueError('Source publication time missing')
    date_part = raw[:10]
    if discovered['indexDate'] and date_part != discovered['indexDate']:
        raise ValueError('Index and source dates disagree')
    if len(raw) == 10:
        published, precision = raw, 'date'
    elif re.fullmatch(r'\d{4}-\d{2}-\d{2}[ -]\d{2}:\d{2}(?::\d{2})?', raw):
        published, precision = date_part + 'T' + raw[11:] + '+08:00', 'minute' if len(raw) == 16 else 'second'
    else:
        raise ValueError('Unrecognized source publication time')
    timing = dict(published_at=published, published_at_precision=precision, timezone='Asia/Shanghai')
    publication_bound(timing)
    if date.fromisoformat(date_part) > receipt.astimezone(TZ).date():
        raise ValueError('Publication date is after receipt')
    if precision != 'date' and instant(published) > receipt:
        raise ValueError('Publication time is after receipt')
    raw_digest = hashlib.sha256(body).hexdigest()
    return dict(**discovered, **timing, sha256=raw_digest, receivedAt=receipt.isoformat(),
                candidateCheckedAt=checked.isoformat(), featureReadyAt=None, signalEligible=False,
                status='pending_review', revisionKey=hashlib.sha256((discovered['url']+'|'+raw_digest).encode()).hexdigest())
