# Public catalog release facts

`apps/index.json` is the public release-facts source for the Simple With Us catalog and the availability block on each product detail page.  It is served unchanged at `https://simplewithus.com/apps/index.json` after publication.  Other public sites can consume it at build time; they should not import the private routing inventory.

Schema 2 keeps the existing `apps[]` identity, editorial, route, and link fields.  Each app now has `availability` keyed by the names in `platforms`.  A platform fact has `status`, `label`, `channel`, `url`, `verifiedOn`, and `verification`.  Status is `live`, `beta`, `source`, or `unverified`.  Channel is `website`, `source`, `appStore`, `testFlight`, `download`, or `null`.  A null URL means the page displays a status and support path without an install CTA.  The verification note records what was observed on its date; it does not establish enrollment or installation.

Update the JSON, then run `python3 scripts/build_catalog.py`.  Run `python3 scripts/build_catalog.py --check` and `python3 -m unittest discover -s scripts -p 'test_*.py'` before committing.  The generator updates the homepage and each marked detail availability block.  It rejects generic TestFlight/store URLs, unknown source repositories, private-repository destinations, missing local routes, and stale generated regions.  This script is on-demand; it creates no background process.

## Anonymous destination check, 26 September 2026

The following product entries returned HTTP 200 after redirects: `codecaps.simplewithus.com`, `botfleet.app`, `socratictrade.com` (redirected to sign-in), `congress.trade`, `contactlogo.com`, and `dealdex.net`.  The public source repositories for CodeCaps, Usage-Monitor, Harness, HogHunter, BotFleet, Socratic-Trade, Congress.Trade, ContactLogo, DealDex, and Autorotate returned HTTP 200.  The BotFleet TestFlight page showed “Join the BotFleet beta.”  The CodeCaps and BotFleet Mac DMG URLs returned HTTP 200 after redirects in a bounded reachability check by the product-site reviewer.  These checks did not install a binary, join a beta, authenticate, or exercise a product workflow.

The owner's `usage.jays.services` deployment is password-gated and is not a public customer signup destination.  Most native betas have no confirmed public invite or download; their URL remains null.  Recheck external links and release status around a release before changing a CTA.
