export function formatTimestamp(date = new Date()) {
  return date.toLocaleString();
}

export function statusBadge(status) {
  const normalized = String(status || '').toLowerCase();
  let cls = 'neutral';
  if (['ok', 'completed', 'approved', 'ready'].some((x) => normalized.includes(x))) cls = 'ok';
  else if (['error', 'failed', 'degraded'].some((x) => normalized.includes(x))) cls = 'err';
  else if (['running', 'pending', 'queued', 'review', 'waiting'].some((x) => normalized.includes(x))) cls = 'warn';
  return `<span class="badge ${cls}">${status ?? 'n/a'}</span>`;
}

export function renderTable(columns, rows, emptyText = 'No items available.') {
  if (!rows || rows.length === 0) {
    return `<p class="muted">${emptyText}</p>`;
  }
  const header = columns.map((c) => `<th>${c.label}</th>`).join('');
  const body = rows
    .map((row) => `<tr>${columns.map((c) => `<td>${c.render ? c.render(row) : (row[c.key] ?? '')}</td>`).join('')}</tr>`)
    .join('');
  return `<table class="table"><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

export function renderPageShell({ title, description, controls = '', body = '', lastUpdated = null }) {
  const stamp = lastUpdated ? `<span class="muted">Last updated: ${lastUpdated}</span>` : '';
  return `
    <div class="meta-row">
      <div>
        <h2 class="panel-title">${title}</h2>
        <p class="muted">${description}</p>
      </div>
      <div>${stamp}</div>
    </div>
    ${controls}
    ${body}
  `;
}

export function renderStateMessage(kind, text) {
  return `<p class="state ${kind || ''}">${text}</p>`;
}
