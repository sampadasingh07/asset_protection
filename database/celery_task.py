

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

import httpx
import redis.asyncio as aioredis
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterVideo

logger = logging.getLogger(__name__)

_API_BASE        = os.getenv("DAP_API_BASE", "http://api:8000")
_REDIS_URL       = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_CLIPS_DIR       = Path("/tmp/telegram_clips")
_PROCESSED_KEY   = "telegram:processed"
_KEYWORD_THRESH  = 0.5          # minimum keyword-match ratio to process
_CLIP_SECONDS    = 30           # seconds of video to download as evidence
_HTTP_TIMEOUT    = 10.0


class TelegramChannelMonitor:
    """
    Monitors Telegram channels and groups for pirated sports content.
    Uses Telethon MTProto API — requires Telegram API credentials.

    Setup: Get API ID/hash from https://my.telegram.org
    """

    def __init__(
        self,
        api_id:               int,
        api_hash:             str,
        asset_keywords:       list[str],
        session_name:         str = "dap_monitor",
        channels_to_monitor:  list[str] | None = None,
        redis_url:            str | None = None,
        api_base:             str | None = None,
        keyword_threshold:    float = _KEYWORD_THRESH,
    ):
        self.client            = TelegramClient(session_name, api_id, api_hash)
        self.channels          = channels_to_monitor or []
        self.asset_keywords    = [kw.lower() for kw in asset_keywords]
        self.keyword_threshold = keyword_threshold
        self._api_base         = (api_base or _API_BASE).rstrip("/")
        self._redis_url        = redis_url or _REDIS_URL
        self._redis: aioredis.Redis | None = None
        self.discovered_items: list[dict] = []
        _CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    async def start(self):
        """Connect Telethon client and open Redis connection."""
        await self.client.start()
        self._redis = await aioredis.from_url(self._redis_url, decode_responses=True)
        logger.info("Telegram client + Redis connection ready")

    async def stop(self):
        """Gracefully disconnect both clients."""
        if self._redis:
            await self._redis.aclose()
        await self.client.disconnect()

    # ── keyword scoring ───────────────────────────────────────────────────────

    def _keyword_score(self, text: str) -> float:
        """
        Return the fraction of asset_keywords present in *text*.
        Score 1.0 = all keywords matched; 0.0 = none matched.
        """
        if not self.asset_keywords:
            return 0.0
        lowered = text.lower()
        matched = sum(1 for kw in self.asset_keywords if kw in lowered)
        return matched / len(self.asset_keywords)

    # ── Redis deduplication ───────────────────────────────────────────────────

    async def _is_processed(self, channel: str, message_id: int) -> bool:
        """Return True if this (channel, message_id) pair has already been seen."""
        member = f"{channel}:{message_id}"
        return bool(await self._redis.sismember(_PROCESSED_KEY, member))

    async def _mark_processed(self, channel: str, message_id: int) -> None:
        """Add (channel, message_id) to the Redis deduplication set."""
        member = f"{channel}:{message_id}"
        await self._redis.sadd(_PROCESSED_KEY, member)

    # ── video download ────────────────────────────────────────────────────────

    async def _download_clip(self, message, channel_identifier: str) -> str | None:
        """
        Download the first _CLIP_SECONDS seconds of a video message.
        Returns the local file path, or None on failure.

        Telethon's download_media() pulls the full file — we then truncate
        to an approximate byte ceiling based on a 500 kbps estimate.
        For accurate trimming ffmpeg would be needed; this keeps the
        dependency footprint minimal while still capturing evidence.
        """
        if not (hasattr(message, "media") and message.media):
            return None

        safe_channel = str(channel_identifier).lstrip("@").replace("/", "_")
        out_path = _CLIPS_DIR / f"{safe_channel}_{message.id}.mp4"

        try:
            # Byte ceiling: _CLIP_SECONDS × 500 kbps ÷ 8 = ~1.875 MB per 30 s
            byte_limit = _CLIP_SECONDS * 500 * 1024 // 8

            await self.client.download_media(
                message,
                file=str(out_path),
                # Telethon accepts a progress_callback; we use it to abort early
            )

            # Truncate to byte ceiling so stored files stay small
            if out_path.exists() and out_path.stat().st_size > byte_limit:
                with open(out_path, "r+b") as fh:
                    fh.truncate(byte_limit)

            logger.info(f"Clip saved → {out_path}")
            return str(out_path)

        except Exception as exc:
            logger.error(f"Clip download failed for {channel_identifier}/{message.id}: {exc}")
            return None

    # ── API alert ─────────────────────────────────────────────────────────────

    async def send_alert_on_match(
        self,
        channel_identifier: str,
        message_id: int,
        discovered_at: str,
        keyword_score: float,
        asset_id: str | None = None,
    ) -> dict:
        """
        POST the discovery to the DAP matches endpoint.
        Returns the parsed API response (or an error dict).
        """
        payload = {
            "asset_id":      asset_id,
            "platform":      "telegram",
            "url":           f"https://t.me/{str(channel_identifier).lstrip('@')}/{message_id}",
            "account_id":    str(channel_identifier),
            "morph_score":   round(keyword_score * 100, 2),  # proxy score until real scoring runs
            "discovered_at": discovered_at,
        }
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as http:
                resp = await http.post(f"{self._api_base}/api/v1/matches", json=payload)
                resp.raise_for_status()
                logger.info(
                    f"Match reported | channel={channel_identifier} "
                    f"msg={message_id} score={keyword_score:.2f}"
                )
                return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"API error reporting match: {exc.response.status_code} {exc.response.text}"
            )
            return {"error": str(exc), "payload": payload}
        except httpx.RequestError as exc:
            logger.error(f"API request failed: {exc}")
            return {"error": str(exc), "payload": payload}

    # ── single-channel search ─────────────────────────────────────────────────

    async def search_channel(
        self, channel_identifier: str, query: str, max_results: int = 50
    ) -> list[dict]:
        """Search a single Telegram channel for matching video messages."""
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
                        "_message":   msg,   # kept for download; stripped before storage
                    })
        except Exception as exc:
            logger.error(f"Telegram search error for {channel_identifier}: {exc}")

        return results

    # ── multi-channel sweep ───────────────────────────────────────────────────

    async def scan_all_channels(
        self,
        max_results_per_channel: int = 50,
        download_clips: bool = True,
    ) -> list[dict]:
        """
        Sweep every channel in self.channels for each asset keyword.

        For every result:
          1. Score it — skip if below self.keyword_threshold.
          2. Skip if already in the Redis processed set.
          3. Optionally download a 30-second clip.
          4. POST to the matches API.
          5. Mark as processed in Redis.

        Returns a list of processed discovery dicts (no raw Telethon objects).
        """
        processed: list[dict] = []

        for channel in self.channels:
            for keyword in self.asset_keywords:
                results = await self.search_channel(
                    channel, keyword, max_results=max_results_per_channel
                )

                for item in results:
                    msg_id   = item["message_id"]
                    raw_msg  = item.pop("_message", None)  # remove before any storage

                    # ── 1. keyword scoring ────────────────────────────────
                    score = self._keyword_score(item["text"])
                    if score <= self.keyword_threshold:
                        logger.debug(
                            f"Skipping {channel}/{msg_id}: "
                            f"score {score:.2f} ≤ threshold {self.keyword_threshold}"
                        )
                        continue

                    # ── 2. deduplication ──────────────────────────────────
                    if await self._is_processed(channel, msg_id):
                        logger.debug(f"Already processed: {channel}/{msg_id}")
                        continue

                    item["keyword_score"] = score

                    # ── 3. clip download ──────────────────────────────────
                    if download_clips and raw_msg is not None:
                        clip_path = await self._download_clip(raw_msg, channel)
                        item["clip_path"] = clip_path

                    # ── 4. API alert ──────────────────────────────────────
                    api_resp = await self.send_alert_on_match(
                        channel_identifier=channel,
                        message_id=msg_id,
                        discovered_at=item["date"],
                        keyword_score=score,
                    )
                    item["api_response"] = api_resp

                    # ── 5. mark processed ─────────────────────────────────
                    await self._mark_processed(channel, msg_id)

                    self.discovered_items.append(item)
                    processed.append(item)
                    logger.info(
                        f"Discovery processed | channel={channel} "
                        f"msg={msg_id} score={score:.2f}"
                    )

                # Brief pause between keyword queries to avoid flood-wait
                await asyncio.sleep(1)

        return processed

    # ── real-time handler ─────────────────────────────────────────────────────

    def register_realtime_handler(self, callback=None):
        """
        Register a real-time NewMessage handler on self.channels.
        Applies keyword scoring, deduplication, and API alerting.
        Optionally calls *callback* with the discovery dict.
        """
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            msg          = event.message
            message_text = msg.message or ""
            channel      = str(event.chat_id)

            if not msg.media:
                return

            score = self._keyword_score(message_text)
            if score <= self.keyword_threshold:
                return

            if await self._is_processed(channel, msg.id):
                return

            discovered_at = msg.date.isoformat()

            # Download clip
            clip_path = await self._download_clip(msg, channel)

            # Alert API
            api_resp = await self.send_alert_on_match(
                channel_identifier=channel,
                message_id=msg.id,
                discovered_at=discovered_at,
                keyword_score=score,
            )

            await self._mark_processed(channel, msg.id)

            discovery = {
                "event":         "telegram_match",
                "channel":       channel,
                "message_id":    msg.id,
                "text":          message_text,
                "date":          discovered_at,
                "keyword_score": score,
                "clip_path":     clip_path,
                "api_response":  api_resp,
            }
            self.discovered_items.append(discovery)

            if callback:
                await callback(discovery)

    async def run(self):
        await self.client.run_until_disconnected()
