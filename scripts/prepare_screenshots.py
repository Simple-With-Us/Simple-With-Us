#!/usr/bin/env python3
"""Prepare and optimize real screenshots across all catalog apps.

Resizes to max 1280px width, converts to WebP (quality 85),
and verifies each image meets the < 150 KB budget from DESIGN-BRIEF.md.
"""
import os
import pathlib
import sys
from PIL import Image

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
    "dealdex": [
        ("/Users/jay/Code/DealDex/.vercel/output/static/__grok/install/assets/homescreen/ob-phone.png", "phone.webp", "DealDex mobile market spread and pricing analysis", "Real-time market comp aggregation, spread detection, and appraisals."),
        ("/Users/jay/Code/DealDex/.vercel/output/static/__grok/install/assets/homescreen/ob-ipad.png", "ipad.webp", "DealDex card appraisal desk on iPad", "Multi-marketplace pricing comparisons and condition multipliers."),
    ],
    "autorotate": [
        ("/Users/jay/Code/Autorotate/assets/screenshots/mac_1.png", "mac.webp", "Autorotate macOS secret and rotation dashboard", "Automated credential rotation with verifiable audit trail on macOS."),
        ("/Users/jay/Code/Autorotate/assets/screenshots/iphone_1.png", "iphone.webp", "Autorotate iOS rotation logs and alerts", "Mobile rotation event logs, push notifications, and compliance audit."),
    ],
    "fleetlink": [
        ("/Users/jay/Code/FleetLink/assets/preview.png", "preview.webp", "FleetLink secure clipboard handoff and verification", "End-to-end encrypted packet handoff between Macs and iOS devices."),
        ("/Users/jay/Code/FleetLink/assets/preview-locked.png", "preview-locked.webp", "FleetLink passphrase protection", "Client-side passphrase encryption protecting shared payloads."),
    ],
    "hoghunter": [
        ("/tmp/hoghunter-ios.png", "companion.webp", "HogHunter iOS companion inspecting Mac resource usage", "HogHunter companion on iPhone monitoring Mac resource usage over local Wi-Fi."),
    ],
}


def process_image(src_path: str, dst_path: pathlib.Path):
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


def main():
    metadata = {}
    for slug, shots in SOURCES.items():
        metadata[slug] = []
        app_dir = OUTPUT_DIR / slug
        for src, filename, alt, caption in shots:
            if not os.path.exists(src):
                print(f"Warning: source missing for {slug}: {src}", file=sys.stderr)
                continue
            dst = app_dir / filename
            w, h = process_image(src, dst)
            metadata[slug].append({
                "src": f"/assets/screenshots/{slug}/{filename}",
                "width": w,
                "height": h,
                "alt": alt,
                "caption": caption
            })

    # Save metadata JSON for catalog generation
    import json
    meta_path = OUTPUT_DIR / "metadata.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {meta_path}")


if __name__ == "__main__":
    main()
