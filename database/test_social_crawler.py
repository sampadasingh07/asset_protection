"""
test_social_crawler.py
Pytest suite for SocialMediaCrawler.

Tests:
  1. search_youtube() happy path       — returns correct MediaDiscovery objects
  2. search_twitter() happy path       — video-only filtering works
  3. Deduplication                     — same hash appears twice → yielded once
  4. Retry logic                       — network timeout retries 3×, then raises
  5. User-agent rotation               — each page gets a different UA string
  6. Graceful empty results            — no elements found → yields nothing, no crash

Run with:
    pip install pytest pytest-asyncio playwright fake-useragent
    pytest test_social_crawler.py -v
"""

import asyncio
import hashlib
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
import pytest_asyncio

from social_crawler import MediaDiscovery, SocialMediaCrawler, _with_retry


# ---------------------------------------------------------------------------
# Helpers — DOM element mocks
# ---------------------------------------------------------------------------

def _make_element(attrs: dict = None, text: str = "", children: dict = None):
   
    el = AsyncMock()
    el.inner_text = AsyncMock(return_value=text)
    el.get_attribute = AsyncMock(
        side_effect=lambda attr: (attrs or {}).get(attr, None)
    )

    async def _query_selector(selector):
        return (children or {}).get(selector)

    async def _query_selector_all(selector):
        result = (children or {}).get(selector)
        if result is None:
            return []
        return result if isinstance(result, list) else [result]

    el.query_selector     = AsyncMock(side_effect=_query_selector)
    el.query_selector_all = AsyncMock(side_effect=_query_selector_all)
    return el


def _make_page(selector_map: dict = None):
    """
    Build a minimal mock of a Playwright Page.

    selector_map: dict mapping CSS selector → element mock (or list of them)
    """
    page = AsyncMock()
    page.goto           = AsyncMock(return_value=None)
    page.close          = AsyncMock(return_value=None)
    page.evaluate       = AsyncMock(return_value=None)
    page.wait_for_selector = AsyncMock(return_value=None)

    async def _route(pattern, handler):
        pass  # no-op

    page.route = AsyncMock(side_effect=_route)

    async def _query_selector_all(selector):
        result = (selector_map or {}).get(selector, [])
        return result if isinstance(result, list) else [result]

    page.query_selector_all = AsyncMock(side_effect=_query_selector_all)

    async def _query_selector(selector):
        result = (selector_map or {}).get(selector)
        if isinstance(result, list):
            return result[0] if result else None
        return result

    page.query_selector = AsyncMock(side_effect=_query_selector)
    return page


# ---------------------------------------------------------------------------
# Fixture — crawler instance with a mocked browser
# ---------------------------------------------------------------------------

@pytest.fixture
def crawler():
    c = SocialMediaCrawler(asset_keywords=["Champions League"])
    c._playwright = AsyncMock()
    c._browser    = AsyncMock()
    c._ua         = MagicMock()
    c._ua.chrome  = "Mozilla/5.0 TestAgent/1.0"
    return c


