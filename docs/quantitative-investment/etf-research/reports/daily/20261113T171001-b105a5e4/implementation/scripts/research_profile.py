"""Request-local dataset selection; frozen v1 remains the default for every caller."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache, wraps

FROZEN = 'frozen-2026-10-30'
RECENT = 'verified-2026-11-12'
current = ContextVar('research_profile', default=FROZEN)


@contextmanager
def using(profile):
    if profile not in (FROZEN, RECENT):
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
