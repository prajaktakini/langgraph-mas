"""
utils/parser.py
Parses LLM responses into structured data.
All functions are pure — no side effects, no logging.
"""

from __future__ import annotations
import re


def parse_agent_response(
    text:        str,
    all_agents:  list[str],
    current:     str,
) -> tuple[str, list[str], bool, str]:
    """
    Parse a discussion-phase agent response.

    Returns:
        message     — the agent's message text
        next_agents — list of valid agent names to speak next
        is_done     — True if agent signalled STATUS: DONE
        decision    — content of DECISION: field (may be empty)
    """

    # ── MESSAGE ───────────────────────────────────────────
    m = re.search(
        r"MESSAGE:\s*(.*?)(?=\nNEXT:|\nSTATUS:|\nDECISION:|$)",
        text, re.DOTALL | re.IGNORECASE
    )
    message = m.group(1).strip() if m else text.strip()

    # ── NEXT ──────────────────────────────────────────────
    n = re.search(r"NEXT:\s*([^\n]+)", text, re.IGNORECASE)
    raw_next = n.group(1).strip() if n else ""

    # Match any token that exactly equals a known agent name (case-insensitive)
    next_agents = []
    for token in re.split(r"[,;\s]+", raw_next):
        token = token.strip().rstrip(".")
        for a in all_agents:
            if a.lower() == token.lower() and a not in next_agents:
                next_agents.append(a)

    # Fallback: next agent in round-robin order
    if not next_agents:
        idx = all_agents.index(current)
        fallback = all_agents[(idx + 1) % len(all_agents)]
        next_agents = [fallback]

    # ── STATUS ────────────────────────────────────────────
    s = re.search(r"STATUS:\s*(DONE|CONTINUE)", text, re.IGNORECASE)
    is_done = bool(s and s.group(1).upper() == "DONE")

    # ── DECISION ──────────────────────────────────────────
    d = re.search(r"DECISION:\s*([^\n]+)", text, re.IGNORECASE)
    decision = d.group(1).strip() if d else ""

    return message, next_agents, is_done, decision


def extract_names(raw: str, all_agents: list[str]) -> list[str]:
    """
    Utility: extract all valid agent names from a free-form string.
    Used by parse_agent_response internally; also exported for tests.
    """
    found = []
    for token in re.split(r"[,;\s]+", raw):
        token = token.strip().rstrip(".")
        for a in all_agents:
            if a.lower() == token.lower() and a not in found:
                found.append(a)
    return found