import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MatchResult:
    asset_id: str
    cosine_similarity: float       # 0.0 – 1.0
    source_confidence: float       # weighted formula from system plan
    verdict: str                   # "definitive" / "probable" / "no_match"


# Thresholds from system plan
DEFINITIVE_THRESHOLD = 0.88
PROBABLE_THRESHOLD   = 0.70


def _verdict(source_confidence: float) -> str:
    if source_confidence >= DEFINITIVE_THRESHOLD:
        return "definitive"     # legal-grade → auto-enforce
    elif source_confidence >= PROBABLE_THRESHOLD:
        return "probable"       # → human review queue
    else:
        return "no_match"


def _source_confidence(cosine_sim: float, metadata: dict = None) -> float:
    """
    From system plan:
    SourceConfidence = 0.5 × CosineSimilarity
                     + 0.3 × MetadataMatch
                     + 0.2 × BlockchainVerified
    """
    metadata = metadata or {}
    cosine_part     = 0.5 * cosine_sim
    metadata_part   = 0.3 * float(metadata.get("metadata_match_score", 0.5))
    blockchain_part = 0.2 * float(metadata.get("blockchain_verified", False))
    return min(1.0, cosine_part + metadata_part + blockchain_part)


# ── Primary: vectorized batch match (replaces the old loop) ───────────────────

def match_embedding(
    query_embedding: np.ndarray,
    database: Dict[str, np.ndarray],
    top_k: int = 3,
    threshold: float = PROBABLE_THRESHOLD,
    metadata_store: Dict[str, dict] = None,
) -> dict:
    """
    Match a query embedding against an in-memory database.
    
    Uses vectorized matrix multiply — no Python loop over pairs.
    All embeddings must be L2-normalized (they are, from fingerprint_engine.py).
    
    Args:
        query_embedding:  (512,) float32, L2-normalized
        database:         {asset_id: embedding (512,)} dict
        top_k:            number of top matches to return
        threshold:        minimum cosine similarity to include in results
        metadata_store:   optional {asset_id: {metadata dict}} for confidence scoring

    Returns:
        {
          "best_match": asset_id or None,
          "best_score": float,
          "verdict": "definitive" / "probable" / "no_match",
          "source_confidence": float,
          "top_matches": [MatchResult, ...]
        }
    """
    if not database:
        return _empty_result()

    # Stack all embeddings into a matrix: (N, 512)
    asset_ids = list(database.keys())
    matrix = np.stack([database[aid] for aid in asset_ids], axis=0)  # (N, 512)

    # Vectorized cosine similarity:
    # Since both query and db vectors are L2-normalized, dot product = cosine similarity
    # Shape: (N,)
    similarities = matrix @ query_embedding  # one matrix multiply, not N separate calls

    # Get top-k indices (unsorted), then sort just those k
    top_k = min(top_k, len(similarities))
    top_k_indices = np.argpartition(similarities, -top_k)[-top_k:]   # O(N) partial sort
    top_k_indices = top_k_indices[np.argsort(similarities[top_k_indices])[::-1]]  # sort k items

    results = []
    for idx in top_k_indices:
        sim = float(similarities[idx])
        if sim < threshold:
            continue                           # skip anything below threshold

        aid = asset_ids[idx]
        meta = (metadata_store or {}).get(aid, {})
        conf = _source_confidence(sim, meta)

        results.append(MatchResult(
            asset_id=aid,
            cosine_similarity=round(sim, 4),
            source_confidence=round(conf, 4),
            verdict=_verdict(conf),
        ))

    if not results:
        return _empty_result()

    best = results[0]   # already sorted descending
    return {
        "best_match":        best.asset_id,
        "best_score":        best.cosine_similarity,
        "verdict":           best.verdict,
        "source_confidence": best.source_confidence,
        "top_matches":       results,
    }


# ── Secondary: FAISS HNSW match (use this in production) ──────────────────────

def match_embedding_faiss(
    query_embedding: np.ndarray,
    index,                          # FingerprintIndex from faiss_index.py
    top_k: int = 3,
    threshold: float = PROBABLE_THRESHOLD,
) -> dict:
    """
    Production path: delegates to FingerprintIndex (HNSW ANN).
    Sub-20ms even at 10M+ vectors. Use this once you have > ~1000 assets.
    
    Args:
        query_embedding: (512,) float32, L2-normalized
        index: FingerprintIndex instance
    """
    results = index.search(query_embedding, top_k=top_k, threshold=threshold)

    if not results:
        return _empty_result()

    best = results[0]
    return {
        "best_match":        best.asset_id,
        "best_score":        best.cosine_similarity,
        "verdict":           best.verdict,
        "source_confidence": best.source_confidence,
        "top_matches":       results,
    }


def _empty_result() -> dict:
    return {
        "best_match":        None,
        "best_score":        0.0,
        "verdict":           "no_match",
        "source_confidence": 0.0,
        "top_matches":       [],
    }