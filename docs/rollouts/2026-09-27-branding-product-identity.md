# Branding and product identity

The catalog now uses one shared header and footer on its public pages.  The header uses the complete high-resolution Simple With Us logo, including its signature, at its natural aspect ratio.  Product pages lead with the app name and icon.  The generator maintains those elements alongside platform actions so future catalog changes cannot silently leave older product pages behind.

The directory has 11 app families.  Usage Monitor has separate Client and Local editions with their own icons, pages, and invitations.  Fleet infrastructure is excluded.  Categories are Coding, Financial, and Utility.  HogHunter includes its iPhone companion, and Harness has a plain typographic icon.

Platform information separates public TestFlight invitations and Mac downloads from invitation-only testing and builds from source.  Apple public invitation pages and current App Store Connect records were checked on September 27.  Retired Socratic Trade and empty BotFleet Mac invitations are omitted.  Current Socratic Trade and DealDex application identifiers replace stale records.  Subsequent beta publication is tracked separately; an external group alone does not establish an installable release.

The homepage reads the existing public Better Stack JSON feed.  It displays the reported service state and retrieval time, refreshes while the page is visible, and retains an incident-history link.  Failed or unknown responses show an unavailable fallback rather than a healthy state.  The site privacy notice reflects this request.

Validation before publication: generated freshness and destination policy; 18 Python regression tests; a Node status-state test; offline route and fragment audit with no broken destinations.  Browser review covered desktop and 390px layouts, including app identity, complete logo, platform actions, and the live status summary.  Some initial local-preview image requests failed transiently and loaded after refresh; public asset checks are required after publication.

The public link auditor now treats generic or explicitly retired TestFlight pages as unverified even when Apple responds with HTTP 200.  Release enrollment and native installation are separate checks.
