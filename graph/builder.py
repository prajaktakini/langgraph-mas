"""
graph/builder.py
Assembles all nodes and edges into a compiled LangGraph.

Graph topology:
                          ┌─────────────────────────┐
                          │                         │
  [START] → agent → logger → queue_manager ──────► agent (loop)
                                           └──────► extractor → [END]
"""

from __future__ import annotations
from pathlib import Path

from langgraph.graph import StateGraph, END

from graph.state import MASState
from graph.nodes import (
    make_agent_node,
    make_logger_node,
    make_queue_manager_node,
    make_extractor_node,
)
from graph.routing import route_queue_manager
from config import Settings


def build_graph(settings: Settings, jsonl_path: Path, txt_path: Path):
    """
    Build and compile the LangGraph.

    All node factories receive settings + paths here — nodes
    themselves stay clean (state → dict signatures).
    """
    g = StateGraph(MASState)

    # ── Register nodes ────────────────────────────────────
    g.add_node("agent",         make_agent_node(settings))
    g.add_node("logger",        make_logger_node(jsonl_path))
    g.add_node("queue_manager", make_queue_manager_node(settings))
    g.add_node("extractor",     make_extractor_node(settings, jsonl_path, txt_path))

    # ── Entry point ───────────────────────────────────────
    g.set_entry_point("agent")

    # ── Edges ─────────────────────────────────────────────
    g.add_edge("agent",  "logger")
    g.add_edge("logger", "queue_manager")

    g.add_conditional_edges(
        "queue_manager",
        route_queue_manager,
        {
            "agent":     "agent",
            "extractor": "extractor",
        },
    )

    g.add_edge("extractor", END)

    return g.compile()