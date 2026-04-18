/* ═══════════════════════════════════════════════════════════════════════
   AssetUpload — Drag-and-drop upload with live processing status
   ═══════════════════════════════════════════════════════════════════════ */

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload, CheckCircle, Fingerprint,
  ShieldCheck, X, Film
} from 'lucide-react';
import { fetchAssetDetails } from '../lib/api';

const PROCESSING_STAGES = [
  { key: 'uploading', label: 'Uploading', icon: Upload },
  { key: 'extracting', label: 'Extracting keyframes', icon: Film },
  { key: 'fingerprinting', label: 'AI Fingerprinting', icon: Fingerprint },
  { key: 'indexing', label: 'Indexing to Milvus', icon: ShieldCheck },
  { key: 'complete', label: 'Protected ✓', icon: CheckCircle },
];

const STAGE_INDEX = PROCESSING_STAGES.reduce((acc, stage, index) => {
  acc[stage.key] = index;
  return acc;
}, {});

function mapBackendStatus(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized === 'queued') return { stageKey: 'extracting', progress: 35 };
  if (normalized === 'processing' || normalized === 'extracting_keyframes') return { stageKey: 'extracting', progress: 50 };
  if (normalized === 'fingerprinting') return { stageKey: 'fingerprinting', progress: 70 };
  if (normalized === 'indexing_milvus') return { stageKey: 'indexing', progress: 90 };
  if (normalized === 'ready') return { stageKey: 'complete', progress: 100 };
  if (normalized === 'failed' || normalized === 'error') return { stageKey: 'indexing', progress: 0, failed: true };
  return { stageKey: 'uploading', progress: 30 };
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function waitForAssetCompletion(assetId, onProgress, maxAttempts = 90, pollIntervalMs = 1500) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const latest = await fetchAssetDetails(assetId);
    const mapped = mapBackendStatus(latest?.status);
    onProgress(mapped);

    if (mapped.failed) {
      throw new Error('Asset processing failed before fingerprinting/indexing completed.');
    }
    if ((latest?.status || '').toLowerCase() === 'ready') {
      return latest;
    }

    await sleep(pollIntervalMs);
  }

  throw new Error('Processing timeout: keyframe extraction/fingerprinting/indexing did not finish in time.');
}

