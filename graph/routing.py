"""
graph/routing.py
All conditional edge functions for the LangGraph.

Routing is kept here — separate from node logic — so the
graph topology can be understood at a glance in builder.py.
"""

from __future__ import annotations
from graph.state import MASState


def route_queue_manager(state: MASState) -> str:
    """
    After queue_manager runs, decide what happens next:
      - simulation is done (status or empty queue) → extractor
      - otherwise → agent
    """
    if state["status"] == "done":
        return "extractor"

    if state["speaking_queue"]:
        return "agent"

    # queue_manager should have handled empty queues,
    # but as a safe fallback:
    return "extractor"