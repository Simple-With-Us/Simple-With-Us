"""Static contracts for the existing PR Autofix caller's bounded Sentry access."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/autofix.yml").read_text()
KODY_WORKFLOW = (ROOT / ".github/workflows/kody-fleet-autofix.yml").read_text()
# Public Git commit fixture, not an authentication credential.
TEST_REUSABLE_COMMIT_SHA = "c97a2dae96762eb9ffc122c753f0dfb0a7840650"
KODY_REUSABLE_COMMIT_SHA = "917a49dfb77e4fce307a985510ab814a6f684ef6"
EXPECTED = {"kody-ai[bot]", "chatgpt-codex-connector[bot]", "cursor[bot]", "claude[bot]", "sentry", "sentry[bot]", "swu-ag[bot]", "swu-bf-builder[bot]", "swu-bf-compiler[bot]", "swu-bf-deployer[bot]", "swu-bf-designer[bot]", "swu-bf-director[bot]", "swu-bf-fixer[bot]", "swu-bf-housekeeper[bot]", "swu-bf-monitor[bot]", "swu-bf-oracle[bot]", "swu-bf-plumber[bot]", "swu-bf-publisher[bot]", "swu-claude[bot]", "swu-clutch[bot]", "swu-codex[bot]", "swu-cursor[bot]", "swu-cursor-cloud[bot]", "swu-echo[bot]", "swu-fx[bot]", "swu-gb-compiler[bot]", "swu-gb-deployer[bot]", "swu-gb-designer[bot]", "swu-gb-director[bot]", "swu-gb-engineer[bot]", "swu-gb-fixer[bot]", "swu-gb-housekeeper[bot]", "swu-gb-monitor[bot]", "swu-gb-oracle[bot]", "swu-gb-plumber[bot]", "swu-gb-publisher[bot]", "swu-gb-trader[bot]", "swu-grok-build[bot]", "swu-grok-web[bot]", "swu-jet[bot]", "swu-mc[bot]", "swu-minimax[bot]", "swu-opencode[bot]", "swu-operator[bot]", "swu-rob[bot]", "swu-wise[bot]"}

class AutofixContractTests(unittest.TestCase):
    def test_verified_reusable_pin(self):
        self.assertIn("pr-autofix-reusable.yml@" + TEST_REUSABLE_COMMIT_SHA, WORKFLOW)

    def test_kody_reusable_pin_is_immutable(self):
        self.assertIn("kody-autofix-reusable.yml@" + KODY_REUSABLE_COMMIT_SHA, KODY_WORKFLOW)
        self.assertNotRegex(KODY_WORKFLOW, r"kody-autofix-reusable\.yml@(?:main|master|v?\d[\w.-]*)$")

    def test_only_existing_actors_and_exact_sentry_aliases(self):
        matches = re.findall(r'^      allowed_bots: "([^"]+)"$', WORKFLOW, re.M)
        self.assertEqual(len(matches), 1)
        actors = matches[0].split(",")
        self.assertEqual(set(actors), EXPECTED)
        self.assertEqual(len(actors), len(EXPECTED))
        for unrelated in ("*", "sentry-spoof", "sentry[bot]-spoof", "someone"):
            self.assertNotIn(unrelated, actors)

    def test_human_events_still_require_bot_type(self):
        self.assertIn('contains(fromJSON(\'["bot", "Bot"]\')', WORKFLOW)
        self.assertNotIn("pull_request_target:", WORKFLOW)

    def test_existing_serialization_and_permissions(self):
        self.assertIn("cancel-in-progress: false", WORKFLOW)
        self.assertIn("group: pr-autofix-", WORKFLOW)
        self.assertIn("permissions: {}", WORKFLOW)
        self.assertIn("      contents: write\n      pull-requests: read\n      issues: write\n      actions: read", WORKFLOW)

    def test_kody_lane_shares_the_pr_autofix_group(self):
        # Every autofix caller holds pr-autofix-<repo>-<pr> so only one of them pushes to a PR
        # at a time (AI-Fleet-Coordinator docs/PR-AUTOFIX.md, Fleet Autofix Coordination).  A
        # kody-fleet group that is renamed or re-keyed would silently end that serialization.
        shared_prefix = "pr-autofix-${{ github.repository }}-"
        main_groups = re.findall(r"^  group: (.+)$", WORKFLOW, re.M)
        kody_groups = re.findall(r"^      group: (.+)$", KODY_WORKFLOW, re.M)
        self.assertEqual(len(main_groups), 1)
        self.assertEqual(len(kody_groups), 1)
        self.assertTrue(main_groups[0].startswith(shared_prefix))
        self.assertTrue(kody_groups[0].startswith(shared_prefix))
        self.assertNotIn("kody-caller-", KODY_WORKFLOW)

    def test_kody_lane_never_cancels_a_running_autofix(self):
        self.assertEqual(len(re.findall(r"^      cancel-in-progress: false$", KODY_WORKFLOW, re.M)), 1)
        self.assertNotIn("cancel-in-progress: true", KODY_WORKFLOW)

if __name__ == "__main__":
    unittest.main()