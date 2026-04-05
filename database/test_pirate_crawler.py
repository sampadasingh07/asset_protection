"""
test_pirate_crawler.py
Pytest suite for PirateSiteCrawler enhancements.

Tests:
  1. _crawl_piratebay()   — extracts title, magnet link, info-hash, detail URL
  2. _crawl_piratebay()   — irrelevant rows are filtered out by is_relevant()
  3. is_relevant()        — above-threshold keywords match; below-threshold don't
  4. TorCircuitManager    — renew() is called after every `renew_every` ticks
  5. RateLimiter          — 31st call in 60 s window triggers a sleep
  6. run_pirate_sweep()   — browser crash is caught; partial results returned;
                            error written to pirate_errors.log
  7. _crawl_1337x()       — irrelevant rows are filtered; relevant rows returned

Run with:
    pip install pytest pytest-asyncio rapidfuzz stem
    pytest test_pirate_crawler.py -v
"""

import asyncio
import os
import time
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

from pirate_crawler import (
    PirateDiscovery,
    PirateSiteCrawler,
    RateLimiter,
    TorCircuitManager,
)


# ---------------------------------------------------------------------------
# Helpers — build minimal Playwright element / page mocks
# ---------------------------------------------------------------------------

def _el(text: str = "", attrs: dict = None, children: dict = None):
    el = AsyncMock()
    el.inner_text    = AsyncMock(return_value=text)
    el.get_attribute = AsyncMock(side_effect=lambda a: (attrs or {}).get(a))

    async def _qs(sel):
        return (children or {}).get(sel)

    async def _qsa(sel):
        v = (children or {}).get(sel, [])
        return v if isinstance(v, list) else [v]

    el.query_selector     = AsyncMock(side_effect=_qs)
    el.query_selector_all = AsyncMock(side_effect=_qsa)
    return el


def _page(selector_map: dict = None):
    pg = AsyncMock()
    pg.goto  = AsyncMock(return_value=None)
    pg.close = AsyncMock(return_value=None)

    async def _qsa(sel):
        v = (selector_map or {}).get(sel, [])
        return v if isinstance(v, list) else [v]

    async def _qs(sel):
        v = (selector_map or {}).get(sel)
        return (v[0] if isinstance(v, list) and v else v)

    pg.query_selector     = AsyncMock(side_effect=_qs)
    pg.query_selector_all = AsyncMock(side_effect=_qsa)
    return pg


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def crawler():
    c = PirateSiteCrawler(
        asset_keywords=["Champions League", "UEFA Final"],
        tor_renew_every=50,
        rate_limit_calls=30,
        rate_limit_period=60.0,
    )
    return c


# ---------------------------------------------------------------------------
# 1. _crawl_piratebay() happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_piratebay_extracts_fields(crawler):
    """
    Given one valid TPB row with a title that matches an asset keyword,
    _crawl_piratebay() should return one PirateDiscovery with the
    correct url, magnet_link, file_hash, site_name, and title.
    """
    fake_hash    = "AABBCCDD" * 5          # 40-char hex info-hash
    magnet_href  = f"magnet:?xt=urn:btih:{fake_hash}&dn=Champions+League+Final"
    detail_href  = "/torrent/123456/Champions-League-Final-2024"

    title_el  = _el(text="Champions League Final 2024 1080p", attrs={"href": detail_href})
    magnet_el = _el(attrs={"href": magnet_href})
    seed_el   = _el(text="412")
    leech_el  = _el(text="38")

    row = _el(children={
        ".detLink":           title_el,
        'a[href^="magnet:"]': magnet_el,
        ".seeds":             seed_el,
        ".leeches":           leech_el,
    })

    page = _page({"#searchResult tr:not(:first-child)": [row]})

    with patch.object(crawler, "_safe_goto", new=AsyncMock()), \
         patch("pirate_crawler.asyncio.sleep", new=AsyncMock()):
        results = await crawler._crawl_piratebay("Champions League Final", page)

    assert len(results) == 1
    r = results[0]
    assert r.site_name   == "thepiratebay"
    assert r.platform    == "torrent"
    assert r.magnet_link == magnet_href
    assert r.file_hash   == fake_hash.upper()
    assert "Champions League" in r.title
    assert r.url         == f"https://thepiratebay.org{detail_href}"


# ---------------------------------------------------------------------------
# 2. _crawl_piratebay() — irrelevant rows filtered out
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_piratebay_filters_irrelevant_rows(crawler):
    """
    Rows whose titles don't fuzzy-match any asset keyword above the threshold
    must not appear in the results.
    """
    irrelevant_title_el = _el(
        text="Random Cooking Show S01E01 720p",
        attrs={"href": "/torrent/999/Random-Cooking-Show"}
    )
    irrelevant_row = _el(children={
        ".detLink":           irrelevant_title_el,
        'a[href^="magnet:"]': None,
        ".seeds":             _el(text="5"),
        ".leeches":           _el(text="1"),
    })

    page = _page({"#searchResult tr:not(:first-child)": [irrelevant_row]})

    with patch.object(crawler, "_safe_goto", new=AsyncMock()), \
         patch("pirate_crawler.asyncio.sleep", new=AsyncMock()):
        results = await crawler._crawl_piratebay("Champions League", page)

    assert results == [], "Irrelevant titles must be filtered out"


# ---------------------------------------------------------------------------
# 3. is_relevant() — fuzzy-matching thresholds
# ---------------------------------------------------------------------------

def test_is_relevant_matches_above_threshold(crawler):
    assert crawler.is_relevant("Champions.League.Final.2024.1080p.BluRay.x264-YIFY") is True
    assert crawler.is_relevant("UEFA Final 2024 Full Match HD")                       is True
    # Slight misspelling / abbreviation should still pass partial_ratio ≥ 75
    assert crawler.is_relevant("Champins League Final Highlights")                    is True


