# App icon attribution

The slug-named icons in this folder (`<slug>.png`, `clutch-wordmark.svg`,
`socratic-trade.svg`) are 128 px downscales of each app's own canonical master,
rendered with `sips -Z 128`.  Each app's repository is the single source of
truth for its mark; the fleet logo set in `jaywedgeworth22/ai-fleet-coordinator`
(`agent-logos/app-*.png`) is a convenience mirror and must not be treated as
authoritative.

Last re-derived: 2026-10-03.

| Slug | Canonical master |
| --- | --- |
| `usage-client.png` | `jaywedgeworth22/Usage-Monitor` — `ios/UsageMonitor/App/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` |
| `usage-local.png` | `jaywedgeworth22/Usage-Monitor` — `ios/UsageMonitor/LocalApp/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` |
| `clutch.png` | `Simple-With-Us/Clutch` — `ios/Assets.xcassets/AppIcon.appiconset/icon-1024.png` |
| `botfleet.png` | `jaywedgeworth22/BotFleet` — `ios/App/Assets.xcassets/AppIcon.appiconset/icon-1024.png` |
| `socratic-trade.png` | `jaywedgeworth22/Socratic-Trade` — `ios/SocraticTrade/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` |
| `socratic-trade.svg` | Byte-identical copy of the fleet mirror `agent-logos/app-st.svg`.  It has no vector counterpart in the Socratic Trade repo, so it is a mirror, not an app master. |
| `congress-trade.png` | `jaywedgeworth22/Congress.Trade` — `clients/ios/CongressTrade/Assets.xcassets/AppIcon.appiconset/AppIcon.png` |
| `hoghunter.png` | `jaywedgeworth22/HogHunter` — `ios/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` |
| `contactlogo.png` | `jaywedgeworth22/ContactLogo` — `Apps/ContactLogoiOS/Assets.xcassets/AppIcon.appiconset/icon_1024x1024.png` |
| `dealdex.png` | `jaywedgeworth22/DealDex` — `native/ios/DealDex/Assets.xcassets/AppIcon.appiconset/Icon-1024.png` |
| `autorotate.png` | `jaywedgeworth22/Autorotate` — `apple/TopSpin-iOS/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png` |
| `fleetlink.png` | `jaywedgeworth22/FleetLink` — `ios/Assets.xcassets/AppIcon.appiconset/icon-1024.png` |

## Third-party marks in `assets/badges/`

These are **not** fleet artwork.  Both come from Apple and are used as
provided; Apple's marketing guidelines say to use only the badge artwork they
publish and never to modify it.

| File | Origin | Terms |
| --- | --- | --- |
| `badges/app-store-badge.svg` | Apple's published "Download on the App Store" badge, fetched unmodified from `developer.apple.com/assets/elements/badges/download-on-the-app-store.svg` (native 119.66407 × 40). | Used exactly as provided.  Apple's guidelines say to use the preferred black badge in all marketing for an app on the App Store, and not to modify, angle or animate it. |
| `badges/testflight-icon.png` | The TestFlight app icon, from Apple's CDN via the public iTunes lookup for id 899247664, resized to 128 px with `sips -Z 128` (4× the 30 px badge tile). | Apple publishes **no TestFlight badge**, so the badge around it is ours; only the icon is Apple's.  It is nominative:  the button it sits in links to `testflight.apple.com`. |

Apple's badge licence covers apps available on the App Store, which is why the
App Store badge appears only for an app that is actually listed, and the
TestFlight badge only for one that is not.

Each icon belongs to its own app and repo, all Apache-2.0.  The two-letter
files (`ar.png`, `bf.png`, and so on) predate the 200 KB image budget and are
slated for removal once every page uses the slug-named icons.

## Change log

2026-10-22: The CodeCaps catalog icon is the transparent ring mark now:
`assets/logos/codecaps-logo-transparent.svg`, taken from
`Simple-With-Us/CodeCaps` — `assets/brand/codecaps-logo-transparent.svg`
(owner-supplied vector art, unaltered), so the catalog serves the mark at any
size.  The 128 px `codecaps.png` downscale is gone with it.  The mark's needle
and its six gauge dots are #222325, drawn for a light surface, so the
stylesheet gives it a light plate in dark mode.

