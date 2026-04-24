"""
TelegramChannelMonitor — Module 3B
Detects pirated sports content across Telegram channels.

Features:
  - scan_all_channels()     : loops all configured channels
  - Keyword scoring         : score = matched_keywords / total_keywords, threshold > 0.5
  - Video clip download     : first 30s saved to /tmp/telegram_clips/ via Telethon
  - Redis persistence       : processed message IDs stored in "telegram:processed"
  - send_alert_on_match()   : POSTs discovery to internal matches API
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import redis.asyncio as aioredis
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaDocument, MessageMediaPhoto

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLIP_DIR = Path("/tmp/telegram_clips")
REDIS_SET_KEY = "telegram:processed"
MATCHES_API_URL = os.getenv("MATCHES_API_URL", "http://api:8000/api/v1/matches")
KEYWORD_SCORE_THRESHOLD = 0.5

# How many seconds of video to keep (approximate — we trim after download)
CLIP_SECONDS = 30


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


class TelegramChannelMonitor:
    """
    Monitors a list of Telegram channels for pirated sports content.

    Parameters
    ----------
    client      : Authenticated Telethon TelegramClient
    channels    : List of channel usernames or invite links, e.g. ["@sports_leaks"]
    assets      : List of asset dicts, each with at minimum:
                    {"id": str, "keywords": [str, ...]}
    redis_url   : Redis connection URL, default "redis://localhost:6379"
    """

    def __init__(
        self,
        client: TelegramClient,
        channels: list[str],
        assets: list[dict[str, Any]],
        redis_url: str = "redis://localhost:6379",
    ) -> None:
        self.client = client
        self.channels = channels
        self.assets = assets
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

        CLIP_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self._redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def _is_processed(self, message_id: str) -> bool:
        r = await self._get_redis()
        return await r.sismember(REDIS_SET_KEY, message_id)

    async def _mark_processed(self, message_id: str) -> None:
        r = await self._get_redis()
        await r.sadd(REDIS_SET_KEY, message_id)

    # ------------------------------------------------------------------
    # Keyword scoring
    # ------------------------------------------------------------------

    def _score_message(self, text: str, asset: dict[str, Any]) -> float:
        """
        Returns matched_keywords / total_keywords for the given asset.
        Score is in [0.0, 1.0]. Returns 0.0 if the asset has no keywords.
        """
        keywords: list[str] = asset.get("keywords", [])
        if not keywords:
            return 0.0
        text_lower = text.lower()
        matched = sum(1 for kw in keywords if kw.lower() in text_lower)
        return matched / len(keywords)

    def _best_asset_match(
        self, text: str
    ) -> tuple[dict[str, Any] | None, float]:
        """
        Returns the asset with the highest keyword score and that score.
        Returns (None, 0.0) if no asset exceeds the threshold.
        """
        best_asset: dict[str, Any] | None = None
        best_score = 0.0
        for asset in self.assets:
            score = self._score_message(text, asset)
            if score > best_score:
                best_score = score
                best_asset = asset
        if best_score > KEYWORD_SCORE_THRESHOLD:
            return best_asset, best_score
        return None, 0.0

    # ------------------------------------------------------------------
    # Video download
    # ------------------------------------------------------------------

    async def _download_clip(
        self, message: Message, channel_id: str
    ) -> Path | None:
        """
        Downloads media attached to *message* into CLIP_DIR.
        Returns the local Path on success, or None if no downloadable media.

        Note: Telethon streams the full file; for very large videos you may
        want to cancel after CLIP_SECONDS using a size/offset heuristic or a
        separate ffmpeg trim step (not included here to avoid a hard ffmpeg
        dependency, but the hook is left in _trim_clip below).
        """
        media = message.media
        if not isinstance(media, (MessageMediaDocument, MessageMediaPhoto)):
            return None

        filename = f"{channel_id}_{message.id}.mp4"
        dest = CLIP_DIR / filename

        try:
            await self.client.download_media(
                message,
                file=str(dest),
            )
            logger.info("Downloaded clip → %s", dest)
            # Optional post-download trim (requires ffmpeg on PATH)
            await self._trim_clip(dest)
            return dest
        except Exception as exc:
            logger.warning("Failed to download media for msg %s: %s", message.id, exc)
            return None

    @staticmethod
    async def _trim_clip(path: Path) -> None:
        """
        Trims the clip at *path* to CLIP_SECONDS using ffmpeg (if available).
        Silently skips if ffmpeg is not installed.
        """
        try:
            trimmed = path.with_stem(path.stem + "_trimmed")
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y",
                "-i", str(path),
                "-t", str(CLIP_SECONDS),
                "-c", "copy",
                str(trimmed),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if trimmed.exists():
                path.unlink(missing_ok=True)
                trimmed.rename(path)
                logger.info("Trimmed clip to %ds → %s", CLIP_SECONDS, path)
        except FileNotFoundError:
            pass  # ffmpeg not available — keep full file

    # ------------------------------------------------------------------
    # Alert
    # ------------------------------------------------------------------

    async def send_alert_on_match(
        self,
        asset_id: str | None,
        channel: str,
        message_id: int,
        morph_score: float,
    ) -> None:
        """
        POSTs a match discovery to the internal API.
        """
        payload = {
            "asset_id": asset_id,
            "platform": "telegram",
            "url": f"https://t.me/{channel.lstrip('@')}/{message_id}",
            "account_id": channel,
            "morph_score": morph_score,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                response = await http.post(MATCHES_API_URL, json=payload)
                response.raise_for_status()
                logger.info(
                    "Alert sent for msg %s in %s (HTTP %s)",
                    message_id, channel, response.status_code,
                )
        except httpx.HTTPStatusError as exc:
            logger.error("API rejected alert: %s — %s", exc.response.status_code, exc.response.text)
        except httpx.RequestError as exc:
            logger.error("Could not reach matches API: %s", exc)

    # ------------------------------------------------------------------
    # Channel search
    # ------------------------------------------------------------------

    async def search_channel(
        self, channel: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        """
        Scans recent messages in *channel*.
        Returns a list of match result dicts.
        """
        results: list[dict[str, Any]] = []

        try:
            async for message in self.client.iter_messages(channel, limit=limit):
                if not isinstance(message, Message):
                    continue

                msg_key = f"{channel}:{message.id}"

                # Skip already-processed messages
                if await self._is_processed(msg_key):
                    continue

                text = message.text or message.message or ""

                # Score against all assets
                matched_asset, score = self._best_asset_match(text)

                # Always mark as processed so we don't revisit
                await self._mark_processed(msg_key)

                if matched_asset is None:
                    continue

                logger.info(
                    "Match in %s msg %s — asset=%s score=%.2f",
                    channel, message.id, matched_asset["id"], score,
                )

                # Download video clip if media is present
                clip_path = await self._download_clip(message, channel.lstrip("@"))

                # Fire alert
                await self.send_alert_on_match(
                    asset_id=matched_asset["id"],
                    channel=channel,
                    message_id=message.id,
                    morph_score=score,
                )

                results.append({
                    "channel": channel,
                    "message_id": message.id,
                    "asset_id": matched_asset["id"],
                    "score": score,
                    "clip_path": str(clip_path) if clip_path else None,
                    "text_preview": text[:200],
                })

        except Exception as exc:
            logger.error("Error scanning channel %s: %s", channel, exc)

        return results

    # ------------------------------------------------------------------
    # Scan all channels
    # ------------------------------------------------------------------

    async def scan_all_channels(
        self, limit_per_channel: int = 200
    ) -> list[dict[str, Any]]:
        """
        Iterates over self.channels and calls search_channel() for each.
        Combines and returns all match results.
        """
        all_results: list[dict[str, Any]] = []

        for channel in self.channels:
            logger.info("Scanning channel: %s", channel)
            channel_results = await self.search_channel(
                channel, limit=limit_per_channel
            )
            all_results.extend(channel_results)
            logger.info(
                "Channel %s — %d match(es) found", channel, len(channel_results)
            )

        logger.info("Scan complete. Total matches: %d", len(all_results))
        return all_results


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

async def _example() -> None:
    API_ID = int(os.environ["TELEGRAM_API_ID"])
    API_HASH = os.environ["TELEGRAM_API_HASH"]

    assets = [
        {"id": "epl_match_123", "keywords": ["premier league", "epl", "full match", "highlights", "hd stream"]},
        {"id": "nba_game_456",  "keywords": ["nba", "basketball", "full game", "replay", "stream"]},
    ]

    channels = ["@sports_unofficial", "@live_football_hd"]

    async with TelegramClient("monitor_session", API_ID, API_HASH) as client:
        monitor = TelegramChannelMonitor(
            client=client,
            channels=channels,
            assets=assets,
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        )
        results = await monitor.scan_all_channels(limit_per_channel=100)
        for r in results:
            print(r)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_example())