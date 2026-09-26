#!/usr/bin/env python3
"""Render the simplewithus.com catalog from apps/index.json.

Usage:
  python3 scripts/build_catalog.py          # rewrite the generated regions of index.html
  python3 scripts/build_catalog.py --check  # exit 1 if index.html is stale or a rule fails

Standard library only.  The generated regions sit between
<!-- catalog:<name>:start --> and <!-- catalog:<name>:end --> markers.
Everything outside the markers is hand-written and left alone.

Rules enforced (see docs/DESIGN-BRIEF.md sections 5 and 9):
  * a link is either null or a real URL of the right shape (no bare testflight.apple.com)
  * every page, support page, and icon named in the data exists in the repo
  * no committed image is over 200 KB, except the legacy files listed below
  * the AASA file is valid JSON and lists every app that sets associatedDomains
  * index.html and each product availability region match the public manifest
  * generated links do not point to private repositories or generic store pages
"""
import html
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "apps" / "index.json"
PAGE = ROOT / "index.html"
AASA = ROOT / ".well-known" / "apple-app-site-association"
IMAGE_BUDGET = 200 * 1024
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}
# Oversize files that predate the budget.  Delete or re-encode them, then drop them from this list.
LEGACY_OVERSIZE = {
    "assets/app-icons/ar.png",
    "assets/app-icons/bf.png",
    "assets/app-icons/ct.png",
    "assets/app-icons/dd.png",
    "assets/app-icons/st.png",
    "assets/app-icons/um.png",
    "assets/logos/swu-logo-wide.svg",
    "assets/logos/swu-logo-wide.webp",
}
NBSP_GAP = "  "  # FLEET-UI-COPY: U+00A0 plus a space between sentences in HTML

LINK_RULES = {
    "website": re.compile(r"^https://[a-z0-9.-]+\.[a-z]{2,}(/.*)?$"),
    "github": re.compile(r"^https://github\.com/jaywedgeworth22/[A-Za-z0-9._-]+$"),
    "appStore": re.compile(r"^https://apps\.apple\.com/app/id\d+$"),
    "testFlight": re.compile(r"^https://testflight\.apple\.com/join/[A-Za-z0-9]+$"),
    "brew": re.compile(r"^brew install (--cask )?[a-z0-9/_-]+$"),
}
LINK_RULES["source"] = LINK_RULES["github"]
LINK_RULES["download"] = re.compile(r"^https://github\.com/jaywedgeworth22/[A-Za-z0-9._-]+/releases/latest/download/[A-Za-z0-9._-]+\.dmg$")
PUBLIC_SOURCE_REPOS = {
    "CodeCaps", "Usage-Monitor", "Harness", "HogHunter", "BotFleet",
    "Socratic-Trade", "Congress.Trade", "ContactLogo", "DealDex", "Autorotate",
}
PRIVATE_DESTINATIONS = ("github.com/jaywedgeworth22/Fleet-OPS", "github.com/jaywedgeworth22/MiniMax-ios")
AVAILABILITY_STATUSES = {"live", "beta", "source", "unverified"}
CHANNELS = {"website", "source", "appStore", "testFlight", "download"}


def gap(text: str) -> str:
    """Escape, then turn a two-ASCII-space sentence gap into U+00A0 plus a space."""
    out = html.escape(text, quote=True)
    for mark in ".?!":
        out = out.replace(mark + "  ", mark + NBSP_GAP)
    return out


def attr(text: str) -> str:
    return html.escape(text, quote=True)


def app_store_url(url: str, slug: str, provider_token) -> str:
    if provider_token:
        return f"{url}?pt={provider_token}&ct=swu-{slug}-card"
    return f"{url}?ct=swu-{slug}-card"


def primary_link(app: dict):
    """Return the app's primary link, or None if it has none.

    Never raises: lint() is what enforces that every app has a primary
    link, so this just reports the fact instead of assuming it holds.
    """
    links = app.get("links") or {}
    return app.get("page") or links.get("website") or links.get("github")


