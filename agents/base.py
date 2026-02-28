"""
agents/base.py
Agent dataclass and registry — loaded from config, not hardcoded.
"""

from __future__ import annotations
from dataclasses import dataclass
from config import Settings


@dataclass(frozen=True)
class Agent:
    """Immutable agent identity. Everything else lives in shared state."""
    name:        str
    personality: str
    role:        str


class AgentRegistry:
    """
    Loaded once from config. Acts as the source of truth for
    who exists in the simulation.
    """

    def __init__(self, settings: Settings) -> None:
        self._agents: dict[str, Agent] = {
            a.name: Agent(
                name        = a.name,
                personality = a.personality,
                role        = a.role,
            )
            for a in settings.agents
        }

    # ── Access ────────────────────────────────────────────

    def get(self, name: str) -> Agent:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not found in registry.")
        return self._agents[name]

    def all(self) -> list[Agent]:
        return list(self._agents.values())

    def names(self) -> list[str]:
        return list(self._agents.keys())

    def personalities(self) -> dict[str, str]:
        return {a.name: a.personality for a in self._agents.values()}

    def roles(self) -> dict[str, str]:
        return {a.name: a.role for a in self._agents.values()}

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents

    def __repr__(self) -> str:
        return f"AgentRegistry({self.names()})"