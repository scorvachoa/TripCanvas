/* ===== Generator: formularios del dashboard / crear ===== */

const Generator = {
  destinations: [],
  categories: [],

  async init() {
    const [dests, cats] = await Promise.all([
      API.destinations.list(),
      API.categories.list(),
    ]);
    this.destinations = dests;
    this.categories = cats;

    this.populateSelect('qg-destination', dests.map((d) => d.name));
    this.populateSelect('c-destination', dests.map((d) => d.name));
    this.populateDatalist(dests.map((d) => d.name));

    this.populateSelect('qg-category', cats.map((c) => ({ value: c.id, label: c.name })));
    this.populateSelect('c-category', cats.map((c) => ({ value: c.id, label: c.name })));
    this.populateSelect('e-category', cats.map((c) => ({ value: c.id, label: c.name })));

    document.getElementById('quick-gen-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.runQuickGenerate();
    });
    document.getElementById('create-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.runCreateGenerate();
    });
  },

  populateSelect(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    for (const item of items) {
      const opt = document.createElement('option');
      if (typeof item === 'string') {
        opt.value = item;
        opt.textContent = item;
      } else {
        opt.value = item.value;
        opt.textContent = item.label;
      }
      el.appendChild(opt);
    }
  },

  populateDatalist(items) {
    const el = document.getElementById('destination-list');
    if (!el) return;
    el.innerHTML = '';
    for (const item of items) {
      const opt = document.createElement('option');
      opt.value = item;
      el.appendChild(opt);
    }
  },

  setStatus(containerId, message, type) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.className = 'gen-status' + (type ? ' ' + type : '');
    el.innerHTML = type === 'error'
      ? message
      : `<span class="status-dot"></span>${message}`;
  },

  clearStatus(containerId) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = '';
  },

  async runQuickGenerate() {
    const dest = document.getElementById('qg-destination').value;
    const category = document.getElementById('qg-category').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('qg-count').value || '5', 10), 1), 20);
    const language = document.getElementById('qg-language').value;
    await this.generate(dest, category, count, language, 'quick-gen-status');
  },

  async runCreateGenerate() {
    const dest = document.getElementById('c-destination').value.trim();
    const category = document.getElementById('c-category').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('c-count').value || '5', 10), 1), 20);
    const language = document.getElementById('c-language').value;
    await this.generate(dest, category, count, language, 'create-status');
  },

  async generate(destination, category, count, language, statusId) {
    if (!destination) {
      this.setStatus(statusId, 'Selecciona un destino.', 'error');
      return;
    }
    const btn = statusId === 'quick-gen-status'
      ? document.getElementById('btn-quick-generate')
      : document.getElementById('btn-create-generate');
    const original = btn.innerHTML;
    btn.disabled = true;

    const messages = [
      'Preparando contenido...',
      'Consultando Gemini...',
      'Generando tarjetas...',
      'Preparando diseño...',
    ];

    try {
      for (const msg of messages) {
        this.setStatus(statusId, msg);
        await new Promise((r) => setTimeout(r, 350));
      }

      const result = await API.generate({ destination, category, count, language });
      this.clearStatus(statusId);
      App.openEditor({
        destination: result.destination || destination,
        cards: result.cards || [],
        category,
        language,
        projectId: null,
        projectName: `${destination} — ${category.replace(/_/g, ' ')}`,
      });
    } catch (err) {
      this.setStatus(statusId, err.message || 'No se pudo generar el contenido.', 'error');
    } finally {
      btn.innerHTML = original;
      btn.disabled = false;
    }
  },
};
