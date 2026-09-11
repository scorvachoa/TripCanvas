/* ===== Preview: muestra el render real del backend en un iframe =====
 *
 * El HTML de la tarjeta lo genera el backend (`POST /api/preview`) usando el
 * mismo motor que la exportación, de modo que el preview del editor y el PNG
 * final siempre coinciden (una sola fuente de verdad).
 */

const FORMATS = {
  instagram_portrait: { w: 1080, h: 1350 },
  square: { w: 1080, h: 1080 },
  story: { w: 1080, h: 1920 },
};

function esc(value) {
  const div = document.createElement('div');
  div.textContent = value == null ? '' : String(value);
  return div.innerHTML;
}

function buildDesignFromControls() {
  const overlay = parseFloat(document.getElementById('d-overlay').value || '0.35');
  const textScale = parseFloat(document.getElementById('d-text-scale').value || '1');
  return {
    background: document.getElementById('d-bg').value || '#0f1a2e',
    text: document.getElementById('d-text').value || '#ffffff',
    accent: document.getElementById('d-accent').value || '#f4b942',
    overlay: `rgba(0,0,0,${overlay})`,
    font: document.getElementById('d-font').value,
    showLogo: document.getElementById('d-logo').checked,
    textScale,
  };
}

let _cardEl = null;

function ensureCardEl() {
  if (!_cardEl || !_cardEl.isConnected) {
    _cardEl = document.getElementById('preview-card');
  }
  return _cardEl;
}

function ensureFrameEl() {
  const el = ensureCardEl();
  let frame = document.getElementById('preview-frame');
  if (!frame) {
    frame = document.createElement('iframe');
    frame.id = 'preview-frame';
    frame.style.border = '0';
    frame.style.display = 'block';
    frame.style.background = '#16233b';
    frame.style.borderRadius = '18px';
    frame.style.overflow = 'hidden';
    el.appendChild(frame);
  }
  return frame;
}

function currentFormat() {
  return FORMATS[document.getElementById('d-format').value] || FORMATS.instagram_portrait;
}

function fitPreview() {
  const stage = document.getElementById('preview-stage');
  const { w, h } = currentFormat();
  const availW = stage.clientWidth - 48;
  const scale = Math.min(availW / w, 1);
  const scaledH = h * scale;
  const minH = Math.max(scaledH + 48, 300);
  stage.style.minHeight = minH + 'px';
  const el = ensureCardEl();
  el.style.width = (w * scale) + 'px';
  el.style.height = (h * scale) + 'px';
  const inner = el.firstElementChild;
  if (inner) {
    inner.style.width = w + 'px';
    inner.style.height = h + 'px';
    inner.style.transform = `scale(${scale})`;
    inner.style.transformOrigin = '0 0';
  }
}

function showMessage(html) {
  const el = ensureCardEl();
  const { w, h } = currentFormat();
  el.innerHTML = `<div style="width:${w}px;height:${h}px;display:flex;align-items:center;justify-content:center;text-align:center;padding:32px;box-sizing:border-box;background:#16233b;border-radius:18px;color:#8ea3c0;font-family:Inter,sans-serif;font-size:18px;line-height:1.6;">${html}</div>`;
  fitPreview();
}

let _previewKey = null;

async function renderPreview() {
  const state = App.state;
  const card = state.cards[state.currentIndex];
  if (!card) {
    showMessage('No hay tarjetas para mostrar.<br>Genera contenido o abre un proyecto en el panel de contenido.');
    return;
  }

  const payload = {
    ...card,
    destination: state.destination,
    template_id: state.template,
    format_id: state.format,
    design: buildDesignFromControls(),
  };
  const key = JSON.stringify(payload);
  if (key === _previewKey) return;
  _previewKey = key;

  let html;
  try {
    html = await API.preview(payload);
  } catch (err) {
    _previewKey = null;
    showMessage(`No se pudo renderizar la tarjeta.<br><span style="color:#ff7a7a;font-size:15px">${esc(err.message)}</span>`);
    return;
  }

  ensureFrameEl().srcdoc = html;
  fitPreview();

  const frame = document.getElementById('preview-frame');
  frame.onload = () => {
    try {
      const doc = frame.contentDocument || frame.contentWindow.document;
      const script = doc.createElement('script');
      script.textContent = `
        (function() {
          var s = document.createElement('style');
          s.textContent = '[data-field]{cursor:pointer;transition:outline .15s}[data-field]:hover{outline:2px dashed rgba(244,185,66,0.6);outline-offset:2px;border-radius:3px}';
          document.head.appendChild(s);
          document.addEventListener('click', function(e) {
            var el = e.target.closest('[data-field]');
            if (el) {
              e.preventDefault();
              e.stopPropagation();
              parent.postMessage({
                type: 'tc-field-click',
                field: el.getAttribute('data-field'),
                value: el.textContent
              }, '*');
            }
          });
        })();
      `;
      doc.body.appendChild(script);
    } catch (err) {
      console.warn('No se pudo inyectar editor en iframe:', err);
    }
  };
}
