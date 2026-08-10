/* ===== Editor: panel de contenido, navegación y guardado ===== */

const Editor = {
  FIELD_MAP: [
    ['e-title', 'title'],
    ['e-body', 'body'],
    ['e-question', 'question'],
    ['e-answer', 'answer'],
    ['e-myth', 'myth'],
    ['e-reality', 'reality'],
    ['e-location', 'location'],
    ['e-altitude', 'altitude'],
    ['e-source', 'source'],
  ],

  init() {
    for (const [elId] of this.FIELD_MAP) {
      document.getElementById(elId).addEventListener('input', (e) => this.onFieldInput(e));
    }
    document.getElementById('e-facts').addEventListener('input', () => this.onFactsInput());
    document.getElementById('e-destination').addEventListener('input', (e) => {
      App.state.destination = e.target.value;
      this.markDirty();
      this.rerender();
    });
    document.getElementById('e-category').addEventListener('change', (e) => {
      this.regenerateCategory(e.target.value);
    });

    document.getElementById('d-template').addEventListener('change', async (e) => {
      App.state.template = e.target.value;
      this.markDirty();
      await this.syncTemplateSelect();
      await renderPreview();
    });
    document.getElementById('d-format').addEventListener('change', async () => {
      App.state.format = document.getElementById('d-format').value;
      await renderPreview();
    });

    for (const id of ['d-bg', 'd-text', 'd-accent', 'd-overlay', 'd-font', 'd-logo', 'd-text-scale']) {
      document.getElementById(id).addEventListener('input', () => this.onDesignInput(id));
    }

    document.getElementById('d-image').addEventListener('input', () => this.onImageInput());

    document.getElementById('d-image-file').addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async () => {
        App.state.cards[App.state.currentIndex].image = reader.result;
        document.getElementById('d-image').value = '';
        this.markDirty();
        await renderPreview();
      };
      reader.readAsDataURL(file);
    });

    document.getElementById('btn-prev').addEventListener('click', () => this.nav(-1));
    document.getElementById('btn-next').addEventListener('click', () => this.nav(1));
    document.getElementById('btn-save').addEventListener('click', () => this.askSave());
    document.getElementById('btn-back').addEventListener('click', () => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        location.href = '/';
      }
    });
  },

  async syncTemplateSelect() {
    const select = document.getElementById('d-template');
    select.value = App.state.template;
  },

  async regenerateCategory(category) {
    if (category === App.state.category) return;
    App.state.category = category;
    const cats = await API.categories.list();
    const match = cats.find((c) => c.id === category);
    if (match && match.template) App.state.template = match.template;
    await this.syncTemplateSelect();
    App.state.currentIndex = 0;
    this.updateCounter();
    this.loadCardIntoPanel(App.state.cards[App.state.currentIndex]);
    await renderPreview();
  },

  onFieldInput(e) {
    const field = this.FIELD_MAP.find(([id]) => id === e.target.id);
    if (!field) return;
    const card = App.state.cards[App.state.currentIndex];
    if (!card) return;
    card[field[1]] = e.target.value;
    this.markDirty();
    this.rerender();
  },

  onFactsInput() {
    const card = App.state.cards[App.state.currentIndex];
    if (!card) return;
    card.facts = this.factsFromLines(document.getElementById('e-facts').value);
    this.markDirty();
    this.rerender();
  },

  factsToLines(facts) {
    return (facts || [])
      .map((f) => (typeof f === 'object' ? `${f.label || ''}: ${f.value || ''}` : String(f)))
      .join('\n');
  },

  factsFromLines(text) {
    const isLabelValue = text.split('\n').some((line) => line.includes(':'));
    if (!isLabelValue) {
      return text.split('\n').map((l) => l.trim()).filter(Boolean);
    }
    return text.split('\n')
      .map((l) => l.trim())
      .filter(Boolean)
      .map((line) => {
        const idx = line.indexOf(':');
        if (idx === -1) return { label: '', value: line };
        return { label: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() };
      });
  },

  onDesignInput(id) {
    if (id === 'd-overlay') {
      document.getElementById('d-overlay-val').textContent =
        (parseFloat(document.getElementById('d-overlay').value) || 0).toFixed(2);
    }
    if (id === 'd-text-scale') {
      const v = Math.round((parseFloat(document.getElementById('d-text-scale').value) || 1) * 100);
      document.getElementById('d-text-scale-val').textContent = v + '%';
    }
    this.markDirty();
    this.rerender();
  },

  onImageInput() {
    const card = App.state.cards[App.state.currentIndex];
    if (!card) return;
    const imgInput = document.getElementById('d-image');
    card.image = imgInput.value || null;
    this.markDirty();
    this.rerender();
  },

  markDirty() {
    App.state._dirty = true;
  },

  clearDirty() {
    App.state._dirty = false;
  },

  loadCardIntoPanel(card) {
    if (!card) return;
    for (const [elId, field] of this.FIELD_MAP) {
      document.getElementById(elId).value = card[field] || '';
    }
    document.getElementById('e-facts').value = this.factsToLines(card.facts);
    document.getElementById('e-destination').value = App.state.destination;
    document.getElementById('d-image').value = card.image || '';
  },

  updateCounter() {
    const total = App.state.cards.length;
    document.getElementById('editor-card-counter').textContent =
      total ? `Tarjeta ${App.state.currentIndex + 1} / ${total}` : 'Sin tarjetas';
  },

  nav(dir) {
    const total = App.state.cards.length;
    if (!total) return;
    App.state.currentIndex = (App.state.currentIndex + dir + total) % total;
    this.updateCounter();
    this.loadCardIntoPanel(App.state.cards[App.state.currentIndex]);
    this.rerender();
  },

  rerender() {
    if (this._rerenderTimer) clearTimeout(this._rerenderTimer);
    this._rerenderTimer = setTimeout(() => {
      renderPreview();
    }, 60);
  },

  async enter() {
    this.updateCounter();
    await this.syncTemplateSelect();
    document.getElementById('d-format').value = App.state.format;
    document.getElementById('e-category').value = App.state.category;
    const card = App.state.cards[App.state.currentIndex];
    this.loadCardIntoPanel(card);
    await renderPreview();
  },

  askSave() {
    const modal = document.getElementById('modal-overlay');
    const nameInput = document.getElementById('modal-name');
    nameInput.value = App.state.projectName || '';
    modal.classList.remove('hidden');
    nameInput.focus();
  },

  hideModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
  },

  async save() {
    const name = document.getElementById('modal-name').value.trim() || App.state.projectName || 'Proyecto sin nombre';
    App.state.projectName = name;
    document.getElementById('editor-project-name').textContent = name;

    const payload = {
      name,
      destination: App.state.destination,
      template: App.state.template,
      format: App.state.format,
      cards: App.state.cards,
    };

    try {
      if (App.state.projectId) {
        await API.projects.update(App.state.projectId, payload);
      } else {
        const created = await API.projects.create(payload);
        App.state.projectId = created.id;
      }
      this.hideModal();
      this.clearDirty();
      App.toast('Proyecto guardado.', 'success');
    } catch (err) {
      App.toast(err.message || 'El proyecto no pudo guardarse.', 'error');
    }
  },

  async loadProject(projectId) {
    App.toast('Abriendo proyecto...');
    try {
      const project = await API.projects.get(projectId);
      App.state = {
        destination: project.destination || '',
        category: (project.cards[0] && project.cards[0].type) || 'dato_curioso',
        cards: project.cards || [],
        template: project.template || 'dato-curioso',
        format: project.format || 'instagram_portrait',
        projectId: project.id,
        projectName: project.name,
        currentIndex: 0,
        language: 'es',
      };
      document.getElementById('editor-project-name').textContent = project.name;
      await this.enter();
    } catch (err) {
      App.toast(err.message || 'No se pudo abrir el proyecto.', 'error');
    }
  },

  async bootstrap() {
    const params = new URLSearchParams(location.search);
    const projectId = params.get('project');
    if (projectId) {
      await this.loadProject(projectId);
      return;
    }

    let draft = null;
    try {
      const raw = sessionStorage.getItem('tc_draft');
      if (raw) {
        draft = JSON.parse(raw);
        sessionStorage.removeItem('tc_draft');
      }
    } catch (err) {
      console.warn('Borrador inválido:', err);
    }

    if (draft && Array.isArray(draft.cards) && draft.cards.length) {
      App.state = {
        destination: draft.destination || '',
        category: draft.category || 'dato_curioso',
        cards: draft.cards,
        template: draft.template || 'dato-curioso',
        format: draft.format || 'instagram_portrait',
        projectId: draft.projectId || null,
        projectName: draft.projectName || 'Proyecto nuevo',
        currentIndex: 0,
        language: draft.language || 'es',
      };
      if (draft.cards[0] && !draft.cardType) {
        App.state.category = draft.category || 'dato_curioso';
      }
      document.getElementById('editor-project-name').textContent = App.state.projectName;
    } else {
      const template = (draft && draft.template) || params.get('template') || 'dato-curioso';
      App.state = {
        destination: '',
        category: 'dato_curioso',
        cards: [],
        template,
        format: 'instagram_portrait',
        projectId: null,
        projectName: draft && draft.projectName ? draft.projectName : 'Proyecto nuevo',
        currentIndex: 0,
        language: 'es',
      };
      document.getElementById('editor-project-name').textContent = App.state.projectName;
    }

    await this.enter();
  },
};
