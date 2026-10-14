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
| `codecaps.png` | `jaywedgeworth22/CodeCaps` — `assets/icon-1024.png` |
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

Each icon belongs to its own app and repo, all Apache-2.0.  The two-letter
files (`ar.png`, `bf.png`, and so on) predate the 200 KB image budget and are
slated for removal once every page uses the slug-named icons.

## Change log

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
