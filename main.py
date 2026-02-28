"""
main.py
Entrypoint for the Multi-Agent Social Simulation.

Usage:
    python main.py
    python main.py --agents config/agents.yaml --settings config/settings.yaml
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from config import load_settings
from graph.builder import build_graph
from graph.state import MASState
from utils.logger import setup_logging

log = logging.getLogger("MAS")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a multi-agent social simulation.")
    p.add_argument(
        "--agents",
        type=Path,
        default=Path("config/agents.yaml"),
        help="Path to agents config YAML (default: config/agents.yaml)",
    )
    p.add_argument(
        "--settings",
        type=Path,
        default=Path("config/settings.yaml"),
        help="Path to settings YAML (default: config/settings.yaml)",
    )
    return p.parse_args()


def run(agents_path: Path, settings_path: Path) -> MASState:
    # ── Load config ───────────────────────────────────────
    settings = load_settings(agents_path, settings_path)

    # ── Set up logging + session folder ───────────────────
    log_paths = setup_logging(
        log_dir       = settings.logging.log_dir,
        console_level = settings.logging.console_level,
        file_level    = settings.logging.file_level,
        agents_path   = agents_path,
        settings_path = settings_path,
    )

    # ── Print startup banner ──────────────────────────────
    log.info("=" * 55)
    log.info(f"MAS SIMULATION  session={log_paths.session_id}")
    log.info(f"Session folder : {log_paths.session_dir}")
    log.info(f"Agents  : {', '.join(settings.agent_names)}")
    log.info(f"Task    : {settings.sim.task.strip()[:80]}...")
    log.info(f"LLM     : {settings.llm.provider}/{settings.llm.model}")
    log.info(f"Cap     : {settings.sim.hard_cap} turns total, "
             f"{settings.sim.max_turns_per_agent} per agent")
    log.info("=" * 55)

    # ── Build initial state ───────────────────────────────
    initial: MASState = {
        "agents":           settings.agent_names,
        "personalities":    settings.personalities,
        "roles":            settings.roles,
        "task":             settings.sim.task,
        "messages":         [],
        "speaking_queue":   [settings.first_speaker],
        "agent_turn_count": {},
        "round":            0,
        "status":           "active",
        "raw_decisions":    [],
        "final_decision":   None,
    }

    # ── Build and run graph ───────────────────────────────
    graph  = build_graph(settings, log_paths.jsonl, log_paths.txt)
    result = graph.invoke(
        initial,
        {"recursion_limit": settings.sim.recursion_limit},
    )

    return result


if __name__ == "__main__":
    args   = parse_args()
    result = run(args.agents, args.settings)

    print(f"\n{'=' * 55}")
    print(f"FINAL DECISION: {result['final_decision']}")
    print(f"{'=' * 55}")