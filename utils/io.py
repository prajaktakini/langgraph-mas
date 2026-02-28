"""
utils/io.py
File I/O helpers: JSONL append, session summary writer.
All functions take explicit paths — no global state.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from graph.state import MASState

log = logging.getLogger("MAS.io")


def append_jsonl(path: Path, record: dict) -> None:
    """Append one JSON record to a .jsonl file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_summary(state: MASState, jsonl_path: Path, txt_path: Path) -> None:
    """
    Print final tally to the logger and append a summary record to JSONL.
    Called by the extractor node after the decision is known.
    """
    log.info("=" * 55)
    log.info("SIMULATION COMPLETE")
    log.info(f"Final decision : {state.get('final_decision', 'N/A')}")
    log.info(f"Total turns    : {state['round']}")

    log.info("\nTurn counts:")
    for agent in state["agents"]:
        count = state["agent_turn_count"].get(agent, 0)
        bar   = "█" * count
        log.info(f"  {agent:>10}: {bar} ({count})")

    if state["raw_decisions"]:
        log.info("\nDecision proposals during discussion:")
        for d in state["raw_decisions"]:
            log.info(f"  → {d}")

    log.info(f"\nLogs → {txt_path}")
    log.info(f"       {jsonl_path}")
    log.info("=" * 55)

    append_jsonl(jsonl_path, {
        "type":           "summary",
        "final_decision": state.get("final_decision"),
        "raw_decisions":  state["raw_decisions"],
        "total_rounds":   state["round"],
        "turn_counts":    state["agent_turn_count"],
    })