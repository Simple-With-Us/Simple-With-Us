# Simple With Us implementation log

> **ARCHIVED Sun, Oct 11, 2026.**  Linear is the system of record: team AFC, https://linear.app/simple-with-us/team/AFC.
> This file is read-only history.  Do not edit it or add rows.  See EFFORT-LOG-PROTOCOL.md.

## In progress

2026-10-10 — AG — Active TestFlight public beta links enabled for CodeCaps, HogHunter, and DealDex.  Canonical 1024 master icons refreshed across the catalog and app pages.  Branch `ag/tf-betas-and-catalog-refresh`.

2026-09-27 — CODEX — Report-only public catalog destination audit for manifest, support/privacy routes, and generated links.  Issue #13; branch `codex/catalog-link-audit`.  The scheduled/manual workflow does not participate in source PR gating and classifies provider challenges and transient failures as unverified.

## Completed

2026-09-27 — CODEX — Catalog identity follow-up to #23: pair Hog Hunter and Autorotate current iOS Apple IDs with their actual bundle identifiers, and remove the hand-written MiniMax invitation claim so availability has one rendered source.  Existing catalog and status tests pass.

- **2026-09-27 — CODEX — COMPLETED — Current beta review and app identities (#22 / PR #23, board e7074f23, codex/beta-review-status-20260927).**  Reflect Apple review pending for DealDex, CodeCaps iOS, and MiniMax Remote; preserve Socratic Trade invitation-only access.  Hog Hunter and Autorotate current-bundle App Store Connect records created.  No pending invitation is presented as an available install.

## Deployed

2026-09-27 — CODEX — Issue #19 / PR #20 (`28af546`): unified complete logo, app identity, 11 app families, corrected icons/platform links and public service-status feed.  Pages run `36303036956` published the exact merge SHA.  All 89 live catalog destinations passed; manifest, CSS, status module, logo and every app icon matched source.  Eighteen Python tests and the Node status test pass.  External beta publication continues separately.

2026-09-26 — CODEX and Instinct — Public catalog release facts, generated platform availability, factual copy and link validation.  PRs #11 and #12 passed CI and were published.  Product links and beta labels were checked live.

2026-09-26 — CODEX — Shared support and terms copy aligned with current distribution, GitHub Pages hosting, and the site privacy notice in PR #16.  Site checks passed, Pages run `36283835776` succeeded, and the live support, terms, and privacy routes returned 200.  Issue #15.

The catalog uses `apps/index.json` for release facts.  Validation covers public destination policy, generated freshness, calendar dates, declared categories and support routes.  Operational tracking remains outside this public document.
