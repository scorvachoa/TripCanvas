/* ===== Templates: carga y caché ===== */
const TemplateStore = {
  list: [],
  details: {},

  async loadList() {
    if (this.list.length) return this.list;
    this.list = await API.templates.list();
    return this.list;
  },

  async get(id) {
    if (this.details[id]) return this.details[id];
    const detail = await API.templates.get(id);
    this.details[id] = detail;
    return detail;
  },

  async defaultTemplateId() {
    const list = await this.loadList();
    if (!list.length) return 'dato-curioso';
    return list[0].id;
  },
};
