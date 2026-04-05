"""
pirate_crawler.py
Tor-proxied pirate site crawler + Telegram channel monitor.
Person 3: Data Engineering & Web Scraping

Enhancements over starter code:
  - _crawl_piratebay()     : scrapes ThePirateBay results including magnet links
  - TorCircuitManager      : renews the Tor circuit every N requests via stem
  - is_relevant()          : rapidfuzz fuzzy-match against asset keywords (threshold > 75)
  - RateLimiter            : token-bucket capped at 30 requests/min, shared across sites
  - run_pirate_sweep()     : wrapped in try/except, failures logged to pirate_errors.log
"""

import asyncio
import hashlib
import logging
import os
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright
from rapidfuzz import fuzz, process
from stem import Signal
from stem.control import Controller
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterVideo

# ---------------------------------------------------------------------------
# Logging — main logger + dedicated error-file logger
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# File logger that writes only WARNING+ to pirate_errors.log
_error_handler = logging.FileHandler("pirate_errors.log")
_error_handler.setLevel(logging.WARNING)
_error_handler.setFormatter(
    logging.Formatter("%(asctime)s  %(levelname)s  %(message)s")
)

_file_logger = logging.getLogger("pirate_crawler.errors")
_file_logger.setLevel(logging.WARNING)
_file_logger.addHandler(_error_handler)
_file_logger.propagate = False   # don't double-print to root logger


# ---------------------------------------------------------------------------
# Data model (unchanged from starter)
# ---------------------------------------------------------------------------

@dataclass
class PirateDiscovery:
    url: str
    site_name: str
    magnet_link: str = None
    video_direct_url: str = None
    file_hash: str = None
    platform: str = "pirate"
    discovered_at: str = None
    title: str = ""          # populated by crawlers; used for is_relevant()


# ---------------------------------------------------------------------------
# Tor circuit renewal
# ---------------------------------------------------------------------------

class TorCircuitManager:
    """
    Renews the Tor exit circuit every `renew_every` requests.

    Requires:
      - Tor running locally on port 9050 (SOCKS) and 9051 (ControlPort)
      - CookieAuthentication or a known password in torrc:
            ControlPort 9051
            CookieAuthentication 1
        OR  HashedControlPassword <hash>

    Usage:
        mgr = TorCircuitManager(renew_every=50)
        mgr.tick()   # call once per outbound request
    """

    TOR_CONTROL_PORT = 9051

    def __init__(self, renew_every: int = 50, password: str = None):
        self.renew_every  = renew_every
        self.password     = password          # None → use cookie auth
        self._count       = 0
        self._last_renew  = datetime.utcnow()

    def tick(self) -> bool:
        """
        Increment the internal counter.  When it crosses `renew_every`,
        send a NEWNYM signal to Tor to obtain a fresh exit circuit.
        Returns True if a renewal was triggered.
        """
        self._count += 1
        if self._count % self.renew_every == 0:
            return self._renew()
        return False

    def _renew(self) -> bool:
        try:
            auth_kwargs = (
                {"password": self.password}
                if self.password
                else {}                         # stem will try cookie auth
            )
            with Controller.from_port(port=self.TOR_CONTROL_PORT) as ctrl:
                ctrl.authenticate(**auth_kwargs)
                ctrl.signal(Signal.NEWNYM)
                # Tor requires a short pause after NEWNYM before the new
                # circuit is actually ready (~1 s is the recommended minimum)
                time.sleep(1.5)
                logger.info(
                    f"Tor circuit renewed after {self._count} requests."
                )
                self._last_renew = datetime.utcnow()
                return True
        except Exception as exc:
            # Circuit renewal failure is non-fatal; log and continue on
            # the existing circuit rather than crashing the whole sweep.
            logger.warning(f"Tor circuit renewal failed: {exc}")
            _file_logger.warning(f"Tor circuit renewal failed: {exc}")
            return False


