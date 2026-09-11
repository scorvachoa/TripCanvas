/* ===== Generator: formularios de generación (home, crear y editor) ===== */

const Generator = {
  templates: [],

  async init() {
    this.templates = await TemplateStore.loadList();

    this.populateSelect('qg-template', this.templates.map((t) => ({ value: t.id, label: t.name })));
    this.populateSelect('c-template', this.templates.map((t) => ({ value: t.id, label: t.name })));

    this.bindOnSubmit('quick-gen-form', () => this.runQuickGenerate());
    this.bindOnSubmit('create-form', () => this.runCreateGenerate());
  },

  bindOnSubmit(formId, handler) {
    const form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      handler();
    });
  },

  populateSelect(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    for (const item of items) {
      const opt = document.createElement('option');
      if (typeof item === 'string') {
        opt.value = item;
        opt.textContent = item;
      } else {
        opt.value = item.value;
        opt.textContent = item.label;
      }
      el.appendChild(opt);
    }
  },

  setStatus(containerId, message, type) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.className = 'gen-status' + (type ? ' ' + type : '');
    el.innerHTML = type === 'error'
      ? message
      : `<span class="status-dot"></span>${message}`;
  },

  clearStatus(containerId) {
    const el = document.getElementById(containerId);
    if (el) el.innerHTML = '';
  },

  runQuickGenerate() {
    const dest = document.getElementById('qg-destination').value;
    const template = document.getElementById('qg-template').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('qg-count').value || '5', 10), 1), 20);
    const language = document.getElementById('qg-language').value;
    this.generate(dest, template, count, language, false, 'quick-gen-status', 'btn-quick-generate');
  },

  runCreateGenerate() {
    const dest = document.getElementById('c-destination').value.trim();
    const template = document.getElementById('c-template').value;
    const count = Math.min(Math.max(parseInt(document.getElementById('c-count').value || '5', 10), 1), 20);
    const language = document.getElementById('c-language').value;
    this.generate(dest, template, count, language, false, 'create-status', 'btn-create-generate');
  },

  checked(id, defaultValue) {
    const el = document.getElementById(id);
    return el ? el.checked : defaultValue;
  },

  async generate(destination, template, count, language, withImages, statusId, btnId) {
    if (!destination) {
      this.setStatus(statusId, 'Selecciona un destino.', 'error');
      return;
    }
    const btn = document.getElementById(btnId);
    const original = btn ? btn.innerHTML : '';
    if (btn) btn.disabled = true;

    const messages = withImages
      ? ['Preparando contenido...', 'Consultando Gemini...', 'Generando tarjetas...', 'Generando fotos del destino...']
      : ['Preparando contenido...', 'Consultando Gemini...', 'Generando tarjetas...', 'Preparando diseño...'];

    try {
      for (const msg of messages) {
        this.setStatus(statusId, msg);
        await new Promise((r) => setTimeout(r, 350));
      }

      const result = await API.generate({ destination, template_id: template, count, language, with_images: withImages });
      this.clearStatus(statusId);
      const tplName = (this.templates.find((t) => t.id === template) || {}).name || template;
      App.launchEditor({
        destination: result.destination || destination,
        cards: result.cards || [],
        template,
        language,
        projectId: null,
        projectName: `${destination} — ${tplName}`,
      });
    } catch (err) {
      this.setStatus(statusId, err.message || 'No se pudo generar el contenido.', 'error');
    } finally {
      if (btn) {
        btn.innerHTML = original;
        btn.disabled = false;
      }
    }
  },

  SAMPLE_CARDS: {
    quiz: [
      { question: '¿Cuál es la capital de Francia?', option1: 'Lyon', option2: 'Marsella', option3: 'París', option4: 'Niza', correctOption: 3, image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800' },
      { question: '¿En qué país se encuentra Machu Picchu?', option1: 'Colombia', option2: 'Perú', option3: 'Bolivia', option4: 'Ecuador', correctOption: 2, image: 'https://images.unsplash.com/photo-1587595431973-160d0d94add1?w=800' },
      { question: '¿Cuál es el río más largo del mundo?', option1: 'Amazonas', option2: 'Nilo', option3: 'Misisipi', option4: 'Yangtsé', correctOption: 1, image: 'https://images.unsplash.com/photo-1516426122078-c23e76319801?w=800' },
    ],
    mito_realidad: [
      { titulo: 'Los gladiadores romanos siempre morían en la arena', texto_realidad: 'La mayoría de los gladiadores eran profesionales bien pagados que sobrevivían a sus batallas. Las muertes eran más bien excepcionales.', image: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800' },
      { titulo: 'Las pirámides fueron construidas por esclavos', texto_realidad: 'Evidencias recientes sugieren que fueron construidas por trabajadores bien alimentados y remunerados, no por esclavos.', image: 'https://images.unsplash.com/photo-1503177119275-0aa32b3a9368?w=800' },
    ],
    cinco_datos: [
      { titulo: '5 datos curiosos de París', dato1: 'La Torre Eiffel se encoge 15 cm en invierno', dato2: 'Hay más de 200 escaleras en el metro', dato3: 'El Louvre fue originalmente una fortaleza', dato4: 'París tiene una sola dirección de calle sin nombre', dato5: 'Hay un viñedo secreto en Montmartre', image: 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800' },
    ],
    consejos: [
      { titulo: 'Consejos para visitar Roma', consejo1: 'Lleva calzado cómodo para caminar por las calles empedradas', consejo2: 'Visita el Coliseo al atardecer para mejores fotos', consejo3: 'Prueba la auténtica pasta alla carbonara', consejo4: 'Reserva entradas con antelación para el Vaticano', consejo5: 'Explora el barrio de Trastevere por la noche', image: 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800' },
    ],
    sabias_que: [
      { titulo: '¿Sabías que en Japón...', dato: 'Hay más de 6.800 islas, pero el 97% de la población vive en solo 4 de ellas', imagen: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800' },
      { titulo: '¿Sabías que en Islandia...', dato: 'No hay mosquitos, ni hormigas, ni serpientes en toda la isla', imagen: 'https://images.unsplash.com/photo-1504829857797-ddff27c55064?w=800' },
    ],
    comparativa: [
      { titulo: 'Europa vs Sudamérica', subtitulo1: 'Europa', subtitulo2: 'Sudamérica', punto1e: 'Ciudades históricas', punto1s: 'Naturaleza exuberante', punto2e: 'Trenes rápidos', punto2s: 'Aventura extrema', punto3e: 'Gastronomía variada', punto3s: 'Festivales coloridos', image: 'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=800' },
    ],
    historia: [
      { titulo: 'La historia de Machu Picchu', texto: 'Construida en el siglo XV como refugio real del emperador Pachacuti, esta ciudadela inca a 2.430 metros de altura fue abandonada durante la conquista española y redescubierta en 1911 por Hiram Bingham.', image: 'https://images.unsplash.com/photo-1587595431973-160d0d94add1?w=800' },
    ],
    arquitectura: [
      { titulo: 'La Sagrada Familia', texto: 'Diseñada por Antoni Gaudí, esta basílica lleva en construcción desde 1882. Su diseño combina el gótico con el art nouveau, y cada fachada representa un aspecto de la vida de Cristo.', image: 'https://images.unsplash.com/photo-1523482887225-4fee1a267c73?w=800' },
    ],
    como_llegar: [
      { titulo: 'Cómo llegar a Santorini', texto: 'Vuela al aeropuerto de Santorini (JTR) desde Atenas (45 min) o toma un ferry desde Pireo (5-8 horas). En la isla, los autobuses conectan las principales playas y pueblos.', image: 'https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=800' },
    ],
    cultura: [
      { titulo: 'La cultura japonesa', texto: 'Japón combina tradiciones milenarias como la ceremonia del té, el kabuki y los templos zen, con una cultura pop vanguardista de anime, tecnología y moda única en el mundo.', image: 'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800' },
    ],
    guia_rapida: [
      { titulo: 'Guía rápida de Barcelona', dato1: 'Visita La Rambla y el Mercado de La Boquería', dato2: 'Explora el Park Güell al amanecer', dato3: 'Tapea por el Born y la Ribera', dato4: 'Relájate en la Barceloneta', dato5: 'Descubre el Barrio Gótico al atardecer', image: 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800' },
    ],
    informacion_general: [
      { titulo: 'Información general de Tailandia', dato1: 'Moneda: Baht tailandés (THB)', dato2: 'Idioma: Tailandés', dato3: 'Clima: Tropical, seco de noviembre a abril', dato4: 'Visa: Exenta de visa hasta 30 días para muchos países', dato5: 'Moneda: 1 EUR ≈ 38 THB', image: 'https://images.unsplash.com/photo-1528181304800-259b08848526?w=800' },
    ],
    mejor_epoca: [
      { titulo: 'Mejor época para visitar la Patagonia', texto: 'De octubre a marzo (primavera-verano austral). Diciembre y enero ofrecen los mejores días para trekking, con temperaturas de 5°C a 20°C y hasta 17 horas de luz.', image: 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800' },
    ],
    naturaleza: [
      { titulo: 'Maravillas naturales de Costa Rica', texto: 'Con el 5% de la biodiversidad mundial, Costa Rica alberga volcanes activos, selvas tropicales, arrecifes de coral y playas vírgenes. Destinos imperdibles: Arenal, Monteverde y Manuel Antonio.', image: 'https://images.unsplash.com/photo-1519999482648-25049ddd37b1?w=800' },
    ],
  },
};