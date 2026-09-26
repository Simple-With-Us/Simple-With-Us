"""Regression checks for public release actions and generated detail regions."""
import copy
import json
import unittest
from pathlib import Path

import build_catalog as catalog


class CatalogContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(catalog.DATA.read_text())

    def test_current_release_facts_and_detail_regions(self):
        self.assertEqual([], catalog.lint(self.data))
        for app in self.data["apps"]:
            if not app.get("page"):
                continue
            path = catalog.ROOT / app["page"].lstrip("/") / "index.html"
            page = path.read_text()
            self.assertEqual(page, catalog.splice(page, "availability", catalog.availability_region(app)))
            for fact in app["availability"].values():
                if fact["url"]:
                    self.assertIn(f'href="{fact["url"]}"', page)

    def test_private_source_and_generic_invite_are_rejected(self):
        data = copy.deepcopy(self.data)
        private_app = next(app for app in data["apps"] if app["slug"] == "minimax-remote")
        private_app["links"]["github"] = "https://github.com/jaywedgeworth22/MiniMax-ios"
        botfleet = next(app for app in data["apps"] if app["slug"] == "botfleet")
        botfleet["availability"]["iOS"]["url"] = "https://testflight.apple.com/"
        errors = catalog.lint(data)
        self.assertTrue(any("source repository has not been verified public" in error for error in errors), errors)
        self.assertTrue(any("destination does not match its channel" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
