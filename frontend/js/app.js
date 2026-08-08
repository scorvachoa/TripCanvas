/* ===== App: router, estado global e inicialización ===== */

const App = {
  state: {
    destination: '',
    category: 'dato_curioso',
    cards: [],
    template: 'dato-curioso',
    format: 'instagram_portrait',
    projectId: null,
    projectName: '',
    currentIndex: 0,
    language: 'es',
  },

  _toastTimer: null,

  async init() {
    try {
      this.setupNav();
      this.setupEditorButtons();
      await Generator.init();
      Editor.init();
      await this.renderTemplates();
      await this.renderDestinations();
      this.loadRecentProjects();
      await this.setupTemplateSelect();
      this.show('dashboard');
    } catch (err) {
      console.error('Error al iniciar la aplicación:', err);
      const target = document.getElementById('view-dashboard');
      if (target) target.classList.remove('hidden');
      const toast = document.getElementById('toast');
      if (toast) {
        toast.textContent = 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.';
        toast.className = 'toast show error';
      }
    }
  },

  setupNav() {
    document.querySelectorAll('[data-nav]').forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.show(link.dataset.nav);
      });
    });
    document.getElementById('btn-hero-create').addEventListener('click', () => this.show('create'));
  },

  setupEditorButtons() {
    document.getElementById('btn-export-one').addEventListener('click', () => Exporter.exportOne());
    document.getElementById('btn-export-all').addEventListener('click', () => Exporter.exportAll());
    document.getElementById('btn-copy-copy').addEventListener('click', () => Exporter.copyCopyText());
    document.getElementById('modal-close').addEventListener('click', () => Editor.hideModal());
    document.getElementById('modal-cancel').addEventListener('click', () => Editor.hideModal());
    document.getElementById('modal-save').addEventListener('click', () => Editor.save());
    window.addEventListener('beforeunload', (e) => {
      if (this.state && this.state._dirty) {
        e.preventDefault();
        e.returnValue = '';
      }
    });
    window.addEventListener('resize', () => {
      if (document.getElementById('view-editor').classList.contains('hidden') === false) {
        fitPreview();
      }
    });
  },

  async setupTemplateSelect() {
    const templates = await TemplateStore.loadList();
    const select = document.getElementById('d-template');
    select.innerHTML = '';
    for (const tpl of templates) {
      const opt = document.createElement('option');
      opt.value = tpl.id;
      opt.textContent = tpl.name;
      select.appendChild(opt);
    }
    if (templates.length && !templates.some((t) => t.id === this.state.template)) {
      this.state.template = templates[0].id;
    }
  },

  show(view) {
    const inEditor = !document.getElementById('view-editor').classList.contains('hidden');
    if (inEditor && view !== 'editor' && this.state._dirty) {
      if (!confirm('Tienes cambios sin guardar. ¿Salir de todos modos?')) return;
    }

    document.querySelectorAll('.view').forEach((v) => v.classList.add('hidden'));
    const target = document.getElementById('view-' + view);
    if (target) target.classList.remove('hidden');

    document.querySelectorAll('.nav-link').forEach((l) => l.classList.remove('active'));
    const navLink = document.querySelector(`.nav-link[data-nav="${view}"]`);
    if (navLink) navLink.classList.add('active');

    if (view === 'editor') {
      Editor.enter();
    } else {
      clearPreviewStyles();
      if (view === 'projects') {
        this.loadProjects();
      } else if (view === 'dashboard') {
        this.loadRecentProjects();
      }
    }
  },

  async openEditor(payload) {
    let template = payload.template || this.state.template || 'dato-curioso';
    if (!payload.template) {
      try {
        const cats = await API.categories.list();
        const match = cats.find((c) => c.id === payload.category);
        if (match && match.template) template = match.template;
      } catch (err) {
        console.warn('No se pudo resolver la plantilla por categoría:', err);
      }
    }
    this.state = {
      destination: payload.destination || '',
      category: payload.category || 'dato_curioso',
      cards: payload.cards || [],
      template,
      format: payload.format || this.state.format || 'instagram_portrait',
      projectId: payload.projectId || null,
      projectName: payload.projectName || 'Proyecto nuevo',
      currentIndex: 0,
      language: payload.language || 'es',
    };
    document.getElementById('editor-project-name').textContent = this.state.projectName;
    this.show('editor');
  },

  async renderTemplates() {
    const templates = await TemplateStore.loadList();
    const grid = document.getElementById('templates-grid');
    grid.innerHTML = '';
    if (!templates.length) {
      grid.innerHTML = '<div class="empty-state">No hay plantillas.</div>';
      return;
    }
    for (const tpl of templates) {
      const card = document.createElement('div');
      card.className = 'template-card';
      card.innerHTML = `
        <div class="template-preview tp-${tpl.id}">${tpl.name[0]}</div>
        <div class="template-name">${esc(tpl.name)}</div>
        <div class="template-desc">${esc(tpl.description)}</div>
      `;
      card.addEventListener('click', () => {
        this.state.template = tpl.id;
        this.openEditor({
          destination: this.state.destination,
          category: this.state.category,
          cards: this.state.cards,
          template: tpl.id,
          format: this.state.format,
          projectId: this.state.projectId,
          projectName: this.state.projectName,
        });
      });
      grid.appendChild(card);
    }
  },

  async renderDestinations() {
    const dests = await API.destinations.list();
    const grid = document.getElementById('destinations-grid');
    grid.innerHTML = '';
    if (!dests.length) {
      grid.innerHTML = '<div class="empty-state">No hay destinos.</div>';
      return;
    }
    for (const d of dests) {
      const card = document.createElement('div');
      card.className = 'dest-card';
      card.innerHTML = `
        <div class="dest-name">${esc(d.name)}</div>
        <div class="dest-region">${esc(d.region)}</div>
      `;
      grid.appendChild(card);
    }
  },

  renderProjectCard(project) {
    const div = document.createElement('div');
    div.className = 'project-card';
    const date = project.updated_at ? new Date(project.updated_at).toLocaleDateString() : '';
    const emoji = '🖼';
    div.innerHTML = `
      <div class="project-thumb">${emoji}</div>
      <div class="project-body">
        <div class="project-name">${esc(project.name)}</div>
        <div class="project-meta">${esc(project.destination || '—')}<br>${esc(date)} · ${project.cards_count || 0} tarjetas</div>
      </div>
      <div class="project-actions">
        <button class="btn btn-primary btn-sm act-open">Editar</button>
        <button class="btn btn-ghost btn-sm act-del">Eliminar</button>
      </div>
    `;
    div.querySelector('.act-open').addEventListener('click', (e) => {
      e.stopPropagation();
      Editor.loadProject(project.id);
    });
    div.querySelector('.act-del').addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!confirm(`¿Eliminar el proyecto "${project.name}"?`)) return;
      try {
        await API.projects.del(project.id);
        App.toast('Proyecto eliminado.', 'success');
        this.loadRecentProjects();
        this.loadProjects();
      } catch (err) {
        App.toast(err.message || 'No se pudo eliminar.', 'error');
      }
    });
    return div;
  },

  async loadProjects() {
    const grid = document.getElementById('projects-list');
    grid.innerHTML = '';
    try {
      const projects = await API.projects.list();
      if (!projects.length) {
        grid.innerHTML = '<div class="empty-state">Aún no tienes proyectos. ¡Crea tu primera tarjeta!</div>';
        return;
      }
      for (const p of projects) grid.appendChild(this.renderProjectCard(p));
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">${esc(err.message)}</div>`;
    }
  },

  async loadRecentProjects() {
    const grid = document.getElementById('recent-projects');
    grid.innerHTML = '';
    try {
      const projects = await API.projects.list();
      if (!projects.length) {
        grid.innerHTML = '<div class="empty-state">Sin proyectos aún. Genera tu primer contenido.</div>';
        return;
      }
      for (const p of projects.slice(0, 4)) grid.appendChild(this.renderProjectCard(p));
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">${esc(err.message)}</div>`;
    }
  },

  toast(message, type) {
    const el = document.getElementById('toast');
    el.textContent = message;
    el.className = 'toast show' + (type ? ' ' + type : '');
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => {
      el.classList.remove('show');
    }, 3200);
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());

window.App = App;
