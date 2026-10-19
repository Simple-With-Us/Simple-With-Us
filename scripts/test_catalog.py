"""Regression checks for public release actions and generated detail regions."""
import copy
import json
import re
import unittest
from pathlib import Path

import build_catalog as catalog


def _specificity(selector: str) -> tuple:
    """(ids, classes, types) for the selector forms this stylesheet uses."""
    ids = len(re.findall(r"#[\w-]+", selector))
    classes = len(re.findall(r"\.[\w-]+", selector))
    classes += len(re.findall(r":[a-z-]+", selector))
    classes += len(re.findall(r"\[[^\]]+\]", selector))
    types = len(re.findall(r"(?:^|[\s>+~])[a-zA-Z][\w-]*", selector))
    return (ids, classes, types)


def _luminance(colour: str) -> float:
    def channel(value: int) -> float:
        srgb = value / 255
        return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
    red, green, blue = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)


def _contrast(foreground: str, background: str) -> float:
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _blend(foreground: str, background: str, alpha: float) -> str:
    """foreground at `alpha` over background, as a hex colour."""
    parts = []
    for i in (1, 3, 5):
        top, bottom = int(foreground[i:i + 2], 16), int(background[i:i + 2], 16)
        parts.append(f"{round(top * alpha + bottom * (1 - alpha)):02x}")
    return "#" + "".join(parts)


def _matches_compound(compound: str, element: str) -> bool:
    """True when one compound selector matches a described element."""
    tag, _, classes = element.partition(".")
    classes = classes.split(".") if classes else []
    for simple in re.findall(r":not\([^)]*\)|:[\w-]+|\.[\w-]+|#[\w-]+|[\w-]+", compound):
        if simple.startswith(":"):
            name, _, argument = simple.partition("(")
            if name == ":not" and _matches_compound(argument.rstrip(")"), element):
                return False
            # :hover, :focus and friends: assume they can be true.
            continue
        if simple.startswith("."):
            if simple[1:] not in classes:
                return False
        elif simple.startswith("#"):
            return False
        elif simple.lower() != tag.lower():
            return False
    return True


def _matches(selector: str, chain: list) -> bool:
    """True when `selector` matches the first element of `chain`.

    `chain` lists the element and its ancestors, nearest first, each as
    "tag" or "tag.class".  Descendant combinators only, which is all this
    stylesheet uses.
    """
    compounds = selector.split()
    if not compounds or not _matches_compound(compounds[-1], chain[0]):
        return False
    ancestors = chain[1:]
    for compound in reversed(compounds[:-1]):
        for index, ancestor in enumerate(ancestors):
            if _matches_compound(compound, ancestor):
                ancestors = ancestors[index + 1:]
                break
        else:
            return False
    return True


