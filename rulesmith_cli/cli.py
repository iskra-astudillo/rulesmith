"""rulesmith: init / render / check / list."""
import argparse
import json
import os
import sys

from . import __version__
from .library import (RuleSpec, render, AGENT_FILENAMES, SUPPORTED_STACKS,
                      SUPPORTED_SECTORS, SUPPORTED_COMPLIANCE, SUPPORTED_AGENTS)

DEFAULT_SPEC = "rulesmith.json"


def _load(path):
    with open(path) as fh:
        return RuleSpec.from_dict(json.load(fh))


def _targets(agents):
    if not agents or agents == ["all"]:
        return SUPPORTED_AGENTS
    bad = [a for a in agents if a not in AGENT_FILENAMES]
    if bad:
        raise SystemExit("unknown agent(s): %s (choose from %s)" % (", ".join(bad), ", ".join(SUPPORTED_AGENTS)))
    return agents


def cmd_init(a):
    if os.path.exists(a.spec) and not a.force:
        print("%s already exists (use --force to overwrite)" % a.spec, file=sys.stderr)
        return 1
    stacks = [s.strip() for s in a.stack.split(",") if s.strip()]
    unknown = [s for s in stacks if s not in SUPPORTED_STACKS]
    if unknown:
        print("note: no rule block for stack(s) %s; supported: %s" % (unknown, SUPPORTED_STACKS), file=sys.stderr)
    spec = RuleSpec(team=a.team, sector=a.sector, stacks=stacks, compliance=a.compliance)
    with open(a.spec, "w") as fh:
        json.dump(spec.to_dict(), fh, indent=2)
        fh.write("\n")
    print("wrote %s" % a.spec)
    return 0


def cmd_render(a):
    spec = _load(a.spec)
    out_dir = a.out or os.path.dirname(os.path.abspath(a.spec))
    for agent in _targets(a.agent):
        path = os.path.join(out_dir, AGENT_FILENAMES[agent])
        with open(path, "w") as fh:
            fh.write(render(spec, agent))
        print("wrote %s" % path)
    return 0


def cmd_check(a):
    spec = _load(a.spec)
    out_dir = a.out or os.path.dirname(os.path.abspath(a.spec))
    drift = []
    for agent in _targets(a.agent):
        path = os.path.join(out_dir, AGENT_FILENAMES[agent])
        want = render(spec, agent)
        try:
            with open(path) as fh:
                have = fh.read()
        except FileNotFoundError:
            drift.append("%s: missing" % path)
            continue
        if have != want:
            drift.append("%s: differs from %s" % (path, a.spec))
    for d in drift:
        print("DRIFT " + d)
    if drift:
        print("run `rulesmith render` and commit the result", file=sys.stderr)
        return 1
    print("ok: generated files match %s" % a.spec)
    return 0


def cmd_list(_a):
    print("stacks:     " + ", ".join(SUPPORTED_STACKS))
    print("sectors:    " + ", ".join(SUPPORTED_SECTORS))
    print("compliance: " + ", ".join(SUPPORTED_COMPLIANCE))
    print("agents:     " + ", ".join("%s -> %s" % (k, v) for k, v in AGENT_FILENAMES.items()))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rulesmith",
                                 description="Write AI coding rules once; render CLAUDE.md, AGENTS.md, "
                                             ".cursorrules, .clinerules and CONVENTIONS.md from one spec.")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create %s" % DEFAULT_SPEC)
    p.add_argument("--team", default="Your Team")
    p.add_argument("--stack", default="python", help="comma list, e.g. python,react")
    p.add_argument("--sector", default="general", choices=SUPPORTED_SECTORS)
    p.add_argument("--compliance", default="none", choices=SUPPORTED_COMPLIANCE)
    p.add_argument("--spec", default=DEFAULT_SPEC)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    for name, fn, hlp in (("render", cmd_render, "write the agent rule files"),
                          ("check", cmd_check, "exit 1 if generated files drifted from the spec (CI)")):
        p = sub.add_parser(name, help=hlp)
        p.add_argument("--spec", default=DEFAULT_SPEC)
        p.add_argument("--agent", action="append", help="one of %s (repeatable; default all)" % SUPPORTED_AGENTS)
        p.add_argument("--out", help="output directory (default: the spec's directory)")
        p.set_defaults(fn=fn)

    p = sub.add_parser("list", help="show supported stacks, sectors, compliance sets and agents")
    p.set_defaults(fn=cmd_list)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
