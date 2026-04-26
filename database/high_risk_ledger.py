

import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
import redis

logger = logging.getLogger(__name__)

# Redis TTL for violation history: 30 days
_VIOLATION_TTL_SECONDS = 30 * 24 * 60 * 60
_API_BASE = os.getenv("DAP_API_BASE", "http://api:8000")


def send_alert(severity: str, message: str) -> None:
    """Send alert via Telegram and Slack (from celery_tasks.py)."""
    import httpx as _httpx

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat  = os.getenv("TELEGRAM_ALERT_CHAT_ID")
    slack_webhook  = os.getenv("SLACK_WEBHOOK_URL")

    emoji_map = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}
    formatted = f"{emoji_map.get(severity, '')} [{severity}] {message}"

    if telegram_token and telegram_chat:
        try:
            _httpx.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                json={"chat_id": telegram_chat, "text": formatted, "parse_mode": "HTML"},
                timeout=5.0,
            )
        except Exception as exc:
            logger.error(f"Telegram alert failed: {exc}")

    if slack_webhook:
        try:
            _httpx.post(slack_webhook, json={"text": formatted}, timeout=5.0)
        except Exception as exc:
            logger.error(f"Slack alert failed: {exc}")


class HighRiskAccountManager:
    """
    Manages violation tracking, composite risk scoring, watchlist escalation,
    and account reporting for high-risk accounts.

    Args:
        redis_url:   Redis connection string (default: REDIS_URL env var).
        api_base:    Base URL of the DAP REST API (default: DAP_API_BASE env var).
        http_timeout: Seconds before httpx requests time out.
    """

    def __init__(
        self,
        redis_url:    Optional[str] = None,
        api_base:     Optional[str] = None,
        http_timeout: float = 10.0,
    ) -> None:
        self._api_base    = (api_base or _API_BASE).rstrip("/")
        self._http_timeout = http_timeout
        self._redis       = redis.from_url(
            redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )

    # ── internal helpers ──────────────────────────────────────────────────────

    def _redis_key(self, account_id: str) -> str:
        return f"violations:{account_id}"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_violations(self, account_id: str) -> list[dict]:
        """Return all stored violations for *account_id* (never raises)."""
        try:
            raw = self._redis.get(self._redis_key(account_id))
            return json.loads(raw) if raw else []
        except (redis.RedisError, json.JSONDecodeError) as exc:
            logger.error(f"Redis read failed for {account_id}: {exc}")
            return []

    def _save_violations(self, account_id: str, violations: list[dict]) -> None:
        """Persist *violations* to Redis with a 30-day TTL (never raises)."""
        try:
            self._redis.set(
                self._redis_key(account_id),
                json.dumps(violations),
                ex=_VIOLATION_TTL_SECONDS,
            )
        except redis.RedisError as exc:
            logger.error(f"Redis write failed for {account_id}: {exc}")

    def _violations_last_30d(self, violations: list[dict]) -> list[dict]:
        """Filter violations to those within the last 30 calendar days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent = []
        for v in violations:
            try:
                ts = datetime.fromisoformat(v["timestamp"])
                # Make naive timestamps timezone-aware (assume UTC)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    recent.append(v)
            except (KeyError, ValueError):
                pass
        return recent

    # ── public API ────────────────────────────────────────────────────────────

    def record_violation(
        self,
        account_id: str,
        platform:   str,
        morph_score: float,
        asset_id:   str,
        url:        str,
    ) -> dict:
        """
        Record a new violation for *account_id*.

        1. POSTs to /api/v1/high-risk-accounts.
        2. Appends the violation to Redis (TTL = 30 days).

        Returns the API response body (dict), or a minimal local dict on error.
        """
        violation = {
            "account_id":  account_id,
            "platform":    platform,
            "morph_score": morph_score,
            "asset_id":    asset_id,
            "url":         url,
            "timestamp":   self._now_iso(),
        }

        # ── 1. Persist to API ────────────────────────────────────────────────
        api_response: dict = {}
        try:
            resp = httpx.post(
                f"{self._api_base}/api/v1/high-risk-accounts",
                json=violation,
                timeout=self._http_timeout,
            )
            resp.raise_for_status()
            api_response = resp.json()
            logger.info(
                f"Violation recorded via API | account={account_id} "
                f"platform={platform} morph={morph_score:.1f}"
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"API error recording violation for {account_id}: "
                f"{exc.response.status_code} {exc.response.text}"
            )
        except httpx.RequestError as exc:
            logger.error(f"API request failed for {account_id}: {exc}")

        # ── 2. Persist to Redis ──────────────────────────────────────────────
        violations = self._load_violations(account_id)
        violations.append(violation)
        self._save_violations(account_id, violations)

        return api_response or violation

    # ─────────────────────────────────────────────────────────────────────────

    def get_risk_score(self, account_id: str) -> float:
        """
        Compute a composite risk score in [0, 100]:

            score = min(violation_count_30d × 15, 60)
                  + average_morph_score_30d × 0.4

        Returns 0.0 if no violations are found.
        """
        violations = self._load_violations(account_id)
        recent     = self._violations_last_30d(violations)

        if not recent:
            return 0.0

        count_component = min(len(recent) * 15, 60)

        morph_scores    = [v["morph_score"] for v in recent if "morph_score" in v]
        avg_morph       = sum(morph_scores) / len(morph_scores) if morph_scores else 0.0
        morph_component = avg_morph * 0.4

        score = count_component + morph_component
        return round(min(score, 100.0), 2)

    # ─────────────────────────────────────────────────────────────────────────

    def check_and_escalate(self, account_id: str, platform: str) -> bool:
        """
        Escalate to watchlist if violation_count_30d >= 3.

        - POSTs to /api/v1/high-risk-accounts/{account_id}/watchlist.
        - Sends a CRITICAL alert.

        Returns True if the account was escalated, False otherwise.
        """
        violations = self._load_violations(account_id)
        recent     = self._violations_last_30d(violations)
        count      = len(recent)

        if count < 3:
            logger.debug(
                f"No escalation for {account_id}: only {count} violation(s) in last 30d"
            )
            return False

        risk_score = self.get_risk_score(account_id)

        # ── POST watchlist ───────────────────────────────────────────────────
        escalated = False
        try:
            resp = httpx.post(
                f"{self._api_base}/api/v1/high-risk-accounts/{account_id}/watchlist",
                json={
                    "platform":        platform,
                    "violation_count": count,
                    "risk_score":      risk_score,
                    "escalated_at":    self._now_iso(),
                },
                timeout=self._http_timeout,
            )
            resp.raise_for_status()
            escalated = True
            logger.warning(
                f"Account {account_id} escalated to watchlist "
                f"({count} violations, risk={risk_score:.1f})"
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Watchlist API error for {account_id}: "
                f"{exc.response.status_code} {exc.response.text}"
            )
        except httpx.RequestError as exc:
            logger.error(f"Watchlist request failed for {account_id}: {exc}")

        # ── Alert regardless of API success ──────────────────────────────────
        send_alert(
            severity="CRITICAL",
            message=(
                f"HIGH-RISK ACCOUNT: {account_id} on {platform} — "
                f"{count} violations in 30d | risk score {risk_score:.1f}/100"
            ),
        )

        return escalated

    # ─────────────────────────────────────────────────────────────────────────

    def generate_account_report(self, account_id: str) -> dict:
        """
        Return a summary report dict for *account_id*:

        {
            "account_id":        str,
            "total_violations":  int,
            "violations_30d":    int,
            "platforms":         list[str],
            "first_violation":   str | None,   # ISO-8601
            "risk_score":        float,
            "is_watchlisted":    bool,
            "generated_at":      str,
        }
        """
        violations = self._load_violations(account_id)
        recent     = self._violations_last_30d(violations)

        # Platforms involved (all time)
        platforms = sorted({v.get("platform", "unknown") for v in violations})

        # Earliest violation timestamp
        first_violation: Optional[str] = None
        if violations:
            timestamps = []
            for v in violations:
                try:
                    timestamps.append(datetime.fromisoformat(v["timestamp"]))
                except (KeyError, ValueError):
                    pass
            if timestamps:
                first_violation = min(timestamps).isoformat()

        # Watchlist status (best-effort API check)
        is_watchlisted = False
        try:
            resp = httpx.get(
                f"{self._api_base}/api/v1/high-risk-accounts/{account_id}",
                timeout=self._http_timeout,
            )
            if resp.status_code == 200:
                is_watchlisted = resp.json().get("is_watchlisted", False)
            elif resp.status_code != 404:
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                f"Could not fetch watchlist status for {account_id}: "
                f"{exc.response.status_code}"
            )
        except httpx.RequestError as exc:
            logger.warning(f"Watchlist status request failed for {account_id}: {exc}")

        return {
            "account_id":       account_id,
            "total_violations": len(violations),
            "violations_30d":   len(recent),
            "platforms":        platforms,
            "first_violation":  first_violation,
            "risk_score":       self.get_risk_score(account_id),
            "is_watchlisted":   is_watchlisted,
            "generated_at":     self._now_iso(),
        }
