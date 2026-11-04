---
name: rulesmith
description: Maintain a repository's AI coding rules from one spec (rulesmith.json) and regenerate CLAUDE.md, AGENTS.md, .cursorrules, .clinerules and CONVENTIONS.md. Use when asked to add, change or sync coding rules for AI agents.
---

# rulesmith

1. If `rulesmith.json` is missing, run `rulesmith init --team "<team>" --stack <stacks> --sector <sector> --compliance <set>`; `rulesmith list` shows the options.
2. Add team-specific rules to `extra_rules` in `rulesmith.json`. Never hand-edit the generated files; they are overwritten.
3. Run `rulesmith render`, then `rulesmith check` (it must print `ok`).
4. Commit `rulesmith.json` and the generated files together in one commit.
