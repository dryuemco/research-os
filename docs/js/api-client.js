export class ApiClient {
  constructor(config) {
    this.base = config.backendBaseUrl;
    this.timeoutMs = config.requestTimeoutMs;
    this.bearerToken = '';
  }

  async get(path) {
    return this._request(path);
  }

  async post(path, body, withAuth = true) {
    return this._request(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }, withAuth);
  }

  setBearerToken(token) {
    this.bearerToken = token || '';
  }

  async _request(path, options = {}, withAuth = true) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    const headers = { ...(options.headers || {}) };
    if (withAuth && this.bearerToken) {
      headers.Authorization = `Bearer ${this.bearerToken}`;
    }
    try {
      const response = await fetch(`${this.base}${path}`, {
        ...options,
        headers,
        signal: controller.signal,
      });
      const responseText = await response.text();
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}${responseText ? ` - ${responseText}` : ''}`);
      }
      return responseText ? JSON.parse(responseText) : {};
    } catch (error) {
      if (error?.name === 'AbortError') {
        throw new Error(`Request timed out after ${this.timeoutMs}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }
}
