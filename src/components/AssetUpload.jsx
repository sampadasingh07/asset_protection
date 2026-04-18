/* ═══════════════════════════════════════════════════════════════════════
   AssetUpload — Drag-and-drop upload with live processing status
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, CheckCircle, Fingerprint,
  ShieldCheck, X, Film
} from 'lucide-react';

const PROCESSING_STAGES = [
  { key: 'uploading', label: 'Uploading', icon: Upload, duration: 2000 },
  { key: 'extracting', label: 'Extracting keyframes', icon: Film, duration: 3000 },
  { key: 'fingerprinting', label: 'AI Fingerprinting', icon: Fingerprint, duration: 4000 },
  { key: 'indexing', label: 'Indexing to Milvus', icon: ShieldCheck, duration: 2000 },
  { key: 'complete', label: 'Protected ✓', icon: CheckCircle, duration: 0 },
];

function UploadItem({ file, onRemove }) {
  const [stageIdx, setStageIdx] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (stageIdx >= PROCESSING_STAGES.length - 1) return;

    const stage = PROCESSING_STAGES[stageIdx];
    const interval = 50;
    const steps = stage.duration / interval;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      setProgress(Math.min(100, (step / steps) * 100));
      if (step >= steps) {
        clearInterval(timer);
        setStageIdx(prev => prev + 1);
        setProgress(0);
      }
    }, interval);

    return () => clearInterval(timer);
  }, [stageIdx]);

  const currentStage = PROCESSING_STAGES[stageIdx];
  const isComplete = currentStage.key === 'complete';
  const overallProgress = ((stageIdx / (PROCESSING_STAGES.length - 1)) * 100);
  const StageIcon = currentStage.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="upload-progress-item"
    >
      <div style={{
        width: 40, height: 40, borderRadius: 'var(--radius-sm)',
        background: isComplete ? 'var(--risk-safe-bg)' : 'rgba(255, 255, 255, 0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: isComplete ? 'var(--risk-safe)' : 'var(--brand-primary-light)',
        flexShrink: 0,
      }}>
        {isComplete ? (
          <CheckCircle size={20} />
        ) : (
          <StageIcon size={20} style={{ animation: 'spin 2s linear infinite' }} />
        )}
      </div>

      <div className="upload-file-info">
        <div className="upload-file-name">{file.name}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="upload-file-size">
            {(file.size / (1024 * 1024)).toFixed(1)} MB
          </span>
          <span style={{
            fontSize: '0.7rem', color: isComplete ? 'var(--risk-safe)' : 'var(--brand-primary-light)',
            fontWeight: 500,
          }}>
            {currentStage.label}
          </span>
        </div>

        {!isComplete && (
          <div className="upload-progress-bar">
            <div className="upload-progress-fill" style={{ width: `${overallProgress}%` }} />
          </div>
        )}

        {file.error && (
          <div style={{ fontSize: '0.72rem', color: 'var(--risk-critical)', marginTop: '4px' }}>
            {file.error}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className={`upload-status-tag ${isComplete ? 'complete' : stageIdx > 1 ? 'fingerprinting' : 'processing'}`}>
          {isComplete ? 'Protected' : `${Math.round(overallProgress)}%`}
        </span>
        <button
          onClick={() => onRemove(file.id)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', padding: 4,
          }}
        >
          <X size={14} />
        </button>
      </div>
    </motion.div>
  );
}

export default function AssetUpload({ onUpload }) {
  const [files, setFiles] = useState([]);

  const onDrop = useCallback((acceptedFiles) => {
    const queued = acceptedFiles.map((f) => ({
      name: f.name,
      size: f.size,
      id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7),
      rawFile: f,
      error: null,
    }));

    setFiles(prev => [...prev, ...queued]);

    if (typeof onUpload !== 'function') {
      return;
    }

    queued.forEach(async (item) => {
      try {
        await onUpload(item.rawFile);
      } catch (error) {
        setFiles((prev) => prev.map((file) => (
          file.id === item.id
            ? { ...file, error: error instanceof Error ? error.message : 'Upload failed.' }
            : file
        )));
      }
    });
  }, [onUpload]);

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv'], 'image/*': ['.jpg', '.png', '.webp'] },
    maxSize: 500 * 1024 * 1024,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'active' : ''}`}
      >
        <input {...getInputProps()} id="asset-upload-input" />
        <div className="upload-icon-wrapper">
          <Upload size={28} />
        </div>
        <div className="upload-text">
          <div className="upload-text-primary">
            {isDragActive ? 'Drop your media files here...' : 'Upload Protected Assets'}
          </div>
          <div className="upload-text-secondary">
            Drag & drop video or image files, or{' '}
            <span className="upload-text-highlight">browse</span>
          </div>
          <div style={{
            fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px',
            display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'center',
          }}>
            <span>MP4, AVI, MOV, MKV</span>
            <span style={{ opacity: 0.3 }}>•</span>
            <span>Max 500MB</span>
            <span style={{ opacity: 0.3 }}>•</span>
            <span>Auto-fingerprinted</span>
          </div>
        </div>
      </div>

      {/* Processing pipeline info */}
      <div style={{
        display: 'flex', gap: 'var(--space-sm)', justifyContent: 'center',
        margin: 'var(--space-lg) 0', flexWrap: 'wrap',
      }}>
        {PROCESSING_STAGES.slice(0, -1).map((stage, idx) => {
          const Icon = stage.icon;
          return (
            <div key={stage.key} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '4px 10px', borderRadius: 'var(--radius-full)',
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                fontSize: '0.7rem', color: 'var(--text-secondary)',
              }}>
                <Icon size={12} />
                {stage.label}
              </div>
              {idx < PROCESSING_STAGES.length - 2 && (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>→</span>
              )}
            </div>
          );
        })}
      </div>

      {/* File queue */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="upload-progress-list"
          >
            {files.map(file => (
              <UploadItem key={file.id} file={file} onRemove={removeFile} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

