export class ApiClient {
  constructor(config) {
    this.base = config.backendBaseUrl;
    this.timeoutMs = config.requestTimeoutMs;
  }

  async get(path) {
    return this._request(path);
  }

  async post(path, body) {
    return this._request(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  }

  async _request(path, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.base}${path}`, {
        ...options,
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