# ---------------------------------------------------------------------------
# Token-bucket rate limiter (max 30 requests / 60 s)
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Sliding-window rate limiter.

    Tracks the timestamps of the last `max_calls` requests in a deque.
    If the oldest timestamp in the window is less than `period` seconds
    ago, we sleep for the remaining time before allowing the next call.

    Default: 30 requests / 60 seconds across all sites.
    """

    def __init__(self, max_calls: int = 30, period: float = 60.0):
        self.max_calls = max_calls
        self.period    = period
        self._calls: deque = deque()    # stores epoch timestamps

    async def acquire(self):
        """
        Async-safe acquire.  Suspends the coroutine (not the whole thread)
        if the rate limit has been reached.
        """
        now = time.monotonic()

        # Evict timestamps older than the sliding window
        while self._calls and now - self._calls[0] >= self.period:
            self._calls.popleft()

        if len(self._calls) >= self.max_calls:
            # How long until the oldest request falls out of the window
            sleep_for = self.period - (now - self._calls[0]) + 0.05
            logger.debug(f"Rate limit reached. Sleeping {sleep_for:.2f}s")
            await asyncio.sleep(sleep_for)
            # Re-evict after sleeping
            now = time.monotonic()
            while self._calls and now - self._calls[0] >= self.period:
                self._calls.popleft()

        self._calls.append(time.monotonic())


# ---------------------------------------------------------------------------
# Main crawler class
# ---------------------------------------------------------------------------

class PirateSiteCrawler:
    """
    Crawls known pirate streaming sites and torrent aggregators
    through Tor SOCKS5 proxy for anonymity.
    """

    TOR_PROXY = "socks5://127.0.0.1:9050"

    PIRATE_TARGETS = [
        "https://123movies.fm",
        "https://thepiratebay.org/search.php?q={query}",
        "https://1337x.to/search/{query}/1/",
        "https://rarbg.to/torrents.php?search={query}",
    ]

    # Fuzzy-match threshold: 0–100, where 100 = exact match.
    # 75 catches common variants: abbreviations, extra words, slight misspellings.
    RELEVANCE_THRESHOLD = 75

    def __init__(
        self,
        asset_keywords: list,
        tor_renew_every: int = 50,
        tor_password: str = None,
        rate_limit_calls: int = 30,
        rate_limit_period: float = 60.0,
    ):
        self.asset_keywords = asset_keywords
        self._tor           = TorCircuitManager(
                                  renew_every=tor_renew_every,
                                  password=tor_password,
                              )
        self._limiter       = RateLimiter(
                                  max_calls=rate_limit_calls,
                                  period=rate_limit_period,
                              )

    # ------------------------------------------------------------------
    # Relevance check  ← NEW
    # ------------------------------------------------------------------

    def is_relevant(self, title: str) -> bool:
        """
        Return True if `title` fuzzy-matches any asset keyword above
        RELEVANCE_THRESHOLD using rapidfuzz partial_ratio.

        partial_ratio is better than simple ratio here because torrent
        titles are padded with extra tokens like resolution, codec, and
        uploader tags:
            "Champions.League.Final.2024.1080p.BluRay.x264-YIFY"
        partial_ratio scores the best matching *substring*, so the keyword
        "Champions League Final 2024" still scores ~95 against that title.
        """
        if not title:
            return False
        title_lower = title.lower()
        for kw in self.asset_keywords:
            score = fuzz.partial_ratio(kw.lower(), title_lower)
            if score >= self.RELEVANCE_THRESHOLD:
                logger.debug(
                    f"Relevance match: '{kw}' vs '{title[:60]}' → score {score}"
                )
                return True
        return False

    # ------------------------------------------------------------------
    # Internal helper: rate-limit + Tor tick before every page.goto()
    # ------------------------------------------------------------------

    async def _safe_goto(self, page, url: str, **kwargs):
        """Acquire rate-limit slot, tick Tor counter, then navigate."""
        await self._limiter.acquire()
        self._tor.tick()
        await page.goto(url, **kwargs)

    # ------------------------------------------------------------------
    # 1337x crawler (original, now uses _safe_goto + is_relevant)
    # ------------------------------------------------------------------

    async def _crawl_1337x(self, query: str, page) -> list[PirateDiscovery]:
        """Crawl 1337x for torrent listings."""
        results = []
        url = f"https://1337x.to/search/{query.replace(' ', '+')}/1/"

        try:
            await self._safe_goto(page, url, timeout=30_000, wait_until="domcontentloaded")
            rows = await page.query_selector_all("tbody tr")

            for row in rows[:10]:
                try:
                    name_el = await row.query_selector(".coll-1 a:last-child")
                    name    = await name_el.inner_text() if name_el else ""
                    link    = await name_el.get_attribute("href") if name_el else ""

                    if not self.is_relevant(name):
                        continue

                    results.append(PirateDiscovery(
                        url=f"https://1337x.to{link}" if link else "",
                        site_name="1337x",
                        platform="torrent",
                        title=name,
                        discovered_at=datetime.utcnow().isoformat(),
                    ))
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"1337x crawl failed for '{query}': {e}")
            _file_logger.warning(f"1337x crawl failed for '{query}': {e}")

        return results

    # ------------------------------------------------------------------
    # ThePirateBay crawler  ← NEW
    # ------------------------------------------------------------------

    async def _crawl_piratebay(self, query: str, page) -> list[PirateDiscovery]:
        """
        Crawl ThePirateBay search results and extract torrent entries
        including magnet links.

        TPB DOM structure (current as of 2025):
          Table: #searchResult  (or class "table-list")
          Each row: <tr> with cells
            [0] category icon  (skip)
            [1] .detName > .detLink  → title text + href to detail page
                .detName ~ .detDesc  → uploader info
            [2] .seeds
            [3] .leeches
          Magnet link: <a href="magnet:?..."> inside the row

        Note: TPB's layout differs slightly between mirrors; we try both
        the official selector and a fallback table-list selector.
        """
        results = []
        encoded = query.replace(" ", "+")
        url     = f"https://thepiratebay.org/search.php?q={encoded}&cat=200"
        # cat=200 = Video category; filters out software/music noise

        try:
            await self._safe_goto(page, url, timeout=30_000, wait_until="domcontentloaded")
            await asyncio.sleep(1.5)   # TPB renders JS-side on some mirrors

            # Try primary selector, fall back to generic table rows
            rows = await page.query_selector_all("#searchResult tr:not(:first-child)")
            if not rows:
                rows = await page.query_selector_all(".table-list tr:not(:first-child)")

            for row in rows[:15]:
                try:
                    # Title + detail-page link
                    title_el = await row.query_selector(".detLink")
                    if not title_el:
                        title_el = await row.query_selector("a.detLink")
                    title    = await title_el.inner_text() if title_el else ""
                    det_href = await title_el.get_attribute("href") if title_el else ""

                    if not title or not self.is_relevant(title):
                        continue

                    # Magnet link (first <a> whose href starts with "magnet:")
                    magnet_el   = await row.query_selector('a[href^="magnet:"]')
                    magnet_link = await magnet_el.get_attribute("href") if magnet_el else None

                    # Extract info-hash from magnet for file_hash field.
                    # Magnet format: magnet:?xt=urn:btih:HASH&dn=...&tr=...
                    # Split on "?" first to drop the "magnet:" prefix, then
                    # split the query string on "&" to find the xt parameter.
                    file_hash = None
                    if magnet_link and "?" in magnet_link:
                        query_str = magnet_link.split("?", 1)[1]
                        for part in query_str.split("&"):
                            if part.startswith("xt=urn:btih:"):
                                file_hash = part.split(":")[-1].upper()
                                break

                    # Seed / leech counts (useful signal: high seeds = active leak)
                    seed_el  = await row.query_selector(".seeds")
                    leech_el = await row.query_selector(".leeches")
                    seeds    = int((await seed_el.inner_text()).strip() or 0)  if seed_el  else 0
                    leeches  = int((await leech_el.inner_text()).strip() or 0) if leech_el else 0

                    # Build canonical TPB URL
                    if det_href and det_href.startswith("/"):
                        detail_url = f"https://thepiratebay.org{det_href}"
                    elif det_href:
                        detail_url = det_href
                    else:
                        detail_url = url

                    results.append(PirateDiscovery(
                        url=detail_url,
                        site_name="thepiratebay",
                        magnet_link=magnet_link,
                        file_hash=file_hash,
                        platform="torrent",
                        title=title,
                        discovered_at=datetime.utcnow().isoformat(),
                    ))

                    logger.info(
                        f"TPB hit: '{title[:60]}' | seeds={seeds} | "
                        f"hash={file_hash or 'n/a'}"
                    )

                except Exception as e:
                    logger.debug(f"TPB row parse error: {e}")

        except Exception as e:
            logger.warning(f"ThePirateBay crawl failed for '{query}': {e}")
            _file_logger.warning(f"ThePirateBay crawl failed for '{query}': {e}")

        return results

    # ------------------------------------------------------------------
    # Full sweep (now includes TPB, rate-limiting, Tor renewal, try/except)
    # ------------------------------------------------------------------

    async def run_pirate_sweep(self) -> list[PirateDiscovery]:
        """
        Run sweep across all pirate sites through Tor proxy.

        Changes from starter:
          - Includes ThePirateBay via _crawl_piratebay()
          - Every page.goto() goes through _safe_goto() for rate-limiting
            and Tor circuit tick
          - Entire method wrapped in try/except; all failures written to
            pirate_errors.log so a single broken site never kills the sweep
          - Returns whatever was collected even if the sweep is interrupted
        """
        all_results: list[PirateDiscovery] = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    proxy={"server": self.TOR_PROXY},
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )

                try:
                    page = await browser.new_page()

                    for keyword in self.asset_keywords:
                        query_variants = [
                            keyword,
                            f"{keyword} full match",
                            f"{keyword} highlights",
                        ]
                        for query in query_variants:
                            logger.info(f"Pirate sweep: query='{query}'")

                            # 1337x
                            try:
                                hits = await self._crawl_1337x(query, page)
                                all_results.extend(hits)
                                logger.info(
                                    f"1337x → {len(hits)} relevant results for '{query}'"
                                )
                            except Exception as exc:
                                _file_logger.error(
                                    f"1337x sweep error | query='{query}' | {exc}"
                                )
                                logger.error(f"1337x sweep error for '{query}': {exc}")

                            await asyncio.sleep(2)

                            # ThePirateBay
                            try:
                                hits = await self._crawl_piratebay(query, page)
                                all_results.extend(hits)
                                logger.info(
                                    f"TPB → {len(hits)} relevant results for '{query}'"
                                )
                            except Exception as exc:
                                _file_logger.error(
                                    f"TPB sweep error | query='{query}' | {exc}"
                                )
                                logger.error(f"TPB sweep error for '{query}': {exc}")

                            await asyncio.sleep(2)

                finally:
                    await browser.close()

        except Exception as exc:
            # Top-level catch: browser launch failure, Tor unreachable, etc.
            _file_logger.critical(
                f"run_pirate_sweep() crashed before completing: {exc}"
            )
            logger.critical(f"Pirate sweep aborted: {exc}")

        logger.info(
            f"Pirate sweep finished. {len(all_results)} total relevant discoveries."
        )
        return all_results


# ---------------------------------------------------------------------------
# TelegramChannelMonitor (unchanged from starter — kept for completeness)
# ---------------------------------------------------------------------------

class TelegramChannelMonitor:
    """
    Monitors Telegram channels and groups for pirated sports content.
    Uses Telethon MTProto API — requires Telegram API credentials.

    Setup: Get API ID/hash from https://my.telegram.org
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str = "dap_monitor",
        channels_to_monitor: list = None,
    ):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.channels = channels_to_monitor or []
        self.discovered_items = []

    async def start(self):
        await self.client.start()
        logger.info("Telegram client started")

    async def search_channel(
        self, channel_identifier: str, query: str, max_results: int = 50
    ) -> list:
        """Search a Telegram channel for matching content."""
        results = []
        try:
            entity = await self.client.get_entity(channel_identifier)
            messages = await self.client(
                SearchRequest(
                    peer=entity,
                    q=query,
                    filter=InputMessagesFilterVideo(),
                    min_date=None,
                    max_date=None,
                    offset_id=0,
                    add_offset=0,
                    limit=max_results,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )

            for msg in messages.messages:
                if hasattr(msg, "media") and msg.media:
                    results.append({
                        "channel":    channel_identifier,
                        "message_id": msg.id,
                        "date":       msg.date.isoformat(),
                        "text":       msg.message or "",
                        "has_video":  True,
                        "views":      getattr(msg, "views", 0),
                        "platform":   "telegram",
                    })
        except Exception as e:
            logger.error(f"Telegram search error for {channel_identifier}: {e}")

        return results

    def register_realtime_handler(self, asset_keywords: list, callback):
        """Register real-time message handler for live monitoring."""
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            message_text = event.message.message or ""
            if any(kw.lower() in message_text.lower() for kw in asset_keywords):
                if event.message.media:
                    await callback({
                        "event":      "telegram_match",
                        "channel":    str(event.chat_id),
                        "message_id": event.message.id,
                        "text":       message_text,
                        "date":       event.message.date.isoformat(),
                    })

    async def run(self):
        await self.client.run_until_disconnected()
