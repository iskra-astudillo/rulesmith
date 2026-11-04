"""rulesmith-cli: write your AI coding rules once, render them for every coding agent."""
__version__ = "0.1.0"

from .library import RuleSpec, render, compose_sections, AGENT_FILENAMES  # noqa: E402,F401
