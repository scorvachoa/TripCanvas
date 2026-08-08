/* ===== Preview: renderiza tarjetas HTML/CSS reales ===== */

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

function renderFactsList(facts) {
  return (facts || [])
    .map((fact, i) => {
      const label = typeof fact === 'object' ? fact.label : i + 1;
      const value = typeof fact === 'object' ? fact.value : fact;
      const badge = typeof fact === 'object' ? '' : `<span class='fact-num'>${i + 1}</span>`;
      return `<li>${badge}<span>${esc(value)}</span>${label !== '' && typeof fact === 'object' ? `<span class='fv-label'>${esc(label)}</span>` : ''}</li>`;
    })
    .join('\n');
}

function renderFactsLabelValue(facts) {
  return (facts || [])
    .map((fact) => {
      if (typeof fact === 'object') {
        return `<div class='fv-row'><span class='fv-label'>${esc(fact.label)}</span><span class='fv-value'>${esc(fact.value)}</span></div>`;
      }
      return `<div class='fv-row'><span class='fv-value'>${esc(fact)}</span></div>`;
    })
    .join('\n');
}

function renderOptions(options) {
  const letters = ['A', 'B', 'C', 'D'];
  return (options || [])
    .map((opt, i) => {
      const letter = letters[i] || i + 1;
      return `<div class='quiz-option'><span class='quiz-letter'>${letter}</span><span>${esc(opt)}</span></div>`;
    })
    .join('\n');
}

function renderItems(items) {
  return (items || [])
    .map((item) =>
      item && typeof item === 'object'
        ? `<div class='cmp-row'><span class='cmp-label'>${esc(item.label)}</span><span class='cmp-value'>${esc(item.value)}</span></div>`
        : ''
    )
    .join('\n');
}

function factsAreLabelValue(facts) {
  return Array.isArray(facts) && facts.length > 0 && typeof facts[0] === 'object';
}

function buildCardHTML(card, template, destination, design) {
  const extra = card.extra || {};
  const factsHtml = factsAreLabelValue(card.facts)
    ? renderFactsLabelValue(card.facts)
    : renderFactsList(card.facts);

  const logo = design.showLogo
    ? `<div class="tc-logo"><span class="tc-logo-mark">✈</span><span class="tc-logo-text">TRIPCANVAS</span></div>`
    : '';

  const tokens = {
    DESTINATION: esc(destination),
    TITLE: esc(card.title),
    BODY: esc(card.body),
    QUESTION: esc(card.question),
    ANSWER: esc(card.answer),
    MYTH: esc(card.myth),
    REALITY: esc(card.reality),
    LOCATION: esc(card.location),
    ALTITUDE: esc(card.altitude),
    SOURCE: esc(card.source),
    NUMBER: esc(card.number != null ? card.number : ''),
    DATE: esc(extra.fecha || ''),
    FACTS_LIST: factsHtml,
    FACTS_LABEL_VALUE: factsHtml,
    OPTIONS: renderOptions(card.options),
    ITEMS: renderItems(extra.items),
    IMAGE: esc(card.image || ''),
    IMAGE_QUERY: esc(card.image_query || ''),
    LOGO: logo,
    BG: esc(design.background),
    TEXT: esc(design.text),
    ACCENT: esc(design.accent),
    OVERLAY: esc(design.overlay),
    FONT: esc(design.font),
  };

  let html = template.html;
  for (const [key, value] of Object.entries(tokens)) {
    html = html.split('{{' + key + '}}').join(value);
  }
  html = html.replace(/\{\{[A-Z_]+\}\}/g, '');

  return html;
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

let _cssEl = null;
let _cardEl = null;

function ensureCssEl() {
  if (!_cssEl || !_cssEl.isConnected) {
    _cssEl = document.createElement('style');
    document.getElementById('preview-stage').appendChild(_cssEl);
  }
  return _cssEl;
}

function ensureCardEl() {
  if (!_cardEl || !_cardEl.isConnected) {
    _cardEl = document.getElementById('preview-card');
  }
  return _cardEl;
}

function currentFormat() {
  return FORMATS[document.getElementById('d-format').value] || FORMATS.instagram_portrait;
}

function fitPreview() {
  const stage = document.getElementById('preview-stage');
  const { w, h } = currentFormat();
  const availW = stage.clientWidth - 48;
  const availH = Math.max(stage.clientHeight - 48, 300);
  const scale = Math.min(availW / w, availH / h, 1);
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

async function renderPreview() {
  const state = App.state;
  const card = state.cards[state.currentIndex];
  if (!card) return;

  const template = await TemplateStore.get(state.template);
  const design = buildDesignFromControls();

  ensureCssEl().textContent = `
    * { margin: 0; padding: 0; box-sizing: border-box; }

    .travel-card {
      --tc-bg: ${design.background};
      --tc-text: ${design.text};
      --tc-accent: ${design.accent};
      --tc-overlay: ${design.overlay};
      --tc-text-scale: ${design.textScale};
    }

    .tc-logo {
      position: absolute;
      top: 34px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(0, 0, 0, 0.4);
      color: #ffffff;
      font-weight: 700;
      font-size: calc(var(--tc-text-scale) * 26px);
      letter-spacing: 0.08em;
      padding: 10px 22px;
      border-radius: 999px;
      z-index: 20;
      font-family: 'Inter', 'Segoe UI', sans-serif;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    .tc-logo-mark { font-size: calc(var(--tc-text-scale) * 28px); line-height: 1; }

    .preview-stage { font-family: ${design.font}; }
    ${template.css}
  `;

  const html = buildCardHTML(card, template, state.destination, design);
  const el = ensureCardEl();
  const { w, h } = currentFormat();
  el.innerHTML = `<div style="width:${w}px;height:${h}px">${html}</div>`;
  fitPreview();
}
