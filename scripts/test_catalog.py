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

    def test_header_uses_full_owner_lockup(self):
        self.assertIn('/assets/logos/swu-wordmark-light.webp', catalog.HEADER)
        # The dark wordmark has to ship in the same <picture>, or the grey WITH vanishes on a dark page.
        self.assertIn('<source media="(prefers-color-scheme: dark)" srcset="/assets/logos/swu-wordmark-dark.webp" type="image/webp">', catalog.HEADER)
        self.assertIn('alt="Simple With Us - Jay Wedgeworth"', catalog.HEADER)
        # aria-label overrides the image alt in the accessible name, so it has to carry the signature too.
        self.assertIn('class="wordmark" href="/" aria-label="Simple With Us - Jay Wedgeworth home"', catalog.HEADER)
        self.assertNotIn('swu-wordmark.webp', catalog.HEADER)

    def test_every_page_ships_the_light_and_dark_favicon_pair(self):
        """The favicon is the one asset that breaks where nobody looks at it.

        The plate has to follow prefers-color-scheme, or the icon floats on
        a black square in a light tab.  This walks every published page plus
        _template/, so a new app page cannot ship a single-variant icon.
        """
        pair = [
            '<link rel="icon" href="/assets/logos/swu-favicon-32-light.webp" type="image/webp" media="(prefers-color-scheme: light)">',
            '<link rel="icon" href="/assets/logos/swu-favicon-32-dark.webp" type="image/webp" media="(prefers-color-scheme: dark)">',
            '<link rel="apple-touch-icon" media="(prefers-color-scheme: light)" href="/assets/logos/swu-favicon-180-light.webp">',
            '<link rel="apple-touch-icon" media="(prefers-color-scheme: dark)" href="/assets/logos/swu-favicon-180-dark.webp">',
        ]
        retired = ["swu-square-32.webp", "swu-square-32-light.webp", "swu-square-192-light.webp"]
        checked = 0
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts:
                continue
            page = path.read_text()
            with self.subTest(page=str(path.relative_to(catalog.ROOT))):
                for tag in pair:
                    self.assertIn(tag, page)
                for name in retired:
                    self.assertNotIn(name, page)
            checked += 1
        self.assertGreaterEqual(checked, 39)

    def test_title_and_icon_share_a_centered_row(self):
        for app in self.data["apps"]:
            identity = catalog.identity_region(app)
            self.assertNotIn('class="back-link"', identity)
            self.assertIn(f'    <h1>{app["name"]}</h1>', identity)
            self.assertNotIn('<div><a', identity)
        css = (catalog.ROOT / "assets/site.css").read_text()
        self.assertIn('.app-identity h1 { margin: 0;', css)
        # fleetlink/privacy.html keeps a back link above its h1, so that pair needs its own gap.
        self.assertIn('.back-link + h1 { margin-top: 8px; }', css)

    def test_autorotate_is_last_closed_archive_without_testflight(self):
        rendered = catalog.render(self.data)
        self.assertNotIn('/autorotate/', rendered["grid"])
        archive = rendered["archived"]
        self.assertIn('<summary>Archived</summary>', archive)
        self.assertIn('<details class="archived-apps">', archive)
        self.assertNotIn(' open', archive)
        self.assertIn('/autorotate/', archive)
        self.assertNotIn('testflight.apple.com', archive)
        app = next(a for a in self.data["apps"] if a["slug"] == "autorotate")
        self.assertTrue(app["archived"])
        self.assertFalse(app["links"].get("testFlight"))
        self.assertNotIn('testflight.apple.com', catalog.availability_region(app))
        home = catalog.PAGE.read_text()
        self.assertLess(home.index('id="status"'), home.index('id="archived"'))
        self.assertLess(home.index('id="archived"'), home.index('</main>'))

    def test_catalog_count_matches_rendered_active_cards(self):
        rendered = catalog.render(self.data)
        archived = [a for a in self.data["apps"] if a.get("archived")]
        self.assertTrue(archived)
        visible = [a for a in self.data["apps"] if not a.get("archived")]
        self.assertEqual(f'<p class="facts">{catalog.app_count(visible)} apps</p>', rendered["facts"])
        self.assertEqual(catalog.app_count(visible), rendered["grid"].count('<li class="card'))

    def test_splice_with_empty_body_is_idempotent(self):
        page = '<main>\n  <!-- catalog:archived:start -->\nold\n  <!-- catalog:archived:end -->\n</main>'
        once = catalog.splice(page, "archived", "")
        self.assertEqual(once, catalog.splice(once, "archived", ""))
        self.assertEqual('<main>\n  <!-- catalog:archived:start -->\n  <!-- catalog:archived:end -->\n</main>', once)
        filled = catalog.splice(once, "archived", "body")
        self.assertEqual(filled, catalog.splice(filled, "archived", "body"))

    def test_private_source_and_generic_invite_are_rejected(self):
        data = copy.deepcopy(self.data)
        private_app = next(app for app in data["apps"] if app["slug"] == "dealdex")
        private_app["links"]["github"] = "https://github.com/Simple-With-Us/Personal-Site"
        botfleet = next(app for app in data["apps"] if app["slug"] == "botfleet")
        botfleet["availability"]["iOS"]["url"] = "https://testflight.apple.com/"
        errors = catalog.lint(data)
        self.assertTrue(any("source repository has not been verified public" in error for error in errors), errors)
        self.assertTrue(any("destination does not match its channel" in error for error in errors), errors)

    def test_companion_does_not_inherit_desktop_domain_association(self):
        data = copy.deepcopy(self.data)
        app = next(a for a in data["apps"] if a["slug"] == "hoghunter")
        self.assertIn("com.simplewithus.hoghunter.ios", app["bundleIds"])
        self.assertEqual([], catalog.lint(data))
        app["associatedDomainBundleIds"].append("com.simplewithus.hoghunter.ios")
        self.assertTrue(any("hoghunter.ios declares associated domains" in e for e in catalog.lint(data)))
        app["associatedDomainBundleIds"] = ["not.a.declared.bundle"]
        self.assertTrue(any("associatedDomainBundleIds must match" in e for e in catalog.lint(data)))

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

    def test_every_page_exposes_exactly_one_main_landmark(self):
        """axe landmark-one-main: a skip link to id=main is not a main landmark.

        Per-app pages shipped <article class="article" id="main">, so the skip
        link worked but screen reader users had no main landmark (Lighthouse
        accessibility 98).  This walks every published HTML file, not just the
        cataloged ones, so a new app page cannot regress the same way.
        """
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if "_template" in path.parts:
                continue
            page = path.read_text()
            with self.subTest(page=str(path.relative_to(catalog.ROOT))):
                self.assertEqual(1, page.count("<main"), "expected exactly one <main> element")
                self.assertNotIn('<article class="article" id="main">', page)
                if 'class="skip-link"' in page:
                    self.assertIn('id="main"', page, "skip link has no target")

    def test_shared_asset_urls_change_with_content(self):
        rendered = catalog.chrome('<link href="/assets/site.css"><script src="/assets/status.mjs"></script>')
        self.assertRegex(rendered, r'site\.css\?v=[a-f0-9]{12}')
        self.assertRegex(rendered, r'status\.mjs\?v=[a-f0-9]{12}')
        self.assertEqual(rendered, catalog.chrome(rendered))

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
        # With support restored the button comes back, and it is labelled Contact, not Support:
        # the nav and footer still say Support, so the detail button needed its own word.
        app["support"] = "/support.html"
        region = catalog.availability_region(app)
        self.assertIn('>Contact</a>', region)
        self.assertNotIn('>Support</a>', region)


if __name__ == "__main__":
    unittest.main()
