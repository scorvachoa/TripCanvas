/* ===== App: estado global compartido y utilidades de página ===== */

const App = {
  state: {
    destination: '',
    cards: [],
    template: 'dato-curioso',
    format: 'instagram_portrait',
    projectId: null,
    projectName: '',
    currentIndex: 0,
    language: 'es',
  },

  toast(message, type) {
    Swal.fire({
      toast: true,
      position: 'top-end',
      icon: type === 'error' ? 'error' : type === 'success' ? 'success' : 'info',
      title: message,
      showConfirmButton: false,
      timer: 3200,
      timerProgressBar: true,
    });
  },

  setActiveNav() {
    const path = location.pathname;
    document.querySelectorAll('.nav-link').forEach((link) => {
      const dest = link.getAttribute('href') || '';
      link.classList.toggle('active', dest === path || (dest === '/' && path === '/'));
    });
  },

  setupMobileNav() {
    const toggle = document.getElementById('menu-toggle');
    const nav = document.getElementById('main-nav');
    if (!toggle || !nav) return;
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = nav.classList.toggle('open');
      toggle.textContent = open ? '✕' : '☰';
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    });
    document.addEventListener('click', (e) => {
      if (nav.contains(e.target) || toggle.contains(e.target)) return;
      nav.classList.remove('open');
      toggle.textContent = '☰';
      toggle.setAttribute('aria-expanded', 'false');
    });
  },

  /* ===== Navegación hacia el editor (otra página) ===== */

  launchEditor(payload) {
    try {
      sessionStorage.setItem('tc_draft', JSON.stringify(payload));
    } catch (err) {
      console.warn('No se pudo guardar el borrador:', err);
    }
    location.href = '/editor';
  },

  launchEditorFromTemplate(template) {
    this.launchEditor({ template, cards: [], projectName: 'Proyecto nuevo' });
  },

  async setupTemplateSelect(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    const templates = await TemplateStore.loadList();
    select.innerHTML = '';
    for (const tpl of templates) {
      const opt = document.createElement('option');
      opt.value = tpl.id;
      opt.textContent = tpl.name;
      select.appendChild(opt);
    }
  },

  /* ===== Proyectos ===== */

  renderProjectCard(project, onAction) {
    const div = document.createElement('div');
    div.className = 'project-card';
    const date = project.updated_at ? new Date(project.updated_at).toLocaleDateString() : '';
    div.innerHTML = `
      <div class="project-thumb">🖼</div>
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
      location.href = '/editor?project=' + encodeURIComponent(project.id);
    });
    div.querySelector('.act-del').addEventListener('click', async (e) => {
      e.stopPropagation();
      const res = await Swal.fire({
        title: '¿Eliminar proyecto?',
        text: `Se eliminará "${project.name}" y no podrás recuperarlo.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Eliminar',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#d33',
      });
      if (!res.isConfirmed) return;
      try {
        await API.projects.del(project.id);
        App.toast('Proyecto eliminado.', 'success');
        if (onAction) onAction();
      } catch (err) {
        App.toast(err.message || 'No se pudo eliminar.', 'error');
      }
    });
    return div;
  },

  async loadProjects(gridId) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    grid.innerHTML = '';
    try {
      const projects = await API.projects.list();
      if (!projects.length) {
        grid.innerHTML = '<div class="empty-state">Aún no tienes proyectos. ¡Crea tu primera tarjeta!</div>';
        return;
      }
      for (const p of projects) grid.appendChild(this.renderProjectCard(p, () => {
        this.loadProjects(gridId);
        this.loadRecentProjects('recent-projects');
      }));
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">${esc(err.message)}</div>`;
    }
  },

  async loadRecentProjects(gridId) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    grid.innerHTML = '';
    try {
      const projects = await API.projects.list();
      if (!projects.length) {
        grid.innerHTML = '<div class="empty-state">Sin proyectos aún. Genera tu primer contenido.</div>';
        return;
      }
      for (const p of projects.slice(0, 4)) grid.appendChild(this.renderProjectCard(p, () => {
        this.loadProjects('projects-list');
        this.loadRecentProjects(gridId);
      }));
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">${esc(err.message)}</div>`;
    }
  },

  /* ===== Plantillas ===== */

  async renderTemplates(gridId) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    grid.innerHTML = '';
    try {
      const templates = await TemplateStore.loadList();
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
          <button class="btn btn-primary btn-sm tpl-use">Usar plantilla</button>
        `;
        card.addEventListener('click', () => {
          App.launchEditorFromTemplate(tpl.id);
        });
        grid.appendChild(card);
      }
    } catch (err) {
      grid.innerHTML = `<div class="empty-state">${esc(err.message)}</div>`;
    }
  },
};

window.App = App;