def _share_card_problems(page: str) -> list:
    """What is wrong with the share card a page declares, if anything.

    A page that declares no og:image is not a problem here: only the apps
    whose own site already publishes a card get one, and that set grows
    when an app publishes a card, not when the catalog invents one.
    """
    problems = []
    image = re.search(r'<meta property="og:image" content="([^"]+)"', page)
    if not image:
        return problems
    url = image.group(1)
    if not url.startswith("https://"):
        problems.append(f"og:image must be an absolute https URL: {url}")
    for name, value in (("og:image:width", "1200"), ("og:image:height", "630")):
        match = re.search(rf'<meta property="{name}" content="([^"]+)"', page)
        if not match:
            problems.append(f"{name} is missing")
        elif match.group(1) != value:
            problems.append(f"{name} is {match.group(1)}, not {value}")
    if not re.search(r'<meta property="og:image:alt" content="[^"]+"', page):
        problems.append("og:image:alt is missing")
    if not re.search(r'<meta name="twitter:card" content="summary_large_image"', page):
        problems.append("twitter:card is not summary_large_image")
    return problems


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

    def test_every_local_asset_a_page_pulls_in_exists(self):
        """A referenced file that is not in the repo is a broken image.

        The header markup has always named the dark wordmark, and the markup
        test above has always passed, but the 1x file was never in the repo:
        dark mode showed a broken-image icon and the alt text on every page.
        Asserting the markup cannot catch that, so assert the files.
        """
        missing = []
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts:
                continue
            for ref in catalog.missing_local_assets(path.read_text()):
                missing.append(f"{path.relative_to(catalog.ROOT)}: {ref}")
        self.assertEqual([], missing, "these pages reference files that are not in the repo")

    def test_the_asset_check_reports_a_file_that_is_not_there(self):
        """The check above is only worth having if it can still fail.

        A detector that finds nothing is indistinguishable from a detector
        that is not looking, so give it a page with a file that cannot exist
        and require the name back.
        """
        page = '<picture><source srcset="/assets/logos/not-a-real-file.webp" type="image/webp">'
        page += '<img src="/assets/logos/also-not-real.webp" alt=""></picture>'
        missing = catalog.missing_local_assets(page)
        self.assertIn("/assets/logos/not-a-real-file.webp", missing)
        self.assertIn("/assets/logos/also-not-real.webp", missing)
        # A file that does exist must not be reported.
        self.assertEqual([], catalog.missing_local_assets('<img src="/assets/site.css" alt="">'))
        # A srcset carries a width descriptor; the descriptor is not the path.
        self.assertEqual(
            [],
            catalog.missing_local_assets('<img srcset="/assets/site.css 480w" alt="">'),
        )
        # External and data URLs are not repo files, so they are not this check's business.
        self.assertEqual(
            [],
            catalog.missing_local_assets('<img src="https://example.com/logo.png" alt="">'),
        )

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

    def test_badge_label_is_readable_on_every_plate(self):
        """The badge is a plate with its own colour, so the label has to wear it.

        `.availability-list span` paints the row's right-hand cell muted grey
        (#525c67).  The badge label lives inside that cell, so without an
        explicit opt-in it renders muted grey on the near-black plate (2.9:1)
        and the download glyph, which strokes with currentColor, all but
        disappears into it.  The opt-in has to cover the tile as well as both
        label lines, and every plate/label pair the stylesheet defines has to
        clear AA on its own.
        """
        css = re.sub(r"/\*.*?\*/", "", (catalog.ROOT / "assets/site.css").read_text(), flags=re.S)

        opt_in = re.search(
            r"(\.badge [^,{]+(?:,\s*\.badge [^,{]+)*)\s*\{([^}]*)\}", css)
        self.assertIsNotNone(opt_in, "the badge parts must opt back in to the plate colour")
        self.assertIn("color: inherit", opt_in.group(2))
        covered = set(re.findall(r"\.badge \.([\w-]+)", opt_in.group(1)))
        self.assertEqual({"badge-lines", "badge-tile", "badge-l1", "badge-l2"}, covered)
        # The opt-in has to outrank the muted rule it is undoing.
        self.assertGreater(_specificity(".badge .badge-l1"), _specificity(".availability-list span"))

        # Every plate the stylesheet defines has to carry a label that reads on it.
        plates = 0
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            selector = " ".join(selector.split())
            if not selector.split(",")[-1].strip().endswith(".badge"):
                continue
            plate = re.search(r"background:\s*(#[0-9a-fA-F]{6})\b", body)
            label = re.search(r"(?<![-a-z])color:\s*(#[0-9a-fA-F]{6})\b", body)
            if not (plate and label):
                continue
            plates += 1
            with self.subTest(selector=selector):
                self.assertGreaterEqual(_contrast(label.group(1), plate.group(1)), 4.5)
                # The small line sits at 66% opacity over the plate, so it is the
                # one that can fall through even when the big line passes.
                small = _blend(label.group(1), plate.group(1), 0.66)
                self.assertGreaterEqual(_contrast(small, plate.group(1)), 4.5)
        self.assertGreaterEqual(plates, 2, "expected a light and a dark badge plate")

    def test_badge_never_gets_the_row_hover_underline(self):
        """The row's hover underline is for text links.

        On the badge it paints a white rule straight through the label, and
        because the plate is dark the rule reads louder than the label itself.
        """
        css = re.sub(r"/\*.*?\*/", "", (catalog.ROOT / "assets/site.css").read_text(), flags=re.S)
        # The badge as it sits in an availability row.
        chain = ["a.badge", "span", "li", "ul.availability-list", "section.availability", "main", "body", "html"]
        underlines = 0
        for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            if not re.search(r"text-decoration(?:-line)?:\s*[^;}]*underline", body):
                continue
            for part in " ".join(selector.split()).split(","):
                part = part.strip()
                if not part:
                    continue
                underlines += 1
                if _matches(part, chain):
                    self.assertIn(":not(.badge)", part, f"underline rule would strike the badge: {part}")
        self.assertGreater(underlines, 0, "the availability row still underlines its text links")
        # The row's own text links keep the underline; the badge does not.
        self.assertRegex(css, r"\.availability-list a:not\(\.badge\):hover\s*\{[^}]*underline")

    def test_every_badge_carries_the_parts_the_plate_colour_covers(self):
        """The CSS opt-in only helps if the markup still has those parts."""
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts:
                continue
            page = path.read_text()
            for anchor in re.findall(r'<a class="badge"[^>]*>.*?</a>', page, flags=re.S):
                with self.subTest(page=str(path.relative_to(catalog.ROOT))):
                    self.assertIn('class="badge-tile"', anchor)
                    self.assertIn('class="badge-l1"', anchor)
                    self.assertIn('class="badge-l2"', anchor)

    def test_every_span_inside_a_badge_takes_the_plate_colour(self):
        """The colour is inherited down the chain, so every part has to be listed.

        A new span inside the badge that is missing from the opt-in rule
        silently takes the availability row's muted grey again, and nothing
        in the page then says so.
        """
        css = re.sub(r"/\*.*?\*/", "", (catalog.ROOT / "assets/site.css").read_text(), flags=re.S)
        opt_in = re.search(r"(\.badge [^,{]+(?:,\s*\.badge [^,{]+)*)\s*\{[^}]*color:\s*inherit", css)
        self.assertIsNotNone(opt_in, "the badge parts must opt back in to the plate colour")
        covered = set(re.findall(r"\.badge \.([\w-]+)", opt_in.group(1)))
        seen = set()
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts:
                continue
            page = path.read_text()
            for anchor in re.findall(r'<a class="badge"[^>]*>.*?</a>', page, flags=re.S):
                for part in re.findall(r'<span class="([^"]+)"', anchor):
                    seen.add(part)
        self.assertTrue(seen, "no badge markup found to check")
        self.assertEqual(set(), seen - covered, "these badge parts are not covered by the plate-colour rule")

    def test_every_declared_share_card_is_complete(self):
        """A share card that is missing its size or its alt text is a bad card.

        The platform reads og:image, then og:image:width and og:image:height
        to lay the preview out, and og:image:alt for the text under it.  A
        page that names a card and forgets the rest still renders, so the
        omission is silent.
        """
        declared = 0
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts:
                continue
            page = path.read_text()
            with self.subTest(page=str(path.relative_to(catalog.ROOT))):
                self.assertEqual([], _share_card_problems(page))
            if 'property="og:image"' in page:
                declared += 1
        self.assertGreater(declared, 0, "no page declares a share card")

    def test_an_app_with_a_card_keeps_it_on_its_page(self):
        """The card an app publishes on its own site belongs on its page.

        Which apps have a card is data, in apps/index.json, so the set is
        reviewable and a card cannot quietly disappear from a page.
        """
        data = json.loads(catalog.DATA.read_text())
        with_card = [a for a in data["apps"] if a.get("ogImage")]
        self.assertTrue(with_card, "no app claims a share card")
        for app in with_card:
            page = catalog.ROOT / app["page"].lstrip("/") / "index.html"
            with self.subTest(app=app["slug"]):
                self.assertTrue(page.is_file(), f"{app['slug']}: detail page is missing")
                html = page.read_text()
                self.assertIn(f'<meta property="og:image" content="{app["ogImage"]}"', html)
                self.assertEqual([], _share_card_problems(html))

    def test_no_page_keeps_a_card_the_data_does_not_claim(self):
        """A card left on a page that no longer has one is stale."""
        data = json.loads(catalog.DATA.read_text())
        for app in data["apps"]:
            if app.get("ogImage"):
                continue
            page = catalog.ROOT / app["page"].lstrip("/") / "index.html"
            if not page.is_file():
                continue
            with self.subTest(app=app["slug"]):
                self.assertIsNone(
                    re.search(r'<meta property="og:image" content="([^"]+)"', page.read_text()),
                    "this page declares a card that apps/index.json does not claim",
                )

    def test_the_share_card_check_catches_a_broken_card(self):
        """The check above is only worth having if it can still fail."""
        good = (
            '<meta property="og:image" content="https://example.com/card.png" />'
            '<meta property="og:image:width" content="1200" />'
            '<meta property="og:image:height" content="630" />'
            '<meta name="twitter:card" content="summary_large_image" />'
            '<meta property="og:image:alt" content="Example" />'
        )
        self.assertEqual([], _share_card_problems(good))
        # A card with no size and no alt text is exactly the silent failure.
        self.assertIn(
            "og:image:width is missing",
            _share_card_problems('<meta property="og:image" content="https://example.com/card.png" />'),
        )
        self.assertIn(
            "og:image:alt is missing",
            _share_card_problems('<meta property="og:image" content="https://example.com/card.png" />'),
        )
        # A square card is not a share card, and the declared size has to say 1200 by 630.
        square = good.replace('content="1200"', 'content="512"').replace('content="630"', 'content="512"')
        self.assertIn("og:image:width is 512, not 1200", _share_card_problems(square))
        # A relative path cannot be fetched by a platform crawler.
        self.assertIn(
            "og:image must be an absolute https URL: /card.png",
            _share_card_problems(good.replace("https://example.com/card.png", "/card.png")),
        )
        # A page with no card at all is not a failure: only some apps have one.
        self.assertEqual([], _share_card_problems('<meta property="og:title" content="Example" />'))

    def test_an_app_that_carries_its_support_offers_no_contact_link(self):
        """An app whose page carries the support details needs no Contact button.

        The button sent the reader to a page with the same words, one click
        away from where they already were.  The standalone support page stays
        published, because App Store Connect records point at its URL.
        """
        inline = [a for a in self.data["apps"] if a.get("supportInline")]
        self.assertTrue(inline, "no app claims an inline support section")
        for app in inline:
            with self.subTest(app=app["slug"]):
                region = catalog.availability_region(app)
                self.assertNotIn(">Contact</a>", region)
                self.assertNotIn("btn-row", region)
                self.assertTrue(app.get("support"), "the standalone support page must stay")
                self.assertTrue((catalog.ROOT / app["support"].lstrip("/")).is_file())
                page = (catalog.ROOT / app["page"].lstrip("/") / "index.html").read_text()
                self.assertIn("<!-- catalog:support:start -->", page)
                self.assertIn("<h2>Support</h2>", page)
                # The words have to be on the page, not only a heading over them.
                self.assertIn("contact@simplewithus.com", page)

    def test_an_app_without_inline_support_still_offers_the_contact_link(self):
        """The rule above must not take the button away from every other app."""
        for app in self.data["apps"]:
            if app.get("supportInline"):
                continue
            with self.subTest(app=app["slug"]):
                self.assertIn(">Contact</a>", catalog.availability_region(app))

    def test_the_inline_support_section_and_the_contact_link_have_to_agree(self):
        """A page with inline support but no flag still shows a link out of itself.

        Either way the reader is stranded: a link back to the page they are
        on, or a page with no way to ask for help at all.
        """
        data = copy.deepcopy(self.data)
        app = next(a for a in data["apps"] if a.get("supportInline"))
        app.pop("supportInline")
        self.assertTrue(any("supportInline is not set" in e for e in catalog.lint(data)))
        # The other way round: the flag promises a section the page does not carry.
        data = copy.deepcopy(self.data)
        app = next(a for a in data["apps"] if a.get("supportInline"))
        app["page"] = "/codecaps/"
        self.assertTrue(any("no inline support section" in e for e in catalog.lint(data)))

    def test_the_two_monitor_editions_carry_their_new_names(self):
        """The editions are Usage Monitor Client and Usage Monitor Local.

        The old names would otherwise survive in a title, an alt text, or the
        privacy notice, where no generator goes looking for them.
        """
        names = {a["slug"]: a["name"] for a in self.data["apps"]}
        self.assertEqual("Usage Monitor Client", names["usage-client"])
        self.assertEqual("Usage Monitor Local", names["usage-local"])
        stale = re.compile(r"Usage (Client|Local) Monitor")
        for path in sorted(catalog.ROOT.rglob("*.html")):
            if ".git" in path.parts or "_template" in path.parts:
                continue
            with self.subTest(page=str(path.relative_to(catalog.ROOT))):
                self.assertIsNone(stale.search(path.read_text()), "this page still carries the old name")


if __name__ == "__main__":
    unittest.main()
