/* ===== Generator: formularios de generación (home, crear y editor) ===== */

const Generator = {
  templates: [],

  async init() {
    this.templates = await TemplateStore.loadList();

    this.populateSelect('qg-template', this.templates.map((t) => ({ value: t.id, label: t.name })));
    this.populateSelect('c-template', this.templates.map((t) => ({ value: t.id, label: t.name })));

    this.bindOnSubmit('quick-gen-form', () => this.runQuickGenerate());
    this.bindOnSubmit('create-form', () => this.runCreateGenerate());
  },

  bindOnSubmit(formId, handler) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      handler();
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

  runQuickGenerate() {
    const dest = document.getElementById('qg-destination').value;
    const template = document.getElementById('qg-template').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('qg-count').value || '5', 10), 1), 20);
    const language = document.getElementById('qg-language').value;
    const withImages = this.checked('qg-with-images', true);
    this.generate(dest, template, count, language, withImages, 'quick-gen-status', 'btn-quick-generate');
  },

  runCreateGenerate() {
    const dest = document.getElementById('c-destination').value.trim();
    const template = document.getElementById('c-template').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('c-count').value || '5', 10), 1), 20);
    const language = document.getElementById('c-language').value;
    const withImages = this.checked('c-with-images', true);
    this.generate(dest, template, count, language, withImages, 'create-status', 'btn-create-generate');
  },

  checked(id, defaultValue) {
    const el = document.getElementById(id);
    return el ? el.checked : defaultValue;
  },

  async generate(destination, template, count, language, withImages, statusId, btnId) {
    if (!destination) {
      this.setStatus(statusId, 'Selecciona un destino.', 'error');
      return;
    }
    const btn = document.getElementById(btnId);
    const original = btn ? btn.innerHTML : '';
    if (btn) btn.disabled = true;

    const messages = withImages
      ? ['Preparando contenido...', 'Consultando Gemini...', 'Generando tarjetas...', 'Generando fotos del destino...']
      : ['Preparando contenido...', 'Consultando Gemini...', 'Generando tarjetas...', 'Preparando diseño...'];

    try {
      for (const msg of messages) {
        this.setStatus(statusId, msg);
        await new Promise((r) => setTimeout(r, 350));
      }

      const result = await API.generate({ destination, template_id: template, count, language, with_images: withImages });
      this.clearStatus(statusId);
      const tplName = (this.templates.find((t) => t.id === template) || {}).name || template;
      App.launchEditor({
        destination: result.destination || destination,
        cards: result.cards || [],
        template,
        language,
        projectId: null,
        projectName: `${destination} — ${tplName}`,
      });
    } catch (err) {
      this.setStatus(statusId, err.message || 'No se pudo generar el contenido.', 'error');
    } finally {
      if (btn) {
        btn.innerHTML = original;
        btn.disabled = false;
      }
    }
  },
};