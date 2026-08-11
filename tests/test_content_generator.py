import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from gemini import content_generator  # noqa: E402
from gemini.content_generator import (  # noqa: E402
    MAX_IMAGE_GENERATIONS,
    generate_content,
)


def _deck_json(count: int) -> str:
    cards = [
        {
            "type": "dato_curioso",
            "title": f"Título {i}",
            "body": f"Cuerpo {i}",
            "image_query": f"consulta {i}",
        }
        for i in range(count)
    ]
    return json.dumps({"destination": "Cusco", "cards": cards})


class FakeClient:
    """Cliente falso: siempre devuelve un deck JSON válido."""

    def generate(self, prompt, temperature=0.7):
        return _deck_json(2)


class GenerateContentImagesTest(unittest.TestCase):
    def _args(self, **overrides):
        defaults = {
            "destination": "Cusco",
            "category": "dato_curioso",
            "count": 2,
        }
        defaults.update(overrides)
        return defaults

    def test_disabled_images_do_not_search_pexels(self):
        with mock.patch.object(
            content_generator, "search_photo_urls"
        ) as search, mock.patch.object(
            content_generator, "PEXELS_API_KEY", "clave"
        ):
            result = generate_content(
                client=FakeClient(), **self._args(with_images=False)
            )
        search.assert_not_called()
        self.assertEqual(len(result.cards), 2)
        self.assertIsNone(result.cards[0].image)

    def test_enabled_images_use_image_query(self):
        with mock.patch.object(
            content_generator, "search_photo_urls", return_value=[
                "https://images.pexels.com/1.jpg",
                "https://images.pexels.com/2.jpg",
            ]
        ) as search, mock.patch.object(
            content_generator, "PEXELS_API_KEY", "clave"
        ):
            result = generate_content(
                client=FakeClient(), **self._args(with_images=True)
            )
        self.assertEqual(search.call_count, 2)
        self.assertEqual(
            search.call_args_list[0].args[0], "consulta 0"
        )
        self.assertEqual(result.cards[0].image, "https://images.pexels.com/1.jpg")
        self.assertEqual(result.cards[1].image, "https://images.pexels.com/2.jpg")

    def test_missing_api_key_keeps_cards_without_photo(self):
        with mock.patch.object(
            content_generator, "search_photo_urls"
        ) as search, mock.patch.object(
            content_generator, "PEXELS_API_KEY", ""
        ):
            result = generate_content(
                client=FakeClient(), **self._args(with_images=True)
            )
        search.assert_not_called()
        self.assertIsNone(result.cards[0].image)

    def test_search_failure_keeps_card_without_photo(self):
        with mock.patch.object(
            content_generator,
            "search_photo_urls",
            side_effect=ConnectionError("red caída"),
        ), mock.patch.object(
            content_generator, "PEXELS_API_KEY", "clave"
        ):
            result = generate_content(
                client=FakeClient(), **self._args(with_images=True)
            )
        self.assertEqual(len(result.cards), 2)
        self.assertIsNone(result.cards[0].image)
        self.assertIsNone(result.cards[1].image)

    def test_empty_results_keeps_card_without_photo(self):
        with mock.patch.object(
            content_generator, "search_photo_urls", return_value=[]
        ), mock.patch.object(
            content_generator, "PEXELS_API_KEY", "clave"
        ):
            result = generate_content(
                client=FakeClient(), **self._args(with_images=True)
            )
        self.assertIsNone(result.cards[0].image)

    def test_caps_number_of_fetched_photos(self):
        class ManyCardsClient(FakeClient):
            def generate(self, prompt, temperature=0.7):
                return _deck_json(MAX_IMAGE_GENERATIONS + 2)

        with mock.patch.object(
            content_generator,
            "search_photo_urls",
            return_value=["https://images.pexels.com/a.jpg"],
        ) as search, mock.patch.object(
            content_generator, "PEXELS_API_KEY", "clave"
        ):
            result = generate_content(
                client=ManyCardsClient(),
                **self._args(count=MAX_IMAGE_GENERATIONS + 2, with_images=True),
            )
        self.assertEqual(len(result.cards), MAX_IMAGE_GENERATIONS + 2)
        self.assertEqual(search.call_count, MAX_IMAGE_GENERATIONS)
        self.assertIsNotNone(result.cards[0].image)
        self.assertIsNone(result.cards[MAX_IMAGE_GENERATIONS].image)


if __name__ == "__main__":
    unittest.main()
