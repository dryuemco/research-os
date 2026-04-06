export function getFrontendConfig() {
  const cfg = window.RPOS_SITE_CONFIG || {};
  const backendBaseUrl = (cfg.backendBaseUrl || '').replace(/\/$/, '');
  return {
    backendBaseUrl,
    requestTimeoutMs: Number(cfg.requestTimeoutMs || 12000),
    notificationsUserId: cfg.notificationsUserId || 'ops-admin',
    pageSize: Number(cfg.pageSize || 25),
  };
}

export function validateFrontendConfig(config) {
  if (!config.backendBaseUrl) {
    return 'Missing backendBaseUrl in docs/site-config.js';
  }
  if (!config.backendBaseUrl.startsWith('http')) {
    return `Invalid backendBaseUrl: ${config.backendBaseUrl}`;
  }
  return null;
}
