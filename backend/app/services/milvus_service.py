from math import sqrt
from threading import RLock


class MilvusService:
    """Small in-memory adapter that mimics the shape of a vector DB."""

    def __init__(self) -> None:
        self._vectors: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def upsert(self, *, asset_id: str, organisation_id: str, vector: list[float]) -> None:
        if not vector:
            return
        with self._lock:
            self._vectors[asset_id] = {
                "asset_id": asset_id,
                "organisation_id": organisation_id,
                "vector": vector,
            }

    def get_vector(self, asset_id: str) -> list[float] | None:
        with self._lock:
            record = self._vectors.get(asset_id)
            if record is None:
                return None
            return list(record["vector"])

    def delete(self, asset_id: str) -> None:
        with self._lock:
            self._vectors.pop(asset_id, None)

    def search(
        self,
        *,
        vector: list[float],
        limit: int,
        organisation_id: str | None = None,
        exclude_asset_id: str | None = None,
    ) -> list[dict[str, object]]:
        with self._lock:
            candidates = list(self._vectors.values())

        results: list[dict[str, object]] = []
        for candidate in candidates:
            candidate_asset_id = candidate["asset_id"]
            candidate_org_id = candidate["organisation_id"]
            candidate_vector = candidate["vector"]

            if exclude_asset_id and candidate_asset_id == exclude_asset_id:
                continue
            if organisation_id and candidate_org_id != organisation_id:
                continue

            score = self.cosine_similarity(vector, candidate_vector)
            results.append(
                {
                    "asset_id": candidate_asset_id,
                    "organisation_id": candidate_org_id,
                    "score": round(score, 6),
                }
            )

        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    @staticmethod
    def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0

        dot_product = sum(left * right for left, right in zip(vector_a, vector_b))
        magnitude_a = sqrt(sum(item * item for item in vector_a))
        magnitude_b = sqrt(sum(item * item for item in vector_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)
