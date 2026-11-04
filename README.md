# rulesmith

**Write your team's AI coding rules once. Generate `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.clinerules` and Aider's `CONVENTIONS.md` from that one source.**

Every coding agent reads its own rules file. Teams that use more than one agent end up with five copies of the same standards, edited by hand, drifting apart. `rulesmith` keeps one spec (`rulesmith.json`), composes it from tested rule blocks, renders each agent's native file, and fails CI when a generated file has drifted.

Pure Python standard library. No network calls, no API keys.

```console
$ rulesmith init --team "Acme Platform" --stack python,react --sector saas --compliance soc2
wrote rulesmith.json
$ rulesmith render
wrote ./.clinerules
wrote ./CLAUDE.md
wrote ./.cursorrules
wrote ./AGENTS.md
wrote ./CONVENTIONS.md
$ rulesmith check
ok: generated files match rulesmith.json
```

See [`examples/`](examples/) for the exact output of that run.

## Install

```bash
pipx install git+https://github.com/iskra-astudillo/rulesmith
# or, from a clone:
python -m rulesmith_cli list
```

Python 3.8 or newer. No dependencies. The command is `rulesmith`; the package name is `rulesmith-cli`.

## Commands

| Command | What it does |
|---|---|
| `rulesmith init` | Writes `rulesmith.json` from `--team`, `--stack`, `--sector`, `--compliance`. |
| `rulesmith render` | Writes the agent files next to the spec (or `--out DIR`). `--agent claude` limits it to one. |
| `rulesmith check` | Exits 1 if any generated file is missing or differs from the spec. Use it in CI. |
| `rulesmith list` | Shows the supported stacks, sectors, compliance sets and agents. |

## Rule blocks

- **Safety baseline** (on by default): no destructive operations without human approval, no inline secrets, safety gates fail closed, money math carries units, changes are revertable.
- **Code quality**: validate external data against a schema, re-read rotated secrets, fix a whole class of issue rather than the first instance, verify before claiming done.
- **Stacks**: go, node, python, rails, react, sql, typescript.
- **Industries**: ai-agent, ecommerce, fintech, healthcare, saas.
- **Compliance**: gdpr, hipaa, pci, soc2.
- **Team rules**: anything in `extra_rules` is appended verbatim.

```json
{
  "team": "Acme Platform",
  "sector": "saas",
  "stacks": ["python", "react"],
  "compliance": "soc2",
  "include_baseline": true,
  "extra_rules": ["All public endpoints are documented in openapi.yaml."]
}
```

## CI

```yaml
- run: pipx run --spec git+https://github.com/iskra-astudillo/rulesmith rulesmith check
```

The check compares each file byte for byte with a fresh render, so a hand edit to `CLAUDE.md` fails the build and the fix is to change the spec.

## Agent skill

[`SKILL.md`](SKILL.md) lets Claude Code, Codex or Cursor maintain the spec themselves: edit `rulesmith.json`, render, check, commit both together.

## Why the safety baseline looks like this

The baseline rules come from the failure modes that recur in AI-written code: a gate that fails open when its flag is missing, a secret pasted inline, a destructive command run without approval, a fix applied to the first instance of a bug and not the rest. The companion tool [bugclass-detectors](https://github.com/iskra-astudillo/bugclass-detectors) detects several of these in Python code.

## Hosted version

[RuleSmith](https://rulesmith.eliteaiempire.com) generates the same files in the browser.

## License

MIT. See [LICENSE](LICENSE).
