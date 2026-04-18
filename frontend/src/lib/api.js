const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const DEMO_EMAIL = import.meta.env.VITE_DEMO_EMAIL || 'admin@demo.org';
const DEMO_PASSWORD = import.meta.env.VITE_DEMO_PASSWORD || 'demo123';

function getAccessToken() {
  return localStorage.getItem('verilens_access_token') || localStorage.getItem('access_token');
}

function setAccessToken(token) {
  if (!token) return;
  localStorage.setItem('verilens_access_token', token);
  localStorage.setItem('access_token', token);
}

function clearAccessToken() {
  localStorage.removeItem('verilens_access_token');
  localStorage.removeItem('access_token');
}

async function requestDemoToken() {
  const response = await fetch(`${API_BASE_URL}/auth/token`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: DEMO_EMAIL,
      password: DEMO_PASSWORD,
    }),
  });

  if (!response.ok) {
    return null;
  }

  const payload = await response.json();
  if (!payload?.access_token) {
    return null;
  }

  setAccessToken(payload.access_token);
  return payload.access_token;
}

async function ensureAccessToken() {
  const existingToken = getAccessToken();
  if (existingToken) {
    return existingToken;
  }

  const demoToken = await requestDemoToken();
  if (demoToken) {
    return demoToken;
  }

  throw new Error('No access token found, and demo auto-login failed.');
}

async function parseError(response) {
  try {
    const payload = await response.json();
    return payload?.detail || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

async function apiRequest(path, options = {}) {
  const buildRequest = (token) => ({
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`,
    },
  });

  const token = await ensureAccessToken();

  let response = await fetch(`${API_BASE_URL}${path}`, buildRequest(token));

  // If a stale token is stored, refresh it once and retry automatically.
  if (response.status === 401) {
    clearAccessToken();
    const freshToken = await requestDemoToken();
    if (freshToken) {
      response = await fetch(`${API_BASE_URL}${path}`, buildRequest(freshToken));
    }
  }

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function fetchDashboardStats() {
  return apiRequest('/stats/dashboard');
}

export async function fetchSystemStats() {
  return apiRequest('/stats/system');
}

export async function fetchAssets() {
  return apiRequest('/assets');
}

export async function uploadAsset(file, sourceUrl = null) {
  const formData = new FormData();
  const title = file.name.replace(/\.[^.]+$/, '') || file.name;

  formData.append('title', title);
  if (sourceUrl) {
    formData.append('source_url', sourceUrl);
  }
  formData.append('file', file);

  return apiRequest('/assets', {
    method: 'POST',
    body: formData,
  });
}

// ═════════════════════════════════════════════════════════════════════
// SEARCH ENDPOINTS
// ═════════════════════════════════════════════════════════════════════

export async function searchAssets(searchQuery, limit = 20) {
  const query = String(searchQuery || '').trim().toLowerCase();
  if (!query) {
    return [];
  }

  const assets = await fetchAssets();
  return assets
    .filter((asset) => {
      const haystack = [asset.title, asset.file_name, asset.source_url]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    })
    .slice(0, Math.min(limit, 20))
    .map((asset) => ({
      asset_id: asset.id,
      title: asset.title,
      score: 1,
      confidence_label: 'match',
      source_url: asset.source_url,
      content_type: asset.content_type,
      created_at: asset.created_at,
    }));
}

export async function searchAssetById(assetId, limit = 5) {
  return apiRequest('/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      asset_id: assetId,
      limit: Math.min(limit, 20),
    }),
  });
}

// ═════════════════════════════════════════════════════════════════════
// VIOLATIONS ENDPOINTS
// ═════════════════════════════════════════════════════════════════════

export async function fetchViolations() {
  return apiRequest('/violations');
}

export async function fetchViolation(violationId) {
  return apiRequest(`/violations/${violationId}`);
}

export async function updateViolationStatus(violationId, status) {
  return apiRequest(`/violations/${violationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
}

export async function createEnforcementRecord(violationId, actionType, platformName, options = {}) {
  return apiRequest(`/violations/${violationId}/enforcement`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action_type: actionType,
      platform_name: platformName,
      status: options.status || 'PENDING',
      external_reference: options.externalReference || null,
      notes: options.notes || null,
    }),
  });
}

// ═════════════════════════════════════════════════════════════════════
// PROPAGATION ENDPOINTS
// ═════════════════════════════════════════════════════════════════════

export async function fetchPropagationGraph(assetId) {
  return apiRequest(`/propagation/${assetId}`);
}

// ═════════════════════════════════════════════════════════════════════
// ASSET DETAILS ENDPOINTS
// ═════════════════════════════════════════════════════════════════════

export async function fetchAssetDetails(assetId) {
  return apiRequest(`/assets/${assetId}`);
}

// ═════════════════════════════════════════════════════════════════════
// HEALTH & SYSTEM ENDPOINTS
// ═════════════════════════════════════════════════════════════════════

export async function fetchHealthStatus() {
  const token = getAccessToken();
  // Health check doesn't require auth
  const response = await fetch(`${API_BASE_URL}/health`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}
