import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    asset_id: str
    cosine_similarity: float        # 0.0 – 1.0
    source_confidence: float        # 0.0 – 1.0
    verdict: str                    # "definitive" / "probable" / "no_match"


class FingerprintIndex:
    """
    HNSW-based ANN index for sub-20ms fingerprint search at scale.
    
    Key improvements over IndexFlatL2:
    - HNSW is logarithmic search vs linear brute-force
    - Cosine similarity via L2-normed inner product (correct metric for embeddings)
    - Full persistence: save/load index + metadata
    - Source confidence scoring matching the system spec
    """

    # Thresholds from the system plan
    DEFINITIVE_THRESHOLD = 0.88
    PROBABLE_THRESHOLD   = 0.70

    def __init__(self, dimension: int = 512, hnsw_m: int = 32):
        """
        Args:
            dimension: embedding size (512 for CLIP ViT-B/32)
            hnsw_m: HNSW connections per node. Higher = more accurate, more RAM.
                    32 is good balance. Plan specifies M=16 for production scale.
        """
        self.dimension = dimension

        # Inner product index → cosine similarity when vectors are L2-normalized
        self.index = faiss.IndexHNSWFlat(dimension, hnsw_m, faiss.METRIC_INNER_PRODUCT)
        self.index.hnsw.efConstruction = 200   # build quality (plan: ef_construction=200)
        self.index.hnsw.efSearch = 64          # search quality/speed tradeoff

        # Metadata store: maps FAISS integer ID → asset info
        self.id_to_metadata: Dict[int, dict] = {}
        self._next_id = 0

    # ── Indexing ───────────────────────────────────────────────────────────────

    def add(self, embedding: np.ndarray, asset_id: str, metadata: dict = None):
        """
        Add a single 512-dim L2-normalized embedding to the index.
        
        Args:
            embedding: (512,) float32, must be L2-normalized
            asset_id: unique string ID (e.g. UUID from PostgreSQL)
            metadata: optional dict (filename, upload_time, platform, etc.)
        """
        vec = np.array([embedding], dtype=np.float32)
        self.index.add(vec)
        self.id_to_metadata[self._next_id] = {
            "asset_id": asset_id,
            **(metadata or {}),
        }
        self._next_id += 1
        logger.debug(f"Indexed asset {asset_id} (total: {self._next_id})")

    def add_batch(self, embeddings: np.ndarray, asset_ids: List[str], metadatas: List[dict] = None):
        """Batch add. embeddings shape: (N, 512)."""
        n = len(embeddings)
        self.index.add(embeddings.astype(np.float32))
        for i, aid in enumerate(asset_ids):
            self.id_to_metadata[self._next_id + i] = {
                "asset_id": aid,
                **((metadatas[i] if metadatas else None) or {}),
            }
        self._next_id += n

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.70,
    ) -> List[MatchResult]:
        """
        Search for similar fingerprints.
        
        Returns:
            List of MatchResult sorted by cosine_similarity descending.
            Only results above `threshold` are returned.
        """
        if self._next_id == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        top_k = min(top_k, self._next_id)

        similarities, indices = self.index.search(query, top_k)

        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx < 0 or sim < threshold:
                continue

            meta = self.id_to_metadata.get(int(idx), {})
            source_confidence = self._compute_source_confidence(
                cosine_sim=float(sim),
                metadata=meta,
            )
            verdict = self._verdict(source_confidence)

            results.append(MatchResult(
                asset_id=meta.get("asset_id", f"unknown_{idx}"),
                cosine_similarity=round(float(sim), 4),
                source_confidence=round(source_confidence, 4),
                verdict=verdict,
            ))

        return sorted(results, key=lambda r: r.cosine_similarity, reverse=True)

    # ── Source Confidence ──────────────────────────────────────────────────────

    def _compute_source_confidence(self, cosine_sim: float, metadata: dict) -> float:
        """
        Formula from system spec:
        SourceConfidence = 0.5 × CosineSimilarity
                         + 0.3 × MetadataMatch
                         + 0.2 × BlockchainVerified
        """
        cosine_component = 0.5 * cosine_sim

        # MetadataMatch: 1.0 if hash matches, 0.5 if same platform, else 0
        metadata_match = metadata.get("metadata_match_score", 0.5)
        metadata_component = 0.3 * metadata_match

        # Blockchain: 1 if verified, 0 if not
        blockchain_verified = float(metadata.get("blockchain_verified", False))
        blockchain_component = 0.2 * blockchain_verified

        return min(1.0, cosine_component + metadata_component + blockchain_component)

    def _verdict(self, source_confidence: float) -> str:
        if source_confidence >= self.DEFINITIVE_THRESHOLD:
            return "definitive"    # legal-grade match → auto-enforce
        elif source_confidence >= self.PROBABLE_THRESHOLD:
            return "probable"      # human review queue
        else:
            return "no_match"

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, directory: str):
        """Save FAISS index + metadata to disk."""
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "hnsw.index"))
        with open(os.path.join(directory, "metadata.pkl"), "wb") as f:
            pickle.dump(
                {"id_to_metadata": self.id_to_metadata, "_next_id": self._next_id}, f
            )
        logger.info(f"Index saved to {directory} ({self._next_id} vectors)")

    @classmethod
    def load(cls, directory: str, dimension: int = 512) -> "FingerprintIndex":
        """Load a saved index from disk."""
        instance = cls(dimension=dimension)
        instance.index = faiss.read_index(os.path.join(directory, "hnsw.index"))
        with open(os.path.join(directory, "metadata.pkl"), "rb") as f:
            state = pickle.load(f)
        instance.id_to_metadata = state["id_to_metadata"]
        instance._next_id = state["_next_id"]
        logger.info(f"Loaded index from {directory} ({instance._next_id} vectors)")
        return instance

    def __len__(self):
        return self._next_id