import unittest
from unittest import mock

from services import tinify_service


def _fake_tinify(compressed=b"compressed", error=None):
    fake = mock.MagicMock()
    if error is not None:
        fake.from_buffer.side_effect = error
    else:
        source = mock.MagicMock()
        source.to_buffer.return_value = compressed
        fake.from_buffer.return_value = source
    return fake


class TinifyServiceTest(unittest.TestCase):
    def test_no_key_returns_original(self):
        with mock.patch.object(tinify_service, "TINIFY_API_KEY", ""):
            out = tinify_service.compress_image(b"original")
        self.assertEqual(out, b"original")

    def test_empty_data_returns_original(self):
        with mock.patch.object(tinify_service, "TINIFY_API_KEY", "clave"):
            out = tinify_service.compress_image(b"")
        self.assertEqual(out, b"")

    def test_compresses_when_smaller(self):
        fake = _fake_tinify(compressed=b"small")
        with mock.patch.object(tinify_service, "TINIFY_API_KEY", "clave"), mock.patch.dict(
            "sys.modules", {"tinify": fake}
        ):
            out = tinify_service.compress_image(b"longer original bytes")
        self.assertEqual(out, b"small")

    def test_keeps_original_when_not_smaller(self):
        fake = _fake_tinify(compressed=b"aaaaaaaaaaaaaaaaaa")
        with mock.patch.object(tinify_service, "TINIFY_API_KEY", "clave"), mock.patch.dict(
            "sys.modules", {"tinify": fake}
        ):
            out = tinify_service.compress_image(b"aaa")
        self.assertEqual(out, b"aaa")

    def test_error_returns_original(self):
        fake = _fake_tinify(error=Exception("cuota agotada"))
        with mock.patch.object(tinify_service, "TINIFY_API_KEY", "clave"), mock.patch.dict(
            "sys.modules", {"tinify": fake}
        ):
            out = tinify_service.compress_image(b"original")
        self.assertEqual(out, b"original")


if __name__ == "__main__":
    unittest.main()
