#!/usr/bin/env python3
"""Audit public catalog destinations without changing the release gate.

This is intentionally separate from build_catalog.py.  It is suitable for a
scheduled or manually dispatched GitHub Actions job, and never needs a token or
other credential.  A provider challenge, rate limit, timeout, or transient
server error is reported as unverified; clear 404/410 responses are broken.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import re
from html import unescape
from pathlib import Path
import socket
import sys
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "apps" / "index.json"
DEFAULT_REPORT = ROOT / "catalog-link-audit.md"
USER_AGENT = "Mozilla/5.0 (compatible; SimpleWithUsCatalogAudit/1.0; +https://simplewithus.com/)"
EXTERNAL_SCHEMES = {"http", "https"}
LOCAL_SCHEME = "https"


@dataclass(frozen=True)
class Target:
    url: str
    kind: str
    sources: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Result:
    target: Target
    status: str
    detail: str
    final_url: str = ""
    http_status: int | None = None


class HTMLLinks(HTMLParser):
    """Collect anchors and fragment identifiers from a generated page."""

    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.fragments: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag.lower() == "a" and values.get("href"):
            self.hrefs.append(values["href"] or "")
        if values.get("id"):
            self.fragments.add(values["id"] or "")
        if tag.lower() == "a" and values.get("name"):
            self.fragments.add(values["name"] or "")


def html_files(root: Path = ROOT) -> Iterable[Path]:
    yield from sorted(p for p in root.rglob("*.html") if ".git" not in p.parts and "_template" not in p.parts)


def route_for_page(page: Path, root: Path = ROOT) -> str:
    """Return the public route represented by an HTML file."""
    relative = page.relative_to(root).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("index.html")]
    return "/" + relative




def local_file_for_route(route: str, root: Path = ROOT) -> Path | None:
    """Resolve a site route while keeping it inside the checkout."""
    path = unquote(urlsplit(route).path or "/")
    candidate = (root / path.lstrip("/")).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate if candidate.is_file() else None


def fragment_exists(page: Path, fragment: str) -> bool:
    if not fragment:
        return True
    parser = HTMLLinks()
    try:
        parser.feed(page.read_text())
    except (OSError, UnicodeError):
        return False
    return unquote(fragment) in parser.fragments


def local_result(target: Target, root: Path = ROOT) -> Result:
    split = urlsplit(target.url)
    route = split.path or "/"
    page = local_file_for_route(route, root)
    if page is None:
        return Result(target, "broken", f"missing local path {route}")
    if split.fragment and not fragment_exists(page, split.fragment):
        return Result(target, "broken", f"missing fragment #{split.fragment}")
    return Result(target, "ok", "local path and fragment resolved")


def _add(targets: dict[str, dict[str, object]], url: str, kind: str, source: str) -> None:
    if not url:
        return
    key = url.strip()
    if not key:
        return
    entry = targets.setdefault(key, {"kind": kind, "sources": set()})
    sources = entry["sources"]
    assert isinstance(sources, set)
    sources.add(source)
    if entry["kind"] != "local" and kind == "local":
        entry["kind"] = kind


def collect_targets(data: dict, root: Path = ROOT) -> list[Target]:
    """Collect public manifest destinations and links found in generated HTML."""
    targets: dict[str, dict[str, object]] = {}
    for app in data.get("apps", []):
        slug = app.get("slug", "unknown")
        for key in ("page", "support"):
            value = app.get(key)
            if value:
                _add(targets, value, "local", f"{slug}.{key}")
        for key, value in (app.get("links") or {}).items():
            # brew is a command, not an HTTP destination.
            if value and key != "brew":
                _add(targets, value, "external", f"{slug}.links.{key}")
        for platform, fact in (app.get("availability") or {}).items():
            if fact.get("url"):
                _add(targets, fact["url"], "external", f"{slug}.availability.{platform}")

    for page in html_files(root):
        source = route_for_page(page, root)
        parser = HTMLLinks()
        parser.feed(page.read_text())
        document_url = f"{LOCAL_SCHEME}://simplewithus.com{source}"
        for href in parser.hrefs:
            if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                continue
            absolute = urljoin(document_url, href)
            split = urlsplit(absolute)
            if split.scheme in EXTERNAL_SCHEMES and split.netloc == "simplewithus.com":
                route = split.path or "/"
                local_url = route + (f"?{split.query}" if split.query else "") + (f"#{split.fragment}" if split.fragment else "")
                _add(targets, local_url, "local", f"html:{source}")
            elif split.scheme in EXTERNAL_SCHEMES:
                _add(targets, absolute, "external", f"html:{source}")
    return [Target(url, value["kind"], tuple(sorted(value["sources"]))) for url, value in sorted(targets.items())]


def classify_http_status(status: int) -> str:
    if 200 <= status < 400:
        return "ok"
    if status in {401, 403, 405, 408, 425, 429} or status >= 500:
        return "unverified"
    return "broken"


def validate_final_destination(target_url: str, final_url: str) -> str | None:
    """Return a mismatch explanation when an Apple CTA loses product identity."""
    target = urlsplit(target_url)
    final = urlsplit(final_url)
    if target.hostname == "apps.apple.com":
        product_id = next((part for part in target.path.split("/") if part.startswith("id")), "")
        if final.hostname != "apps.apple.com" or not product_id or product_id not in final.path.split("/"):
            return f"App Store redirect lost product identity ({product_id or 'missing product id'})"
    if target.hostname == "testflight.apple.com":
        invite = target.path.split("/join/", 1)[-1] if "/join/" in target.path else ""
        if final.hostname != "testflight.apple.com" or not invite or final.path.rstrip("/") != f"/join/{invite}":
            return f"TestFlight redirect lost invite identity ({invite or 'missing invite'})"
    return None


def testflight_content_issue(body: str) -> str | None:
    """A 200 response may be a generic or explicitly retired Apple invite."""
    match = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    title = unescape(re.sub(r"\s+", " ", match[1])).strip() if match else ""
    if re.search(r"\b(ignore|retired|obsolete)\b", title, re.I):
        return "TestFlight page identifies a retired app"
    if not re.search(r"\bjoin\b.+\bbeta\b", title, re.I):
        return "TestFlight returned no named beta invitation"
    return None


def external_result(target: Target, timeout: float = 10.0) -> Result:
    request = Request(target.url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9,*/*;q=0.5"})
    try:
        with urlopen(request, timeout=timeout) as response:
            is_testflight = urlsplit(target.url).hostname == "testflight.apple.com"
            body = response.read(262144).decode("utf-8", errors="replace") if is_testflight else ""
            if not is_testflight:
                response.read(1)
            status = int(response.status)
            final_url = response.geturl()
            state = classify_http_status(status)
            mismatch = validate_final_destination(target.url, final_url) if state == "ok" else None
            if mismatch:
                return Result(target, "broken", mismatch, final_url, status)
            if state == "ok" and is_testflight:
                issue = testflight_content_issue(body)
                if issue:
                    return Result(target, "unverified", issue, final_url, status)
            return Result(target, state, f"HTTP {status}", final_url, status)
    except HTTPError as exc:
        status = int(exc.code)
        final_url = exc.geturl() or target.url
        return Result(target, classify_http_status(status), f"HTTP {status} ({'provider access challenge or rate limit' if status in {401, 403, 405, 429} else 'response'})", final_url, status)
    except (TimeoutError, socket.timeout, URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return Result(target, "unverified", f"network check unavailable: {reason}", target.url)


def audit(data: dict, *, offline: bool = False, timeout: float = 10.0, root: Path = ROOT) -> list[Result]:
    results: list[Result] = []
    for target in collect_targets(data, root):
        split = urlsplit(target.url)
        if target.kind == "local" or (split.scheme in EXTERNAL_SCHEMES and split.netloc == "simplewithus.com"):
            local = local_result(target, root)
            if offline:
                results.append(local)
                continue
            route = split.path or target.url
            if split.query:
                route += f"?{split.query}"
            live_target = Target(f"https://simplewithus.com{route}", "external", target.sources)
            live = external_result(live_target, timeout)
            if local.status == "broken":
                results.append(Result(target, "broken", f"{local.detail}; live check: {live.detail}", live.final_url, live.http_status))
            elif live.status == "ok":
                results.append(Result(target, "ok", f"{local.detail}; live {live.detail}", live.final_url, live.http_status))
            else:
                results.append(Result(target, live.status, f"{local.detail}; live check: {live.detail}", live.final_url, live.http_status))
        elif offline:
            results.append(Result(target, "unverified", "network check skipped (--offline)"))
        else:
            results.append(external_result(target, timeout))
    return results


def markdown_report(results: list[Result]) -> str:
    counts = {status: sum(result.status == status for result in results) for status in ("ok", "unverified", "broken")}
    lines = [
        "# Public catalog link audit",
        "",
        "This report checks public manifest destinations and generated HTML links.  `unverified` means access was challenged, rate-limited, timed out, or returned a transient server error; it is not proof that a destination is broken.  A `broken` result is reserved for a clear missing local path/fragment or HTTP 4xx such as 404/410.",
        "",
        f"Summary: {len(results)} unique destinations — {counts['ok']} ok, {counts['unverified']} unverified, {counts['broken']} broken.",
        "",
        "| Status | URL | Detail | Sources | Final destination |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        final = result.final_url or "—"
        sources = ", ".join(result.target.sources)
        lines.append(f"| {result.status} | `{result.target.url}` | {result.detail} | {sources} | `{final}` |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="skip network requests and mark external destinations unverified")
    parser.add_argument("--timeout", type=float, default=10.0, help="per-destination network timeout in seconds (default: 10)")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT, help="Markdown report path (default: catalog-link-audit.md)")
    args = parser.parse_args(argv)
    try:
        data = json.loads(DATA.read_text())
        results = audit(data, offline=args.offline, timeout=args.timeout)
        report = markdown_report(results)
        args.report.write_text(report)
    except (OSError, ValueError, KeyError) as exc:
        print(f"catalog audit could not run: {exc}", file=sys.stderr)
        return 2
    print(report)
    return 1 if any(result.status == "broken" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