def card(app: dict, provider_token) -> str:
    primary = primary_link(app)
    actions = [v for v in app["availability"].values() if v["url"]]
    chosen = next((v for v in actions if v["status"] == "live"), None)
    chosen = chosen or next((v for v in actions if v["status"] == "beta"), None)
    chosen = chosen or next((v for v in actions if v["status"] == "source"), None)
    chosen = chosen or ({"url": app["links"]["github"], "channel": "source"} if app["links"].get("github") else None)
    if chosen and chosen["url"] == primary:
        chosen = None

    out = [f'<li class="card" style="--card-accent: {attr(app["accent"])}">']
    out.append('  <div class="card-head">')
    out.append(f'    <img class="card-icon" src="{attr(app["icon"])}" alt="" width="48" height="48" loading="lazy" decoding="async">')
    out.append("    <div>")
    if primary:
        rel = "" if primary.startswith("/") else ' rel="noopener"'
        out.append(f'      <h4><a href="{attr(primary)}"{rel}>{gap(app["name"])}</a></h4>')
    else:
        out.append(f'      <h4>{gap(app["name"])}</h4>')
    pills = "".join(f'<li class="pill">{gap(p)}</li>' for p in app["platforms"])
    out.append(f'      <ul class="pills" aria-label="Platforms">{pills}</ul>')
    out.append("    </div>")
    out.append("  </div>")
    out.append(f'  <p>{gap(app["tagline"])}</p>')
    out.append(f'  <span class="status status-{attr(app["status"])}">{gap(app["statusText"])}</span>')
    if chosen or app.get("support"):
        out.append('  <div class="card-links">')
        if chosen:
            label = {"website": "Open web app", "source": "View public source", "download": "Download Mac beta", "testFlight": "Open TestFlight beta", "appStore": "Open App Store listing"}[chosen["channel"]]
            out.append(f'    <a href="{attr(chosen["url"])}" rel="noopener">{label}<span aria-hidden="true"> ↗</span></a>')
        if app.get("support"):
            out.append(f'    <a href="{attr(app["support"])}">Support</a>')
        out.append("  </div>")
    out.append("</li>")
    return "\n".join(out)


def render(data: dict) -> dict:
    apps = data["apps"]
    token = data.get("appStoreProviderToken")
    grid = []
    for shelf, title in data["shelves"].items():
        subset = [a for a in apps if a["shelf"] == shelf]
        grid += [f'<section class="catalog-group" aria-labelledby="shelf-{attr(shelf)}">',
                 f'  <h3 id="shelf-{attr(shelf)}">{gap(title)}</h3>',
                 '  <ul class="grid" role="list">']
        grid += [card(a, token) for a in subset]
        grid += ['  </ul>', '</section>']
    public_src = sum(1 for a in apps if a["links"].get("github"))
    facts = f'<p class="facts">{len(apps)} apps · {public_src} with public source · platform availability shown per app</p>'
    return {"facts": facts, "grid": "\n".join(grid)}


def availability_region(app: dict) -> str:
    rows = ['<section class="availability" aria-labelledby="availability-title">',
            '  <h2 id="availability-title">Availability</h2>',
            '  <ul class="availability-list">']
    for platform, fact in app["availability"].items():
        rows.append(f'    <li><strong>{gap(platform)}</strong><span>{gap(fact["label"])}</span></li>')
    rows += ['  </ul>', '  <div class="btn-row">']
    for platform, fact in app["availability"].items():
        if not fact["url"]:
            continue
        label = {"website": "Open web app", "source": "View public source", "appStore": "Open App Store listing", "testFlight": "Open TestFlight beta", "download": "Download Mac beta"}[fact["channel"]]
        klass = "btn btn-primary" if fact["status"] == "live" else "btn btn-secondary"
        rows.append(f'    <a class="{klass}" href="{attr(fact["url"])}" rel="noopener">{label}</a>')
    rows.append(f'    <a class="btn btn-secondary" href="{attr(app["support"])}">Support</a>')
    rows += ['  </div>', f'  <p class="availability-note">Checked 26 Sep 2026.{NBSP_GAP}Beta enrollment and native installation were not verified.</p>', '</section>']
    return "\n".join(rows)


def splice(page: str, name: str, body: str, filename="index.html") -> str:
    pat = re.compile(rf"(<!-- catalog:{name}:start -->)(.*?)(\s*<!-- catalog:{name}:end -->)", re.S)
    if not pat.search(page):
        raise SystemExit(f"{filename} is missing the catalog:{name} markers")
    return pat.sub(lambda m: m.group(1) + "\n" + body + m.group(3), page, count=1)


def exists(path: str) -> bool:
    p = ROOT / path.lstrip("/")
    return p.is_file() or (p / "index.html").is_file()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs += [value for key, value in attrs if key == "href" and value]


