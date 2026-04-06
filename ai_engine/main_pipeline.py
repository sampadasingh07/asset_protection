"""
main_pipeline.py  —  Person 1: AI & Media Forensics Lead
"""

import sys
from fingerprint_engine import ContentFingerprintEngine
from faiss_index import FingerprintIndex
from morph_scorer import MorphScoringEngine
from matcher import match_embedding_faiss


def run_pipeline(video_path: str):
    print(f"\n{'='*50}")
    print(f"Processing: {video_path}")
    print('='*50)

    engine = ContentFingerprintEngine()
    scorer = MorphScoringEngine()
    index  = FingerprintIndex(dimension=512)

    # ── Step 1: Fingerprint ────────────────────────────────────────────────────
    print("\n[1/3] Generating fingerprint...")
    frames      = engine.extract_keyframes(video_path)
    fingerprint = engine.fingerprint_video(video_path)

    if fingerprint is None:
        print("  ✗ Could not extract frames. Check video path.")
        return

    print(f"  ✓ Shape: {fingerprint.shape} | norm: {float(sum(fingerprint**2))**0.5:.4f} | frames: {len(frames)}")

    # ── Step 2: Index + match ──────────────────────────────────────────────────
    print("\n[2/3] Indexing and searching...")
    index.add(fingerprint, asset_id="test_asset_001", metadata={"filename": video_path})
    result = match_embedding_faiss(fingerprint, index, top_k=3, threshold=0.5)

    print(f"  Best match        : {result['best_match']}")
    print(f"  Cosine similarity : {result['best_score']:.4f}")
    print(f"  Verdict           : {result['verdict']}")
    print(f"  Source confidence : {result['source_confidence']:.4f}")

    for m in result["top_matches"]:
        print(f"    → {m.asset_id} | cosine={m.cosine_similarity:.4f} | {m.verdict}")

    # ── Step 3: Morph score ────────────────────────────────────────────────────
    print("\n[3/3] Computing morph score...")
    scores = scorer.score_video(frames)

    print(f"  MorphScore  : {scores['morph_score']}")
    print(f"  GAN Score   : {scores['gan_score']}")
    print(f"  Freq Score  : {scores['freq_score']}")
    print(f"  Temporal    : {scores['temporal_score']}")
    print(f"  Verdict     : {scores['verdict']}")

    # ── Enforcement decision ───────────────────────────────────────────────────
    print("\n[ENFORCEMENT]")
    morph_score = scores["morph_score"]
    cosine      = result["best_score"]

    if morph_score > 80 and cosine > 0.92:
        print("  🔴 AUTO TAKEDOWN  — high morph score + definitive match")
    elif morph_score > 50 or cosine > 0.85:
        print("  🟡 HUMAN REVIEW   — suspicious signal detected")
    else:
        print("  🟢 CLEAN          — no action required")

    print(f"\n{'='*50}\n")


if __name__ == "__main__":
    video = sys.argv[1] if len(sys.argv) > 1 else "test.mp4"
    run_pipeline(video)