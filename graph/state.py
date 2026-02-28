"""
graph/state.py
Single source of truth for shared agent state.
Compatible with Python 3.9+
"""

from __future__ import annotations
from typing import TypedDict, Literal, Optional, List, Dict


class MASState(TypedDict):
    # ── Society ───────────────────────────────────────────
    agents:            List[str]          # ordered list of all agent names
    personalities:     Dict[str, str]     # name → personality string
    roles:             Dict[str, str]     # name → role label
    task:              str                # what the group must decide

    # ── Conversation ──────────────────────────────────────
    messages:          List[dict]         # full log: {agent, content, round, status, decision}
    speaking_queue:    List[str]          # FIFO — who speaks next
    agent_turn_count:  Dict[str, int]     # turns taken per agent (loop guard)
    round:             int                # global turn counter

    # ── Outcome ───────────────────────────────────────────
    status:            Literal["active", "done"]
    raw_decisions:     List[str]          # DECISION: lines written by agents
    final_decision:    Optional[str]      # extracted by extractor node