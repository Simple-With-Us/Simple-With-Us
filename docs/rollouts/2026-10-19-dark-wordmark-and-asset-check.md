# Dark wordmark and the local asset check

The shared header names a dark wordmark in its `<picture>` element, and it did so on every published page.  The 1x file behind that name was never in the repository, so a browser in dark mode asked for `/assets/logos/swu-wordmark-dark.webp`, received a 404, and drew a broken-image icon beside the alt text instead of the lockup.  The 2x file was present, but a browser picks the 1x source first and only falls back when the image it selected fails to load, so the 2x never rescued the header.

The missing file is not new art.  It is the master-derived 288 pixel dark wordmark from the brand pipeline, exported as it stands.  The repository's light 1x and dark 2x files are byte-identical to the 288 and 576 pixel outputs of the same pipeline, so the dark 1x is the one file the same run never produced.  It is 288 by 30 pixels, matching the light 1x, and it carries no recolouring, no redraw, and no regeneration.

The markup test that names the dark wordmark could not catch this, because it asserts the markup and not the file.  The generator now collects the local files each page pulls in: image sources, source sets with their width descriptors, and the icon and stylesheet links.  Every one of those paths is checked against the repository, and a page that names a file that is not there fails the release gate with the page and the path.  The check covers assets only, because an anchor may point at a page and the existing destination check already covers that case.

Validation before publication: generated freshness and destination policy; 37 Python regression tests; a Node status-state test.  The asset check was confirmed to fail when the exported file is removed, and the build gate named the file on all 33 pages that referenced it.  Browser review covered the local catalog in both colour schemes: dark mode now loads the dark wordmark at 288 by 30 pixels and draws the full lockup, and light mode still selects the light 2x at 576 by 60 pixels.

## Publication

Pending.  This section is completed with the merge commit and the live asset check once the pull request lands.