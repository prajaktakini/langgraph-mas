"""
config/__init__.py
Loads agents.yaml + settings.yaml and exposes typed objects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_CONFIG_DIR = Path(__file__).parent


# ─────────────────────────────────────────────────────────
# TYPED CONFIG OBJECTS
# ─────────────────────────────────────────────────────────

@dataclass
class AgentConfig:
    name:          str
    personality:   str
    role:          str = "Agent"
    first_speaker: bool = False


@dataclass
class LLMConfig:
    provider:    str   = "openai"
    model:       str   = "gpt-4o-mini"
    temperature: float = 0.85


@dataclass
class SimConfig:
    task:               str   = "Discuss and reach a decision."
    hard_cap:           int   = 24
    max_turns_per_agent: int  = 5
    recursion_limit:    int   = 500


@dataclass
class LogConfig:
    log_dir:       str = "logs"
    console_level: str = "INFO"
    file_level:    str = "DEBUG"


@dataclass
class Settings:
    agents:     list[AgentConfig]
    sim:        SimConfig
    llm:        LLMConfig
    logging:    LogConfig

    # ── convenience ──────────────────────────────────────
    @property
    def agent_names(self) -> list[str]:
        return [a.name for a in self.agents]

    @property
    def personalities(self) -> dict[str, str]:
        return {a.name: a.personality for a in self.agents}

    @property
    def roles(self) -> dict[str, str]:
        return {a.name: a.role for a in self.agents}

    @property
    def first_speaker(self) -> str:
        for a in self.agents:
            if a.first_speaker:
                return a.name
        return self.agents[0].name   # fallback


# ─────────────────────────────────────────────────────────
# LOADER
# ─────────────────────────────────────────────────────────

def load_settings(
    agents_path:   Optional[Path] = None,
    settings_path: Optional[Path] = None,
) -> Settings:
    """
    Load config from YAML files.
    Paths default to config/agents.yaml and config/settings.yaml.
    """
    agents_path   = agents_path   or _CONFIG_DIR / "agents.yaml"
    settings_path = settings_path or _CONFIG_DIR / "settings.yaml"

    with open(agents_path,   encoding="utf-8") as f:
        agents_raw = yaml.safe_load(f)

    with open(settings_path, encoding="utf-8") as f:
        settings_raw = yaml.safe_load(f)

    # ── Parse agents ─────────────────────────────────────
    agents = [
        AgentConfig(
            name          = a["name"],
            personality   = a["personality"],
            role          = a.get("role", "Agent"),
            first_speaker = a.get("first_speaker", False),
        )
        for a in agents_raw["agents"]
    ]

    if not agents:
        raise ValueError("agents.yaml must define at least 2 agents.")
    if len(agents) < 2:
        raise ValueError("MAS requires at least 2 agents.")

    # ── Parse settings ────────────────────────────────────
    s   = settings_raw.get("simulation", {})
    l   = settings_raw.get("llm", {})
    lg  = settings_raw.get("logging", {})

    return Settings(
        agents  = agents,
        sim     = SimConfig(
            task                = s.get("task", "Discuss and reach a decision."),
            hard_cap            = int(s.get("hard_cap", 24)),
            max_turns_per_agent = int(s.get("max_turns_per_agent", 5)),
            recursion_limit     = int(s.get("recursion_limit", 500)),
        ),
        llm     = LLMConfig(
            provider    = l.get("provider", "openai"),
            model       = l.get("model", "gpt-4o-mini"),
            temperature = float(l.get("temperature", 0.85)),
        ),
        logging = LogConfig(
            log_dir       = lg.get("log_dir", "logs"),
            console_level = lg.get("console_level", "INFO"),
            file_level    = lg.get("file_level", "DEBUG"),
        ),
    )


# ── Module-level singleton — import this everywhere ──────
settings = load_settings()