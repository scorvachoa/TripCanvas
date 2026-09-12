import unittest

from services.template_service import (
    FORMATS,
    format_size,
    is_safe_template_id,
    list_templates,
    load_template,
)


class SafeTemplateIdTest(unittest.TestCase):
    def test_valid_ids(self):
        for tid in ("dato-curioso", "cinco_datos", "ABC_123", "mito-realidad"):
            self.assertTrue(is_safe_template_id(tid), tid)

    def test_invalid_ids(self):
        for tid in ("", "../", "a/b", "a\\b", "..", "a b", "a?b", "a.b"):
            self.assertFalse(is_safe_template_id(tid), tid)


class FormatSizeTest(unittest.TestCase):
    def test_known_formats(self):
        self.assertEqual(format_size("instagram_portrait"), (1080, 1350))
        self.assertEqual(format_size("square"), (1080, 1080))
        self.assertEqual(format_size("story"), (1080, 1920))

    def test_unknown_falls_back_to_portrait(self):
        self.assertEqual(format_size("no-existe"), (1080, 1350))

    def test_formats_dict_has_required(self):
        for fid in ("instagram_portrait", "square", "story"):
            self.assertIn(fid, FORMATS)
            self.assertIn("name", FORMATS[fid])
            self.assertIn("width", FORMATS[fid])
            self.assertIn("height", FORMATS[fid])


class LoadTemplateTest(unittest.TestCase):
    def test_load_known_template(self):
        tpl = load_template("dato-curioso")
        self.assertIsNotNone(tpl)
        self.assertEqual(tpl.id, "dato-curioso")
        self.assertTrue(tpl.html)
        self.assertTrue(tpl.css)

    def test_load_unknown_returns_none(self):
        self.assertIsNone(load_template("no-existe-12345"))

    def test_load_traversal_returns_none(self):
        self.assertIsNone(load_template("../config"))
        self.assertIsNone(load_template(".."))


class ListTemplatesTest(unittest.TestCase):
    def test_lists_templates(self):
        templates = list_templates()
        self.assertGreater(len(templates), 0)
        for tpl in templates:
            for key in ("id", "name", "category", "description"):
                self.assertIn(key, tpl)
            self.assertTrue(is_safe_template_id(tpl["id"]))


if __name__ == "__main__":
    unittest.main()
