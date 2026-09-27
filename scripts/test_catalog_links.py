"""Focused tests for the report-only public catalog destination audit."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import audit_catalog_links as audit


class CatalogLinkAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(audit.DATA.read_text())

    def test_manifest_and_html_destinations_are_deduplicated(self):
        targets = audit.collect_targets(self.data)
        urls = [target.url for target in targets]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("/privacy.html", urls)
        self.assertIn("/codecaps/support.html", urls)
        self.assertIn("https://github.com/jaywedgeworth22/CodeCaps", urls)
        target = next(item for item in targets if item.url == "https://github.com/jaywedgeworth22/Usage-Monitor")
        self.assertGreaterEqual(len(target.sources), 2)

    def test_local_paths_and_fragments_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text('<a id="home" href="/detail.html#section">Detail</a>')
            (root / "detail.html").write_text('<h2 id="section">Details</h2>')
            good = audit.local_result(audit.Target("/detail.html#section", "local"), root)
            missing_fragment = audit.local_result(audit.Target("/detail.html#missing", "local"), root)
            missing_path = audit.local_result(audit.Target("/gone.html", "local"), root)
        self.assertEqual(good.status, "ok")
        self.assertEqual(missing_fragment.status, "broken")
        self.assertEqual(missing_path.status, "broken")

    def test_relative_generated_links_are_resolved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "product").mkdir()
            (root / "product" / "index.html").write_text('<a href="support.html">Support</a><a href="../privacy.html">Privacy</a>')
            (root / "product" / "support.html").write_text("Support")
            (root / "privacy.html").write_text("Privacy")
            targets = audit.collect_targets({"apps": []}, root)
        urls = {target.url for target in targets}
        self.assertIn("/product/support.html", urls)
        self.assertIn("/privacy.html", urls)

    def test_access_challenges_and_transient_servers_are_unverified(self):
        for status in (401, 403, 405, 408, 429, 500, 503):
            self.assertEqual(audit.classify_http_status(status), "unverified")
        self.assertEqual(audit.classify_http_status(200), "ok")
        self.assertEqual(audit.classify_http_status(404), "broken")
        self.assertEqual(audit.classify_http_status(410), "broken")

    def test_offline_audit_still_checks_local_routes(self):
        data = copy.deepcopy(self.data)
        results = audit.audit(data, offline=True)
        self.assertTrue(any(result.target.url == "/privacy.html" and result.status == "ok" for result in results))
        self.assertTrue(any(result.target.url.startswith("https://") and result.status == "unverified" for result in results))


if __name__ == "__main__":
    unittest.main()
