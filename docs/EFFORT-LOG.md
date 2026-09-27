# Simple With Us implementation log

## In progress

2026-09-27 — CODEX — Issue #19: unify site branding and app identity, correct platform links and icons, simplify public copy, and embed public service status.  Branch `codex/brand-product-clarity-20260927`.

2026-09-27 — CODEX — Report-only public catalog destination audit for manifest, support/privacy routes, and generated links.  Issue #13; branch `codex/catalog-link-audit`.  The scheduled/manual workflow does not participate in source PR gating and classifies provider challenges and transient failures as unverified.

## Deployed

2026-09-26 — CODEX and Instinct — Public catalog release facts, generated platform availability, factual copy and link validation.  PRs #11 and #12 passed CI and were published.  Product links and beta labels were checked live.

2026-09-26 — CODEX — Shared support and terms copy aligned with current distribution, GitHub Pages hosting, and the site privacy notice in PR #16.  Site checks passed, Pages run `36283835776` succeeded, and the live support, terms, and privacy routes returned 200.  Issue #15.

The catalog uses `apps/index.json` for release facts.  Validation covers public destination policy, generated freshness, calendar dates, declared categories and support routes.  Operational tracking remains outside this public document.
