"""Rule blocks and renderers.

One rules spec is composed from blocks (a safety baseline, code quality,
stack, industry and compliance) into a single rules document, then rendered
into each coding agent's native file: CLAUDE.md, AGENTS.md, .cursorrules,
.clinerules and Aider's CONVENTIONS.md.

Pure Python, no network calls, no dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# ---------------------------------------------------------------------------
# Rule blocks. Each block is a titled list of imperative rules.
# ---------------------------------------------------------------------------

SAFETY_BASELINE = [
    "Production data is sacred. Never run a destructive op (DROP, DELETE without WHERE, "
    "force-push, prod flush) without explicit human approval in the task.",
    "Secrets live in env / a secret manager, NEVER inline in code. Read from env; never "
    "hardcode a key, token, password, or connection string. (secret-landmine)",
    "Safety / feature gates MUST fail CLOSED on a missing or malformed flag, never fail "
    "OPEN. (fail-open-config)",
    "Money / quantity math must carry an explicit unit + side. No raw price*qty without "
    "sign / unit handling. (units-mismatch)",
    "Prefer additive, reversible changes. Every change should be revertable by a single "
    "git revert.",
]

QUALITY_BASELINE = [
    "Validate external data against a schema; do not trust a source by name. (schema-by-name)",
    "Long-lived consumers must re-read rotated secrets, not cache them at start. (rotation-miss)",
    "No top-N shortcuts: when fixing a CLASS of issue, sweep EVERY instance, not the first few.",
    "Verify before claiming done: run against real/realistic data and observe behavior; do "
    "not assert a fix works from reading the diff alone.",
    "Small, reviewable commits with conventional messages; keep a clean audit trail.",
]

# Per-stack blocks --------------------------------------------------------------
STACK_BLOCKS: Dict[str, List[str]] = {
    "python": [
        "Type-hint public functions; run mypy/ruff before PR.",
        "Use pathlib over os.path; f-strings over % / .format.",
        "Never bare-except; catch the narrowest exception and log context.",
        "Pin dependencies; no unpinned `pip install` in build steps.",
    ],
    "typescript": [
        "`strict: true` in tsconfig; no `any` without an inline justification.",
        "Prefer `const`; no implicit `var`. Use discriminated unions over type-casting.",
        "Validate API payloads with zod (or equivalent) at the boundary.",
        "No floating promises; every async call is awaited or explicitly voided.",
    ],
    "react": [
        "No business logic in components; extract to hooks/services.",
        "Keys on list items are stable IDs, never array indices.",
        "Memoize expensive renders; avoid inline object/array props that bust memo.",
        "No secrets or API keys in client bundles.",
    ],
    "go": [
        "Always check and wrap errors with %w; never `_ = err`.",
        "Use context.Context for cancellation/timeouts on I/O.",
        "Run `go vet` + `golangci-lint` before PR.",
    ],
    "node": [
        "No secrets in code; load via env/dotenv at boot.",
        "Validate request bodies before use; never trust client input.",
        "Graceful shutdown on SIGTERM; close DB/redis pools.",
    ],
    "rails": [
        "Strong params on every controller action.",
        "No raw SQL string interpolation; use parameterized queries / AR.",
        "N+1 guard: eager-load associations in index actions.",
    ],
    "sql": [
        "Every migration is reversible (has a down).",
        "No DELETE/UPDATE without an explicit WHERE in app code paths.",
        "Index foreign keys and frequent filter columns.",
    ],
}

# Per-industry / compliance blocks ---------------------------------------------
INDUSTRY_BLOCKS: Dict[str, List[str]] = {
    "healthcare": [
        "PHI is never logged, never sent to a third-party LLM, never left in plaintext at rest.",
        "Access to PHI requires an auditable authz check; log who/what/when (not the PHI itself).",
        "De-identify data before any analytics / model-training path. (HIPAA)",
    ],
    "fintech": [
        "All money is integer minor-units (cents); never float currency.",
        "Every balance-changing op is idempotent (idempotency key) and double-entry auditable.",
        "PII/PAN tokenized; never store raw card data. (PCI / GLBA)",
    ],
    "ecommerce": [
        "Price and inventory mutations are transactional; no oversell race.",
        "Webhook handlers verify provider signatures before acting.",
        "PII minimized; checkout fields validated server-side.",
    ],
    "saas": [
        "Multi-tenant isolation: every query is tenant-scoped; no cross-tenant leakage.",
        "Rate-limit public endpoints; authz on every resource by owner.",
        "Audit log for admin / billing / permission changes.",
    ],
    "ai-agent": [
        "Tool calls that mutate state require a confirmation gate or dry-run default.",
        "Never let model output reach exec/eval/SQL/shell without validation + allowlist.",
        "Redact secrets/PII from prompts and traces.",
    ],
    "general": [],
}

COMPLIANCE_BLOCKS: Dict[str, List[str]] = {
    "soc2": [
        "Change management: every prod change is reviewed, logged, and revertable.",
        "Least-privilege access; no shared credentials; secrets rotated.",
    ],
    "hipaa": [
        "BAA-covered services only for PHI; encryption in transit + at rest.",
        "Audit trail of PHI access retained per policy.",
    ],
    "gdpr": [
        "Data-subject deletion path implemented; honor right-to-erasure.",
        "Lawful-basis + minimization: collect only what's needed.",
    ],
    "pci": [
        "No raw PAN storage; tokenize via the payment provider.",
        "Segment the cardholder-data environment; log access.",
    ],
    "none": [],
}


@dataclass
class RuleSpec:
    team: str = "Your Team"
    sector: str = "general"
    stacks: List[str] = field(default_factory=lambda: ["python"])
    compliance: str = "none"
    include_baseline: bool = True
    extra_rules: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "RuleSpec":
        stacks = d.get("stacks", ["python"])
        if isinstance(stacks, str):
            stacks = [s.strip() for s in stacks.split(",") if s.strip()]
        return cls(
            # accept "customer" as an alias so older specs keep their team name
            team=str(d.get("team") or d.get("customer") or "Your Team"),
            sector=str(d.get("sector", "general")),
            stacks=list(stacks),
            compliance=str(d.get("compliance", "none")),
            include_baseline=bool(d.get("include_baseline", True)),
            extra_rules=list(d.get("extra_rules", [])),
        )

    def to_dict(self) -> dict:
        return {
            "team": self.team,
            "sector": self.sector,
            "stacks": self.stacks,
            "compliance": self.compliance,
            "include_baseline": self.include_baseline,
            "extra_rules": self.extra_rules,
        }


# ---------------------------------------------------------------------------
# Composition + rendering
# ---------------------------------------------------------------------------

def compose_sections(spec: RuleSpec) -> List[tuple]:
    """Return ordered (title, [rules]) sections for the spec."""
    sections: List[tuple] = []
    if spec.include_baseline:
        sections.append(("Safety invariants (non-negotiable)", SAFETY_BASELINE))
        sections.append(("Code quality", QUALITY_BASELINE))
    for s in spec.stacks:
        block = STACK_BLOCKS.get(s.lower().strip())
        if block:
            sections.append((f"Stack: {s}", block))
    ind = INDUSTRY_BLOCKS.get(spec.sector.lower().strip())
    if ind:
        sections.append((f"Industry: {spec.sector}", ind))
    comp = COMPLIANCE_BLOCKS.get(spec.compliance.lower().strip())
    if comp:
        sections.append((f"Compliance: {spec.compliance.upper()}", comp))
    if spec.extra_rules:
        sections.append(("Team-specific rules", spec.extra_rules))
    return sections


def _header(spec: RuleSpec, agent_label: str) -> str:
    return (
        f"# AI Coding Standards — {spec.team}\n"
        f"# Generated by rulesmith-cli from rulesmith.json for {agent_label}. Edit the spec, not this file.\n"
        f"# Sector: {spec.sector} | Stack: {', '.join(spec.stacks)} | "
        f"Compliance: {spec.compliance.upper()}\n"
        f"# These rules are injected into every AI-agent task in this repo.\n"
    )


def render(spec: RuleSpec, agent: str = "clinerules") -> str:
    """Render the spec into a target agent's native rules file format."""
    agent = agent.lower()
    labels = {
        "clinerules": "Cline (.clinerules)",
        "claude": "Claude Code (CLAUDE.md)",
        "cursor": "Cursor (.cursorrules)",
        "agents": "Cross-agent (AGENTS.md)",
        "aider": "Aider (CONVENTIONS.md)",
    }
    label = labels.get(agent, "Cline (.clinerules)")
    sections = compose_sections(spec)
    out = [_header(spec, label), ""]
    for title, rules in sections:
        out.append(f"## {title}")
        for r in rules:
            out.append(f"- {r}")
        out.append("")
    body = "\n".join(out).rstrip() + "\n"
    return body


# The file each agent reads.
AGENT_FILENAMES = {
    "clinerules": ".clinerules",
    "claude": "CLAUDE.md",
    "cursor": ".cursorrules",
    "agents": "AGENTS.md",
    "aider": "CONVENTIONS.md",
}

SUPPORTED_STACKS = sorted(STACK_BLOCKS.keys())
SUPPORTED_SECTORS = sorted(INDUSTRY_BLOCKS.keys())
SUPPORTED_COMPLIANCE = sorted(COMPLIANCE_BLOCKS.keys())
SUPPORTED_AGENTS = list(AGENT_FILENAMES.keys())
