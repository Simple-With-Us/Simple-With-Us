# Public catalog release facts

`apps/index.json` is the public release-facts source for the Simple With Us catalog and the availability block on each product detail page.  It is served unchanged at `https://simplewithus.com/apps/index.json` after publication.  Other public sites can consume it at build time; they should not import the private routing inventory.

Schema 2 keeps the existing `apps[]` identity, editorial, route, and link fields.  Each app now has `availability` keyed by the names in `platforms`.  A platform fact has `status`, `label`, `channel`, `url`, `verifiedOn`, and `verification`.  Status is `live`, `beta`, `source`, or `unverified`.  Channel is `website`, `source`, `appStore`, `testFlight`, `download`, or `null`.  A null URL means the page displays a status and support path without an install CTA.  The verification note records what was observed on its date; it does not establish enrollment or installation.

Update the JSON, then run `python3 scripts/build_catalog.py`.  Run `python3 scripts/build_catalog.py --check` and `python3 -m unittest discover -s scripts -p 'test_*.py'` before committing.  The generator updates the homepage and each marked detail availability block.  It rejects generic TestFlight/store URLs, unknown source repositories, private-repository destinations, missing local routes, and stale generated regions.  This script is on-demand; it creates no background process.

## Public destination audit

Run `python3 scripts/audit_catalog_links.py --offline --report /tmp/catalog-link-audit.md` for a local route and fragment check without network access.  The scheduled/manual `Public Catalog Link Audit` workflow runs the same checker against public destinations and uploads a Markdown artifact with the job summary.  It is separate from source PR checks, so an external provider outage cannot block catalog changes.

The audit deduplicates manifest, homepage, and detail-page links.  `ok` records a reachable local path or HTTP response after redirects.  `broken` is reserved for a missing local path or fragment and clear HTTP 4xx responses such as 404/410.  `unverified` covers provider access challenges, rate limits, timeouts, and transient 5xx responses; review those destinations before changing a release fact.  The check uses an anonymous browser-like user agent and never sends bearer credentials, joins a beta, installs a binary, or mutates production.

## Anonymous destination check, 26 September 2026

The following product entries returned HTTP 200 after redirects: `codecaps.simplewithus.com`, `botfleet.app`, `socratictrade.com` (redirected to sign-in), `congress.trade`, `contactlogo.com`, and `dealdex.net`.  The public source repositories for CodeCaps, Usage-Monitor, Harness, HogHunter, BotFleet, Socratic-Trade, Congress.Trade, ContactLogo, DealDex, and Autorotate returned HTTP 200.  The BotFleet TestFlight page showed “Join the BotFleet beta.”  The CodeCaps and BotFleet Mac DMG URLs returned HTTP 200 after redirects in a bounded reachability check by the product-site reviewer.  These checks did not install a binary, join a beta, authenticate, or exercise a product workflow.

The owner's `usage.jays.services` deployment is password-gated and is not a public customer signup destination.  Most native betas have no confirmed public invite or download; their URL remains null.  Recheck external links and release status around a release before changing a CTA.
