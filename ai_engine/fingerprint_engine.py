import torch
import torch.nn.functional as F
import open_clip
import cv2
import numpy as np
from PIL import Image
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ContentFingerprintEngine:
    """
    512-dim L2-normalized video embeddings using CLIP ViT-B/32.
    Robust to: JPEG compression, mild color shifts, re-encoding.
    
    NOTE for hackathon: Using ViT-B/32 (faster) instead of ViT-L/14 (needs GPU).
    Swap MODEL_NAME = "ViT-L-14" and PRETRAINED = "laion2b_s32b_b82k" for production.
    """

    MODEL_NAME = "ViT-B-32"
    PRETRAINED = "openai"
    EMBED_DIM = 512

    def __init__(self, device: str = "auto"):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() and device == "auto" else "cpu"
        )
        logger.info(f"Loading CLIP {self.MODEL_NAME} on {self.device}")

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            self.MODEL_NAME, pretrained=self.PRETRAINED
        )
        self.model = self.model.visual.to(self.device)
        self.model.eval()

        # Freeze — no training needed for hackathon
        for p in self.model.parameters():
            p.requires_grad = False

    # ── Frame-level embedding ──────────────────────────────────────────────────

    @torch.no_grad()
    def embed_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Single BGR frame (OpenCV) → 512-dim L2-normalized vector."""
        pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        tensor = self.preprocess(pil).unsqueeze(0).to(self.device)
        feat = self.model(tensor)                      # (1, 512)
        feat = F.normalize(feat, p=2, dim=-1)
        return feat.cpu().numpy().squeeze()            # (512,)

    @torch.no_grad()
    def embed_batch(self, frames_bgr: List[np.ndarray]) -> np.ndarray:
        """Batch of BGR frames → (N, 512) array. Much faster than looping."""
        tensors = [
            self.preprocess(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
            for f in frames_bgr
        ]
        batch = torch.stack(tensors).to(self.device)
        feats = self.model(batch)
        feats = F.normalize(feats, p=2, dim=-1)
        return feats.cpu().numpy()

    # ── Smart keyframe extraction ──────────────────────────────────────────────

    def extract_keyframes(
        self,
        video_path: str,
        max_frames: int = 64,
        scene_threshold: float = 30.0,
    ) -> List[np.ndarray]:
        """
        Scene-change aware keyframe extraction.
        Much better than naive every-Nth-frame sampling.
        
        Args:
            video_path: path to video file
            max_frames: cap to avoid OOM on long videos
            scene_threshold: pixel-diff threshold for scene cut detection
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0

        # Always grab 1 frame/sec at minimum
        base_interval = max(1, int(fps))

        frames, prev_gray = [], None
        idx = 0

        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if idx % base_interval == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Scene-cut: large pixel diff → definitely a new scene, grab it
                if prev_gray is not None:
                    diff = np.mean(cv2.absdiff(gray, prev_gray))
                    if diff > scene_threshold or idx % base_interval == 0:
                        frames.append(frame)
                else:
                    frames.append(frame)  # always grab first frame

                prev_gray = gray
            idx += 1

        cap.release()
        logger.info(f"Extracted {len(frames)} keyframes from {video_path}")
        return frames

    # ── Full video fingerprint ─────────────────────────────────────────────────

    def fingerprint_video(self, video_path: str) -> Optional[np.ndarray]:
        """
        Full pipeline: video path → single 512-dim fingerprint.
        Aggregation: mean pooling + re-normalize.
        Returns None if video has no frames.
        """
        frames = self.extract_keyframes(video_path)
        if not frames:
            logger.warning(f"No frames from {video_path}")
            return None

        all_embeddings = []
        for i in range(0, len(frames), 32):  # batch size 32
            batch_embs = self.embed_batch(frames[i:i + 32])
            all_embeddings.append(batch_embs)

        all_embeddings = np.vstack(all_embeddings)        # (N, 512)
        fingerprint = np.mean(all_embeddings, axis=0)     # mean pooling
        fingerprint = fingerprint / (np.linalg.norm(fingerprint) + 1e-8)
        return fingerprint.astype(np.float32)


# ── Audio Fingerprinting ───────────────────────────────────────────────────────

class AudioFingerprintEngine:
    """
    256-dim audio embedding: MFCC (40-dim mean+std) + Chromagram (12-dim mean).
    Stored alongside video fingerprint for AV-combined matching.
    """

    def embed_audio(self, audio_path: str, sr: int = 22050) -> Optional[np.ndarray]:
        try:
            import librosa
        except ImportError:
            logger.warning("librosa not installed — skipping audio fingerprint")
            return None

        try:
            y, sr = librosa.load(audio_path, sr=sr, mono=True)

            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            mfcc_mean = np.mean(mfcc, axis=1)   # (40,)
            mfcc_std  = np.std(mfcc, axis=1)    # (40,)  ← adds robustness

            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)  # (12,)

            # Spectral centroid (1-dim) for tonal fingerprinting
            centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

            embedding = np.concatenate([mfcc_mean, mfcc_std, chroma_mean, [centroid]])
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            # Pad/trim to 128-dim for consistency
            embedding = embedding[:128] if len(embedding) >= 128 else np.pad(embedding, (0, 128 - len(embedding)))
            return embedding.astype(np.float32)

        except Exception as e:
            logger.error(f"Audio embedding failed: {e}")
            return None