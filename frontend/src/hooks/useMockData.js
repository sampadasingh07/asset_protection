/* ═══════════════════════════════════════════════════════════════════════
   Mock Data Generator — Simulates backend API data
   ═══════════════════════════════════════════════════════════════════════ */

const PLATFORMS = ['youtube', 'twitter', 'tiktok', 'telegram', 'pirate', 'torrent'];
const ACCOUNTS = [
  '@sports_leaks_hd', '@replay_king99', '@match_clips_tv', '@goal_uploads',
  '@pirate_streams', '@football_free', '@highlights247', '@live_sports_bot',
  '@clip_master_x', '@stream_zone_hd', '@soccer_replay', '@matches_daily',
  '@sports_hub_free', '@full_match_hd', '@viral_goals_24', '@sport_rip_bot'
];

const ASSET_NAMES = [
  'Champions League Final 2024', 'Premier League GW38 Highlights',
  'World Cup Semi-Final', 'La Liga El Clasico', 'Serie A Derby Milan',
  'Bundesliga TopMatch', 'UEFA Europa League Final', 'Copa America Final',
  'FA Cup Quarter-Final', 'MLS Cup 2024'
];

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

function randInt(min, max) {
  return Math.floor(rand(min, max));
}

function pick(arr) {
  return arr[randInt(0, arr.length)];
}

function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15);
}

function timeAgo(minutesAgo) {
  const d = new Date(Date.now() - minutesAgo * 60000);
  return d.toISOString();
}

// ─── Propagation Graph Data ──────────────────────────────────────────
export function generatePropagationData() {
  const nodeCount = randInt(12, 24);
  const nodes = [];
  const links = [];
  const accountCount = randInt(4, 8);

  // Create account nodes
  for (let i = 0; i < accountCount; i++) {
    nodes.push({
      id: ACCOUNTS[i % ACCOUNTS.length],
      type: 'account',
      platform: pick(PLATFORMS.slice(0, 4)),
    });
  }

  // Create URL nodes
  for (let i = 0; i < nodeCount - accountCount; i++) {
    const morphScore = rand(10, 95);
    nodes.push({
      id: `https://${pick(['pirate-stream', 'free-match', 'watchnow', 'sportsfree', 'replay-zone'])}.com/${generateId().slice(0, 8)}`,
      type: 'url',
      morph_score: Math.round(morphScore),
      cosine_sim: +(rand(0.72, 0.99)).toFixed(3),
    });
  }

  // Create POSTED links (account → url)
  const urlNodes = nodes.filter(n => n.type === 'url');
  const accountNodes = nodes.filter(n => n.type === 'account');
  urlNodes.forEach(urlNode => {
    const account = pick(accountNodes);
    links.push({ source: account.id, target: urlNode.id, type: 'POSTED' });
  });

  // Create some SHARED_TO links (url → url)
  for (let i = 0; i < Math.min(urlNodes.length - 1, randInt(3, 7)); i++) {
    const src = urlNodes[i];
    const tgt = urlNodes[i + 1];
    if (src && tgt) {
      links.push({ source: src.id, target: tgt.id, type: 'SHARED_TO' });
    }
  }

  return { nodes, links };
}

// ─── Morph Score Data ────────────────────────────────────────────────
export function generateMorphScoreData() {
  const currentScore = rand(20, 90);
  const ganScore = rand(15, 95);
  const freqScore = rand(10, 85);
  const temporalScore = rand(5, 75);

  const history = [];
  for (let i = 24; i >= 0; i--) {
    history.push({
      time: `${i}h ago`,
      score: Math.round(rand(Math.max(0, currentScore - 25), Math.min(100, currentScore + 25))),
    });
  }

  return {
    currentScore: Math.round(currentScore * 100) / 100,
    ganScore: Math.round(ganScore * 100) / 100,
    freqScore: Math.round(freqScore * 100) / 100,
    temporalScore: Math.round(temporalScore * 100) / 100,
    history,
  };
}

// ─── High Risk Accounts ─────────────────────────────────────────────
export function generateHighRiskAccounts() {
  return ACCOUNTS.slice(0, randInt(8, 14)).map((account, idx) => ({
    id: generateId(),
    account_id: account,
    platform: pick(PLATFORMS.slice(0, 4)),
    violation_count: randInt(1, 25),
    risk_score: +(rand(30, 99)).toFixed(1),
    first_seen: timeAgo(randInt(1000, 50000)),
    last_seen: timeAgo(randInt(1, 500)),
    is_watchlisted: Math.random() > 0.4,
    total_morph_score_avg: +(rand(20, 85)).toFixed(1),
    assets_targeted: randInt(1, 8),
  }));
}

