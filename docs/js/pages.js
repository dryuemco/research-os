import { formatTimestamp, renderPageShell, renderStateMessage, renderTable, statusBadge } from './ui.js';

function safeIncludes(text, query) {
  return String(text || '').toLowerCase().includes(String(query || '').toLowerCase());
}

export function buildPages({ api, config, setConnectionBanner }) {
  const pageState = {
    opportunitiesQuery: '',
    matchesQuery: '',
    lastUpdated: {},
  };

  const setUpdated = (key) => {
    pageState.lastUpdated[key] = formatTimestamp();
    return pageState.lastUpdated[key];
  };

  const withError = (title, description, errorMessage, key) => {
    setConnectionBanner(`Backend/API issue: ${errorMessage}`, 'error');
    return renderPageShell({
      title,
      description,
      body: renderStateMessage('error', errorMessage),
      lastUpdated: pageState.lastUpdated[key] || null,
    });
  };

  return {
    async overview() {
      const title = 'Overview';
      const description = 'High-level platform counters and quick backend wiring visibility.';
      try {
        const [health, summary] = await Promise.all([
          api.get('/health/ready'),
          api.get('/dashboard/summary'),
        ]);
        setConnectionBanner(
          health.status === 'ok' ? 'Backend reachable and healthy.' : `Backend health status: ${health.status}`,
          health.status === 'ok' ? 'ok' : 'error',
        );
        const cards = Object.entries(summary)
          .map(([k, v]) => `<div class="kpi"><div class="label">${k}</div><div class="value">${v}</div></div>`)
          .join('');
        const body = `
          <p><b>Backend:</b> ${config.backendBaseUrl}</p>
          <p><b>Health:</b> ${statusBadge(health.status)}</p>
          <div class="summary-grid">${cards}</div>
        `;
        return renderPageShell({ title, description, body, lastUpdated: setUpdated('overview') });
      } catch (error) {
        return withError(title, description, error.message, 'overview');
      }
    },

    async health() {
      const title = 'System Health';
      const description = 'Live liveness/readiness and dependency health from backend.';
      try {
        const [health, ready] = await Promise.all([api.get('/health'), api.get('/health/ready')]);
        const body = `
          <div class="summary-grid">
            <div class="kpi"><div class="label">/health</div><div class="value">${statusBadge(health.status)}</div></div>
            <div class="kpi"><div class="label">/health/ready</div><div class="value">${statusBadge(ready.status)}</div></div>
            <div class="kpi"><div class="label">Environment</div><div class="value">${ready.app_env || 'n/a'}</div></div>
            <div class="kpi"><div class="label">Database</div><div class="value">${statusBadge(ready.database?.status || 'unknown')}</div></div>
          </div>
          <h3>Dependencies</h3>
          <pre class="box">${JSON.stringify(ready.dependencies || {}, null, 2)}</pre>
        `;
        return renderPageShell({ title, description, body, lastUpdated: setUpdated('health') });
      } catch (error) {
        return withError(title, description, error.message, 'health');
      }
    },

    async opportunities() {
      const title = 'Opportunities';
      const description = 'Latest opportunities from backend dashboard endpoint.';
      try {
        const data = await api.get(`/dashboard/opportunities?limit=${config.pageSize}`);
        const rows = (data.items || []).filter((item) => (
          !pageState.opportunitiesQuery
          || safeIncludes(item.title, pageState.opportunitiesQuery)
          || safeIncludes(item.id, pageState.opportunitiesQuery)
        ));
        const controls = `
          <div class="filters">
            <input id="opportunities-filter" type="search" placeholder="Filter by ID/title" value="${pageState.opportunitiesQuery}" />
          </div>
        `;
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'title', label: 'Title' },
          { key: 'state', label: 'Status', render: (r) => statusBadge(r.state) },
        ], rows, 'No opportunities available yet.');
        return renderPageShell({
          title,
          description,
          controls,
          body: `${renderStateMessage('', `${rows.length} items shown.`)}${table}`,
          lastUpdated: setUpdated('opportunities'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'opportunities');
      }
    },

    async matches() {
      const title = 'Matches';
      const description = 'Most recent matching outcomes and explanations.';
      try {
        const data = await api.get(`/dashboard/matches?limit=${config.pageSize}`);
        const rows = (data.items || []).filter((item) => (
          !pageState.matchesQuery
          || safeIncludes(item.id, pageState.matchesQuery)
          || safeIncludes(item.opportunity_id, pageState.matchesQuery)
          || safeIncludes(item.recommendation, pageState.matchesQuery)
        ));
        const controls = `
          <div class="filters">
            <input id="matches-filter" type="search" placeholder="Filter by ID/opportunity/recommendation" value="${pageState.matchesQuery}" />
          </div>
        `;
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'opportunity_id', label: 'Opportunity' },
          { key: 'total_score', label: 'Score' },
          { key: 'recommendation', label: 'Recommendation' },
          { key: 'explanations', label: 'Rationale', render: (r) => (r.explanations || []).join('; ') },
        ], rows, 'No matches available yet.');
        return renderPageShell({
          title,
          description,
          controls,
          body: `${renderStateMessage('', `${rows.length} items shown.`)}${table}`,
          lastUpdated: setUpdated('matches'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'matches');
      }
    },

    async notifications() {
      const title = 'Notifications';
      const description = `Notifications for user '${config.notificationsUserId}'.`;
      try {
        const data = await api.get(`/dashboard/operations/notifications?user_id=${encodeURIComponent(config.notificationsUserId)}&limit=${config.pageSize}`);
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'type', label: 'Type' },
          { key: 'status', label: 'Status', render: (r) => statusBadge(r.status) },
          { key: 'related_entity_type', label: 'Entity Type' },
          { key: 'related_entity_id', label: 'Entity ID' },
        ], data.items || [], 'No notifications available yet.');
        return renderPageShell({
          title,
          description,
          body: `${renderStateMessage('', `${(data.items || []).length} items loaded.`)}${table}`,
          lastUpdated: setUpdated('notifications'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'notifications');
      }
    },

    async operations() {
      const title = 'Operational Runs';
      const description = 'Recent operational job run statuses.';
      try {
        const data = await api.get(`/dashboard/operations/jobs?limit=${config.pageSize}`);
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'job_type', label: 'Job Type' },
          { key: 'status', label: 'Status', render: (r) => statusBadge(r.status) },
          { key: 'trigger_source', label: 'Trigger Source' },
          { key: 'error_summary', label: 'Error' },
        ], data.items || [], 'No operational runs available yet.');
        return renderPageShell({
          title,
          description,
          body: `${renderStateMessage('', `${(data.items || []).length} items loaded.`)}${table}`,
          lastUpdated: setUpdated('operations'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'operations');
      }
    },

    async proposals() {
      const title = 'Proposal Workspaces';
      const description = 'Proposal lifecycle status overview.';
      try {
        const data = await api.get(`/dashboard/proposals?limit=${config.pageSize}`);
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'name', label: 'Name' },
          { key: 'state', label: 'State', render: (r) => statusBadge(r.state) },
          { key: 'opportunity_id', label: 'Opportunity ID' },
        ], data.items || [], 'No proposals available yet.');
        return renderPageShell({
          title,
          description,
          body: `${renderStateMessage('', `${(data.items || []).length} items loaded.`)}${table}`,
          lastUpdated: setUpdated('proposals'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'proposals');
      }
    },

    async exports() {
      const title = 'Export Packages';
      const description = 'Export package lifecycle and proposal linkage.';
      try {
        const data = await api.get('/memory/exports');
        const table = renderTable([
          { key: 'id', label: 'ID' },
          { key: 'package_name', label: 'Package Name' },
          { key: 'status', label: 'Status', render: (r) => statusBadge(r.status) },
          { key: 'proposal_id', label: 'Proposal ID' },
        ], data || [], 'No export packages available yet.');
        return renderPageShell({
          title,
          description,
          body: `${renderStateMessage('', `${(data || []).length} items loaded.`)}${table}`,
          lastUpdated: setUpdated('exports'),
        });
      } catch (error) {
        return withError(title, description, error.message, 'exports');
      }
    },

    async intelligence() {
      const title = 'Intelligence';
      const description = 'Retrieval, partner intelligence, and proposal quality previews.';
      try {
        const [retrievalBackends, partners] = await Promise.all([
          api.get('/intelligence/retrieval/backends'),
          api.get('/intelligence/partners?active_only=true'),
        ]);

        let fitPreviewOutput = 'No active partners available; fit preview skipped.';
        if ((partners || []).length > 0) {
          const fitResult = await api.post('/intelligence/partners/fit', {
            opportunity_id: 'dashboard-preview',
            capability_tags: ['ai', 'data'],
            required_countries: [],
            partner_ids: partners.slice(0, 5).map((p) => p.id),
          });
          fitPreviewOutput = JSON.stringify(fitResult, null, 2);
        }

        const retrievalPreview = await api.post('/intelligence/retrieval/preview', {
          query_text: 'proposal execution evidence',
          limit: 5,
        });

        const proposalInput = `
          <div class="filters">
            <input id="proposal-quality-id" type="text" placeholder="Proposal ID for quality summary" />
            <button id="proposal-quality-load" type="button">Load Summary</button>
          </div>
          <pre id="proposal-quality-output" class="box">Provide a proposal ID to fetch quality summary.</pre>
        `;

        const body = `
          <h3>Retrieval Backends</h3>
          <pre class="box">${JSON.stringify(retrievalBackends.items || [], null, 2)}</pre>
          <h3>Retrieval Preview</h3>
          <pre class="box">${JSON.stringify(retrievalPreview, null, 2)}</pre>
          <h3>Partners</h3>
          ${renderTable([
            { key: 'id', label: 'ID' },
            { key: 'partner_name', label: 'Partner' },
            { key: 'country_code', label: 'Country' },
            { key: 'capability_tags', label: 'Capability Tags', render: (r) => (r.capability_tags || []).join(', ') },
          ], partners || [], 'No active partners available yet.')}
          <h3>Partner Fit Preview</h3>
          <pre class="box">${fitPreviewOutput}</pre>
          <h3>Proposal Quality Summary</h3>
          ${proposalInput}
        `;

        return renderPageShell({ title, description, body, lastUpdated: setUpdated('intelligence') });
      } catch (error) {
        return withError(title, description, error.message, 'intelligence');
      }
    },

    bindPostRenderHandlers(pageKey, rerender) {
      if (pageKey === 'opportunities') {
        const input = document.getElementById('opportunities-filter');
        if (input) {
          input.addEventListener('input', (event) => {
            pageState.opportunitiesQuery = event.target.value;
            rerender();
          });
        }
      }
      if (pageKey === 'matches') {
        const input = document.getElementById('matches-filter');
        if (input) {
          input.addEventListener('input', (event) => {
            pageState.matchesQuery = event.target.value;
            rerender();
          });
        }
      }
      if (pageKey === 'intelligence') {
        const button = document.getElementById('proposal-quality-load');
        if (button) {
          button.addEventListener('click', async () => {
            const proposalId = document.getElementById('proposal-quality-id')?.value?.trim();
            const output = document.getElementById('proposal-quality-output');
            if (!output) return;
            if (!proposalId) {
              output.textContent = 'Please enter a proposal ID.';
              return;
            }
            output.textContent = 'Loading...';
            try {
              const result = await api.get(`/intelligence/proposal-quality/${encodeURIComponent(proposalId)}`);
              output.textContent = JSON.stringify(result, null, 2);
            } catch (error) {
              output.textContent = `Failed to load proposal quality: ${error.message}`;
            }
          });
        }
      }
    },
  };
}
