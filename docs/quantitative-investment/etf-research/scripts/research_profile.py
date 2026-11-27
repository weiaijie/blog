"""Request-local dataset selection; frozen v1 remains the default for every caller."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache, wraps
from importlib import import_module

FROZEN = 'frozen-2026-10-30'
RECENT = 'verified-2026-11-12'
LATEST = 'verified-2026-11-20'  # Pinned in the November 20 comparison.
NOV23 = 'verified-2026-11-23'
NOV26 = 'verified-2026-11-26'
API_VERSIONS = {RECENT: 'v2', LATEST: 'v3', NOV23: 'v4', NOV26: 'v5'}
DATA_MODULES = {RECENT: 'recent_market_data', LATEST: 'november_market_data', NOV23: 'nov23_market_data',
                NOV26: 'nov26_market_data'}


def data_module(profile):
    try:
        name = DATA_MODULES[profile]
    except KeyError as exc:
        raise ValueError('Unknown verified data version') from exc
    return import_module(name)

current = ContextVar('research_profile', default=FROZEN)


@contextmanager
def using(profile):
    if profile != FROZEN and profile not in API_VERSIONS:
        raise ValueError('Unknown research data version')
    token = current.set(profile)
    try:
        yield
    finally:
        current.reset(token)


def profile_cache(maxsize=8):
    """Include the immutable dataset ID in caches shared by HTTP worker threads."""
    def decorate(fn):
        @lru_cache(maxsize=maxsize)
        def cached(profile, args, kwargs):
            with using(profile):
                return fn(*args, **dict(kwargs))

        @wraps(fn)
        def call(*args, **kwargs):
            return cached(current.get(), args, tuple(sorted(kwargs.items())))
        call.cache_clear = cached.cache_clear
        return call
    return decorate
