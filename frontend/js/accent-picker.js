/* ===== Accent Picker: modal con colores preestablecidos y color picker ===== */

const ACCENT_PRESETS = [
  { id: 'gold', name: 'Dorado', css: '#f4b942' },
  { id: 'coral', name: 'Coral', css: '#e94560' },
  { id: 'teal', name: 'Turquesa', css: '#11998e' },
  { id: 'sky', name: 'Cielo', css: '#4ecdc4' },
  { id: 'violet', name: 'Violeta', css: '#9b59b6' },
  { id: 'rose', name: 'Rosa', css: '#fd79a8' },
  { id: 'lime', name: 'Lima', css: '#00b894' },
  { id: 'orange', name: 'Naranja', css: '#e17055' },
  { id: 'blue', name: 'Azul', css: '#0984e3' },
  { id: 'red', name: 'Rojo', css: '#d63031' },
];

const ACCENT_SOLID_COLORS = [
  '#f4b942', '#e94560', '#11998e', '#4ecdc4', '#9b59b6',
  '#fd79a8', '#00b894', '#e17055', '#0984e3', '#d63031',
  '#ffffff', '#000000', '#636e72', '#2d3436', '#dfe6e9',
];

const AccentPicker = {
  _selected: null,
  _lastTab: 'presets',

  init() {
    const grid = document.getElementById('accent-presets-grid');
    grid.innerHTML = '';

    ACCENT_SOLID_COLORS.forEach(color => {
      const swatch = document.createElement('div');
      swatch.className = 'bg-swatch';
      swatch.style.background = color;
      swatch.dataset.value = color;
      swatch.title = color;
      swatch.addEventListener('click', () => this._selectSwatch(swatch, color));
      grid.appendChild(swatch);
    });

    ACCENT_PRESETS.forEach(preset => {
      const swatch = document.createElement('div');
      swatch.className = 'bg-swatch';
      swatch.style.background = preset.css;
      swatch.dataset.value = preset.css;
      swatch.title = preset.name;
      swatch.addEventListener('click', () => this._selectSwatch(swatch, preset.css));
      grid.appendChild(swatch);
    });

    document.querySelectorAll('#accent-picker-overlay .tab').forEach(tab => {
      tab.addEventListener('click', () => this._switchTab(tab.dataset.tab));
    });

    document.getElementById('accent-picker-close').addEventListener('click', () => this.close());
    document.getElementById('accent-picker-cancel').addEventListener('click', () => this.close());
    document.getElementById('accent-picker-apply').addEventListener('click', () => this.apply());

    const customColor = document.getElementById('accent-custom-color');
    const customHex = document.getElementById('accent-custom-hex');
    customColor.addEventListener('input', () => {
      customHex.value = customColor.value;
      document.getElementById('accent-custom-circle').style.background = customColor.value;
      this._selected = customColor.value;
    });
    customHex.addEventListener('input', () => {
      if (/^#[0-9a-fA-F]{6}$/.test(customHex.value)) {
        customColor.value = customHex.value;
        document.getElementById('accent-custom-circle').style.background = customHex.value;
        this._selected = customHex.value;
      }
    });
  },

  open() {
    this._selected = null;
    document.getElementById('accent-picker-overlay').classList.remove('hidden');
    this._switchTab(this._lastTab);
    const currentAccent = document.getElementById('d-accent-value').value;
    document.querySelectorAll('#accent-presets-grid .bg-swatch').forEach(s => {
      s.classList.toggle('selected', s.dataset.value === currentAccent);
    });
  },

  close() {
    document.getElementById('accent-picker-overlay').classList.add('hidden');
  },

  _switchTab(tabId) {
    this._lastTab = tabId;
    document.querySelectorAll('#accent-picker-overlay .tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabId);
    });
    document.querySelectorAll('#accent-picker-overlay .tab-content').forEach(c => {
      c.classList.toggle('active', c.id === 'accent-tab-' + tabId);
    });
  },

  _selectSwatch(el, value) {
    document.querySelectorAll('#accent-presets-grid .bg-swatch').forEach(s => s.classList.remove('selected'));
    el.classList.add('selected');
    this._selected = value;
  },

  apply() {
    if (this._selected) {
      this._setAccent(this._selected);
    }
    this.close();
  },

  _setAccent(value) {
    document.getElementById('d-accent-value').value = value;
    if (!value.startsWith('linear-gradient') && !value.startsWith('radial-gradient')) {
      document.getElementById('d-accent').value = value;
    }
    const circle = document.getElementById('d-accent-circle');
    circle.style.background = value;
    if (typeof renderPreview === 'function') {
      renderPreview();
    }
  },
};
