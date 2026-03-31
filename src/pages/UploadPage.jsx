/* ═══════════════════════════════════════════════════════════════════════
   UploadPage — Dedicated asset upload page
   ═══════════════════════════════════════════════════════════════════════ */

import AssetUpload from '../components/AssetUpload';
import { Shield, Fingerprint, Link, Zap } from 'lucide-react';

const FEATURES = [
  {
    icon: Fingerprint,
    title: 'AI Fingerprinting',
    description: 'CLIP ViT-L/14 generates 512-dim transformation-invariant embeddings',
    color: '#FFFFFF',
  },
  {
    icon: Shield,
    title: 'Morph Detection',
    description: 'GAN + DCT + Temporal analysis scores media integrity 0-100',
    color: '#FFFFFF',
  },
  {
    icon: Link,
    title: 'Blockchain Provenance',
    description: 'OpenTimestamps anchoring for legal-grade ownership proof',
    color: '#888888',
  },
  {
    icon: Zap,
    title: 'Sub-20ms Search',
    description: 'Milvus HNSW index enables real-time fingerprint matching at scale',
    color: '#F5F5F5',
  },
];

export default function UploadPage() {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Upload & Protect</h1>
        <p className="page-subtitle">
          Upload media assets for automated AI fingerprinting and continuous monitoring
        </p>
      </div>

      <AssetUpload />

      {/* Features section */}
      <div style={{ marginTop: 'var(--space-2xl)' }}>
        <h3 style={{
          fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase',
          letterSpacing: '0.08em', color: 'var(--text-muted)',
          marginBottom: 'var(--space-lg)',
        }}>
          Protection Pipeline
        </h3>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: 'var(--space-md)',
        }}>
          {FEATURES.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div key={idx} className="card animate-slide-up" style={{ animationDelay: `${idx * 100}ms` }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 'var(--radius-sm)',
                  background: `${feat.color}18`, color: feat.color,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginBottom: 'var(--space-md)',
                }}>
                  <Icon size={20} />
                </div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, fontSize: '0.9rem' }}>
                  {feat.title}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  {feat.description}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