def test_is_relevant_rejects_below_threshold(crawler):
    assert crawler.is_relevant("Fast and Furious 9 Extended Cut 4K")  is False
    assert crawler.is_relevant("Random TV Show S03E05 WEB-DL")        is False
    assert crawler.is_relevant("")                                     is False


def test_is_relevant_case_insensitive(crawler):
    assert crawler.is_relevant("CHAMPIONS LEAGUE SEMI FINAL") is True
    assert crawler.is_relevant("champions league semi final") is True


# ---------------------------------------------------------------------------
# 4. TorCircuitManager — renews exactly at multiples of renew_every
# ---------------------------------------------------------------------------

def test_tor_circuit_renews_at_interval():
    """
    _renew() must be called exactly once after `renew_every` ticks,
    not before, and again after 2×renew_every ticks.
    """
    mgr = TorCircuitManager(renew_every=3, password="test")

    with patch.object(mgr, "_renew", return_value=True) as mock_renew:
        mgr.tick()   # count = 1 → no renewal
        mgr.tick()   # count = 2 → no renewal
        mgr.tick()   # count = 3 → RENEWAL
        mgr.tick()   # count = 4 → no renewal
        mgr.tick()   # count = 5 → no renewal
        mgr.tick()   # count = 6 → RENEWAL

    assert mock_renew.call_count == 2


def test_tor_circuit_renewal_failure_is_non_fatal():
    """
    A failure inside _renew() (e.g. Tor not running) must not raise —
    it should log a warning and return False.
    """
    mgr = TorCircuitManager(renew_every=1, password="wrong")

    with patch("pirate_crawler.Controller") as mock_ctrl_cls:
        mock_ctrl_cls.from_port.side_effect = ConnectionRefusedError("Tor not running")
        result = mgr._renew()

    assert result is False   # non-fatal: returns False, doesn't raise


# ---------------------------------------------------------------------------
# 5. RateLimiter — 31st call triggers sleep
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_rate_limiter_blocks_on_31st_call():
    """
    After 30 calls within a 60-second window, the 31st call must
    await asyncio.sleep (i.e. block until the window rolls over).
    """
    limiter = RateLimiter(max_calls=30, period=60.0)

    # Pre-fill the window with 30 fake timestamps set to "just now"
    now = time.monotonic()
    limiter._calls = deque([now] * 30)

    sleep_calls = []

    async def _fake_sleep(duration):
        sleep_calls.append(duration)

    with patch("pirate_crawler.asyncio.sleep", side_effect=_fake_sleep):
        await limiter.acquire()   # this is the 31st call

    assert len(sleep_calls) == 1, "Expected exactly one sleep call on the 31st request"
    assert sleep_calls[0] > 0,   "Sleep duration must be positive"


@pytest.mark.asyncio
async def test_rate_limiter_does_not_block_under_limit():
    """
    Fewer than max_calls requests must pass through without any sleep.
    """
    limiter = RateLimiter(max_calls=30, period=60.0)
    sleep_calls = []

    async def _fake_sleep(d):
        sleep_calls.append(d)

    with patch("pirate_crawler.asyncio.sleep", side_effect=_fake_sleep):
        for _ in range(5):
            await limiter.acquire()

    assert sleep_calls == [], "No sleep should occur under the rate limit"


# ---------------------------------------------------------------------------
# 6. run_pirate_sweep() — crash is caught; log written; partial results returned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_pirate_sweep_handles_browser_crash(tmp_path, crawler, monkeypatch):
    """
    If the browser crashes mid-sweep, run_pirate_sweep() must:
      - catch the exception (not propagate it)
      - write an entry to pirate_errors.log
      - return whatever partial results were collected (empty list here)
    """
    # Redirect the error log to a temp file so we can inspect it
    log_path = tmp_path / "pirate_errors.log"
    import logging
    file_logger = logging.getLogger("pirate_crawler.errors")
    for h in list(file_logger.handlers):
        file_logger.removeHandler(h)
    handler = logging.FileHandler(str(log_path))
    handler.setLevel(logging.WARNING)
    file_logger.addHandler(handler)

    # Simulate a browser launch failure
    mock_playwright = AsyncMock()
    mock_playwright.__aenter__ = AsyncMock(side_effect=OSError("Chromium not found"))
    mock_playwright.__aexit__  = AsyncMock(return_value=False)

    with patch("pirate_crawler.async_playwright", return_value=mock_playwright):
        results = await crawler.run_pirate_sweep()

    assert isinstance(results, list), "Must always return a list"

    handler.flush()
    log_contents = log_path.read_text()
    assert "crashed" in log_contents or "Chromium" in log_contents, (
        "Error must be written to pirate_errors.log"
    )


# ---------------------------------------------------------------------------
# 7. _crawl_1337x() — relevant + irrelevant rows together
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawl_1337x_filters_irrelevant(crawler):
    """
    _crawl_1337x() must return only the row whose title matches
    an asset keyword, and skip rows that don't match.
    """
    def _make_row(title, href):
        name_el = _el(text=title, attrs={"href": href})
        row = _el(children={".coll-1 a:last-child": name_el})
        return row

    relevant_row   = _make_row("Champions League Final 720p", "/torrent/111/cl-final")
    irrelevant_row = _make_row("Spider-Man No Way Home 4K",   "/torrent/222/spider")

    page = _page({"tbody tr": [relevant_row, irrelevant_row]})

    with patch.object(crawler, "_safe_goto", new=AsyncMock()):
        results = await crawler._crawl_1337x("Champions League", page)

    assert len(results) == 1
    assert "Champions" in results[0].title
    assert results[0].site_name == "1337x"
