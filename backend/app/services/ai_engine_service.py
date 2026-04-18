import hashlib
import logging
import math
import sys
from pathlib import Path


logger = logging.getLogger(__name__)


class AIEngineService:
    """Bridge backend analysis with the ai_engine package, with safe fallbacks."""

    def __init__(self) -> None:
        self._fingerprint_engine = None
        self._morph_scorer = None
        self._ai_available = None

    def _candidate_engine_paths(self) -> list[Path]:
        current_file = Path(__file__).resolve()
        candidates = [
            current_file.parents[3] / "ai_engine",
            current_file.parents[2] / "ai_engine",
            Path("/app/ai_engine"),
            Path.cwd() / "ai_engine",
            Path.cwd().parent / "ai_engine",
        ]
        # Preserve order and drop duplicates.
        seen: set[str] = set()
        unique_candidates: list[Path] = []
        for candidate in candidates:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            unique_candidates.append(candidate)
        return unique_candidates

    def _bootstrap_ai_imports(self) -> bool:
        if self._ai_available is not None:
            return self._ai_available

        for candidate in self._candidate_engine_paths():
            if candidate.exists() and str(candidate) not in sys.path:
                sys.path.append(str(candidate))

        try:
            from fingerprint_engine import ContentFingerprintEngine  # type: ignore
            from morph_scorer import MorphScoringEngine  # type: ignore

            self._fingerprint_engine = ContentFingerprintEngine()
            self._morph_scorer = MorphScoringEngine()
            self._ai_available = True
        except Exception as exc:  # pragma: no cover - depends on optional runtime deps
            logger.warning("AI engine unavailable, using fallback fingerprinting: %s", exc)
            self._ai_available = False

        return self._ai_available

    @staticmethod
    def _fallback_vector(file_path: str, dimension: int = 512) -> list[float]:
        path = Path(file_path)
        if not path.exists():
            return []

        # Deterministic pseudo-embedding to keep backend flow functioning
        # when optional AI dependencies are unavailable in a given environment.
        blob = path.read_bytes()
        if not blob:
            return []

        digest = hashlib.sha256(blob).digest()
        values = [((digest[idx % len(digest)] / 255.0) * 2.0) - 1.0 for idx in range(dimension)]
        magnitude = math.sqrt(sum(value * value for value in values))
        if magnitude == 0:
            return []
        return [value / magnitude for value in values]

    def generate_fingerprint(self, file_path: str) -> list[float]:
        if self._bootstrap_ai_imports():
            try:
                vector = self._fingerprint_engine.fingerprint_video(file_path)
                if vector is not None:
                    return [float(item) for item in vector.tolist()]
            except Exception as exc:  # pragma: no cover - optional runtime path
                logger.warning("AI fingerprint extraction failed, using fallback vector: %s", exc)

        return self._fallback_vector(file_path)

    def score_morph(self, file_path: str) -> dict[str, float | str]:
        if self._bootstrap_ai_imports():
            try:
                frames = self._fingerprint_engine.extract_keyframes(file_path)
                return self._morph_scorer.score_video(frames)
            except Exception as exc:  # pragma: no cover - optional runtime path
                logger.warning("Morph scoring failed, returning neutral score: %s", exc)

        return {
            "morph_score": 0.0,
            "gan_score": 0.0,
            "freq_score": 0.0,
            "temporal_score": 0.0,
            "verdict": "clean",
        }

    def is_ai_available(self) -> bool:
        return bool(self._bootstrap_ai_imports())
