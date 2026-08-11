/* ===== API client ===== */
const API = {
  async request(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data && data.detail ? data.detail : 'Error de conexión con el servidor.';
      throw new Error(detail);
    }
    return data;
  },

  get(path) { return this.request('GET', path); },
  post(path, body) { return this.request('POST', path, body); },
  put(path, body) { return this.request('PUT', path, body); },
  del(path) { return this.request('DELETE', path); },

  async getBlob(path, body) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error((data && data.detail) || 'Error al exportar.');
    }
    return res.blob();
  },

  async postText(path, body) {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error((data && data.detail) || 'Error al renderizar.');
    }
    return res.text();
  },

  templates: {
    list: () => API.get('/api/templates'),
    get: (id) => API.get('/api/templates/' + id),
  },
  generate: (payload) => API.post('/api/generate', payload),
  projects: {
    list: () => API.get('/api/projects'),
    get: (id) => API.get('/api/projects/' + id),
    create: (payload) => API.post('/api/projects', payload),
    update: (id, payload) => API.put('/api/projects/' + id, payload),
    del: (id) => API.del('/api/projects/' + id),
  },
  export: {
    one: (payload) => API.getBlob('/api/export', payload),
    all: (payload) => API.getBlob('/api/export/all', payload),
  },
  preview: (payload) => API.postText('/api/preview', payload),
};
