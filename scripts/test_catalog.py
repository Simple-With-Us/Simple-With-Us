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
            token = self.data.get("appStoreProviderToken")
            self.assertEqual(page, catalog.splice(page, "availability", catalog.availability_region(app, token)))
            for fact in app["availability"].values():
                if fact["url"]:
                    destination = catalog.app_store_url(fact["url"], app["slug"], token, "hero") if fact["channel"] == "appStore" else fact["url"]
                    self.assertIn(f'href="{catalog.attr(destination)}"', page)

    def test_private_source_and_generic_invite_are_rejected(self):
        data = copy.deepcopy(self.data)
        private_app = next(app for app in data["apps"] if app["slug"] == "minimax-remote")
        private_app["links"]["github"] = "https://github.com/jaywedgeworth22/MiniMax-ios"
        botfleet = next(app for app in data["apps"] if app["slug"] == "botfleet")
        botfleet["availability"]["iOS"]["url"] = "https://testflight.apple.com/"
        errors = catalog.lint(data)
        self.assertTrue(any("source repository has not been verified public" in error for error in errors), errors)
        self.assertTrue(any("destination does not match its channel" in error for error in errors), errors)

    def test_new_detail_page_template_has_availability_region(self):
        template = (catalog.ROOT / "_template" / "index.html").read_text()
        app = self.data["apps"][0]
        generated = catalog.splice(template, "availability", catalog.availability_region(app))
        self.assertIn('id="availability-title"', generated)
        self.assertIn('<!-- catalog:availability:end -->', generated)
        self.assertEqual(generated, catalog.splice(generated, "availability", catalog.availability_region(app)))

    def test_template_uses_only_generated_availability_actions(self):
        template = (catalog.ROOT / "_template" / "index.html").read_text()
        self.assertEqual(0, template.count('class="btn-row"'))
        self.assertNotIn("{{links.appStore}}", template)
        app = self.data["apps"][0]
        generated = catalog.splice(template, "availability", catalog.availability_region(app))
        self.assertEqual(1, generated.count('class="btn-row"'))

    def test_app_store_attribution_in_card_and_detail(self):
        app = copy.deepcopy(self.data["apps"][0])
        url = "https://apps.apple.com/app/id123456789"
        app["links"]["appStore"] = url
        app["availability"]["iOS"].update(status="live", channel="appStore", url=url)
        for token, query in ((None, "ct="), ("token 123", "pt=token+123&amp;ct=")):
            card = catalog.card(app, token)
            detail = catalog.availability_region(app, token)
            self.assertIn(f'{url}?{query}swu-codecaps-card', card)
            self.assertIn(f'{url}?{query}swu-codecaps-hero', detail)
            self.assertNotIn("{{providerToken}}", card + detail)

    def test_public_copy_omits_internal_verification_notes(self):
        app = self.data["apps"][0]
        region = catalog.availability_region(app)
        self.assertNotIn("not verified", region)
        self.assertNotIn("Checked", region)
        self.assertIn("verification", app["availability"]["iOS"])

    def test_family_count_keeps_both_monitor_editions(self):
        self.assertEqual(11, catalog.app_count(self.data["apps"]))
        editions = [a for a in self.data["apps"] if a.get("catalogGroup") == "usage-monitor"]
        self.assertEqual({"usage-client", "usage-local"}, {a["slug"] for a in editions})
        self.assertEqual(2, len({a["icon"] for a in editions}))
        card = catalog.family_card(editions)
        for app in editions:
            self.assertIn(app["page"], card)
            self.assertIn(app["icon"], card)

    def test_all_public_pages_share_brand_and_product_identity(self):
        for path in catalog.ROOT.rglob("*.html"):
            if ".git" in path.parts or "_template" in path.parts:
                continue
            page = path.read_text()
            self.assertEqual(page, catalog.chrome(page), str(path))
            if 'http-equiv="refresh"' not in page:
                self.assertIn(catalog.HEADER, page)
        for app in self.data["apps"]:
            page = (catalog.ROOT / app["page"].lstrip("/") / "index.html").read_text()
            self.assertIn(catalog.identity_region(app), page)
            self.assertLess(page.index(f'<h1>{app["name"]}</h1>'), page.index('class="lede"'))

    def test_invalid_shelf_support_and_calendar_date_are_rejected(self):
        data = copy.deepcopy(self.data)
        app = data["apps"][0]
        app["shelf"] = "not-a-real-shelf"
        app["support"] = None
        app["availability"]["macOS"]["verifiedOn"] = "2026-99-99"
        errors = catalog.lint(data)
        for message in ["declared catalog shelf", "support destination", "verifiedOn must be a date"]:
            self.assertTrue(any(message in error for error in errors), errors)
        app["availability"]["macOS"]["verifiedOn"] = "2026-09-26"
        self.assertNotIn('>Support</a>', catalog.availability_region(app))


if __name__ == "__main__":
    unittest.main()