def lint(data: dict) -> list:
    errors = []
    seen = set()
    if data.get("schema") != 2:
        errors.append("apps/index.json: expected schema 2")
    for app in data["apps"]:
        slug = app["slug"]
        if slug in seen:
            errors.append(f"{slug}: duplicate slug")
        seen.add(slug)
        for key, rule in LINK_RULES.items():
            val = app["links"].get(key)
            if val is not None and not rule.fullmatch(val):
                errors.append(f"{slug}: links.{key} does not match {rule.pattern}")
        github = app["links"].get("github")
        if github and github.rsplit("/", 1)[-1] not in PUBLIC_SOURCE_REPOS:
            errors.append(f"{slug}: source repository has not been verified public")
        availability = app.get("availability", {})
        if set(availability) != set(app["platforms"]):
            errors.append(f"{slug}: availability must cover exactly the listed platforms")
        for platform, fact in availability.items():
            state, channel, url = fact.get("status"), fact.get("channel"), fact.get("url")
            if state not in AVAILABILITY_STATUSES:
                errors.append(f"{slug}/{platform}: invalid availability status")
            if channel not in CHANNELS | {None} or bool(channel) != bool(url):
                errors.append(f"{slug}/{platform}: channel and URL must appear together")
            if state == "unverified" and url:
                errors.append(f"{slug}/{platform}: unverified availability must have no public URL")
            if state == "beta" and url and channel not in {"download", "testFlight"}:
                errors.append(f"{slug}/{platform}: beta URL must be a product download or invite")
            if state in {"live", "source"} and not url:
                errors.append(f"{slug}/{platform}: available platform needs a destination")
            if channel and url and (not LINK_RULES[channel].fullmatch(url)):
                errors.append(f"{slug}/{platform}: destination does not match its channel")
            if channel == "source" and url != github:
                errors.append(f"{slug}/{platform}: source destination differs from verified public repository")
            if channel == "website" and url != app["links"].get("website"):
                errors.append(f"{slug}/{platform}: web destination differs from website link")
            if not re.fullmatch(r"\d{4}-\d\d-\d\d", fact.get("verifiedOn", "")):
                errors.append(f"{slug}/{platform}: verifiedOn must be a date")
            if not fact.get("verification") or not fact.get("label"):
                errors.append(f"{slug}/{platform}: label and verification are required")
        for key in ("page", "support", "icon"):
            val = app.get(key)
            if val and not exists(val):
                errors.append(f"{slug}: {key} {val} does not exist in the repo")
        if not (app.get("page") or app["links"].get("website") or app["links"].get("github")):
            errors.append(f"{slug}: needs at least one of page, links.website, links.github")
        if app.get("page"):
            page = ROOT / app["page"].lstrip("/") / "index.html"
            if "<!-- catalog:availability:start -->" not in page.read_text():
                errors.append(f"{slug}: detail page lacks generated availability region")
    for page in (p for p in ROOT.rglob("*.html") if "_template" not in p.parts and ".git" not in p.parts):
        parsed = Links()
        parsed.feed(page.read_text())
        for href in parsed.hrefs:
            if any(private in href for private in PRIVATE_DESTINATIONS):
                errors.append(f"{page.relative_to(ROOT)}: private repository destination")
            if href.rstrip("/") in {"https://testflight.apple.com", "https://apps.apple.com", "https://apps.apple.com/app"}:
                errors.append(f"{page.relative_to(ROOT)}: generic store destination")
            if href.startswith("/") and not href.startswith("//") and not exists(href.split("#")[0].split("?")[0]):
                errors.append(f"{page.relative_to(ROOT)}: missing local destination {href}")
    for img in ROOT.rglob("*"):
        rel = img.relative_to(ROOT).as_posix()
        if rel.startswith(".git/") or img.suffix.lower() not in IMAGE_EXTS or not img.is_file():
            continue
        if img.stat().st_size > IMAGE_BUDGET and rel not in LEGACY_OVERSIZE:
            errors.append(f"{rel} is {img.stat().st_size} bytes, over the 200 KB image budget")
    try:
        aasa = json.loads(AASA.read_text())
        listed = {i for d in aasa["applinks"]["details"] for i in d["appIDs"]}
        for app in data["apps"]:
            if app.get("associatedDomains"):
                for bid in app["bundleIds"]:
                    if f'{data["teamId"]}.{bid}' not in listed:
                        errors.append(f"{app['slug']}: {bid} declares associated domains but is not in the AASA file")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"AASA file invalid: {exc}")
    return errors


def main() -> int:
    check = "--check" in sys.argv
    data = json.loads(DATA.read_text())
    errors = lint(data)
    if errors:
        # Never call render() on data lint has already rejected: card() assumes
        # each app has a primary link, and lint() is what guarantees that.
        for e in errors:
            print("error:", e, file=sys.stderr)
        return 1
    page = PAGE.read_text()
    new = page
    for name, body in render(data).items():
        new = splice(new, name, body)
    changed = []
    if new != page:
        if check:
            errors.append("index.html is stale: run python3 scripts/build_catalog.py and commit the result")
        else:
            PAGE.write_text(new)
            changed.append("index.html")
    for app in data["apps"]:
        if not app.get("page"):
            continue
        detail = ROOT / app["page"].lstrip("/") / "index.html"
        original = detail.read_text()
        rendered = splice(original, "availability", availability_region(app), detail.relative_to(ROOT))
        if rendered != original:
            if check:
                errors.append(f"{detail.relative_to(ROOT)} is stale: run python3 scripts/build_catalog.py")
            else:
                detail.write_text(rendered)
                changed.append(str(detail.relative_to(ROOT)))
    if changed:
        print("regenerated:", ", ".join(changed))
    for e in errors:
        print("error:", e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
