/* ===== Exportación: PNG individual, ZIP masivo y copy ===== */

const Exporter = {
  buildPayload(compress) {
    const state = App.state;
    const card = state.cards[state.currentIndex];
    return {
      ...card,
      destination: state.destination,
      template_id: state.template,
      format_id: state.format,
      design: buildDesignFromControls(),
      compress,
    };
  },

  buildBulkPayload(compress) {
    const state = App.state;
    return {
      destination: state.destination,
      count: state.cards.length,
      language: state.language || 'es',
      template_id: state.template,
      format_id: state.format,
      cards: state.cards,
      design: buildDesignFromControls(),
      compress,
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

  /* Devuelve: true=comprimir, false=original, null=cancelar */
  async askCompression() {
    const res = await Swal.fire({
      title: 'Exportar tarjeta',
      html: '¿Quieres comprimir la imagen con <b>Tinify</b> para reducir su peso, o descargar la versión <b>original</b>?',
      icon: 'question',
      showConfirmButton: true,
      confirmButtonText: 'Comprimir (Tinify)',
      showDenyButton: true,
      denyButtonText: 'Descargar original',
      showCancelButton: true,
      cancelButtonText: 'Cancelar',
      buttonsStyling: false,
      customClass: {
        confirmButton: 'btn btn-primary',
        denyButton: 'btn btn-ghost',
        cancelButton: 'btn btn-ghost',
      },
    });
    if (res.isConfirmed) return true;
    if (res.isDenied) return false;
    return null;
  },

  async exportOne() {
    const compress = await this.askCompression();
    if (compress === null) return;
    const btn = document.getElementById('btn-export-one');
    btn.disabled = true;
    try {
      const blob = await API.export.one(this.buildPayload(compress));
      const card = App.state.cards[App.state.currentIndex];
      const type = (card.type || 'card').replace(/_/g, '-');
      const n = String(App.state.currentIndex + 1).padStart(2, '0');
      this.downloadBlob(blob, `${n}_${type}.png`);
      App.toast(compress ? 'Tarjeta exportada y comprimida.' : 'Tarjeta exportada como PNG (original).', 'success');
    } catch (err) {
      App.toast(err.message || 'No se pudo exportar la tarjeta.', 'error');
    } finally {
      btn.disabled = false;
    }
  },

  async exportAll() {
    const compress = await this.askCompression();
    if (compress === null) return;
    const btn = document.getElementById('btn-export-all');
    btn.disabled = true;
    try {
      const blob = await API.export.all(this.buildBulkPayload(compress));
      const safe = (App.state.destination || 'tripcanvas').toLowerCase().replace(/[^a-z0-9_]+/g, '_');
      this.downloadBlob(blob, `tripcanvas_${safe}.zip`);
      App.toast(compress ? 'Tarjetas comprimidas y descargadas en ZIP.' : 'Tarjetas descargadas en ZIP (original).', 'success');
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
