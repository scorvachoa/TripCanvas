/* ===== Exportación: PNG individual, ZIP masivo y copy ===== */

const Exporter = {
  buildPayload() {
    const state = App.state;
    const card = state.cards[state.currentIndex];
    return {
      ...card,
      destination: state.destination,
      template_id: state.template,
      format_id: state.format,
      design: buildDesignFromControls(),
    };
  },

  buildBulkPayload() {
    const state = App.state;
    return {
      destination: state.destination,
      category: state.category,
      count: state.cards.length,
      language: state.language || 'es',
      template_id: state.template,
      format_id: state.format,
      cards: state.cards,
      design: buildDesignFromControls(),
    };
  },

  downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },

  async exportOne() {
    const btn = document.getElementById('btn-export-one');
    btn.disabled = true;
    try {
      const blob = await API.export.one(this.buildPayload());
      const card = App.state.cards[App.state.currentIndex];
      const type = (card.type || 'card').replace(/_/g, '-');
      const n = String(App.state.currentIndex + 1).padStart(2, '0');
      this.downloadBlob(blob, `${n}_${type}.png`);
      App.toast('Tarjeta exportada como PNG.', 'success');
    } catch (err) {
      App.toast(err.message || 'No se pudo exportar la tarjeta.', 'error');
    } finally {
      btn.disabled = false;
    }
  },

  async exportAll() {
    const btn = document.getElementById('btn-export-all');
    btn.disabled = true;
    try {
      const blob = await API.export.all(this.buildBulkPayload());
      const safe = (App.state.destination || 'tripcanvas').toLowerCase().replace(/[^a-z0-9_]+/g, '_');
      this.downloadBlob(blob, `tripcanvas_${safe}.zip`);
      App.toast('Tarjetas descargadas en ZIP.', 'success');
    } catch (err) {
      App.toast(err.message || 'No se pudieron exportar las tarjetas.', 'error');
    } finally {
      btn.disabled = false;
    }
  },

  async copyCopyText() {
    const card = App.state.cards[App.state.currentIndex];
    if (!card) return;
    const lines = [
      `${card.title}`,
      '',
      ...(card.body ? [card.body] : []),
      ...(card.facts && card.facts.length
        ? ['', 'Datos:']
        : []),
      ...(card.facts || []).map((f) =>
        typeof f === 'object' ? `• ${f.label}: ${f.value}` : `• ${f}`
      ),
      ...(card.location ? ['', `📍 ${card.location}`] : []),
      ...(card.source ? [`Fuente: ${card.source}`] : []),
    ];
    const text = lines.join('\n');
    try {
      await navigator.clipboard.writeText(text);
      App.toast('Copy copiado al portapapeles.', 'success');
    } catch (err) {
      App.toast('No se pudo copiar el copy.', 'error');
    }
  },
};
