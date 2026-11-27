"""Admit November 24–26 quotes and event restrictions after the November 23 archive."""
from datetime import date, timedelta
from functools import lru_cache

import nov23_market_data as previous

THROUGH = date(2026, 11, 26)
START = previous.THROUGH + timedelta(days=1)
MARKET = '20261127T1421-close1126'
CONTROL = '20261127T1421-control1126'
DOMESTIC = '20261126T171408-419cfdca-prices'
OFFICIAL = '20261126T171408-419cfdca-official'
SEALS = {
    MARKET: 'b5050581c61d9639dad88df9cb12919c2c88781b10cdd8afc05a77d6cf83f74d',
    CONTROL: '4f6d2f6e33dac118dce2c97458402aca60a1f827dbba4a8bd14ba852ee0b05aa',
    DOMESTIC: '077ab185d2730873482ede411abb976be229910292f94291c10b67ffe383923e',
    OFFICIAL: 'c7d4efae74fff76cbcdeee552bb1721487e222dc617ac300ddfe7697f9d9e321',
}


@lru_cache(maxsize=1)
def admitted():
    records = previous.extension_records(START, THROUGH, MARKET, CONTROL, SEALS)
    return previous.extend(previous, THROUGH, records, DOMESTIC, OFFICIAL, SEALS)