2026-10-18: Rebuilt the Simple With Us brand set in `assets/logos/` from Jay's
master art.  The header now serves WebP through a `<picture>`, so the dark
plate ships with the light one and the lockup survives a dark page.  The
favicon set is the same idea at icon sizes.  Watch the naming:  the **unsuffixed
square files are the black plates**, the `-light` ones are the white plates, and
`swu-square-*-dark.webp` were bare transparent marks with no plate (removed as
unused).  Verified:  `swu-square-32.webp` reads (0, 0, 0) in the corners,
`swu-square-32-light.webp` reads (255, 255, 255).  The master blue is `#36C6F4`.

| File | Role |
| --- | --- |
| `logos/swu-header-lockup.webp` | Header lockup, light plate. 640 × 64. |
| `logos/swu-header-lockup-dark.webp` | Header lockup, dark plate. Same `<picture>`. |
| `logos/swu-wordmark.webp` | Wordmark only, no plate. |
| `logos/swu-wordmark-dark.webp` | Wordmark for dark backgrounds. |
| `logos/swu-square-white.png` | `og:image`, 512 px. PNG because most social scrapers do not read WebP. |

Dropped 20 unused derived variants (~504 KB) — stacked marks, `jay` /
`black` / `light` / `dark` square alternates, and PNG duplicates of WebP
files — so the folder holds only what the site serves plus its PNG fallbacks.
Regenerate rather than redraw.

2026-10-18 (later): **favicons replaced with Jay's own pack.**  The three
`swu-square-*` favicon derivatives are gone; the `swu-square-white.png`
`og:image` stays for now.  Canonical source is Jay's *Latest SimpleWithUs
Favicons — SWU* pack, which holds eight 1024 × 1024 masters:

| Jay's file | Used as |
| --- | --- |
| `SWU Favicon-Icon - Light Mode - White BG.png` | `swu-favicon-*-light.*` — light browser chrome |
| `SWU Favicon-Icon - Dark Mode - Black BG.png` | `swu-favicon-*-dark.*` — dark browser chrome |

The pack also carries Transparent variants of each.  They are **not** wired
up, and the reason is worth keeping:  the two transparent files are not the
same picture.  The thin grey W is `#6A6A6A` in the light one and `#A8A8A8`
in the dark one, so each is tuned to a tab colour.  Dropped onto the wrong
tab the W all but disappears.  The white and black plates carry no such
dependency and are the safe pair for a favicon.

Naming note, replacing the earlier trap:  the old derived set used the
*unsuffixed* file for the black plate, which read `(0,0,0)` in the corners
while `-light` read `(255,255,255)`.  The new set is explicit — the mode
is in the name.  Jay's pack also carries a stray grey pixel at `(0,0)` of
the Black BG master, an export artifact rather than design; it was cleaned
to the plate colour before downscaling.  Three such pixels, not one.

Sizes served: 32 px for `<link rel="icon">`, 180 px for `apple-touch-icon`
(Apple's documented size, not 192).  Both use the light/dark pair via
`media="(prefers-color-scheme: …)"`.  The 1024 masters are **not** kept in
this repository — the favicon PNGs are the same convention as the app icons
above, derived output with the canonical master living with its owner.

2026-10-17: Added `assets/badges/` (Apple App Store badge, Apple TestFlight icon) and this third-party section.

2026-10-10: Re-derived `codecaps.png`, `hoghunter.png`, `fleetlink.png`, and added `clutch.png` from canonical 1024 masters (CodeCaps 3D brand asset, HogHunter full-bleed green fabric mark, FleetLink master, Clutch C-monogram master).

2026-10-03: Re-derived every slug-named icon from the owning app's canonical
master.  `codecaps.png` and `hoghunter.png` were genuinely stale and changed:
the old CodeCaps mark was a teal circuit-and-arrow tile, now a blue gauge with
a white needle; the old HogHunter mark was a grey boar in a crosshair, now an
orange boar head.  `fleetlink.png` is new.  The other eight already matched
their master to within resampling noise, so they only changed bytes, not
pictures.  `usage-client.png`, `usage-local.png`, and `socratic-trade.png` had
been committed at 256 px rather than 128 px; they are now 128 px like the rest.
`clutch-wordmark.svg` is unchanged.  The shared SWU logo is a full-size
re-encoding of the 1920×200 official original, preserving the name and
signature.

2026-09-27: Socratic Trade uses the current native 3D offset ST icon.  Usage
Client and Usage Local use their respective native app icons.

2026-09-25: Initial import from the fleet logo set.  The CodeCaps icon then
named `assets/icon-512.png` in `jaywedgeworth22/CodeCaps`; that file no longer
exists, which is why the 2026-10-03 pass points at `assets/icon-1024.png`.
