from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import monotonic

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency at runtime
    psutil = None


@dataclass(slots=True)
class RuntimeSnapshot:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    process_uptime_seconds: float
    request_latency_p95_ms: float
    requests_last_minute: int


class RuntimeMetrics:
    def __init__(self) -> None:
        self._started_at = monotonic()
        self._request_latencies_ms: deque[float] = deque(maxlen=5000)
        self._request_timestamps: deque[datetime] = deque(maxlen=5000)
        self._lock = Lock()

        if psutil is not None:
            # Warm up first cpu_percent reading to avoid initial 0.0 spikes.
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass

    def record_request(self, latency_ms: float) -> None:
        now = datetime.now(UTC)
        bounded_latency = max(0.0, float(latency_ms))
        with self._lock:
            self._request_latencies_ms.append(bounded_latency)
            self._request_timestamps.append(now)
            self._prune_old_requests(now)

    def snapshot(self) -> RuntimeSnapshot:
        now = datetime.now(UTC)
        with self._lock:
            self._prune_old_requests(now)
            request_count = len(self._request_timestamps)
            latencies = list(self._request_latencies_ms)

        cpu_percent = 0.0
        memory_percent = 0.0
        disk_percent = 0.0

        if psutil is not None:
            try:
                cpu_percent = float(psutil.cpu_percent(interval=None))
                memory_percent = float(psutil.virtual_memory().percent)
                disk_percent = float(psutil.disk_usage('/').percent)
            except Exception:
                cpu_percent = 0.0
                memory_percent = 0.0
                disk_percent = 0.0

        return RuntimeSnapshot(
            cpu_percent=round(cpu_percent, 2),
            memory_percent=round(memory_percent, 2),
            disk_percent=round(disk_percent, 2),
            process_uptime_seconds=round(max(0.0, monotonic() - self._started_at), 2),
            request_latency_p95_ms=round(self._percentile(latencies, 95), 2),
            requests_last_minute=request_count,
        )

    def _prune_old_requests(self, now: datetime) -> None:
        threshold = now - timedelta(minutes=1)
        while self._request_timestamps and self._request_timestamps[0] < threshold:
            self._request_timestamps.popleft()
            if self._request_latencies_ms:
                self._request_latencies_ms.popleft()

    @staticmethod
    def _percentile(values: list[float], percentile: int) -> float:
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(round((percentile / 100) * (len(sorted_values) - 1)))
        return float(sorted_values[index])
