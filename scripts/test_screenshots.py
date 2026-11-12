"""Regression checks for the screenshot manifest the catalog publishes from.

`prepare_screenshots.py` reads its sources from the sibling app repos, and
those paths are absolute paths on one machine.  Any source that is not
present has to leave the published manifest alone, because the published
image is still on disk and still on the page.

The image work itself is not exercised here: the manifest is what this file
guards, and the picture is guarded by the size budget in `build_catalog.py`.
`process_image` is stubbed so the check runs without Pillow, which the
catalog's own CI does not install.
"""
import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest

import prepare_screenshots as shots


class ScreenshotManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = pathlib.Path(self.tmp.name)

        self.sources = shots.SOURCES
        self.output_dir = shots.OUTPUT_DIR
        self.process_image = shots.process_image
        shots.OUTPUT_DIR = self.out
        self.addCleanup(self._restore)

    def _restore(self):
        shots.SOURCES = self.sources
        shots.OUTPUT_DIR = self.output_dir
        shots.process_image = self.process_image

    def _run(self):
        """Run the script, keeping its progress output out of the test log."""
        with contextlib.redirect_stdout(io.StringIO()):
            shots.main()

    def _publish(self, slug, filename, entry=None):
        """Put a published image and its manifest entry on disk."""
        app = self.out / slug
        app.mkdir(parents=True, exist_ok=True)
        (app / filename).write_bytes(b"published")
        if entry is None:
            entry = {
                "src": f"/assets/screenshots/{slug}/{filename}",
                "width": 1280,
                "height": 800,
                "alt": f"{slug} alt",
                "caption": f"{slug} caption",
            }
        return entry

    def _manifest(self):
        return json.loads((self.out / "metadata.json").read_text())

    def test_a_missing_source_leaves_the_published_entry_alone(self):
        """The source is not on this machine; the published image still is.

        The old build rebuilt the manifest from the sources alone, so a run
        on a machine without every sibling repo replaced that app's entry
        with an empty list and dropped the screenshot from the catalog.
        """
        entry = self._publish("hoghunter", "companion.webp")
        (self.out / "metadata.json").write_text(
            json.dumps({"hoghunter": [entry]}, indent=2) + "\n")
        shots.SOURCES = {
            "hoghunter": [("/nowhere/companion.png", "companion.webp", "alt", "caption")],
        }

        self._run()

        self.assertEqual([entry], self._manifest()["hoghunter"])

    def test_a_present_source_refreshes_the_published_entry(self):
        """A source that is here is processed, and its entry is replaced."""
        self._publish("hoghunter", "companion.webp", entry={
            "src": "/assets/screenshots/hoghunter/companion.webp",
            "width": 1,
            "height": 1,
            "alt": "stale",
            "caption": "stale",
        })
        source = self.out / "companion.png"
        source.write_bytes(b"source")
        shots.SOURCES = {
            "hoghunter": [(str(source), "companion.webp", "new alt", "new caption")],
        }
        shots.process_image = lambda src, dst: (1280, 800)

        self._run()

        entry = self._manifest()["hoghunter"][0]
        self.assertEqual(1280, entry["width"])
        self.assertEqual("new alt", entry["alt"])
        self.assertEqual("new caption", entry["caption"])

    def test_a_published_image_keeps_its_entry_when_its_source_is_gone(self):
        """The image is on disk, so the manifest still describes it.

        The manifest is the record of what the catalog publishes.  An entry
        whose picture was deleted has to go, and one whose picture is still
        there has to stay, whatever happened to the source repo.
        """
        kept = self._publish("hoghunter", "companion.webp")
        self._publish("codecaps", "glance-light.webp")
        (self.out / "metadata.json").write_text(json.dumps({
            "hoghunter": [kept],
            "codecaps": [{
                "src": "/assets/screenshots/codecaps/glance-light.webp",
                "width": 1280,
                "height": 800,
                "alt": "codecaps alt",
                "caption": "codecaps caption",
            }],
        }, indent=2) + "\n")
        shots.SOURCES = {}

        self._run()

        manifest = self._manifest()
        self.assertEqual([kept], manifest["hoghunter"])
        self.assertEqual(1, len(manifest["codecaps"]))

    def test_an_entry_whose_picture_is_gone_is_dropped(self):
        """No picture, no entry: the manifest only claims what is published."""
        (self.out / "metadata.json").write_text(json.dumps({
            "hoghunter": [{
                "src": "/assets/screenshots/hoghunter/companion.webp",
                "width": 1280,
                "height": 800,
                "alt": "alt",
                "caption": "caption",
            }],
        }, indent=2) + "\n")
        shots.SOURCES = {}

        self._run()

        self.assertNotIn("hoghunter", self._manifest())

    def test_a_source_that_is_missing_leaves_no_phantom_entry(self):
        """A source that was never published does not invent an entry."""
        shots.SOURCES = {
            "hoghunter": [("/nowhere/companion.png", "companion.webp", "alt", "caption")],
        }

        self._run()

        self.assertNotIn("hoghunter", self._manifest())

    def test_the_manifest_is_written_with_a_trailing_newline(self):
        """The committed manifest ends in a newline; the script has to match.

        Without this, a run of the script rewrites the file with the same
        content and one byte less, which shows up as a change every time.
        """
        shots.SOURCES = {}

        self._run()

        raw = (self.out / "metadata.json").read_bytes()
        self.assertTrue(raw.endswith(b"\n"), "the manifest must end with a newline")
        self.assertEqual(json.loads(raw), json.loads(raw.decode()))

    def test_the_committed_manifest_describes_exactly_what_is_published(self):
        """Every published picture has an entry, and every entry has a picture.

        This is the check that would have caught the manifest losing an app:
        the picture is still in `assets/screenshots/`, so the manifest and
        the directory have to agree.
        """
        root = shots.ROOT
        published = root / "assets" / "screenshots"
        manifest = json.loads((published / "metadata.json").read_text())
        described = {entry["src"] for entries in manifest.values() for entry in entries}
        on_disk = {
            f"/assets/screenshots/{path.parent.name}/{path.name}"
            for path in published.rglob("*.webp")
        }
        self.assertEqual(on_disk, described)


if __name__ == "__main__":
    unittest.main()
