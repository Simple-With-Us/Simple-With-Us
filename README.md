# Simple With Us

Marketing pages for tools published at [simplewithus.com](https://simplewithus.com).

This repository hosts the static catalog and product pages at
`/<slug>/` on the Simple With Us site.  It has no runtime service.
Products retain their own source repositories and product sites; MiniMax
Remote's source is private.

## What lives here

```
index.html             family-directory homepage listing every fleet app
privacy.html           site privacy notice and scoped product data overview
support.html           general support landing
terms.html             universal terms
style.css              product-page stylesheet
assets/site.css        catalog stylesheet
<slug>/                per-app marketing (index.html) + support (support.html)
assets/                shared visual assets (logos, favicons, og images)
LICENSE                Apache 2.0
```

## URL scheme

The catalog details use apex paths:

* `https://simplewithus.com/`                family directory
* `https://simplewithus.com/codecaps/`       CodeCaps catalog details
* `https://simplewithus.com/minimax-remote/` MiniMax Remote landing

Existing product domains retain their current roles.  Unclaimed wildcard
subdomains are not public app destinations.

## Hosting

Deployed via GitHub Pages on the `main` branch root, exposed at
`simplewithus.com` through the `simplewithus.com` Cloudflare DNS
zone.  Apex maps via Cloudflare CNAME flattening to GitHub Pages;
the repo root carries a `CNAME` file so the Pages build serves the
apex directly.

## Conventions

* Use sentence case for prose, Title Case for buttons, headings, and
  the page `<title>`.
* Two literal ASCII spaces between sentences in every human-readable
  surface, including this README.
* Default UI theme follows the system preference, never a hard-coded
  light or dark mode.
* Keep images under the 200 KB build budget unless listed as legacy assets
  in `scripts/build_catalog.py`.

## Local preview

```
cd Simple-With-Us
python3 -m http.server 8080
```

Open `http://localhost:8080/` for the homepage,
`http://localhost:8080/codecaps/` for the CodeCaps landing,
etc.

## License

Apache 2.0.  See [LICENSE](LICENSE).

## Public release manifest

The catalog and per-product availability sections are generated from [`apps/index.json`](apps/index.json).  Its schema and anonymous destination evidence are documented in [`docs/PUBLIC-CATALOG.md`](docs/PUBLIC-CATALOG.md).  Run `python3 scripts/build_catalog.py --check` before opening a PR.
