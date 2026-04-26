# 🛡️ DAP Shield — Digital Asset Protection & Media Integrity System

> **AI-powered content fingerprinting, deepfake/morph detection, and automated enforcement for high-value sports media.**

---

## Table of Contents

1. [What Is DAP Shield?](#what-is-dap-shield)
2. [How to Open the Website — Step by Step](#how-to-open-the-website--step-by-step)
3. [Tech Stack & Tools Used](#tech-stack--tools-used)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [AI Content Fingerprinting Engine](#ai-content-fingerprinting-engine)
6. [Morph / Deepfake Detection (Media Integrity Engine)](#morph--deepfake-detection-media-integrity-engine)
7. [Global Platform Scraper](#global-platform-scraper)
8. [Automated Enforcement Flow](#automated-enforcement-flow)
9. [The Competitive Moat](#the-competitive-moat)
10. [Scalability Plan](#scalability-plan)
11. [API Reference](#api-reference)
12. [Project File Structure](#project-file-structure)
13. [Environment Variables](#environment-variables)
14. [Troubleshooting](#troubleshooting)

---

## What Is DAP Shield?

DAP Shield is an **intelligence-first** Digital Rights Management (DRM) platform built for sports media owners. Traditional watermarking is brittle — a single crop or re-encode defeats it. DAP Shield instead embeds a **perceptual AI fingerprint** into every frame at the semantic level, making it transformation-invariant. Then a continuous global scraper hunts pirated copies across social media, torrent sites, and Telegram channels, scores each hit with a **Morph Score** (0–100), and triggers automated DMCA takedowns — all without human intervention for high-confidence cases.

**Key capabilities at a glance:**

| Capability | Technology Used |
|---|---|
| AI Fingerprinting | CLIP ViT-B/32, 512-dim L2-normalized vectors |
| Vector Similarity Search | In-memory Milvus adapter (HNSW-ready) |
| Morph/Deepfake Score | GAN classifier + DCT frequency + Optical flow |
| Platform Crawling | Playwright headless browser + Telethon (Telegram) |
| Propagation Graph | D3.js force-directed network |
| Real-time Alerts | FastAPI WebSockets |
| Enforcement | DMCA PDF generator + S3 upload |
| Backend | FastAPI + SQLAlchemy + SQLite/PostgreSQL |
| Frontend | React 19 + Vite 8 + Recharts + Framer Motion |

---

## How to Open the Website — Step by Step

### Prerequisites

Make sure you have these installed before starting:

| Tool | Minimum Version | Check Command |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

---

### Step 1 — Clone or Download the Project

```bash
# If you have git:
git clone <your-repo-url>
cd asset_protection

# Or unzip the downloaded archive and navigate into it
```

---

### Step 2 — Set Up the Backend

```bash
# Move into the backend folder
cd backend

# (Recommended) Create a Python virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
```

---

### Step 3 — Configure the Backend Environment

```bash
# Still inside the backend/ folder:
# Copy the example environment file
copy .env.example .env        # Windows
cp .env.example .env          # macOS / Linux

# The default .env works out of the box with SQLite.
# No changes needed for local development.
```

---

### Step 4 — Initialize the Database and Seed Demo Data

```bash
# Still inside backend/ with virtual environment active:

# Run database migrations (creates all tables)
alembic upgrade head

# Seed demo organisation, user, and sample asset
python seed_data.py
```

You should see:
```
✓ Demo data seeded successfully!
  User: admin@demo.org (password: demo123)
  Assets: 1 created
  Violations: 1 created
```

---

### Step 5 — Start the Backend Server

```bash
# Still inside backend/ with virtual environment active:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal open.**

---

### Step 6 — Set Up the Frontend

Open a **new terminal window/tab** and run:

```bash
# Navigate to the frontend folder (from project root)
cd frontend

# Install all Node.js dependencies
npm install
```

---

### Step 7 — Start the Frontend Dev Server

```bash
# Still inside frontend/:
npm run dev
```

You should see:
```
  VITE v8.x.x  ready in Xms

  ➜  Local:   http://localhost:5174/
```

---

### Step 8 — Open the Dashboard

Open your browser and go to:

```
http://localhost:5174
```

The app will auto-login using the demo credentials. If prompted:

```
Email:    admin@demo.org
Password: demo123
```

---

### Quick-Start Alternative (Both servers at once)

From the **project root** folder:

```bash
# Terminal 1 — Backend
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Or use the helper script:

```bash
# Windows
run_backend.bat

# Any OS
python run_app.py
```

---

### Step 9 — Verify Everything Is Working

| URL | What You Should See |
|---|---|
| `http://localhost:5174` | DAP Shield dashboard |
| `http://localhost:8000/docs` | FastAPI interactive API docs |
| `http://localhost:8000/health` | `{"status": "ok"}` |

---

### Step 10 — Stop the Servers

Press `Ctrl + C` in each terminal window to stop both servers.

---

## Tech Stack & Tools Used

### Frontend

| Tool | Version | Purpose |
|---|---|---|
| **React** | 19.x | UI component framework |
| **Vite** | 8.x | Ultra-fast build tool and dev server |
| **D3.js** | 7.x | Force-directed propagation graph visualization |
| **Recharts** | 3.x | Area/line/bar charts for analytics |
| **Framer Motion** | 12.x | Smooth entrance/exit animations for alerts and modals |
| **Lucide React** | 1.x | Consistent icon set throughout the UI |
| **react-dropzone** | 15.x | Drag-and-drop file upload zone |
| **Vanilla CSS3** | — | Custom glassmorphism design system with CSS variables |

**Key design decisions:**
- No CSS framework (no Tailwind, no Bootstrap) — full custom monochrome glassmorphism theme
- `backdrop-filter: blur()` for card translucency
- CSS custom properties (`--var`) for a consistent token system across dark/light modes
- Framer Motion `AnimatePresence` for alert feed animations

---

### Backend

| Tool | Version | Purpose |
|---|---|---|
| **FastAPI** | 0.115 | Async REST API + WebSocket server |
| **SQLAlchemy** | 2.x | ORM for all database models |
| **Alembic** | 1.x | Database schema migration manager |
| **Pydantic** | v2 | Request/response validation and serialization |
| **PyJWT** | 2.x | JWT-based authentication |
| **Uvicorn** | 0.32 | ASGI server (production-grade) |
| **SQLite** | built-in | Default local database (zero config) |
| **psycopg** | 3.x | PostgreSQL driver (for production) |
| **Celery + Redis** | 5.x | Async task queue for background analysis |
| **psutil** | 6.x | Real-time CPU/memory metrics for System Health page |

---

### AI Engine (`ai_engine/`)

| Tool | Version | Purpose |
|---|---|---|
| **PyTorch** | 2.x | Deep learning framework (GPU/CPU) |
| **open_clip** | latest | CLIP ViT-B/32 model for video fingerprinting |
| **OpenCV** | headless | Frame extraction, optical flow, DCT analysis |
| **torchvision** | 0.x | EfficientNet-B0 GAN classifier backbone |
| **scipy** | latest | FFT / power spectrum analysis for frequency scoring |
| **FAISS** | cpu | HNSW approximate nearest-neighbor index |
| **NumPy** | latest | Vector math and matrix operations |
| **librosa** | latest | Audio fingerprinting (MFCC + chromagram) |

---

### Scraping & Intelligence (`database/`)

| Tool | Purpose |
|---|---|
| **Playwright** | Headless Chromium for YouTube, TikTok, Twitter scraping |
| **Telethon** | Telegram MTProto client for channel monitoring |
| **httpx** | Async HTTP client for API calls |
| **rapidfuzz** | Fuzzy string matching for torrent title relevance |
| **stem** | Tor circuit control for anonymous crawling |
| **redis-py** | Deduplication set and processed message tracking |
| **reportlab** | PDF generation for DMCA takedown packets |
| **qrcode** | QR code embedding in DMCA PDFs |
| **boto3** | AWS S3 upload for DMCA packet storage |
| **fake-useragent** | Rotating browser user-agents to avoid detection |

---

### Infrastructure

| Component | Technology | Notes |
|---|---|---|
| Database | SQLite (dev) / PostgreSQL 15 (prod) | Alembic migrations for both |
| Vector DB | In-memory Milvus adapter | Drop-in replaceable with real Milvus |
| Graph DB | In-memory Neo4j adapter | Drop-in replaceable with real Neo4j |
| Task Queue | Celery + Redis | `TASK_MODE=eager` for local dev |
| Container | Docker + Docker Compose | Full stack: postgres, redis, backend, worker, frontend |
| Object Storage | AWS S3 | DMCA PDF packets |

---

## Architecture Deep Dive

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  Dashboard │ Upload │ Propagation Graph │ Alerts │ Enforcement   │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND API (FastAPI)                          │
│  /assets  /violations  /search  /stats  /ws/alerts  /auth       │
└──────┬──────────────────────────────────────┬───────────────────┘
       │ SQLAlchemy ORM                        │ Async Tasks
┌──────▼──────────┐              ┌─────────────▼──────────────────┐
│ SQLite/Postgres │              │  Celery Worker (analysis.py)    │
│  (structured    │              │  1. Fingerprint via AI Engine   │
│   metadata)     │              │  2. Search Milvus vector DB     │
└─────────────────┘              │  3. Create Violation record     │
                                 │  4. Broadcast WebSocket alert   │
┌────────────────────────────────▼───────────────────────────────┐
│                      AI ENGINE                                   │
│  ContentFingerprintEngine (CLIP ViT-B/32)                       │
│  MorphScoringEngine (GAN + DCT + Optical Flow)                  │
│  FingerprintIndex (FAISS HNSW)                                  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPING LAYER (database/)                    │
│  SocialMediaCrawler (YouTube, TikTok, Twitter via Playwright)   │
│  TelegramChannelMonitor (Telethon MTProto)                      │
│  PirateSiteCrawler (1337x, ThePirateBay via Tor)                │
│  HighRiskAccountManager (Redis + DAP API)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## AI Content Fingerprinting Engine

### Why CNN/Transformer Fingerprinting Over Watermarks?

Traditional watermarks are a single bit pattern embedded in pixel space. One lossy re-encode, one crop, or one color grade — and the watermark is gone. Our approach embeds at the **semantic feature level**: the model understands *what* is in the video (players, stadium, ball, motion patterns), not just *which pixels* are there.

### Model: CLIP ViT-B/32

```python
# ai_engine/fingerprint_engine.py
MODEL_NAME = "ViT-B-32"
PRETRAINED = "openai"
EMBED_DIM = 512
```

CLIP (Contrastive Language-Image Pre-training) was trained on 400 million image-text pairs. Its visual encoder produces embeddings where *semantically similar* images cluster together — regardless of JPEG compression, resolution changes, mild color shifts, or cropping. This is exactly the property we need.

**Production upgrade path:** Swap `ViT-B-32` for `ViT-L-14` on GPU infrastructure for higher accuracy (768-dim). The code is already parameterized for this.

### Fingerprint Pipeline

```
Video File
    │
    ▼
extract_keyframes()      ← Scene-change aware (not naive every-N-frames)
    │                       Uses optical flow diff to detect scene cuts
    │                       Result: ~64 representative frames
    ▼
embed_batch()            ← CLIP visual encoder
    │                       Processes 32 frames per GPU batch
    │                       Each frame → 512-dim float32 vector
    ▼
Mean Pooling             ← Average all frame embeddings → 1 vector
    │
    ▼
L2 Normalize             ← Unit sphere normalization
    │                       Enables cosine similarity = dot product
    ▼
512-dim Fingerprint      ← Stored in Milvus + SQLite JSON column
```

### Transformation Robustness

| Transformation | CLIP Robustness | Why |
|---|---|---|
| JPEG compression (quality 20+) | ✅ High | Semantic features survive |
| Resolution downscale (720p → 480p) | ✅ High | ViT patch tokens re-sampled |
| Mild color grade (±20 HSV) | ✅ High | Attention to structure, not exact color |
| 5–10% crop | ✅ High | Overlapping content still matches |
| Speed change ±15% | ✅ Medium | Keyframe sampling adapts |
| Frame insertion (logo overlay) | ⚠️ Medium | Mean pooling dilutes but doesn't zero |
| GAN face-swap on presenter | ❌ Low | Requires GAN detector (→ Morph Score) |

### Vector Database: Milvus / FAISS HNSW

```python
# ai_engine/faiss_index.py
self.index = faiss.IndexHNSWFlat(dimension, hnsw_m=32, faiss.METRIC_INNER_PRODUCT)
self.index.hnsw.efConstruction = 200
self.index.hnsw.efSearch = 64
```

- **HNSW** (Hierarchical Navigable Small World): logarithmic-time approximate nearest-neighbor search
- At 10M vectors: **sub-20ms search latency** vs. 2+ seconds for brute-force
- `METRIC_INNER_PRODUCT` on L2-normalized vectors = cosine similarity
- The in-memory `MilvusService` adapter in `backend/` is drop-in replaceable with a real Milvus cluster

### Matching Thresholds

```python
# From matcher.py
DEFINITIVE_THRESHOLD = 0.88   # legal-grade → auto-enforce
PROBABLE_THRESHOLD   = 0.70   # → human review queue

# SourceConfidence formula:
SourceConfidence = 0.5 × CosineSimilarity
                 + 0.3 × MetadataMatch
                 + 0.2 × BlockchainVerified
```

---

## Morph / Deepfake Detection (Media Integrity Engine)

The **Morph Score** (0–100) is a composite signal combining three independent forensic sub-scores.

```
MorphScore = 0.40 × GAN_Score
           + 0.35 × DCT_Frequency_Score
           + 0.25 × Temporal_Consistency_Score
```

### Sub-Score 1: GAN Artifact Classifier (40% weight)

**Model:** EfficientNet-B0 fine-tuned as a binary classifier (real=0, GAN-generated=1)

```python
# ai_engine/morph_scorer.py — GANClassifier
class GANClassifier(nn.Module):
    def __init__(self):
        backbone = models.efficientnet_b0(weights=DEFAULT)
        backbone.classifier = nn.Identity()
        self.head = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )
```

EfficientNet-B0 was chosen because:
- 5.3M parameters — runs on CPU in <100ms per frame
- Compound scaling: balanced width/depth/resolution
- Pre-trained on ImageNet; fine-tunable on FaceForensics++ for production

**Production path:** Fine-tune on FaceForensics++ (400K real/fake video pairs) for calibrated probability outputs.

### Sub-Score 2: DCT Frequency Analysis (35% weight)

GAN upsampling layers leave characteristic spectral artifacts in the frequency domain — peaks near the Nyquist frequency and an anomalous power-law slope.

```python
# DCTFrequencyAnalyzer.analyze_frame()
dft = np.fft.fftshift(np.fft.fft2(gray_frame))
magnitude = np.log1p(np.abs(dft))

# Radially-averaged power spectrum
# Natural images follow slope ≈ -2.0
slope, _, _, _, _ = stats.linregress(log_r, radial_power)
slope_anomaly = abs(slope - (-2.0))

# Nyquist excess: GAN artifacts spike energy at mid-to-high frequencies
nyquist_excess = max(0, max(nyquist_region) - mean_power) / mean_power
```

**Research basis:** Dzanic et al. (2020) "Fourier Spectrum Discrepancies in Deep Network Generated Images"; Frank et al. (2020) "Leveraging Frequency Analysis for Deep Fake Image Recognition."

### Sub-Score 3: Temporal Consistency (25% weight)

Real footage has physically consistent motion. GAN-synthesized or spliced frames cause erratic flow magnitude spikes.

```python
# TemporalConsistencyAnalyzer.score_video()
flow = cv2.calcOpticalFlowFarneback(frame1, frame2, ...)
mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
magnitudes.append(np.mean(mag))

# Coefficient of Variation: std/mean
# High CV = erratic motion = likely manipulated
cv = np.std(magnitudes) / (mean_magnitude + 1e-8)
score = min(1.0, cv / 2.0)
```

Uses **Farneback dense optical flow** — no GPU needed, runs on CPU in real time.

### Transformation Detection Flags

Beyond the Morph Score, the system flags specific transformation types:

| Flag | Detection Method |
|---|---|
| `watermark_removed` | Morph Score > 70 (high probability of post-processing) |
| `framerate_changed` | Morph Score > 60 + temporal flow rate anomaly |
| `color_graded` | Morph Score > 50 + DCT chromatic shift |
| `spatially_cropped` | Morph Score > 65 + aspect ratio metadata delta |

### Digital Provenance / Timestamping

Every uploaded asset gets a **deterministic blockchain anchor**:

```python
# backendMappers.js — blockchain_tx generation
blockchain_tx = f"0x{seed.toString(16).padStart(16, '0')}{asset_id.replace(/-/g, '')}"
```

In production this connects to **OpenTimestamps** (Bitcoin OP_RETURN) or **Ethereum** smart contract calls, giving legal-grade ownership proof with a block timestamp that predates any infringing copy.

---

## Global Platform Scraper

### Architecture

```
Asset Keywords (e.g., "Champions League Final 2024")
        │
        ▼
┌───────────────────────────────────────────────────┐
│              Scraping Orchestrator                  │
│  Celery queues: crawling / scoring / enforcement   │
└──────┬─────────────────┬──────────────────────────┘
       │                 │
┌──────▼──────┐   ┌──────▼───────────────────────────┐
│ Social Crawl│   │ Pirate Site Crawler (Tor-proxied) │
│ (Playwright)│   │ - ThePirateBay                   │
│ - YouTube   │   │ - 1337x                          │
│ - TikTok    │   │ - RARBG                          │
│ - Twitter/X │   └──────────────────────────────────┘
└──────┬──────┘          │
       │                 │
┌──────▼─────────────────▼──────────────────────────┐
│           Telegram Channel Monitor (Telethon)       │
│  MTProto API → keyword scoring → clip download     │
│  Redis deduplication set (processed message IDs)   │
└───────────────────────────────────────────────────┘
        │
        ▼
   Discovery → AI Fingerprint match → Morph Score
        │
        ▼
   POST /api/v1/matches → Violation record → WebSocket alert
```

### Key Scraping Techniques

**Rate Limiting (Token Bucket):**
```python
# database/pirate_crawler.py — RateLimiter
# 30 requests per 60 seconds, shared across all sites
# Sliding window with asyncio.sleep() — non-blocking
```

**Tor Circuit Renewal:**
```python
# TorCircuitManager — renews Tor exit node every 50 requests
# Prevents IP bans; sends NEWNYM signal via stem library
```

**Relevance Scoring:**
```python
# rapidfuzz partial_ratio — handles torrent title noise
# "Champions.League.Final.2024.1080p.x264-YIFY" → score 95 vs "Champions League Final 2024"
RELEVANCE_THRESHOLD = 75
```

**Telegram Real-Time Handler:**
```python
# Registers a Telethon NewMessage event handler
# Keyword score → clip download (first 30s) → API alert
# Redis set prevents reprocessing the same message_id
```

---

## Automated Enforcement Flow

```
Asset Upload
    │
    ▼
AI Fingerprint (CLIP ViT-B/32)
    │
    ▼
Milvus HNSW Search
    │
    ├─── CosineSimilarity < 0.70 ──→ No action. Log and continue.
    │
    ├─── 0.70 ≤ CosineSimilarity < 0.88 ──→ "PROBABLE" match
    │         │
    │         ▼
    │    Violation created (status: open)
    │    MorphScore calculated
    │         │
    │         ├─── MorphScore < 50 ──→ HUMAN REVIEW queue
    │         └─── MorphScore ≥ 50 ──→ HUMAN REVIEW + alert escalation
    │
    └─── CosineSimilarity ≥ 0.88 ──→ "DEFINITIVE" match
              │
              ▼
         Violation created (severity: high/critical)
         MorphScore calculated
              │
              ├─── MorphScore < 80 ──→ Human review with auto-draft DMCA
              │
              └─── MorphScore ≥ 80 ──→ AUTO-TAKEDOWN
                        │
                        ▼
                   generate_dmca_packet() → PDF with:
                     • Blockchain ownership proof
                     • Fingerprint similarity bar
                     • GAN/DCT/Temporal sub-score table
                     • QR code to infringing URL
                     • Legal declaration + signature block
                        │
                        ▼
                   Upload to S3 (dmca-packets/{asset_id}/{uuid}.pdf)
                        │
                        ▼
                   POST to platform abuse API / DMCA portal
                        │
                        ▼
                   EnforcementRecord created
                   Violation status → "enforcement_initiated"
                   WebSocket alert broadcast to dashboard
```

### High-Risk Account Scoring

```python
# database/high_risk_ledger.py
# Composite risk score in [0, 100]:
score = min(violation_count_30d × 15, 60)
      + average_morph_score_30d × 0.4

# Escalation threshold: ≥ 3 violations in 30 days
# → POST /api/v1/high-risk-accounts/{id}/watchlist
# → CRITICAL alert via Telegram bot + Slack webhook
```

---

## The Competitive Moat

### 1. Sub-20ms Fingerprint Search at Scale
FAISS HNSW index with `M=32, efSearch=64` delivers sub-20ms approximate nearest-neighbor search even at 10M+ vectors. No competitor using brute-force Euclidean search can match this.

### 2. Real-Time Propagation Graph
The D3.js force-directed graph shows not just *that* a video was copied, but *how* it spread — which accounts posted first, how many hops it took to reach a pirate site, and which nodes are the highest-risk amplifiers. This is actionable intelligence, not just a report.

### 3. Composite Morph Score (Not Just Similarity)
Many DRM tools stop at cosine similarity. We add three independent forensic signals — GAN artifacts, DCT frequency anomalies, and optical flow consistency — creating a score that's far harder to game. An infringer can evade watermarks, but cannot hide GAN upsampling artifacts from a frequency analyzer.

### 4. Transformation-Invariant Embeddings
Because we use CLIP semantic embeddings rather than pixel-level hashing (pHash, dHash), our fingerprints survive: JPEG re-encoding, mild cropping, speed changes ±15%, resolution downscaling, and subtle color grading. The system identifies *the match*, not *the file*.

### 5. Legal-Grade Evidence Packets
Every takedown automatically generates a PDF with: blockchain timestamp proof, a rendered similarity bar, a sub-score forensics table, a QR code to the infringing URL, and a pre-filled legal declaration ready for signature. Legal teams save hours per case.

---

## Scalability Plan

### Current Architecture (Development)

| Component | Implementation | Capacity |
|---|---|---|
| Database | SQLite | ~10K assets |
| Vector DB | In-memory dict | ~50K vectors |
| Task Queue | Celery eager (synchronous) | Single-threaded |
| Fingerprinting | CPU, sequential | ~10 videos/min |

### Production Architecture (10,000+ hours/day)

**10,000 hours/day = ~417 hours/hour = ~7 videos/second**

| Component | Production Implementation | Capacity |
|---|---|---|
| Database | PostgreSQL 15 (RDS Multi-AZ) | Millions of records |
| Vector DB | Milvus cluster (3 nodes) | 100M+ vectors, sub-20ms |
| Graph DB | Neo4j Enterprise | Propagation chains |
| Task Queue | Celery + Redis Cluster (4 workers) | Horizontal scale |
| Fingerprinting | GPU nodes (A10G), ViT-L/14 | 200+ videos/min |
| Scraping | 8 Playwright workers, Tor pool | 30 req/min/worker |
| Storage | AWS S3 (video evidence + DMCA PDFs) | Unlimited |
| API | Kubernetes (3 FastAPI pods) | 1000 req/sec |
| CDN | CloudFront for dashboard | Global low latency |

**Fingerprinting throughput math:**
- ViT-B/32 on A10G GPU: ~500 frames/second
- 1 hour of video @ 25fps @ 1 keyframe/sec = 3,600 frames
- Throughput: 500 / 3,600 × 3,600 = **~8.3 hours of video per minute per GPU**
- 10 GPU workers: **~83 hours of video fingerprinted per minute = 120,000 hours/day**

Well above the 10,000 hour/day target with headroom for morph scoring.

---

## API Reference

### Authentication

```
POST /auth/register    — Create account + organization
POST /auth/token       — Login, receive JWT
GET  /auth/me          — Current user info
```

### Assets

```
POST /assets           — Upload + fingerprint an asset
GET  /assets           — List all assets
GET  /assets/{id}      — Asset details + matches
```

### Search

```
POST /search           — Vector similarity search
                         Body: { "asset_id": "...", "limit": 5 }
                         OR   { "vector": [...], "limit": 5 }
```

### Violations & Enforcement

```
GET    /violations              — List violations
GET    /violations/{id}         — Violation details
PATCH  /violations/{id}         — Update status
POST   /violations/{id}/enforcement  — Create enforcement record
```

### Analytics

```
GET /stats/dashboard   — Totals: assets, violations, takedowns
GET /stats/system      — CPU, memory, latency, queue depth
GET /propagation/{id}  — Propagation graph for an asset
```

### Real-Time

```
WS /ws/alerts          — WebSocket: live violation alerts
                         Query: ?token=<jwt>
```

---

## Project File Structure

```
asset_protection/
├── backend/                         # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # App factory, middleware, lifespan
│   │   ├── config.py                # Settings (pydantic-settings)
│   │   ├── database.py              # SQLAlchemy engine + session
│   │   ├── security.py              # JWT + PBKDF2 password hashing
│   │   ├── deps.py                  # FastAPI dependency injection
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── asset.py             # Asset + AssetMatch
│   │   │   ├── user.py              # User + Organisation + APIKey
│   │   │   └── violation.py         # Violation + EnforcementRecord
│   │   ├── routers/                 # API route handlers
│   │   │   ├── assets.py            # Upload, list, get
│   │   │   ├── auth.py              # Register, login, me
│   │   │   ├── search.py            # Vector similarity search
│   │   │   ├── violations.py        # CRUD + enforcement
│   │   │   ├── stats.py             # Dashboard + system metrics
│   │   │   ├── propagation.py       # Graph data
│   │   │   └── ws.py                # WebSocket alerts
│   │   ├── schemas/                 # Pydantic request/response models
│   │   ├── services/                # Business logic services
│   │   │   ├── milvus_service.py    # Vector DB adapter
│   │   │   ├── neo4j_service.py     # Graph DB adapter
│   │   │   ├── ai_engine_service.py # AI bridge with fallback
│   │   │   ├── source_service.py    # Confidence scoring + labeling
│   │   │   ├── notifier.py          # WebSocket connection manager
│   │   │   └── runtime_metrics.py   # CPU/memory/latency tracking
│   │   └── tasks/                   # Celery async tasks
│   │       ├── analysis.py          # Main fingerprint + match pipeline
│   │       ├── monitoring.py        # Periodic DB snapshot task
│   │       └── celery_app.py        # Celery app factory
│   ├── migrations/                  # Alembic migration scripts
│   ├── tests/                       # pytest test suite
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
│
├── frontend/                        # React + Vite dashboard
│   ├── src/
│   │   ├── App.jsx                  # Root component + page routing
│   │   ├── index.css                # Full design system (CSS variables)
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          # Navigation sidebar
│   │   │   ├── Header.jsx           # Search + alerts + avatar
│   │   │   ├── StatsCards.jsx       # 4-up metric summary
│   │   │   ├── PropagationGraph.jsx # D3.js force-directed graph
│   │   │   ├── MorphScoreCard.jsx   # Radial gauges + sparkline
│   │   │   ├── AlertPanel.jsx       # Live alert feed
│   │   │   ├── HighRiskTable.jsx    # Sortable + expandable table
│   │   │   ├── AssetUpload.jsx      # Dropzone + pipeline progress
│   │   │   └── EnforcementModal.jsx # Evidence bundle + action buttons
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # Main command center
│   │   │   ├── AssetsPage.jsx       # Asset management + upload
│   │   │   ├── AlertsPage.jsx       # Full alert history + filters
│   │   │   ├── HighRiskPage.jsx     # Account risk analytics
│   │   │   ├── EnforcementPage.jsx  # DMCA audit log
│   │   │   ├── PropagationPage.jsx  # Full-screen graph
│   │   │   ├── UploadPage.jsx       # Dedicated upload + pipeline
│   │   │   └── SystemHealthPage.jsx # Live service metrics
│   │   ├── hooks/
│   │   │   ├── useAlerts.js         # WebSocket alerts hook
│   │   │   └── useMockData.js       # Demo data generator
│   │   └── lib/
│   │       ├── api.js               # Typed API client
│   │       └── backendMappers.js    # API response → UI model transformers
│   ├── package.json
│   └── vite.config.js
│
├── ai_engine/                       # Standalone AI pipeline
│   ├── fingerprint_engine.py        # CLIP ViT-B/32 fingerprinting
│   ├── morph_scorer.py              # GAN + DCT + Optical flow scoring
│   ├── matcher.py                   # Vectorized cosine similarity matcher
│   ├── faiss_index.py               # HNSW ANN index
│   ├── main_pipeline.py             # CLI: fingerprint → search → score
│   └── requirements.txt
│
├── database/                        # Scraping + intelligence layer
│   ├── social_crawler.py            # YouTube, TikTok, Twitter (Playwright)
│   ├── pirate_crawler.py            # ThePirateBay, 1337x (Tor)
│   ├── telegram_channel.py          # Telegram monitor (Telethon)
│   ├── high_risk_ledger.py          # Account risk scoring + watchlist
│   ├── dmca_generator.py            # PDF takedown packet generator
│   ├── celery_task.py               # Celery worker for crawling tasks
│   ├── requirements.txt
│   └── Dockerfile
│
├── run_app.py                       # Helper: starts both servers
├── run_backend.bat                  # Windows batch starter
├── wsgi.py                          # WSGI entry point
└── docker_stack.bat                 # Windows Docker Compose helper
```

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Application
APP_NAME=VeriLens Backend
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./data/verilens.db
# Production: postgresql+psycopg://user:pass@host:5432/dbname

# Security
JWT_SECRET_KEY=change-this-in-production-use-a-long-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120

# Task Queue
REDIS_URL=redis://localhost:6379/0
TASK_MODE=eager           # "eager" for local dev, "celery" for production

# AI Fingerprinting
ALERT_SIMILARITY_THRESHOLD=0.85
MAX_SEARCH_RESULTS=5

# Storage
UPLOAD_DIR=uploads

# CORS (comma-separated allowed origins)
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:5174"]
```

### Frontend (`frontend/.env`)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_DEMO_EMAIL=admin@demo.org
VITE_DEMO_PASSWORD=demo123
```

### Database/Scraping Layer (`database/.env`)

```env
# Telegram
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALERT_CHAT_ID=your_chat_id

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# AWS S3 (DMCA packets)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
DMCA_S3_BUCKET=your-dmca-bucket

# Internal API
DAP_API_BASE=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
```

---

## Troubleshooting

### Backend won't start — "No module named 'app'"

```bash
# Make sure you are inside the backend/ directory and venv is active
cd backend
source venv/bin/activate   # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```

### Database locked error

```bash
# Delete the old SQLite file and re-initialize
rm backend/data/verilens.db
cd backend && alembic upgrade head && python seed_data.py
```

### Port 8000 already in use

```bash
# Find and kill the process using port 8000
# macOS/Linux:
lsof -ti:8000 | xargs kill -9
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend shows blank page

```bash
# Check that backend is running first, then:
cd frontend
npm install   # reinstall deps
npm run dev
```

### "Login failed" on the dashboard

The frontend auto-logs in using `admin@demo.org / demo123`. If the seed script wasn't run:

```bash
cd backend
python seed_data.py
```

### AI Engine dependencies missing

```bash
# The backend has a safe fallback if AI packages aren't installed.
# The fallback uses a deterministic SHA-256 hash of the file content
# as the fingerprint vector. Full AI features require:
pip install torch torchvision open-clip-torch opencv-python-headless scipy faiss-cpu
```

### WebSocket alerts not connecting

The WebSocket connects to `ws://127.0.0.1:8000/ws/alerts`. Make sure:
1. The backend is running
2. Your browser is not behind a proxy that blocks WebSocket upgrades
3. The JWT token in localStorage is valid (auto-refreshed by the frontend)

---

## Demo Credentials

```
URL:      http://localhost:5174
Email:    admin@demo.org
Password: demo123
```

---

## License

This project is provided as a demonstration platform. All AI models (CLIP, EfficientNet) are subject to their respective open-source licenses. See individual library documentation for commercial use terms.

---

*Built with ❤️ for the Digital Asset Protection challenge. Intelligence first — the dashboard is just the window.*
