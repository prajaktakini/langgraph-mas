"""
graph/nodes.py
All LangGraph node functions.

Each node:
  - receives the full MASState
  - returns a PARTIAL dict (LangGraph merges it — never mutate state directly)
  - has exactly one responsibility

Nodes:
  agent_node        — runs one agent turn (discussion or vote)
  logger_node       — side-effect: writes last message to JSONL
  queue_manager     — pure logic: handles empty queue / hard cap
  extractor_node    — synthesises final decision via neutral LLM call
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic

from graph.state import MASState
from agents.prompts import build_agent_prompt, build_extractor_prompt
from utils.parser import parse_agent_response
from utils.io import append_jsonl, write_summary
from config import Settings

log = logging.getLogger("MAS.nodes")


# ─────────────────────────────────────────────────────────
# LLM FACTORY
# ─────────────────────────────────────────────────────────

_llm_cache: dict[str, object] = {}

def get_llm(settings: Settings):
    key = f"{settings.llm.provider}:{settings.llm.model}"
    if key not in _llm_cache:
        if settings.llm.provider == "openai":
            _llm_cache[key] = ChatOpenAI(
                model       = settings.llm.model,
                temperature = settings.llm.temperature,
            )
        elif settings.llm.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            _llm_cache[key] = ChatAnthropic(
                model       = settings.llm.model,
                temperature = settings.llm.temperature,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {settings.llm.provider}")
    return _llm_cache[key]


# ─────────────────────────────────────────────────────────
# NODE FACTORIES
# Each factory binds settings + paths, returns the actual node fn.
# This keeps node signatures compatible with LangGraph (state → dict).
# ─────────────────────────────────────────────────────────

def make_agent_node(settings: Settings):
    """
    Generic agent node — identity is read from speaking_queue, not the node.
    One node handles ALL agents → fully scalable.
    """
    llm = get_llm(settings)

    def agent_node(state: MASState) -> dict:
        if not state["speaking_queue"]:
            return {}

        agent = state["speaking_queue"][0]
        queue = state["speaking_queue"][1:]   # consume front (immutably)

        # ── Build prompt and call LLM ─────────────────────
        prompt = build_agent_prompt(agent, state, settings.sim.max_turns_per_agent)
        raw    = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        message, next_agents, is_done, decision = parse_agent_response(
            raw, state["agents"], agent
        )

        # ── Loop protection ───────────────────────────────
        filtered = [
            a for a in next_agents
            if state["agent_turn_count"].get(a, 0) < settings.sim.max_turns_per_agent
            and a != agent
        ]
        if not filtered and not is_done:
            log.warning(f"  ⚠  All nominated agents at turn cap → forcing DONE")
            is_done = True

        # ── Deduplicate queue (no echo chambers) ──────────
        existing    = set(queue)
        new_entries = [a for a in filtered if a not in existing]

        # ── Assemble return values ────────────────────────
        new_msg = {
            "agent":    agent,
            "content":  message,
            "round":    state["round"],
            "status":   "DONE" if is_done else "CONTINUE",
            "decision": decision,
        }
        new_turns = {
            **state["agent_turn_count"],
            agent: state["agent_turn_count"].get(agent, 0) + 1,
        }

        # ── Console log ───────────────────────────────────
        badge = "🔴 DONE" if is_done else "🟢 CONT"
        log.info(f"[t{state['round']:02d}] [{badge}] {agent}: {message}")
        if next_agents:
            arrow = ", ".join(filtered) or "none (capped)"
            log.info(f"         → NEXT: {arrow}")
        if decision:
            log.info(f"         → DECISION: {decision}")

        return {
            "messages":         state["messages"] + [new_msg],
            "speaking_queue":   queue + new_entries if not is_done else [],
            "agent_turn_count": new_turns,
            "round":            state["round"] + 1,
            "status":           "done" if is_done else "active",
            "raw_decisions":    state["raw_decisions"] + ([decision] if decision else []),
        }

    return agent_node


def make_logger_node(jsonl_path: Path):
    """
    Side-effect only: appends the last message to JSONL.
    Returns {} — never modifies state.
    """
    def logger_node(state: MASState) -> dict:
        if state["messages"]:
            append_jsonl(jsonl_path, state["messages"][-1])
        return {}

    return logger_node


def make_queue_manager_node(settings: Settings):
    """
    Pure logic — no LLM.
    Handles edge cases the agent node can't cleanly manage:
      1. Hard cap exceeded             → force done
      2. Queue empty, no decision yet  → inject least-heard agent
      3. All agents capped             → force done
    """
    def queue_manager_node(state: MASState) -> dict:
        if state["status"] == "done":
            return {}

        if state["round"] >= settings.sim.hard_cap:
            log.warning(f"  ⚠  Hard cap ({settings.sim.hard_cap}) reached → terminating")
            return {"status": "done", "speaking_queue": []}

        if not state["speaking_queue"]:
            counts     = state["agent_turn_count"]
            least      = min(state["agents"], key=lambda a: counts.get(a, 0))
            turns_left = settings.sim.max_turns_per_agent - counts.get(least, 0)

            if turns_left > 0:
                log.info(f"  ↩  Queue empty, no decision → injecting {least}")
                return {"speaking_queue": [least]}
            else:
                log.info("  ↩  All agents capped, queue empty → terminating")
                return {"status": "done"}

        return {}

    return queue_manager_node


def make_extractor_node(settings: Settings, jsonl_path: Path, txt_path: Path):
    """
    Synthesises the final decision from the full conversation.
    Uses a neutral, persona-free LLM call.
    """
    llm = get_llm(settings)

    def extractor_node(state: MASState) -> dict:
        log.info("─" * 55)
        log.info("EXTRACTING FINAL DECISION...")

        prompt   = build_extractor_prompt(state)
        decision = llm.invoke([HumanMessage(content=prompt)]).content.strip()

        updated = {**state, "final_decision": decision}
        write_summary(updated, jsonl_path, txt_path)

        return {"final_decision": decision}

    return extractor_node