function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B';
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function UploadItem({ file, onRemove }) {
  const isComplete = file.status === 'success';
  const isErrored = file.status === 'error';

  const currentStage = isComplete
    ? PROCESSING_STAGES[4]
    : PROCESSING_STAGES.find((stage) => stage.key === file.stageKey) || PROCESSING_STAGES[0];

  const overallProgress = Math.max(0, Math.min(100, file.progress ?? 0));
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
        background: isComplete ? 'var(--risk-safe-bg)' : isErrored ? 'var(--risk-critical-bg)' : 'rgba(255, 255, 255, 0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: isComplete ? 'var(--risk-safe)' : isErrored ? 'var(--risk-critical)' : 'var(--brand-primary-light)',
        flexShrink: 0,
      }}>
        {isComplete ? (
          <CheckCircle size={20} />
        ) : (
          <StageIcon size={20} style={isErrored ? undefined : { animation: 'spin 2s linear infinite' }} />
        )}
      </div>

      <div className="upload-file-info">
        <div className="upload-file-name">{file.name}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="upload-file-size">
            {formatFileSize(file.size)}
          </span>
          <span style={{
            fontSize: '0.7rem', color: isComplete ? 'var(--risk-safe)' : isErrored ? 'var(--risk-critical)' : 'var(--brand-primary-light)',
            fontWeight: 500,
          }}>
            {isErrored ? 'Upload failed' : currentStage.label}
          </span>
        </div>

        {!isComplete && !isErrored && (
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
        <span className={`upload-status-tag ${isComplete ? 'complete' : isErrored ? 'critical' : file.status === 'processing' ? 'fingerprinting' : 'processing'}`}>
          {isComplete ? 'Protected' : isErrored ? 'Failed' : `${Math.round(overallProgress)}%`}
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

  const activeFile = files.find((file) => file.status === 'uploading' || file.status === 'processing') || files[0] || null;
  const activeStageKey = activeFile?.status === 'success'
    ? 'complete'
    : activeFile?.stageKey || 'uploading';
  const activeStage = PROCESSING_STAGES.find((stage) => stage.key === activeStageKey) || PROCESSING_STAGES[0];
  const activeStageIndex = STAGE_INDEX[activeStage.key] ?? 0;

  const onDrop = useCallback((acceptedFiles) => {
    const queued = acceptedFiles.map((f) => ({
      name: f.name,
      size: f.size,
      id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(7),
      rawFile: f,
      assetId: null,
      stageKey: 'uploading',
      error: null,
      status: 'uploading',
      progress: 15,
    }));

    setFiles(prev => [...prev, ...queued]);

    if (typeof onUpload !== 'function') {
      setFiles((prev) => prev.map((file) => (
        queued.some((item) => item.id === file.id)
          ? { ...file, status: 'error', error: 'Upload handler is not available.', progress: 0 }
          : file
      )));
      return;
    }

    queued.forEach(async (item) => {
      try {
        setFiles((prev) => prev.map((file) => (
          file.id === item.id ? { ...file, status: 'uploading', progress: 35, stageKey: 'uploading' } : file
        )));

        const createdAsset = await onUpload(item.rawFile);
        const createdAssetId = createdAsset?.id;
        if (!createdAssetId) {
          throw new Error('Upload succeeded but asset id was not returned by backend.');
        }

        setFiles((prev) => prev.map((file) => {
          if (file.id !== item.id) return file;
          const mapped = mapBackendStatus(createdAsset?.status);
          return {
            ...file,
            assetId: createdAssetId,
            status: 'processing',
            stageKey: mapped.stageKey,
            progress: mapped.progress,
            error: null,
          };
        }));

        await waitForAssetCompletion(createdAssetId, (mapped) => {
          setFiles((prev) => prev.map((file) => (
            file.id === item.id
              ? {
                ...file,
                status: mapped.failed ? 'error' : 'processing',
                stageKey: mapped.stageKey,
                progress: mapped.progress,
                error: mapped.failed ? 'Processing failed.' : null,
              }
              : file
          )));
        });

        setFiles((prev) => prev.map((file) => (
          file.id === item.id ? { ...file, status: 'success', progress: 100, stageKey: 'complete', error: null } : file
        )));
      } catch (error) {
        setFiles((prev) => prev.map((file) => (
          file.id === item.id
            ? {
              ...file,
              status: 'error',
              stageKey: file.stageKey || 'indexing',
              progress: 0,
              error: error instanceof Error ? error.message : 'Upload failed.',
            }
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
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv'], 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
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
          const stageIndex = STAGE_INDEX[stage.key] ?? idx;
          const isCompleted = stageIndex < activeStageIndex;
          const isActive = stage.key === activeStage.key;

          let stageBg = 'var(--bg-card)';
          let stageColor = 'var(--text-secondary)';
          let stageBorder = '1px solid var(--border-subtle)';

          if (isCompleted) {
            stageBg = 'var(--risk-safe-bg)';
            stageColor = 'var(--risk-safe)';
            stageBorder = '1px solid var(--risk-safe-border)';
          } else if (isActive && activeFile?.status !== 'error') {
            stageBg = 'rgba(255, 255, 255, 0.12)';
            stageColor = 'var(--brand-primary-light)';
            stageBorder = '1px solid var(--border-default)';
          }

          return (
            <div key={stage.key} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '4px 10px', borderRadius: 'var(--radius-full)',
                background: stageBg, border: stageBorder,
                fontSize: '0.7rem', color: stageColor,
                transition: 'all 0.2s ease',
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

      {activeFile && (
        <div style={{
          marginTop: '-8px',
          marginBottom: 'var(--space-md)',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: activeFile.status === 'error' ? 'var(--risk-critical)' : 'var(--text-secondary)',
          fontWeight: 500,
        }}>
          {activeFile.status === 'error'
            ? `Current stage: ${activeStage.label} (failed)`
            : `Current stage: ${activeStage.label}`}
        </div>
      )}

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

