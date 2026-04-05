

import asyncio
import hashlib
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, AsyncGenerator, Set

from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Browser, Page
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

async def _with_retry(coro_fn, retries: int = 3, base_delay: float = 2.0):
    """
    Calls an async coroutine-factory `coro_fn` (a zero-arg lambda returning a coroutine)
    up to `retries` times, using exponential backoff with ±20 % jitter.

    Usage:
        result = await _with_retry(lambda: some_async_fn(arg1, arg2))
    """
    last_exc = None
    for attempt in range(retries):
        try:
            return await coro_fn()
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                delay = base_delay * (2 ** attempt) * random.uniform(0.8, 1.2)
                logger.warning(
                    f"Attempt {attempt + 1}/{retries} failed ({exc}). "
                    f"Retrying in {delay:.1f}s…"
                )
                await asyncio.sleep(delay)
    raise last_exc


# ---------------------------------------------------------------------------
# Data model (unchanged from starter)
# ---------------------------------------------------------------------------

@dataclass
class MediaDiscovery:
    url: str
    media_url: str
    platform: str
    account_id: str
    post_id: str
    thumbnail_url: Optional[str]
    duration_seconds: Optional[float]
    view_count: Optional[int]
    discovered_at: str
    raw_html_hash: str


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------

class SocialMediaCrawler:
    """
    Headless browser crawler for social media platforms.
    Detects video/image content matching our fingerprint database.
    Uses rotating user-agents and proxy support.
    """

    SEARCH_TERMS = [
        "match highlights",
        "goal clip",
        "sports replay",
        "full match",
        "official broadcast",
    ]

    PLATFORMS = {
        "twitter": "https://twitter.com/search?q={query}&f=video&src=typed_query",
        "tiktok":  "https://www.tiktok.com/search?q={query}",
        "youtube": "https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%3D%3D",
    }

    # Maximum results harvested per platform per query
    _YT_MAX    = 20
    _TIKTOK_MAX = 15
    _TW_MAX    = 20

    def __init__(self, asset_keywords: list, proxy_url: str = None):
        self.asset_keywords = asset_keywords
        self.proxy_url = proxy_url
        self._browser: Optional[Browser] = None
        self._ua = UserAgent()                      # rotating user-agent pool
        self._seen_hashes: Set[str] = set()         # dedup across the whole sweep

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        self._playwright = await async_playwright().start()
        kwargs = {"headless": True}
        if self.proxy_url:
            kwargs["proxy"] = {"server": self.proxy_url}
        self._browser = await self._playwright.chromium.launch(**kwargs)
        logger.info("Playwright browser started")

    async def stop(self):
        if self._browser:
            await self._browser.close()
        await self._playwright.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _random_ua(self) -> str:
        """Return a random Chrome-family user-agent string."""
        try:
            return self._ua.chrome
        except Exception:
            # Fallback if fake-useragent cache is stale
            return (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

    async def _get_page(self, user_agent: str = None) -> Page:
        context = await self._browser.new_context(
            user_agent=user_agent or self._random_ua(),
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True,
        )
        page = await context.new_page()
        # Block images and fonts to speed up crawling (allow media URLs through)
        await page.route(
            "**/*.{png,jpg,jpeg,gif,webp,woff,woff2}",
            lambda route: (
                route.abort()
                if "media" not in route.request.url
                else route.continue_()
            ),
        )
        return page

    def _is_duplicate(self, raw_html_hash: str) -> bool:
        """Return True if this hash was already seen; otherwise register it."""
        if raw_html_hash in self._seen_hashes:
            return True
        self._seen_hashes.add(raw_html_hash)
        return False

    # ------------------------------------------------------------------
    # YouTube (original, wrapped with retry + dedup)
    # ------------------------------------------------------------------

    async def search_youtube(self, query: str) -> AsyncGenerator[MediaDiscovery, None]:
        """Scrape YouTube search results for video matches (3-retry, dedup)."""

        async def _do_search():
            page = await self._get_page()
            url = self.PLATFORMS["youtube"].format(query=query.replace(" ", "+"))
            results = []

            try:
                await page.goto(url, wait_until="networkidle", timeout=30_000)
                await asyncio.sleep(2)

                video_elements = await page.query_selector_all("ytd-video-renderer")

                for elem in video_elements[: self._YT_MAX]:
                    try:
                        title_el = await elem.query_selector("#video-title")
                        title = await title_el.get_attribute("title") if title_el else ""
                        href  = await title_el.get_attribute("href")  if title_el else ""
                        video_url = f"https://www.youtube.com{href}" if href else ""

                        channel_el = await elem.query_selector("ytd-channel-name a")
                        channel    = await channel_el.inner_text() if channel_el else "unknown"

                        thumbnail_el = await elem.query_selector("img")
                        thumbnail    = await thumbnail_el.get_attribute("src") if thumbnail_el else None

                        if video_url:
                            raw_hash = hashlib.md5(title.encode()).hexdigest()
                            results.append(
                                MediaDiscovery(
                                    url=video_url,
                                    media_url=video_url,
                                    platform="youtube",
                                    account_id=channel.strip(),
                                    post_id=href.split("v=")[-1].split("&")[0] if "v=" in href else "",
                                    thumbnail_url=thumbnail,
                                    duration_seconds=None,
                                    view_count=None,
                                    discovered_at=datetime.utcnow().isoformat(),
                                    raw_html_hash=raw_hash,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Failed to parse YouTube video element: {e}")
            finally:
                await page.close()

            return results

        items = await _with_retry(_do_search)
        for item in items:
            if not self._is_duplicate(item.raw_html_hash):
                yield item

    # ------------------------------------------------------------------
    # TikTok (original, wrapped with retry + dedup)
    # ------------------------------------------------------------------

    async def search_tiktok(self, query: str) -> AsyncGenerator[MediaDiscovery, None]:
        """Scrape TikTok search results (3-retry, dedup)."""

        async def _do_search():
            page = await self._get_page()
            url = self.PLATFORMS["tiktok"].format(query=query.replace(" ", "%20"))
            results = []

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await asyncio.sleep(3)

                video_cards = await page.query_selector_all(
                    '[data-e2e="search_top-item-list"] > div'
                )

                for card in video_cards[: self._TIKTOK_MAX]:
                    try:
                        link = await card.query_selector("a")
                        href = await link.get_attribute("href") if link else ""
                        video_url = (
                            f"https://www.tiktok.com{href}"
                            if href and href.startswith("/")
                            else href
                        )
                        author = (
                            href.split("@")[1].split("/")[0]
                            if href and "@" in href
                            else "unknown"
                        )

                        if video_url:
                            raw_hash = hashlib.md5(href.encode()).hexdigest()
                            results.append(
                                MediaDiscovery(
                                    url=video_url,
                                    media_url=video_url,
                                    platform="tiktok",
                                    account_id=f"@{author}",
                                    post_id=href.split("/")[-1] if href else "",
                                    thumbnail_url=None,
                                    duration_seconds=None,
                                    view_count=None,
                                    discovered_at=datetime.utcnow().isoformat(),
                                    raw_html_hash=raw_hash,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"TikTok parse error: {e}")
            finally:
                await page.close()

            return results

        items = await _with_retry(_do_search)
        for item in items:
            if not self._is_duplicate(item.raw_html_hash):
                yield item

    # ------------------------------------------------------------------
    # Twitter/X  ← NEW
    # ------------------------------------------------------------------

    async def search_twitter(self, query: str) -> AsyncGenerator[MediaDiscovery, None]:
        """
        Scrape Twitter/X video search results (3-retry, dedup).

        Twitter renders its feed via React, so we wait for the tweet article
        elements to appear after a short settle delay. We filter to only
        tweets that contain a video card by checking for the presence of
        a <video> or the native-video wrapper div.

        Selector notes (verified against Twitter's current DOM, April 2025):
          - Article container : article[data-testid="tweet"]
          - Tweet permalink   : a[href*="/status/"] (first match per article)
          - User handle       : div[data-testid="User-Name"] span starting with "@"
          - Video indicator   : div[data-testid="videoComponent"] or <video>
        """

        async def _do_search():
            # Twitter requires a logged-in-looking UA; use a realistic Chrome UA
            ua = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.6261.112 Safari/537.36"
            )
            page = await self._get_page(user_agent=ua)
            encoded_query = query.replace(" ", "%20").replace("#", "%23")
            url = self.PLATFORMS["twitter"].format(query=encoded_query)
            results = []

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)

                # Wait for at least one tweet article to render
                try:
                    await page.wait_for_selector(
                        'article[data-testid="tweet"]', timeout=15_000
                    )
                except Exception:
                    logger.warning(f"Twitter: no tweet articles found for query='{query}'")
                    return results

                # Scroll once to trigger lazy loading
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)

                articles = await page.query_selector_all('article[data-testid="tweet"]')

                for article in articles[: self._TW_MAX]:
                    try:
                        # Only process tweets that visibly contain a video component
                        video_indicator = await article.query_selector(
                            'div[data-testid="videoComponent"], video'
                        )
                        if not video_indicator:
                            continue

                        # Tweet permalink (e.g. /username/status/1234567890)
                        link_el = await article.query_selector('a[href*="/status/"]')
                        tweet_path = (
                            await link_el.get_attribute("href") if link_el else ""
                        )
                        tweet_url = (
                            f"https://twitter.com{tweet_path}" if tweet_path else ""
                        )
                        tweet_id = tweet_path.split("/status/")[-1].split("?")[0] if tweet_path else ""

                        # Author handle: look for a span that starts with "@"
                        handle_spans = await article.query_selector_all(
                            'div[data-testid="User-Name"] span'
                        )
                        account_id = "unknown"
                        for span in handle_spans:
                            text = (await span.inner_text()).strip()
                            if text.startswith("@"):
                                account_id = text
                                break

                        # Tweet text (used as the dedup key)
                        text_el = await article.query_selector(
                            'div[data-testid="tweetText"]'
                        )
                        tweet_text = await text_el.inner_text() if text_el else tweet_id

                        # View count (aria-label on the view stat group, optional)
                        view_count = None
                        view_el = await article.query_selector(
                            'span[data-testid="app-text-transition-container"]'
                        )
                        if view_el:
                            raw_views = (await view_el.inner_text()).strip().replace(",", "")
                            try:
                                view_count = int(raw_views)
                            except ValueError:
                                pass

                        if tweet_url:
                            raw_hash = hashlib.md5(tweet_url.encode()).hexdigest()
                            results.append(
                                MediaDiscovery(
                                    url=tweet_url,
                                    media_url=tweet_url,
                                    platform="twitter",
                                    account_id=account_id,
                                    post_id=tweet_id,
                                    thumbnail_url=None,
                                    duration_seconds=None,
                                    view_count=view_count,
                                    discovered_at=datetime.utcnow().isoformat(),
                                    raw_html_hash=raw_hash,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Twitter: failed to parse article: {e}")

            finally:
                await page.close()

            return results

        items = await _with_retry(_do_search)
        for item in items:
            if not self._is_duplicate(item.raw_html_hash):
                yield item

    # ------------------------------------------------------------------
    # Full sweep (now includes Twitter)
    # ------------------------------------------------------------------

    async def run_full_sweep(self) -> list:
        """
        Run a complete sweep across all platforms and keywords.
        Deduplication is shared across the entire sweep via self._seen_hashes.
        """
        all_discoveries = []
        for keyword in self.asset_keywords:
            for term in self.SEARCH_TERMS:
                query = f"{keyword} {term}"
                logger.info(f"Searching: '{query}'")

                async for disc in self.search_youtube(query):
                    all_discoveries.append(disc)

                async for disc in self.search_tiktok(query):
                    all_discoveries.append(disc)

                async for disc in self.search_twitter(query):
                    all_discoveries.append(disc)

                await asyncio.sleep(1.5)  # polite delay between platform groups

        logger.info(f"Sweep complete. {len(all_discoveries)} unique discoveries.")
        return all_discoveries
