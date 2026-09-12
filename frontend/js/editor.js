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
    ['e-source', 'source'],
  ],

  TEMPLATE_FIELDS: {
    dato_curioso:       ['title', 'body'],
    quiz:               ['question', 'answer'],
    mito_realidad:      ['title', 'myth', 'reality'],
    cinco_datos:        ['title', 'facts'],
    consejos:           ['title', 'facts'],
    sabias_que:         ['question', 'answer'],
    comparativa:        ['title', 'body'],
    historia:           ['title', 'body'],
    arquitectura:       ['title', 'body', 'facts'],
    como_llegar:        ['title', 'facts'],
    cultura:            ['title', 'body', 'facts'],
    guia_rapida:        ['title', 'facts'],
    informacion_general:['title', 'body', 'facts'],
    mejor_epoca:        ['title', 'facts'],
    naturaleza:         ['title', 'body', 'facts'],
  },

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

    const imageEnabled = document.getElementById('d-image-enabled');
    const imageFields = document.getElementById('d-image-fields');
    imageEnabled.addEventListener('change', async () => {
      imageFields.style.display = imageEnabled.checked ? '' : 'none';
      if (!imageEnabled.checked) {
        App.state.cards[App.state.currentIndex].image = '';
        document.getElementById('d-image').value = '';
        this.markDirty();
        await renderPreview();
      }
    });

    document.getElementById('btn-prev').addEventListener('click', () => this.nav(-1));
    document.getElementById('btn-next').addEventListener('click', () => this.nav(1));
    document.getElementById('btn-save').addEventListener('click', () => this.askSave());
    document.getElementById('btn-download-project').addEventListener('click', () => this.downloadProject());
    document.getElementById('btn-upload-project').addEventListener('change', (e) => this.uploadProject(e));
    document.getElementById('btn-back').addEventListener('click', () => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        location.href = '/';
      }
    });

    window.addEventListener('message', (e) => {
      if (e.data && e.data.type === 'tc-field-click') {
        this.openFieldEditor(e.data.field, e.data.value);
      }
    });

    document.getElementById('edit-field-save').addEventListener('click', () => this.saveFieldEdit());
    document.getElementById('edit-field-cancel').addEventListener('click', () => this.closeFieldEditor());
    document.getElementById('edit-field-close').addEventListener('click', () => this.closeFieldEditor());
    document.getElementById('edit-field-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.saveFieldEdit();
      } else if (e.key === 'Escape') {
        this.closeFieldEditor();
      }
    });
  },

  _editingField: null,

  FIELD_LABELS: {
    TITLE: 'Título', BODY: 'Descripción', QUESTION: 'Pregunta',
    ANSWER: 'Respuesta', MYTH: 'Mito', REALITY: 'Realidad',
    DESTINATION: 'Destino', SOURCE: 'Fuente', LOCATION: 'Ubicación',
    ALTITUDE: 'Altitud', NUMBER: 'Número', DATE: 'Fecha',
  },

  FIELD_TO_CARD: {
    TITLE: 'title', BODY: 'body', QUESTION: 'question',
    ANSWER: 'answer', MYTH: 'myth', REALITY: 'reality',
    DESTINATION: 'destination', SOURCE: 'source', LOCATION: 'location',
    ALTITUDE: 'altitude', NUMBER: 'number', DATE: null,
  },

  openFieldEditor(field, value) {
    this._editingField = field;
    const indexedMatch = field.match(/^(FACT|FACT_LABEL|OPTION|ITEM|ITEM_LABEL)_(\d+)$/);
    let label;
    if (indexedMatch) {
      const type = indexedMatch[1];
      const idx = parseInt(indexedMatch[2], 10) + 1;
      const typeLabels = { FACT: 'Dato', FACT_LABEL: 'Etiqueta', OPTION: 'Opción', ITEM: 'Elemento', ITEM_LABEL: 'Etiqueta' };
      label = `${typeLabels[type]} ${idx}`;
    } else {
      label = this.FIELD_LABELS[field] || field;
    }
    document.getElementById('edit-field-title').textContent = 'Editar ' + label;
    const input = document.getElementById('edit-field-input');
    input.value = value;
    document.getElementById('edit-field-overlay').classList.remove('hidden');
    input.focus();
    input.select();
  },

  closeFieldEditor() {
    document.getElementById('edit-field-overlay').classList.add('hidden');
    this._editingField = null;
  },

  saveFieldEdit() {
    const field = this._editingField;
    if (!field) return;
    const newValue = document.getElementById('edit-field-input').value;
    this.closeFieldEditor();

    const card = App.state.cards[App.state.currentIndex];
    if (!card) return;

    const indexedMatch = field.match(/^(FACT|FACT_LABEL|OPTION|ITEM|ITEM_LABEL)_(\d+)$/);
    if (indexedMatch) {
      const type = indexedMatch[1];
      const idx = parseInt(indexedMatch[2], 10);
      if (type === 'FACT' && card.facts) {
        if (typeof card.facts[idx] === 'object') card.facts[idx].value = newValue;
        else card.facts[idx] = newValue;
      } else if (type === 'FACT_LABEL' && card.facts && typeof card.facts[idx] === 'object') {
        card.facts[idx].label = newValue;
      } else if (type === 'OPTION' && card.options) {
        card.options[idx] = newValue;
      } else if (type === 'ITEM' && card.extra && card.extra.items && card.extra.items[idx]) {
        card.extra.items[idx].value = newValue;
      } else if (type === 'ITEM_LABEL' && card.extra && card.extra.items && card.extra.items[idx]) {
        card.extra.items[idx].label = newValue;
      }
    } else {
      const cardKey = this.FIELD_TO_CARD[field];
      if (cardKey) {
        card[cardKey] = newValue;
      } else if (field === 'DATE') {
        if (!card.extra) card.extra = {};
        card.extra.fecha = newValue;
      }

      if (cardKey === 'destination') {
        App.state.destination = newValue;
        document.getElementById('e-destination').value = newValue;
      }

      const panelField = document.querySelector(`[data-editor-field="${cardKey}"]`);
      if (panelField) {
        const input = panelField.querySelector('textarea, input');
        if (input) input.value = newValue;
      }
    }

    this.markDirty();
    this.rerender();
  },

  async syncTemplateSelect() {
    const select = document.getElementById('d-template');
    const available = Array.from(select.options).map((o) => o.value);
    if (!available.includes(App.state.template)) {
      await App.setupTemplateSelect('d-template');
    }
    select.value = App.state.template;
    this.updateFieldVisibility();
  },

  updateFieldVisibility() {
    const fields = this.TEMPLATE_FIELDS[App.state.template] || [];
    document.querySelectorAll('[data-editor-field]').forEach((el) => {
      const field = el.getAttribute('data-editor-field');
      el.style.display = fields.includes(field) ? '' : 'none';
    });
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
    if (id === 'd-bg' || id === 'd-text' || id === 'd-accent') {
      const hex = document.getElementById(id).value;
      const circle = document.getElementById(id + '-circle');
      if (circle) circle.style.background = hex;
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
    const hasImage = !!card.image;
    document.getElementById('d-image-enabled').checked = hasImage;
    document.getElementById('d-image-fields').style.display = hasImage ? '' : 'none';
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
    const card = App.state.cards[App.state.currentIndex];
    this.loadCardIntoPanel(card);
    this.updateFieldVisibility();
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
        cards: draft.cards,
        template: draft.template || 'dato-curioso',
        format: draft.format || 'instagram_portrait',
        projectId: draft.projectId || null,
        projectName: draft.projectName || 'Proyecto nuevo',
        currentIndex: 0,
        language: draft.language || 'es',
      };
      document.getElementById('editor-project-name').textContent = App.state.projectName;
    } else {
      const template = (draft && draft.template) || params.get('template') || 'dato-curioso';
      App.state = {
        destination: '',
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

  async downloadProject() {
    const projectId = App.state.projectId;
    if (!projectId) {
      App.toast('Guarda el proyecto primero para poder descargarlo.', 'info');
      return;
    }
    try {
      const blob = await API.projects.download(projectId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = (App.state.projectName || 'proyecto') + '.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      App.toast('Proyecto descargado.', 'success');
    } catch (err) {
      App.toast(err.message || 'No se pudo descargar.', 'error');
    }
  },

  async uploadProject(e) {
    const file = e.target.files[0];
    if (!file) return;
    try {
      App.toast('Subiendo proyecto...');
      const project = await API.projects.upload(file);
      App.toast('Proyecto importado. Abriendo...', 'success');
      location.href = '/editor?project=' + project.id;
    } catch (err) {
      App.toast(err.message || 'No se pudo subir el proyecto.', 'error');
    }
    e.target.value = '';
  },
};
