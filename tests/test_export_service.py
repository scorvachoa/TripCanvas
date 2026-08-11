import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from models.content import Card  # noqa: E402
from services import export_service  # noqa: E402
from services.export_service import (  # noqa: E402
    _maybe_compress,
    render_card_html,
)


class RenderCardHtmlTest(unittest.TestCase):
    def _card(self, **overrides):
        base = {
            "type": "dato_curioso",
            "title": "Machu Picchu",
            "body": "Ciudadela inca en lo alto de los Andes.",
            "facts": [],
            "question": "",
            "answer": "",
            "myth": "",
            "reality": "",
            "options": [],
            "location": "Cusco",
            "altitude": "2430 m",
            "source": "UNESCO",
            "number": 1,
            "extra": {},
            "image": None,
            "image_query": "",
        }
        base.update(overrides)
        return Card(**base)

    def test_substitutes_tokens(self):
        card = self._card()
        html = render_card_html(card, "dato-curioso", destination="Peru")
        self.assertIn("Machu Picchu", html)
        self.assertIn("Ciudadela inca", html)
        self.assertIn("Peru", html)
        self.assertIn("UNESCO", html)

    def test_no_leftover_tokens(self):
        card = self._card()
        html = render_card_html(card, "dato-curioso", destination="Peru")
        import re

        leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
        self.assertEqual(leftovers, [])

    def test_quiz_renders_options(self):
        card = self._card(
            type="quiz",
            question="¿Dónde está Machu Picchu?",
            answer="En Perú",
            options=["Perú", "Bolivia", "Chile", "Ecuador"],
        )
        html = render_card_html(card, "quiz", destination="Peru")
        self.assertIn("Perú", html)
        self.assertIn("Bolivia", html)
        self.assertIn("Chile", html)

    def test_mito_realidad_renders_myth_and_reality(self):
        card = self._card(
            type="mito_realidad",
            title="Mito de la altura",
            myth="Cusco está al nivel del mar.",
            reality="Cusco está a más de 3000 m.",
        )
        html = render_card_html(card, "mito-realidad", destination="Peru")
        self.assertIn("nivel del mar", html)
        self.assertIn("3000 m", html)

    def test_comparativa_renders_items(self):
        card = self._card(
            type="comparativa",
            title="Cusco vs Lima",
            body="Dos mundos.",
            extra={"items": [{"label": "Altitud", "value": "3400 m"}]},
        )
        html = render_card_html(card, "comparativa", destination="Peru")
        self.assertIn("Altitud", html)
        self.assertIn("3400 m", html)

    def test_facts_list_renders(self):
        card = self._card(type="cinco_datos", facts=["Dato A", "Dato B", "Dato C"])
        html = render_card_html(card, "cinco-datos", destination="Peru")
        self.assertIn("Dato A", html)
        self.assertIn("Dato C", html)

    def test_square_adds_class(self):
        card = self._card()
        html = render_card_html(card, "dato-curioso", destination="Peru", format_id="square")
        self.assertIn("tc-square", html)

    def test_photo_injects_background(self):
        card = self._card(image="https://example.com/photo.jpg")
        html = render_card_html(card, "dato-curioso", destination="Peru")
        self.assertIn("tc-has-photo", html)
        self.assertIn("background-image", html)

    def test_design_colors_applied(self):
        card = self._card()
        design = {
            "background": "#123456",
            "text": "#abcdef",
            "accent": "#ff0000",
            "overlay": "rgba(0,0,0,0.5)",
            "font": "'Poppins', sans-serif",
            "showLogo": True,
            "textScale": 1.1,
        }
        html = render_card_html(card, "dato-curioso", destination="Peru", design=design)
        self.assertIn("#123456", html)
        self.assertIn("#abcdef", html)
        self.assertIn("#ff0000", html)

    def test_unknown_template_raises(self):
        card = self._card()
        with self.assertRaises(ValueError):
            render_card_html(card, "no-existe-plantilla")

    def test_html_content_escaped(self):
        card = self._card(title='<script>alert(1)</script>', body='<b>x</b>')
        html = render_card_html(card, "dato-curioso", destination="Peru")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


class MaybeCompressTest(unittest.TestCase):
    def _png(self, data=b"png-data"):
        tmp = Path(tempfile.mkdtemp())
        p = tmp / "card.png"
        p.write_bytes(data)
        return p

    def test_no_compress_leaves_file(self):
        p = self._png()
        with mock.patch.object(
            export_service, "compress_image", return_value=b"smaller"
        ) as compress:
            _maybe_compress(p, compress=False)
        compress.assert_not_called()
        self.assertEqual(p.read_bytes(), b"png-data")

    def test_compress_writes_when_smaller(self):
        p = self._png()
        with mock.patch.object(
            export_service, "compress_image", return_value=b"smaller"
        ) as compress:
            _maybe_compress(p, compress=True)
        compress.assert_called_once()
        self.assertEqual(p.read_bytes(), b"smaller")

    def test_compress_error_keeps_original(self):
        p = self._png()
        with mock.patch.object(
            export_service,
            "compress_image",
            side_effect=Exception("boom"),
        ):
            _maybe_compress(p, compress=True)
        self.assertEqual(p.read_bytes(), b"png-data")


if __name__ == "__main__":
    unittest.main()