// ─── Alerts ──────────────────────────────────────────────────────────
export function generateAlert() {
  const severity = pick(['CRITICAL', 'WARNING', 'INFO']);
  const platform = pick(PLATFORMS);
  const morphScore = severity === 'CRITICAL' ? rand(70, 98) : severity === 'WARNING' ? rand(40, 70) : rand(5, 40);
  const account = pick(ACCOUNTS);
  
  const messages = {
    CRITICAL: [
      `AUTO-TAKEDOWN filed on ${platform} — morph score ${morphScore.toFixed(1)}`,
      `High-confidence piracy detected: ${pick(ASSET_NAMES)} on ${platform}`,
      `Repeat offender ${account} posted copyrighted content on ${platform}`,
    ],
    WARNING: [
      `Probable match found on ${platform} — similarity ${rand(85, 95).toFixed(1)}%`,
      `New match requires review: ${pick(ASSET_NAMES)} on ${platform}`,
      `Content transformation detected on ${platform} — morph ${morphScore.toFixed(1)}`,
    ],
    INFO: [
      `New content scan completed on ${platform} — ${randInt(10, 200)} URLs checked`,
      `Fingerprint indexed for ${pick(ASSET_NAMES)}`,
      `Watchlist update: ${account} activity on ${platform}`,
    ],
  };

  return {
    id: generateId(),
    severity,
    message: pick(messages[severity]),
    platform,
    assetId: generateId(),
    morphScore: Math.round(morphScore * 10) / 10,
    url: `https://${platform}.com/${generateId().slice(0, 10)}`,
    timestamp: timeAgo(randInt(0, 180)),
    read: false,
  };
}

export function generateInitialAlerts(count = 12) {
  return Array.from({ length: count }, () => generateAlert())
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

// ─── Dashboard Stats ─────────────────────────────────────────────────
export function generateDashboardStats() {
  return {
    totalAssets: randInt(1200, 5000),
    matchesDetected: randInt(300, 1500),
    takedownsFiled: randInt(80, 400),
    highRiskAccounts: randInt(15, 80),
    matchesToday: randInt(5, 45),
    changeAssets: +(rand(-5, 15)).toFixed(1),
    changeMatches: +(rand(-10, 30)).toFixed(1),
    changeTakedowns: +(rand(-5, 20)).toFixed(1),
    changeHighRisk: +(rand(-3, 12)).toFixed(1),
  };
}

// ─── Assets List ─────────────────────────────────────────────────────
export function generateAssets() {
  return ASSET_NAMES.map((name, i) => ({
    id: generateId(),
    filename: `${name.toLowerCase().replace(/\s+/g, '_')}.mp4`,
    name,
    status: pick(['active', 'processing', 'fingerprinted', 'active', 'active']),
    matches_count: randInt(0, 50),
    morph_score_avg: +(rand(15, 80)).toFixed(1),
    uploaded_at: timeAgo(randInt(100, 20000)),
    duration: `${randInt(10, 120)}:${String(randInt(0, 59)).padStart(2, '0')}`,
    blockchain_verified: Math.random() > 0.3,
  }));
}

// ─── Enforcement Action ──────────────────────────────────────────────
export function generateEnforcementData() {
  return {
    violation_id: generateId(),
    asset_name: pick(ASSET_NAMES),
    infringing_url: `https://${pick(['pirate-tv', 'free-sports', 'streamhub'])}.com/${generateId().slice(0, 8)}`,
    platform: pick(PLATFORMS),
    account_id: pick(ACCOUNTS),
    cosine_similarity: +(rand(0.82, 0.99)).toFixed(4),
    morph_score: +(rand(50, 98)).toFixed(1),
    gan_score: +(rand(30, 95)).toFixed(1),
    freq_score: +(rand(20, 85)).toFixed(1),
    temporal_score: +(rand(10, 70)).toFixed(1),
    discovered_at: timeAgo(randInt(1, 60)),
    blockchain_tx: '0x' + Array.from({ length: 64 }, () => '0123456789abcdef'[randInt(0, 16)]).join(''),
    transformation_flags: {
      watermark_removed: Math.random() > 0.5,
      framerate_changed: Math.random() > 0.7,
      color_graded: Math.random() > 0.6,
      spatially_cropped: Math.random() > 0.5,
    },
    propagation_depth: randInt(1, 6),
    views_estimate: randInt(500, 500000),
  };
}

