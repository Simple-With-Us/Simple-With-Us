# Share cards on app pages

A shared app link on the catalog previews without a card.  The twelve app detail pages carry og:type, og:title, og:description and og:url, and no og:image, so a platform has nothing to draw in the preview.  The homepage has carried the owner's 1200 by 630 share card throughout.

Three apps already publish their own card on their own site, designed by the owner, and those cards are the ones the catalog now points at:  ContactLogo at contactlogo.com/og.png, Congress.Trade at congress.trade/og-image.png, and DealDex at dealdex.net/og.jpg.  Each was measured at 1200 by 630 before it was referenced.  No new art was made for this, and no existing card was changed, cropped, or recoloured.

Which apps have a card is now data, in apps/index.json, rather than a fact buried in page markup.  An app entry may carry an ogImage, and the page has to carry the matching card.  A card cannot quietly disappear from a page, because the data still claims it, and a page cannot keep a card the data no longer claims.

The per-app landing template had the same defect in a worse form:  its og:image pointed at the app's own square icon, so every future app page copied from it would have shared a small square image.  The template now points at the catalog's own 1200 by 630 card, and its comment says to point at the app's own published card instead when the app has one.

Nine apps still have no card.  CodeCaps and BotFleet publish square icons at 192 by 192 and 1024 by 1024, and FleetLink publishes a 1376 by 768 preview, so none of those is a valid share card.  Usage Client, Clutch.Codes, Socratic Trade and Autorotate publish no card at all.  The catalog would have to invent a card for those nine, which is the owner's design call and is not done here.

Validation before publication:  generated freshness and destination policy; 39 Python regression tests; a Node status-state test.  The share card checks were confirmed to fail when a card is removed from a page while the data still claims it, and when a card declares the wrong size.  The template's own card was caught this way.
