import { ApiClient } from './js/api-client.js';
import { getFrontendConfig, validateFrontendConfig } from './js/config.js';
import { buildPages } from './js/pages.js';

const config = getFrontendConfig();
const configError = validateFrontendConfig(config);
const api = new ApiClient(config);

const TOKEN_KEY = 'rpos_access_token';

const dom = {
  banner: document.getElementById('connection-banner'),
  refreshCurrent: document.getElementById('refresh-current'),
  links: {
    ui: document.getElementById('ui-link'),
    docs: document.getElementById('docs-link'),
    health: document.getElementById('health-link'),
  },
  shell: document.querySelector('.shell'),
  loginMount: document.createElement('section'),
};

dom.loginMount.id = 'login-gate';
dom.loginMount.className = 'page active';

function loadToken() {
  return window.localStorage.getItem(TOKEN_KEY) || '';
}

function saveToken(token) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

function setConnectionBanner(message, kind = '') {
  if (!dom.banner) return;
  if (!message) {
    dom.banner.textContent = '';
    dom.banner.className = 'banner hidden';
    return;
  }
  dom.banner.textContent = message;
  dom.banner.className = `banner ${kind || ''}`.trim();
}

function applyHeaderLinks() {
  dom.links.ui.href = `${config.backendBaseUrl}/ui`;
  dom.links.docs.href = `${config.backendBaseUrl}/docs`;
  dom.links.health.href = `${config.backendBaseUrl}/health/ready`;
}

const pages = buildPages({ api, config, setConnectionBanner });
let currentPage = 'overview';

function showPage(pageKey) {
  document.querySelectorAll('.nav-link').forEach((el) => {
    el.classList.toggle('active', el.dataset.page === pageKey);
  });
  document.querySelectorAll('.page').forEach((el) => {
    el.classList.toggle('active', el.id === `page-${pageKey}`);
  });
}

async function renderCurrentPage() {
  const target = document.getElementById(`page-${currentPage}`);
  if (!target) return;
  target.innerHTML = `<p class="state loading">Loading ${currentPage}...</p>`;
  const renderer = pages[currentPage];
  if (!renderer) {
    target.innerHTML = `<p class="state error">Unknown page: ${currentPage}</p>`;
    return;
  }
  const html = await renderer();
  target.innerHTML = html;
  pages.bindPostRenderHandlers(currentPage, renderCurrentPage);
}

function wireNavigation() {
  document.querySelectorAll('.nav-link').forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      currentPage = link.dataset.page;
      history.replaceState({}, '', `#${currentPage}`);
      showPage(currentPage);
      renderCurrentPage();
    });
  });
}

function wireRefresh() {
  dom.refreshCurrent.addEventListener('click', () => renderCurrentPage());
}

function deriveInitialPage() {
  const hash = window.location.hash.replace('#', '').trim();
  if (hash && pages[hash]) return hash;
  return 'overview';
}

function renderLoginGate(message = '') {
  dom.loginMount.innerHTML = `
    <div class="card">
      <h2>Login required</h2>
      <p class="muted">Sign in with your RPOS admin username/password before using the dashboard.</p>
      ${message ? `<p class="state error">${message}</p>` : ''}
      <form id="login-form" class="stack" style="max-width: 420px; gap: 10px;">
        <label>Username<br /><input id="login-username" type="text" required /></label>
        <label>Password<br /><input id="login-password" type="password" required /></label>
        <button type="submit">Login</button>
      </form>
    </div>
  `;

  const form = document.getElementById('login-form');
  form?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const username = document.getElementById('login-username')?.value?.trim();
    const password = document.getElementById('login-password')?.value || '';
    if (!username || !password) {
      renderLoginGate('Username and password are required.');
      return;
    }
    try {
      const result = await api.post('/auth/login', { username, password }, false);
      saveToken(result.access_token);
      api.setBearerToken(result.access_token);
      bootDashboard();
    } catch (error) {
      renderLoginGate(error.message || 'Login failed');
    }
  });
}

function showLoginGate(message = '') {
  if (dom.shell) {
    dom.shell.style.display = 'none';
    dom.shell.insertAdjacentElement('beforebegin', dom.loginMount);
  }
  renderLoginGate(message);
}

function hideLoginGate() {
  dom.loginMount.remove();
  if (dom.shell) dom.shell.style.display = '';
}

function bootDashboard() {
  hideLoginGate();
  currentPage = deriveInitialPage();
  showPage(currentPage);
  renderCurrentPage();
}

function init() {
  if (configError) {
    setConnectionBanner(configError, 'error');
  }
  applyHeaderLinks();
  wireNavigation();
  wireRefresh();

  const token = loadToken();
  if (!token) {
    showLoginGate();
    return;
  }

  api.setBearerToken(token);
  bootDashboard();
}

init();