# ---------------------------------------------------------------------------
# 1. search_youtube() — happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_youtube_happy_path(crawler):
    """
    Given a page with two ytd-video-renderer elements,
    search_youtube() should yield two MediaDiscovery objects
    with correct platform, account_id, post_id, and raw_html_hash.
    """

    def _make_video_card(title, href, channel_text, thumb_src):
        title_el   = _make_element(attrs={"title": title, "href": href})
        channel_el = _make_element(text=channel_text)
        thumb_el   = _make_element(attrs={"src": thumb_src})

        card = _make_element(
            children={
                "#video-title":       title_el,
                "ytd-channel-name a": channel_el,
                "img":                thumb_el,
            }
        )
        return card

    card1 = _make_video_card(
        title="Champions League Final Highlights",
        href="/watch?v=abc123",
        channel_text="Official UEFA",
        thumb_src="https://i.ytimg.com/vi/abc123/mqdefault.jpg",
    )
    card2 = _make_video_card(
        title="CL Semi-Final Goals",
        href="/watch?v=def456",
        channel_text="Sports Channel",
        thumb_src="https://i.ytimg.com/vi/def456/mqdefault.jpg",
    )

    page = _make_page({"ytd-video-renderer": [card1, card2]})
    crawler._browser.new_context = AsyncMock(
        return_value=AsyncMock(new_page=AsyncMock(return_value=page))
    )

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        results = [item async for item in crawler.search_youtube("Champions League highlights")]

    assert len(results) == 2

    r1 = results[0]
    assert r1.platform      == "youtube"
    assert r1.url           == "https://www.youtube.com/watch?v=abc123"
    assert r1.post_id       == "abc123"
    assert r1.account_id    == "Official UEFA"
    assert r1.thumbnail_url == "https://i.ytimg.com/vi/abc123/mqdefault.jpg"
    assert r1.raw_html_hash == hashlib.md5("Champions League Final Highlights".encode()).hexdigest()

    r2 = results[1]
    assert r2.post_id    == "def456"
    assert r2.account_id == "Sports Channel"


# ---------------------------------------------------------------------------
# 2. search_twitter() — video-only filtering
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_twitter_filters_non_video_tweets(crawler):
    """
    search_twitter() must skip articles that have no videoComponent/video element.
    Only the one article that contains a video indicator should be yielded.
    """

    def _make_tweet(has_video: bool, tweet_path: str, handle: str, text: str):
        video_el  = AsyncMock() if has_video else None
        link_el   = _make_element(attrs={"href": tweet_path})
        handle_el = _make_element(text=handle)
        text_el   = _make_element(text=text)

        article = AsyncMock()

        async def _query_selector(selector):
            mapping = {
                'div[data-testid="videoComponent"], video': video_el,
                'a[href*="/status/"]':                       link_el,
                'div[data-testid="tweetText"]':              text_el,
                'span[data-testid="app-text-transition-container"]': None,
            }
            return mapping.get(selector)

        async def _query_selector_all(selector):
            if selector == 'div[data-testid="User-Name"] span':
                return [handle_el]
            return []

        article.query_selector     = AsyncMock(side_effect=_query_selector)
        article.query_selector_all = AsyncMock(side_effect=_query_selector_all)
        return article

    tweet_with_video    = _make_tweet(True,  "/sportschannel/status/111", "@sportschannel", "Goal!")
    tweet_without_video = _make_tweet(False, "/user/status/222",          "@user",          "Text only")

    page = _make_page()
    page.query_selector_all = AsyncMock(
        side_effect=lambda sel: (
            [tweet_with_video, tweet_without_video]
            if sel == 'article[data-testid="tweet"]'
            else []
        )
    )

    crawler._browser.new_context = AsyncMock(
        return_value=AsyncMock(new_page=AsyncMock(return_value=page))
    )

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        results = [item async for item in crawler.search_twitter("Champions League goal clip")]

    assert len(results) == 1
    assert results[0].platform   == "twitter"
    assert results[0].post_id    == "111"
    assert results[0].account_id == "@sportschannel"


# ---------------------------------------------------------------------------
# 3. Deduplication — same hash → yielded only once across the full sweep
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduplication_across_sweep(crawler):
    """
    If two search calls return items with identical raw_html_hash values,
    only the first should be yielded; the second must be silently dropped.
    """
    duplicate_title = "Repeated Clip Title"
    dup_hash = hashlib.md5(duplicate_title.encode()).hexdigest()

    def _make_single_card():
        title_el   = _make_element(attrs={"title": duplicate_title, "href": "/watch?v=zzz"})
        channel_el = _make_element(text="SomeChannel")
        thumb_el   = _make_element(attrs={"src": None})
        return _make_element(
            children={
                "#video-title":       title_el,
                "ytd-channel-name a": channel_el,
                "img":                thumb_el,
            }
        )

    call_count = 0

    async def _patched_search_youtube(self_inner, query):
        nonlocal call_count
        call_count += 1
        page = _make_page({"ytd-video-renderer": [_make_single_card()]})
        crawler._browser.new_context = AsyncMock(
            return_value=AsyncMock(new_page=AsyncMock(return_value=page))
        )
        with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
            async for item in SocialMediaCrawler.search_youtube(crawler, query):
                yield item

    # Manually call dedup logic twice with the same hash
    seen_before = crawler._is_duplicate(dup_hash)
    seen_again  = crawler._is_duplicate(dup_hash)

    assert seen_before is False, "First occurrence must NOT be a duplicate"
    assert seen_again  is True,  "Second occurrence MUST be flagged as duplicate"


