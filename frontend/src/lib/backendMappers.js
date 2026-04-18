function safeNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function hashToInt(input) {
  const text = String(input || 'seed');
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function inferPlatformFromUrl(url) {
  const value = String(url || '').toLowerCase();
  if (value.includes('youtube')) return 'youtube';
  if (value.includes('twitter') || value.includes('x.com')) return 'twitter';
  if (value.includes('tiktok')) return 'tiktok';
  if (value.includes('telegram')) return 'telegram';
  if (value.includes('facebook')) return 'facebook';
  return 'web';
}

function inferAccountIdFromUrl(url, fallbackId) {
  try {
    const parsed = new URL(url);
    const path = parsed.pathname.split('/').filter(Boolean)[0];
    if (path) {
      return `@${path.replace(/[^a-zA-Z0-9_]/g, '').slice(0, 16) || 'unknown'}`;
    }
    return `@${parsed.hostname.split('.')[0]}`;
  } catch {
    return `@acct_${String(fallbackId || '').slice(0, 8) || 'unknown'}`;
  }
}

function severityWeight(severity) {
  const normalized = String(severity || '').toLowerCase();
  if (normalized === 'critical') return 20;
  if (normalized === 'high') return 14;
  if (normalized === 'medium') return 8;
  if (normalized === 'low') return 3;
  return 5;
}

function statusToActionStatus(status) {
  const normalized = String(status || '').toLowerCase();
  if (normalized.includes('review')) return 'human_review';
  if (normalized.includes('enforcement') || normalized.includes('takedown')) return 'auto_takedown';
  if (normalized.includes('reject')) return 'rejected';
  if (normalized.includes('confirm') || normalized.includes('closed')) return 'confirmed';
  return 'pending';
}

export function buildAssetMap(assets = []) {
  return new Map(assets.map((asset) => [asset.id, asset]));
}

export function mapViolationToEnforcementData(violation, assetMap) {
  if (!violation) return null;
  const confidence = Math.max(0, Math.min(1, safeNumber(violation.confidence)));
  const severityBonus = severityWeight(violation.severity);
  const morphScore = Math.max(0, Math.min(99, Math.round(confidence * 100 + severityBonus / 2)));
  const seed = hashToInt(violation.id);
  const asset = assetMap?.get?.(violation.asset_id);
  const platform = inferPlatformFromUrl(violation.source_url);

  const ganScore = Math.max(0, Math.min(100, Math.round(morphScore * 0.9)));
  const freqScore = Math.max(0, Math.min(100, Math.round(morphScore * 0.75)));
  const temporalScore = Math.max(0, Math.min(100, Math.round(morphScore * 0.6)));

  return {
    violation_id: violation.id,
    asset_name: asset?.title || `Asset ${String(violation.asset_id).slice(0, 8)}`,
    infringing_url: violation.source_url || 'Not provided',
    platform,
    account_id: inferAccountIdFromUrl(violation.source_url, violation.id),
    cosine_similarity: Number(confidence.toFixed(4)),
    morph_score: morphScore,
    gan_score: ganScore,
    freq_score: freqScore,
    temporal_score: temporalScore,
    discovered_at: violation.created_at,
    blockchain_tx: `0x${seed.toString(16).padStart(16, '0')}${String(violation.asset_id || '').replace(/-/g, '').slice(0, 48)}`.slice(0, 66),
    transformation_flags: {
      watermark_removed: morphScore > 70,
      framerate_changed: morphScore > 60,
      color_graded: morphScore > 50,
      spatially_cropped: morphScore > 65,
    },
    propagation_depth: 1 + (seed % 5),
    views_estimate: Math.max(250, Math.round((confidence * 120000) + (seed % 3000))),
    action_status: statusToActionStatus(violation.status),
    summary: violation.summary,
    raw_violation: violation,
  };
}

export function buildHighRiskAccounts(violations = []) {
  const grouped = new Map();

  for (const violation of violations) {
    const platform = inferPlatformFromUrl(violation.source_url);
    const account_id = inferAccountIdFromUrl(violation.source_url, violation.id);
    const key = `${platform}::${account_id}`;

    if (!grouped.has(key)) {
      grouped.set(key, {
        id: key,
        account_id,
        platform,
        violations: [],
        assets: new Set(),
        first_seen: violation.created_at,
        last_seen: violation.created_at,
      });
    }

    const bucket = grouped.get(key);
    bucket.violations.push(violation);
    bucket.assets.add(violation.asset_id);
    if (new Date(violation.created_at) < new Date(bucket.first_seen)) {
      bucket.first_seen = violation.created_at;
    }
    if (new Date(violation.created_at) > new Date(bucket.last_seen)) {
      bucket.last_seen = violation.created_at;
    }
  }

  return Array.from(grouped.values()).map((bucket) => {
    const avgConfidence = bucket.violations.reduce((sum, item) => sum + safeNumber(item.confidence), 0) / Math.max(1, bucket.violations.length);
    const severityAvg = bucket.violations.reduce((sum, item) => sum + severityWeight(item.severity), 0) / Math.max(1, bucket.violations.length);
    const riskScore = Math.max(0, Math.min(99.9, (avgConfidence * 100) + severityAvg));

    return {
      id: bucket.id,
      account_id: bucket.account_id,
      platform: bucket.platform,
      violation_count: bucket.violations.length,
      risk_score: Number(riskScore.toFixed(1)),
      first_seen: bucket.first_seen,
      last_seen: bucket.last_seen,
      is_watchlisted: riskScore >= 70,
      total_morph_score_avg: Number((avgConfidence * 100).toFixed(1)),
      assets_targeted: bucket.assets.size,
      sample_violation_id: bucket.violations[0]?.id,
    };
  });
}

export function buildPropagationGraph(violations = [], assetMap) {
  const nodes = [];
  const links = [];
  const nodeSeen = new Set();
  const linkSeen = new Set();

  for (const violation of violations) {
    const accountId = inferAccountIdFromUrl(violation.source_url, violation.id);
    const urlId = violation.source_url || `url://${violation.id}`;
    const platform = inferPlatformFromUrl(violation.source_url);
    const confidence = Math.max(0, Math.min(1, safeNumber(violation.confidence)));

    if (!nodeSeen.has(accountId)) {
      nodeSeen.add(accountId);
      nodes.push({
        id: accountId,
        type: 'account',
        platform,
      });
    }

    if (!nodeSeen.has(urlId)) {
      nodeSeen.add(urlId);
      const asset = assetMap?.get?.(violation.asset_id);
      nodes.push({
        id: urlId,
        type: 'url',
        morph_score: Math.round(confidence * 100),
        cosine_sim: Number(confidence.toFixed(3)),
        violation_id: violation.id,
        asset_name: asset?.title || 'Protected Asset',
      });
    }

    const postedKey = `${accountId}->${urlId}:POSTED`;
    if (!linkSeen.has(postedKey)) {
      linkSeen.add(postedKey);
      links.push({ source: accountId, target: urlId, type: 'POSTED' });
    }
  }

  const urlNodes = nodes.filter((item) => item.type === 'url');
  for (let index = 0; index < urlNodes.length - 1; index += 1) {
    const source = urlNodes[index];
    const target = urlNodes[index + 1];
    const shareKey = `${source.id}->${target.id}:SHARED_TO`;
    if (!linkSeen.has(shareKey)) {
      linkSeen.add(shareKey);
      links.push({ source: source.id, target: target.id, type: 'SHARED_TO' });
    }
  }

  return { nodes, links };
}

export function buildMorphScoreData(violations = []) {
  if (!violations.length) {
    return {
      currentScore: 0,
      ganScore: 0,
      freqScore: 0,
      temporalScore: 0,
      history: [{ time: 'now', score: 0 }],
    };
  }

  const sorted = [...violations]
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  const scores = sorted.map((item) => Math.round(Math.max(0, Math.min(1, safeNumber(item.confidence))) * 100));
  const currentScore = scores[scores.length - 1] || 0;
  const avg = scores.reduce((sum, item) => sum + item, 0) / Math.max(1, scores.length);

  return {
    currentScore,
    ganScore: Number(Math.min(100, avg * 1.02).toFixed(1)),
    freqScore: Number(Math.min(100, avg * 0.92).toFixed(1)),
    temporalScore: Number(Math.min(100, avg * 0.82).toFixed(1)),
    history: scores.slice(-24).map((score, idx, arr) => ({
      time: `${arr.length - idx - 1}h ago`,
      score,
    })),
  };
}

export function mapViolationsToEnforcementLog(violations = [], assetMap) {
  return violations.map((violation) => mapViolationToEnforcementData(violation, assetMap)).filter(Boolean);
}
