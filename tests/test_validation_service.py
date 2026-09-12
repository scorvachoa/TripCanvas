import unittest

from services.validation_service import (
    CATEGORY_REQUIRED_FIELDS,
    extract_json,
    validate_response,
)


class ExtractJsonTest(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(extract_json('{"a": 1}'), {"a": 1})

    def test_with_code_fence(self):
        self.assertEqual(extract_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_json_embedded_in_text(self):
        self.assertEqual(extract_json('Texto antes\n{"cards": []}\nalgo despues'), {"cards": []})

    def test_invalid_returns_none(self):
        self.assertIsNone(extract_json("no json here"))
        self.assertIsNone(extract_json(""))


class ValidateResponseTest(unittest.TestCase):
    def test_valid_card(self):
        data = {"cards": [{"title": "T", "body": "B"}]}
        result = validate_response(data, expected_count=1, category="dato_curioso")
        self.assertTrue(result.valid)

    def test_wrong_count(self):
        data = {"cards": [{"title": "T", "body": "B"}]}
        result = validate_response(data, expected_count=2, category="dato_curioso")
        self.assertFalse(result.valid)
        self.assertTrue(any("Se esperaban 2" in e for e in result.errors))

    def test_duplicate_titles(self):
        data = {"cards": [
            {"title": "Igual", "body": "A"},
            {"title": "igual", "body": "B"},
        ]}
        result = validate_response(data, expected_count=2, category="dato_curioso")
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicado" in e.lower() for e in result.errors))

    def test_title_too_long(self):
        data = {"cards": [{"title": "X" * 101, "body": "B"}]}
        result = validate_response(data, expected_count=1, category="dato_curioso")
        self.assertFalse(result.valid)
        self.assertTrue(any("título demasiado largo" in e.lower() for e in result.errors))

    def test_missing_body_for_dato_curioso(self):
        data = {"cards": [{"title": "Solo titulo"}]}
        result = validate_response(data, expected_count=1, category="dato_curioso")
        self.assertFalse(result.valid)
        self.assertTrue(any("'body'" in e for e in result.errors))

    def test_quiz_requires_options(self):
        data = {"cards": [{"question": "Q", "answer": "A", "options": ["solo"]}]}
        result = validate_response(data, expected_count=1, category="quiz")
        self.assertFalse(result.valid)
        self.assertTrue(any("options" in e for e in result.errors))

    def test_quiz_valid(self):
        data = {"cards": [{"question": "Q", "answer": "A", "options": ["a", "b", "c", "d"]}]}
        result = validate_response(data, expected_count=1, category="quiz")
        self.assertTrue(result.valid)

    def test_historia_requires_fecha(self):
        data = {"cards": [{"title": "T", "body": "B"}]}
        result = validate_response(data, expected_count=1, category="historia")
        self.assertFalse(result.valid)
        self.assertTrue(any("extra.fecha" in e for e in result.errors))

    def test_comparativa_requires_items(self):
        data = {"cards": [{"title": "T", "body": "B"}]}
        result = validate_response(data, expected_count=1, category="comparativa")
        self.assertFalse(result.valid)
        self.assertTrue(any("extra.items" in e for e in result.errors))

    def test_all_categories_defined(self):
        expected = {
            "dato_curioso", "sabias_que", "historia", "mito_realidad", "quiz",
            "comparativa", "guia_rapida", "cinco_datos", "consejos", "cultura",
            "arquitectura", "naturaleza", "como_llegar", "mejor_epoca",
            "informacion_general",
        }
        self.assertEqual(set(CATEGORY_REQUIRED_FIELDS), expected)

    def test_none_data_invalid(self):
        result = validate_response(None, expected_count=1)
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