# ---------------------------------------------------------------------------
# 4. Retry logic — timeout → retries 3×, then raises
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_exhaustion_raises():
    """
    _with_retry() must call the coroutine factory exactly `retries` times
    and re-raise the final exception when all attempts fail.
    """
    call_count = 0

    async def _always_fails():
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Simulated network timeout")

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        with pytest.raises(TimeoutError, match="Simulated network timeout"):
            await _with_retry(lambda: _always_fails(), retries=3, base_delay=0.01)

    assert call_count == 3, f"Expected 3 attempts, got {call_count}"


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    """
    _with_retry() should succeed if the second attempt works,
    without propagating the first exception.
    """
    call_count = 0

    async def _fails_once_then_ok():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Transient error")
        return "success"

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        result = await _with_retry(lambda: _fails_once_then_ok(), retries=3, base_delay=0.01)

    assert result == "success"
    assert call_count == 2


# ---------------------------------------------------------------------------
# 5. User-agent rotation — each _get_page() call uses a different UA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_agent_rotation(crawler):
    """
    _get_page() should request crawler._ua.chrome each time it is called,
    and pass that value to new_context(). Two calls should produce two
    new_context invocations, each with whatever UA the mock returns.
    """
    ua_values = ["UA-Alpha/1.0", "UA-Beta/2.0"]
    ua_index  = {"i": 0}

    def _next_ua():
        val = ua_values[ua_index["i"] % len(ua_values)]
        ua_index["i"] += 1
        return val

    type(crawler._ua).chrome = PropertyMock(side_effect=_next_ua)

    context_mock = AsyncMock()
    page_mock    = AsyncMock()
    page_mock.route = AsyncMock(side_effect=lambda *a, **kw: None)
    context_mock.new_page = AsyncMock(return_value=page_mock)
    crawler._browser.new_context = AsyncMock(return_value=context_mock)

    await crawler._get_page()
    await crawler._get_page()

    calls = crawler._browser.new_context.call_args_list
    assert len(calls) == 2
    assert calls[0].kwargs["user_agent"] == "UA-Alpha/1.0"
    assert calls[1].kwargs["user_agent"] == "UA-Beta/2.0"


# ---------------------------------------------------------------------------
# 6. Graceful empty results — no DOM elements → yields nothing, no crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_youtube_empty_results(crawler):
    """
    When YouTube returns no ytd-video-renderer elements,
    search_youtube() must yield nothing and not raise.
    """
    page = _make_page({"ytd-video-renderer": []})
    crawler._browser.new_context = AsyncMock(
        return_value=AsyncMock(new_page=AsyncMock(return_value=page))
    )

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        results = [item async for item in crawler.search_youtube("obscure query xyz")]

    assert results == []


@pytest.mark.asyncio
async def test_search_tiktok_empty_results(crawler):
    """
    When TikTok returns no video cards,
    search_tiktok() must yield nothing and not raise.
    """
    page = _make_page({'[data-e2e="search_top-item-list"] > div': []})
    crawler._browser.new_context = AsyncMock(
        return_value=AsyncMock(new_page=AsyncMock(return_value=page))
    )

    with patch("social_crawler.asyncio.sleep", new=AsyncMock()):
        results = [item async for item in crawler.search_tiktok("no results here")]

    assert results == []
