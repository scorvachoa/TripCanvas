"""Prompts especializados por categoría de contenido.

Gemini solo devuelve datos JSON. Nunca HTML, CSS ni instrucciones de diseño.
"""

CATEGORY_GUIDANCE: dict[str, str] = {
    "dato_curioso": (
        "Genera datos curiosos: información interesante y poco conocida, "
        "evita clichés, evita información inventada, lenguaje claro y directo, "
        "escrito para redes sociales, sin párrafos largos, prioriza datos verificables "
        "y evita repetir información entre tarjetas."
    ),
    "sabias_que": (
        "Genera preguntas tipo '¿Sabías que...?' llamativas. La pregunta va en 'title' "
        "(y también en 'question'), la respuesta breve en 'body' (y también en 'answer'). "
        "Evita clichés y datos inventados."
    ),
    "historia": (
        "Genera historias breves con fecha en 'extra.fecha' (formato '1899' o 'Siglo XV'). "
        "Estilo editorial: 'title' atractivo, 'body' que cuente un momento histórico real. "
        "Prioriza datos verificables."
    ),
    "mito_realidad": (
        "Genera pares 'mito' y 'realidad'. El mito es una creencia popular común (puede ser "
        "falsa o exagerada) y la realidad es el dato correcto con base verificable. "
        "Escribe ambos en lenguaje claro para redes. Completa también 'title' y 'body' breves."
    ),
    "quiz": (
        "Genera una pregunta con 4 opciones ('options'). La pregunta va en 'title' "
        "(y en 'question'), la respuesta correcta marcada en 'extra.correct_index' (0-3) "
        "y la explicación breve en 'body' (y en 'answer'). Contenido verificable y entretenido."
    ),
    "comparativa": (
        "Genera una comparativa entre dos conceptos/destinos. En 'extra.items' incluye una "
        "lista de objetos con 'label' y 'value' (ej: ubicación, altitud, dificultad, "
        "duración, atractivo principal). 'title' llamativo, resumen en 'body'."
    ),
    "guia_rapida": (
        "Genera una guía rápida con campos prácticos en 'facts': ubicación, altitud, "
        "mejor época, dificultad y duración. Cada fact es un objeto con 'label' y 'value'. "
        "'title' llamativo y 'body' con un resumen breve."
    ),
    "cinco_datos": (
        "Genera exactamente 5 datos numerados en 'facts' (lista de strings cortos). "
        "Título llamativo en 'title'. Datos verificables y variados entre sí."
    ),
    "consejos": (
        "Genera consejos prácticos y útiles para viajeros en 'facts' (lista de strings cortos). "
        "Consejos reales, específicos del destino y no genéricos. 'title' llamativo."
    ),
    "cultura": (
        "Genera información sobre la cultura del destino: tradiciones, costumbres, "
        "gastronomía o festividades. Texto breve en 'body', 'title' atractivo, "
        "datos extra en 'facts'."
    ),
    "arquitectura": (
        "Genera información sobre arquitectura del destino: estilos, técnicas "
        "constructivas, materiales o detalles destacados. Texto breve en 'body', "
        "'title' atractivo."
    ),
    "naturaleza": (
        "Genera información sobre la naturaleza del destino: fauna, flora, paisajes o "
        "clima. Texto breve en 'body', 'title' atractivo, datos extra en 'facts'."
    ),
    "como_llegar": (
        "Genera instrucciones claras sobre cómo llegar al destino: rutas, transportes "
        "y tiempos. En 'facts' lista de objetos con 'label' y 'value'. 'title' llamativo."
    ),
    "mejor_epoca": (
        "Genera información sobre la mejor época para visitar: estaciones, clima, "
        "eventos. En 'facts' lista de objetos con 'label' y 'value'. 'title' llamativo."
    ),
    "informacion_general": (
        "Genera información general útil del destino: qué es, dónde está, datos clave. "
        "Texto breve en 'body', 'title' atractivo, datos en 'facts'."
    ),
}

LANGUAGES: dict[str, str] = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
}

# Esquema de la tarjeta que el modelo debe completar.
SCHEMA_HINT = """Cada tarjeta debe ser un objeto con esta forma:
{
  "type": "<tipo de contenido>",
  "title": "título llamativo (máx 100 caracteres)",
  "body": "texto corto para redes (máx 400 caracteres)",
  "facts": ["dato 1", "dato 2", ...],  // o lista de objetos {"label": "...", "value": "..."} si aplica
  "question": "pregunta, si aplica",
  "answer": "respuesta breve, si aplica",
  "myth": "mito, si aplica",
  "reality": "realidad, si aplica",
  "options": ["opción A", "opción B", "opción C", "opción D"],  // solo quiz
  "extra": {},  // datos extra opcionales (ej. fecha, correct_index, items)
  "location": "ciudad, país",
  "altitude": "altitud en m s. n. m.",
  "source": "fuente o institución (ej. UNESCO)"
}
"""


def build_generation_prompt(
    destination: str,
    category: str,
    count: int,
    language: str = "es",
    destinations_data: str = "",
) -> str:
    guidance = CATEGORY_GUIDANCE.get(category, CATEGORY_GUIDANCE["dato_curioso"])
    lang = LANGUAGES.get(language, "Español")

    prompt = f"""
Eres un experto en contenido turístico y copywriting para redes sociales.

Destino: {destination}
Tipo de contenido: {category}
Cantidad de tarjetas: {count}
Idioma de todo el contenido: {lang}

REGLAS:
- Genera exactamente {count} tarjetas DIFERENTES entre sí.
- Siempre completa 'title' y 'body' aunque sean breves: son los campos principales que se muestran.
- {guidance}
- NO inventes datos. Si no estás seguro, omite el campo.
- Todo el contenido debe estar en {lang}.
- No uses markdown. No uses texto libre.
- Responde ÚNICAMENTE con JSON válido (sin bloques ```, sin comentarios).

FORMATO DE LA RESPUESTA (JSON):
{{
  "destination": "{destination}",
  "cards": [ {SCHEMA_HINT} ]
}}

DATOS DE REFERENCIA DEL DESTINO:
{destinations_data if destinations_data else "(sin datos adicionales)"}
"""
    return prompt.strip()


def build_correction_prompt(
    raw_response: str,
    validation_errors: list[str],
    category: str,
    count: int,
) -> str:
    guidance = CATEGORY_GUIDANCE.get(category, CATEGORY_GUIDANCE["dato_curioso"])
    errors = "\n".join(f"- {e}" for e in validation_errors)

    return f"""
Tu respuesta anterior no pasó la validación. Corrígela.

Errores de validación:
{errors}

Respuesta anterior (inválida):
{raw_response}

REGLA:
- Genera exactamente {count} tarjetas.
- {guidance}
- Respónde SOLO con JSON válido siguiendo este esquema exacto:
{{
  "destination": "<destino>",
  "cards": [ {SCHEMA_HINT} ]
}}
No uses bloques ``` ni texto adicional.
""".strip()
