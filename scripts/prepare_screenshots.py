#!/usr/bin/env python3
"""Prepare and optimize real screenshots across all catalog apps.

Resizes to max 1280px width, converts to WebP (quality 85),
and verifies each image meets the < 150 KB budget from DESIGN-BRIEF.md.
"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "assets" / "screenshots"
MAX_WIDTH = 1280
BUDGET_BYTES = 150 * 1024

SOURCES = {
    "codecaps": [
        ("/Users/jay/Code/CodeCaps/docs/screenshots/glance-light.png", "glance-light.webp", "CodeCaps Glance showing AI plan quotas, reset windows, and pacing markers", "CodeCaps Glance menu bar popover with dual-window monitoring and pacing indicators."),
        ("/Users/jay/Code/CodeCaps/docs/screenshots/glance-fleet.png", "glance-fleet.webp", "CodeCaps Fleet view showing quotas across configured Macs", "Optional fleet view combining readings from multiple Mac machines."),
    ],
    "usage-client": [
        ("/Users/jay/Code/Usage-Monitor/docs/asc/screenshots/client/iphone/dashboard.png", "dashboard.webp", "Usage Client dashboard with real-time model quota tracking", "Real-time AI model quota and usage monitoring on iPhone."),
        ("/Users/jay/Code/Usage-Monitor/docs/asc/screenshots/client/iphone/alerts.png", "alerts.webp", "Usage Client quota alerts and thresholds", "Configurable usage alerts and rate-limit threshold warnings."),
    ],
    "usage-local": [
        ("/Users/jay/Code/Usage-Monitor/docs/asc/screenshots/local/iphone/overview.png", "overview.webp", "Usage Local Monitor overview with on-device subscription costs", "On-device subscription cost tracking and quota monitoring."),
        ("/Users/jay/Code/Usage-Monitor/docs/asc/screenshots/local/iphone/providers.png", "providers.webp", "Usage Local Monitor provider breakdown", "Detailed usage breakdown across supported AI providers."),
    ],
    "clutch": [
        ("/Users/jay/Code/Clutch/e2e/web-visual.spec.ts-snapshots/web-home-chromium-linux.png", "dashboard.webp", "Clutch local agent dashboard and active tasks", "Local coding agent interface with DeepSeek and MiniMax support."),
        ("/Users/jay/Code/Clutch/e2e/web-visual.spec.ts-snapshots/web-settings-chromium-linux.png", "settings.webp", "Clutch model and agent settings", "Configuration panel for local models, tools, and execution environments."),
    ],
    "botfleet": [
        ("/Users/jay/Code/BotFleet/docs/screenshots/marketplace.png", "marketplace.webp", "BotFleet agent marketplace and automation skills", "Catalog of autonomous agents and customizable routines."),
        ("/Users/jay/Code/BotFleet/docs/screenshots/agent-profile-desktop.png", "agent-profile.webp", "BotFleet desktop agent workspace", "Interactive desktop workspace for supervising running agents."),
        ("/Users/jay/Code/BotFleet/docs/screenshots/tasks-routines.png", "tasks-routines.webp", "BotFleet scheduled routines and background tasks", "Automated background routines and scheduled task execution."),
    ],
    "socratic-trade": [
        ("/Users/jay/Code/Socratic-Trade/test/e2e/visual.spec.ts-snapshots/console-autonomy-desk-chromium-linux.png", "autonomy-desk.webp", "Socratic Trade autonomy desk and signal monitor", "Signal analysis, autonomous execution desk, and risk controls."),
        ("/Users/jay/Code/Socratic-Trade/test/e2e/visual.spec.ts-snapshots/login-chromium-linux.png", "login.webp", "Socratic Trade secure sign-in and account portal", "Secure workspace entry with multi-factor authentication."),
    ],
    "congress-trade": [
        ("/Users/jay/Code/Congress.Trade/docs/brand/app-store-screenshots/iphone_69/iphone_69_01_feed.png", "feed.webp", "Congress.Trade public disclosure feed", "Real-time public STOCK Act disclosure feed and trade analysis."),
        ("/Users/jay/Code/Congress.Trade/docs/brand/app-store-screenshots/iphone_69/iphone_69_02_trends.png", "trends.webp", "Congress.Trade politician trading trends", "Aggregate volume, ticker trends, and committee trading patterns."),
    ],
    "contactlogo": [
        ("/Users/jay/Code/ContactLogo/web/tests/e2e/visual.spec.ts-snapshots/homepage-chromium-linux.png", "search.webp", "ContactLogo vector brand search and preview", "Instant vector brand logo lookup and high-resolution contact artwork."),
        ("/Users/jay/Code/ContactLogo/web/tests/e2e/visual.spec.ts-snapshots/settings-chromium-linux.png", "settings.webp", "ContactLogo synchronization preferences", "Google and iCloud contact card sync and artwork preferences."),
    ],
    "autorotate": [
        ("/Users/jay/Code/Autorotate/assets/screenshots/mac_1.png", "mac.webp", "Autorotate macOS secret and rotation dashboard", "Automated credential rotation with verifiable audit trail on macOS."),
        ("/Users/jay/Code/Autorotate/assets/screenshots/iphone_1.png", "iphone.webp", "Autorotate iOS rotation logs and alerts", "Mobile rotation event logs, push notifications, and compliance audit."),
    ],
    "fleetlink": [
        ("/Users/jay/Code/FleetLink/docs/screenshots/landing-hero.png", "landing-hero.webp", "FleetLink dashboard listing live shares with their owner, team, and expiry", "Every share carries its owner, its team, and the day it expires."),
        ("/Users/jay/Code/FleetLink/docs/screenshots/handoff.png", "handoff.webp", "FleetLink handoff steps showing the fleet-share command and a share link", "One command publishes the share; the link goes where the work is."),
    ],
    "hoghunter": [
        ("/tmp/hoghunter-ios.png", "companion.webp", "HogHunter iOS companion inspecting Mac resource usage", "HogHunter companion on iPhone monitoring Mac resource usage over local Wi-Fi."),
    ],
    "dealdex": [
        ("/Users/jay/Code/DealDex/docs/screenshots/scan-results.png", "scan-results.webp", "DealDex market scan with live Mercari listings, verdicts, and desk ranges", "A live scan comparing listing asks against market references."),
    ],
}


def process_image(src_path: str, dst_path: pathlib.Path):
    from PIL import Image
    img = Image.open(src_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        pass
    else:
        img = img.convert("RGB")
    
    width, height = img.size
    if width > MAX_WIDTH:
        new_height = int(height * (MAX_WIDTH / width))
        img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)
        width, height = img.size

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_path, "WEBP", quality=85, method=6)
    size = dst_path.stat().st_size
    print(f"Processed {dst_path.name}: {width}x{height} ({size // 1024} KB)")
    if size > BUDGET_BYTES:
        # Re-save with lower quality if above budget
        img.save(dst_path, "WEBP", quality=75, method=6)
        size = dst_path.stat().st_size
        print(f"  Re-compressed {dst_path.name}: {size // 1024} KB")
        if size > BUDGET_BYTES:
            raise ValueError(f"{dst_path} is {size} bytes, exceeds {BUDGET_BYTES} budget")
    return width, height


def _load_previous(meta_path: pathlib.Path) -> dict:
    """The manifest as it stands, so a partial run can build on it."""
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path) as handle:
            loaded = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _published(previous: dict, output_dir: pathlib.Path) -> dict:
    """The published entries whose image file is still on disk.

    Keyed by slug and then filename, so a carried-forward entry can be
    matched to the shot it describes.
    """
    kept: dict = {}
    for slug, entries in previous.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("src", "")).rsplit("/", 1)[-1]
            if name and (output_dir / slug / name).exists():
                kept.setdefault(slug, {})[name] = entry
    return kept


def main():
    meta_path = OUTPUT_DIR / "metadata.json"
    previous = _load_previous(meta_path)
    carried = _published(previous, OUTPUT_DIR)
    metadata: dict = {}

    # Walk the published manifest first.  The order is the order the pages
    # were built with, and a run that changed nothing has to reproduce the
    # committed file byte for byte.
    for slug, entries in previous.items():
        kept = carried.get(slug, {})
        rebuilt = []
        for entry in entries:
            name = str(entry.get("src", "")).rsplit("/", 1)[-1]
            if name in kept:
                rebuilt.append(kept[name])
        if rebuilt:
            metadata[slug] = rebuilt

    for slug, shots in SOURCES.items():
        entries = metadata.setdefault(slug, [])
        for src, filename, alt, caption in shots:
            if not os.path.exists(src):
                print(f"Warning: source missing for {slug}: {src}", file=sys.stderr)
                # The source repo is not checked out here, not that the
                # published image is gone.  The entry stays as it was
                # published, in the place it was published.
                continue
            dst = OUTPUT_DIR / slug / filename
            w, h = process_image(src, dst)
            fresh = {
                "src": f"/assets/screenshots/{slug}/{filename}",
                "width": w,
                "height": h,
                "alt": alt,
                "caption": caption
            }
            for index, entry in enumerate(entries):
                if str(entry.get("src", "")).rsplit("/", 1)[-1] == filename:
                    entries[index] = fresh
                    break
            else:
                entries.append(fresh)

    for slug, entries in list(metadata.items()):
        if not entries:
            del metadata[slug]

    # Save metadata JSON for catalog generation
    with open(meta_path, "w") as f:
        f.write(json.dumps(metadata, indent=2) + "\n")
    print(f"Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
