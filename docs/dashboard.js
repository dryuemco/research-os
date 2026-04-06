const cfg = window.RPOS_SITE_CONFIG || {};
const base = (cfg.backendBaseUrl || '').replace(/\/$/, '');

const state = {
  partnerIds: [],
};

function setState(id, text, kind = '') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.className = `state ${kind}`.trim();
}

function badge(status) {
  const normalized = String(status || '').toLowerCase();
  let cls = 'neutral';
  if (['ok', 'completed', 'approved', 'ready'].some((x) => normalized.includes(x))) cls = 'ok';
  else if (['error', 'failed', 'degraded'].some((x) => normalized.includes(x))) cls = 'err';
  else if (['running', 'pending', 'queued', 'review', 'waiting'].some((x) => normalized.includes(x))) cls = 'warn';
  return `<span class="badge ${cls}">${status ?? 'n/a'}</span>`;
}

function renderTable(targetId, columns, rows) {
  const target = document.getElementById(targetId);
  if (!target) return;
  if (!rows || rows.length === 0) {
    target.innerHTML = '<p class="muted">No items available.</p>';
    return;
  }
  const header = columns.map((c) => `<th>${c.label}</th>`).join('');
  const body = rows
    .map((row) => `<tr>${columns.map((c) => `<td>${c.render ? c.render(row) : (row[c.key] ?? '')}</td>`).join('')}</tr>`)
    .join('');
  target.innerHTML = `<table class="table"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

async function fetchJson(path, options) {
  const res = await fetch(`${base}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`);
  }
  return res.json();
}

function applyLinks() {
  document.getElementById('backend-label').textContent = base
    ? `Backend URL: ${base}`
    : 'Backend URL is missing. Update docs/site-config.js.';
  document.getElementById('ui-link').href = `${base}/ui`;
  document.getElementById('docs-link').href = `${base}/docs`;
  document.getElementById('health-link').href = `${base}/health/ready`;
}

async function loadSummary() {
  setState('connectivity', 'Loading backend health...', 'loading');
  const [health, summary] = await Promise.all([
    fetchJson('/health/ready'),
    fetchJson('/dashboard/summary'),
  ]);
  const connectivity = health.status === 'ok' ? 'Backend healthy.' : `Backend reported: ${health.status}`;
  setState('connectivity', connectivity, health.status === 'ok' ? '' : 'error');
  const grid = document.getElementById('summary-grid');
  grid.innerHTML = Object.entries(summary)
    .map(([k, v]) => `<div class="kpi"><div class="label">${k}</div><div class="value">${v}</div></div>`)
    .join('');
}

async function loadOpportunities() {
  setState('opportunities-state', 'Loading...', 'loading');
  const data = await fetchJson('/dashboard/opportunities?limit=25');
  renderTable('opportunities-table', [
    { key: 'id', label: 'ID' },
    { key: 'title', label: 'Title' },
    { key: 'state', label: 'Status', render: (r) => badge(r.state) },
  ], data.items || []);
  setState('opportunities-state', `${(data.items || []).length} items loaded.`);
}

async function loadMatches() {
  setState('matches-state', 'Loading...', 'loading');
  const data = await fetchJson('/dashboard/matches?limit=25');
  renderTable('matches-table', [
    { key: 'id', label: 'ID' },
    { key: 'opportunity_id', label: 'Opportunity' },
    { key: 'total_score', label: 'Score' },
    { key: 'recommendation', label: 'Recommendation' },
    { key: 'explanations', label: 'Rationale', render: (r) => (r.explanations || []).join('; ') },
  ], data.items || []);
  setState('matches-state', `${(data.items || []).length} items loaded.`);
}

async function loadNotifications() {
  setState('notifications-state', 'Loading...', 'loading');
  const data = await fetchJson('/dashboard/operations/notifications?user_id=ops-admin&limit=25');
  renderTable('notifications-table', [
    { key: 'id', label: 'ID' },
    { key: 'type', label: 'Type' },
    { key: 'status', label: 'Status', render: (r) => badge(r.status) },
    { key: 'related_entity_type', label: 'Entity' },
  ], data.items || []);
  setState('notifications-state', `${(data.items || []).length} items loaded.`);
}

async function loadOperations() {
  setState('operations-state', 'Loading...', 'loading');
  const data = await fetchJson('/dashboard/operations/jobs?limit=25');
  renderTable('operations-table', [
    { key: 'id', label: 'ID' },
    { key: 'job_type', label: 'Job Type' },
    { key: 'status', label: 'Status', render: (r) => badge(r.status) },
    { key: 'trigger_source', label: 'Trigger' },
  ], data.items || []);
  setState('operations-state', `${(data.items || []).length} items loaded.`);
}

async function loadProposals() {
  setState('proposals-state', 'Loading...', 'loading');
  const data = await fetchJson('/dashboard/proposals?limit=25');
  renderTable('proposals-table', [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Proposal' },
    { key: 'state', label: 'Status', render: (r) => badge(r.state) },
    { key: 'opportunity_id', label: 'Opportunity' },
  ], data.items || []);
  setState('proposals-state', `${(data.items || []).length} items loaded.`);
}

async function loadExports() {
  setState('exports-state', 'Loading...', 'loading');
  const data = await fetchJson('/memory/exports');
  renderTable('exports-table', [
    { key: 'id', label: 'ID' },
    { key: 'package_name', label: 'Package' },
    { key: 'status', label: 'Status', render: (r) => badge(r.status) },
    { key: 'proposal_id', label: 'Proposal' },
  ], data || []);
  setState('exports-state', `${(data || []).length} items loaded.`);
}

async function loadRetrievalBackends() {
  setState('retrieval-backends-state', 'Loading...', 'loading');
  const data = await fetchJson('/intelligence/retrieval/backends');
  document.getElementById('retrieval-backends').textContent = JSON.stringify(data.items || [], null, 2);
  setState('retrieval-backends-state', 'Loaded retrieval backend capabilities.');
}

async function runRetrievalPreview() {
  const queryText = document.getElementById('retrieval-query').value.trim();
  if (!queryText) {
    setState('retrieval-state', 'Enter a query first.', 'error');
    return;
  }
  setState('retrieval-state', 'Running retrieval preview...', 'loading');
  const data = await fetchJson('/intelligence/retrieval/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query_text: queryText, limit: 5 }),
  });
  document.getElementById('retrieval-output').textContent = JSON.stringify(data, null, 2);
  setState('retrieval-state', `Retrieved ${data.count || 0} items.`);
}

async function loadPartnersAndFit() {
  setState('partners-state', 'Loading...', 'loading');
  const partners = await fetchJson('/intelligence/partners?active_only=true');
  state.partnerIds = (partners || []).map((p) => p.id).filter(Boolean);
  renderTable('partners-table', [
    { key: 'id', label: 'ID' },
    { key: 'partner_name', label: 'Partner' },
    { key: 'country_code', label: 'Country' },
    { key: 'capability_tags', label: 'Capabilities', render: (r) => (r.capability_tags || []).join(', ') },
  ], partners || []);
  setState('partners-state', `${(partners || []).length} partner profiles loaded.`);

  if (!state.partnerIds.length) {
    setState('partner-fit-state', 'No partners available for fit preview yet.', 'error');
    document.getElementById('partner-fit-output').textContent = 'Create partner profiles via API to enable live fit preview.';
    return;
  }

  setState('partner-fit-state', 'Running partner fit preview...', 'loading');
  const fit = await fetchJson('/intelligence/partners/fit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      opportunity_id: 'dashboard-preview',
      capability_tags: ['ai', 'data'],
      required_countries: [],
      partner_ids: state.partnerIds.slice(0, 5),
    }),
  });
  document.getElementById('partner-fit-output').textContent = JSON.stringify(fit, null, 2);
  setState('partner-fit-state', `Fit preview returned ${fit.length || 0} candidates.`);
}

async function runProposalQuality() {
  const proposalId = document.getElementById('proposal-id').value.trim();
  if (!proposalId) {
    setState('proposal-quality-state', 'Enter a proposal ID.', 'error');
    return;
  }
  setState('proposal-quality-state', 'Loading proposal quality...', 'loading');
  const data = await fetchJson(`/intelligence/proposal-quality/${encodeURIComponent(proposalId)}`);
  document.getElementById('proposal-quality-output').textContent = JSON.stringify(data, null, 2);
  setState('proposal-quality-state', 'Proposal quality summary loaded.');
}

async function safeLoad(loader, label) {
  try {
    await loader();
  } catch (error) {
    setState(`${label}-state`, `Failed to load ${label}: ${error.message}`, 'error');
  }
}

async function refreshAll() {
  if (!base) {
    setState('connectivity', 'Missing backendBaseUrl in docs/site-config.js.', 'error');
    return;
  }
  await safeLoad(loadSummary, 'connectivity');
  await Promise.all([
    safeLoad(loadOpportunities, 'opportunities'),
    safeLoad(loadMatches, 'matches'),
    safeLoad(loadNotifications, 'notifications'),
    safeLoad(loadOperations, 'operations'),
    safeLoad(loadProposals, 'proposals'),
    safeLoad(loadExports, 'exports'),
    safeLoad(loadRetrievalBackends, 'retrieval-backends'),
    safeLoad(loadPartnersAndFit, 'partners'),
  ]);
}

function wireEvents() {
  document.getElementById('refresh-all').addEventListener('click', refreshAll);
  document.getElementById('retrieval-run').addEventListener('click', () => safeLoad(runRetrievalPreview, 'retrieval'));
  document.getElementById('proposal-quality-run').addEventListener('click', () => safeLoad(runProposalQuality, 'proposal-quality'));
}

applyLinks();
wireEvents();
refreshAll();
