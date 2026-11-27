"""Read-only policy and market research samples. The replay engines use separate inputs."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from etf_research.policy_events import instant, select_as_of

REPORT = Path(__file__).resolve().parents[1] / 'reports/2026-11-27-policy-pilot'
VERSION = 'policy-pilot-2026-11-27'
EXPECTED_SHA256 = {
    'events.json': '42e963f2b1dbf5e7face7fffee047db20b810ac3f82a5e152198458370ad3445',
    'etf-flow.json': 'ba99fd5861757ec4ccd75be0d876be449ac3293a4417561ba180f6ff12c16599',
    'market-state.json': '9b49db92d67eb94737abf30e6f840e6cd689d4fe3b7144afe973a5f40394b22f',
}


def decision_time(value):
    try:
        return instant(value).isoformat()
    except ValueError as error:
        raise ValueError('决策时间须为带时区的 ISO 8601 时间。') from error


@lru_cache(maxsize=1)
def report():
    data = {}
    for field, name in [('policy','events.json'), ('etf','etf-flow.json'), ('market','market-state.json')]:
        raw = (REPORT/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256[name]:
            raise ValueError('Policy pilot source file changed: '+name)
        data[field] = json.loads(raw)
    return dict(schemaVersion=1, version=VERSION, scope='read_only_research', **data)


def as_of(cutoff):
    return dict(schemaVersion=1, version=VERSION, decisionAt=cutoff,
                events=select_as_of(report()['policy'], cutoff))
