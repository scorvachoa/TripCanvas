/* ===== Background Picker: modal con fondos preestablecidos y color picker ===== */

const BG_PRESETS = [
  { id: 'ocean', name: 'Océano profundo', css: 'linear-gradient(135deg, #0f1a2e 0%, #1a3a5c 100%)' },
  { id: 'night', name: 'Noche estrellada', css: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)' },
  { id: 'aurora', name: 'Aurora', css: 'linear-gradient(135deg, #2d1b69 0%, #11998e 100%)' },
  { id: 'deep', name: 'Púrpura profundo', css: 'linear-gradient(135deg, #0c0c1d 0%, #1a1a3e 50%, #2d1b69 100%)' },
  { id: 'steel', name: 'Acero azul', css: 'linear-gradient(135deg, #141e30 0%, #243b55 100%)' },
  { id: 'royal', name: 'Real púrpura', css: 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)' },
  { id: 'sunset', name: 'Atardecer', css: 'linear-gradient(135deg, #1a1a2e 0%, #e94560 100%)' },
];

const BG_SOLID_COLORS = [
  '#0f1a2e', '#1a1a2e', '#16213e', '#0f3460', '#2d1b69',
  '#11998e', '#141e30', '#243b55', '#302b63', '#24243e',
  '#e94560', '#0c0c1d', '#1a3a5c', '#ffffff', '#000000',
];

const BackgroundPicker = {
  _selected: null,
  _lastTab: 'presets',

  init() {
    const grid = document.getElementById('bg-presets-grid');
    grid.innerHTML = '';

    BG_SOLID_COLORS.forEach(color => {
      const swatch = document.createElement('div');
      swatch.className = 'bg-swatch';
      swatch.style.background = color;
      swatch.dataset.value = color;
      swatch.title = color;
      swatch.addEventListener('click', () => this._selectSwatch(swatch, color));
      grid.appendChild(swatch);
    });

    BG_PRESETS.forEach(preset => {
      const swatch = document.createElement('div');
      swatch.className = 'bg-swatch';
      swatch.style.background = preset.css;
      swatch.dataset.value = preset.css;
      swatch.title = preset.name;
      swatch.addEventListener('click', () => this._selectSwatch(swatch, preset.css));
      grid.appendChild(swatch);
    });

    document.querySelectorAll('#bg-picker-overlay .tab').forEach(tab => {
      tab.addEventListener('click', () => this._switchTab(tab.dataset.tab));
    });

    document.getElementById('bg-picker-close').addEventListener('click', () => this.close());
    document.getElementById('bg-picker-cancel').addEventListener('click', () => this.close());
    document.getElementById('bg-picker-apply').addEventListener('click', () => this.apply());

    const customColor = document.getElementById('bg-custom-color');
    const customHex = document.getElementById('bg-custom-hex');
    customColor.addEventListener('input', () => {
      customHex.value = customColor.value;
      document.getElementById('bg-custom-circle').style.background = customColor.value;
      this._selected = customColor.value;
    });
    customHex.addEventListener('input', () => {
      if (/^#[0-9a-fA-F]{6}$/.test(customHex.value)) {
        customColor.value = customHex.value;
        document.getElementById('bg-custom-circle').style.background = customHex.value;
        this._selected = customHex.value;
      }
    });
  },

  open() {
    this._selected = null;
    document.getElementById('bg-picker-overlay').classList.remove('hidden');
    this._switchTab(this._lastTab);
    const currentBg = document.getElementById('d-bg-value').value;
    document.querySelectorAll('.bg-swatch').forEach(s => {
      s.classList.toggle('selected', s.dataset.value === currentBg);
    });
  },

  close() {
    document.getElementById('bg-picker-overlay').classList.add('hidden');
  },

  _switchTab(tabId) {
    this._lastTab = tabId;
    document.querySelectorAll('#bg-picker-overlay .tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabId);
    });
    document.querySelectorAll('#bg-picker-overlay .tab-content').forEach(c => {
      c.classList.toggle('active', c.id === 'tab-' + tabId);
    });
  },

  _selectSwatch(el, value) {
    document.querySelectorAll('.bg-swatch').forEach(s => s.classList.remove('selected'));
    el.classList.add('selected');
    this._selected = value;
  },

  apply() {
    if (this._selected) {
      this._setBg(this._selected);
    }
    this.close();
  },

  _setBg(value) {
    document.getElementById('d-bg-value').value = value;
    if (!value.startsWith('linear-gradient') && !value.startsWith('radial-gradient')) {
      document.getElementById('d-bg').value = value;
    }
    const circle = document.getElementById('d-bg-circle');
    circle.style.background = value;
    if (typeof renderPreview === 'function') {
      renderPreview();
    }
  },
};
