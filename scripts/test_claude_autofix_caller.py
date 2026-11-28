"""Static contract for the Claude Code Autofix caller: pin, trigger, guard, permissions."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/claude-code-autofix.yml").read_text()


class ClaudeAutofixCallerContract(unittest.TestCase):
    def test_reusable_is_pinned_to_a_full_commit(self):
        pins = re.findall(
            r"^    uses: Simple-With-Us/AI-Fleet-Coordinator/\.github/workflows/claude-code-autofix-reusable\.yml@([0-9a-f]{40})$",
            WORKFLOW, re.M)
        self.assertEqual(len(pins), 1)

    def test_only_review_and_dispatch_triggers(self):
        self.assertIn("  pull_request_review:\n    types: [submitted]\n", WORKFLOW)
        self.assertIn("  workflow_dispatch:\n", WORKFLOW)
        for forbidden in ("pull_request_target:", "issue_comment:", "pull_request_review_comment:"):
            self.assertNotIn(forbidden, WORKFLOW)

    def test_shared_concurrency_group_without_cancel(self):
        self.assertIn(
            "group: pr-autofix-${{ github.repository }}-${{ github.event.pull_request.number || github.event.inputs.pr }}",
            WORKFLOW)
        self.assertIn("  cancel-in-progress: false\n", WORKFLOW)

    def test_write_job_waits_for_the_open_same_repo_guard(self):
        self.assertRegex(WORKFLOW, r"(?m)^  autofix:\n    needs: guard\n    if: needs\.guard\.outputs\.ok == 'true'\n")
        self.assertIn("'.state + \" \" + (.head.repo.full_name // \"\")'", WORKFLOW)
        self.assertIn('[ "$info" = "open ${REPO}" ]', WORKFLOW)
        self.assertIn("grep -Eq '^[0-9]+$'", WORKFLOW)

    def test_guard_runs_only_for_dispatch_or_tagged_bot_reviews(self):
        guard = WORKFLOW.split("  guard:\n", 1)[1].split("  autofix:\n", 1)[0]
        self.assertIn("github.event_name == 'workflow_dispatch'", guard)
        self.assertIn("""contains(fromJSON('["bot", "Bot"]'), github.event.review.user.type)""", guard)
        self.assertIn("contains(github.event.review.body, '@claude-code-autofix')", guard)
        # Sentry is exempt from both reusables' tags, so only autofix.yml may serve it.
        self.assertIn("github.event.review.user.login != 'sentry[bot]'", guard)
        self.assertIn("github.event.review.user.login != 'sentry'", guard)

    def test_guard_has_read_only_scope_and_event_text_stays_out_of_the_script(self):
        guard = WORKFLOW.split("  guard:\n", 1)[1].split("  autofix:\n", 1)[0]
        self.assertIn("    permissions:\n      pull-requests: read\n", guard)
        run = guard.split("run: |", 1)[1]
        self.assertNotIn("${{", run)

    def test_workflow_permissions_are_the_reusable_minimum(self):
        head = WORKFLOW.split("concurrency:", 1)[0]
        scopes = dict(re.findall(r"^  ([a-z-]+): (read|write)$", head.split("permissions:", 1)[1], re.M))
        self.assertEqual(scopes, {"contents": "write", "pull-requests": "write", "issues": "write"})


if __name__ == "__main__":
    unittest.main()
