import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rulesmith_cli import RuleSpec, render  # noqa: E402
from rulesmith_cli.cli import main  # noqa: E402


class RenderTests(unittest.TestCase):
    def test_team_name_is_used(self):
        out = render(RuleSpec(team="Acme Platform"), "claude")
        self.assertIn("AI Coding Standards — Acme Platform", out)
        self.assertNotIn("Your Team", out)

    def test_customer_alias(self):
        self.assertEqual(RuleSpec.from_dict({"customer": "Old Name"}).team, "Old Name")

    def test_blocks_compose(self):
        out = render(RuleSpec(stacks=["python", "react"], sector="fintech", compliance="soc2"), "agents")
        for heading in ("Safety invariants", "Stack: python", "Stack: react", "Industry: fintech", "Compliance: SOC2"):
            self.assertIn(heading, out)

    def test_each_agent_has_label(self):
        for agent, label in (("claude", "CLAUDE.md"), ("cursor", ".cursorrules"), ("clinerules", ".clinerules"),
                             ("agents", "AGENTS.md"), ("aider", "CONVENTIONS.md")):
            self.assertIn(label, render(RuleSpec(), agent))

    def test_init_render_check_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            spec = os.path.join(d, "rulesmith.json")
            self.assertEqual(main(["init", "--spec", spec, "--team", "T", "--stack", "go"]), 0)
            self.assertEqual(main(["render", "--spec", spec]), 0)
            self.assertEqual(main(["check", "--spec", spec]), 0)
            with open(os.path.join(d, "CLAUDE.md"), "a") as fh:
                fh.write("- hand edit\n")
            self.assertEqual(main(["check", "--spec", spec]), 1)


if __name__ == "__main__":
    unittest.main()
