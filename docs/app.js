import { ApiClient } from './js/api-client.js';
import { getFrontendConfig, validateFrontendConfig } from './js/config.js';
import { buildPages } from './js/pages.js';

const config = getFrontendConfig();
const configError = validateFrontendConfig(config);
const api = new ApiClient(config);

const dom = {
  banner: document.getElementById('connection-banner'),
  refreshCurrent: document.getElementById('refresh-current'),
  links: {
    ui: document.getElementById('ui-link'),
    docs: document.getElementById('docs-link'),
    health: document.getElementById('health-link'),
  },
};

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

function init() {
  if (configError) {
    setConnectionBanner(configError, 'error');
  }
  applyHeaderLinks();
  wireNavigation();
  wireRefresh();
  currentPage = deriveInitialPage();
  showPage(currentPage);
  renderCurrentPage();
}

init();
