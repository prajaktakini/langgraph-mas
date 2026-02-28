"""
agents/prompts.py
Builds LLM prompts for the discussion and extraction phases.
Kept separate so you can swap prompt strategies without touching graph logic.
"""

from __future__ import annotations
from graph.state import MASState

# ─────────────────────────────────────────────────────────
# RESPONSE FORMAT (injected into every agent prompt)
# ─────────────────────────────────────────────────────────

RESPONSE_FORMAT = """\
Respond in EXACTLY this format — no extra lines, no preamble:

MESSAGE: <your message to the group>
NEXT: <comma-separated names of who should speak next>
STATUS: <CONTINUE or DONE>
DECISION: <the group's final decision if STATUS is DONE, else leave blank>
"""


# ─────────────────────────────────────────────────────────
# DISCUSSION PROMPT
# ─────────────────────────────────────────────────────────

def build_agent_prompt(agent: str, state: MASState, max_turns_per_agent: int) -> str:
    """Full prompt for one agent turn during discussion."""

    # Society block — every agent sees who exists and their roles
    society_lines = []
    for a in state["agents"]:
        tag  = " (you)" if a == agent else ""
        role = state["roles"].get(a, "Agent")
        society_lines.append(f"  {a}{tag} [{role}]: {state['personalities'][a]}")
    society_block = "\n".join(society_lines)

    # Conversation history
    if state["messages"]:
        history_lines = [
            f"  [t{m['round']:02d}] {m['agent']}: {m['content']}"
            for m in state["messages"]
        ]
        history_block = "\n".join(history_lines)
    else:
        history_block = "  (you speak first — open the discussion)"

    # Availability block — shows how many turns each other agent has left
    others = [a for a in state["agents"] if a != agent]
    avail_lines = []
    for a in others:
        left = max_turns_per_agent - state["agent_turn_count"].get(a, 0)
        avail_lines.append(f"  {a}: {left} turn{'s' if left != 1 else ''} remaining")
    availability_block = "\n".join(avail_lines)

    return f"""You are {agent}.
Personality: {state['personalities'][agent]}
Role: {state['roles'].get(agent, 'Agent')}

━━ SOCIETY ━━
{society_block}

━━ TASK ━━
{state['task'].strip()}

━━ CONVERSATION SO FAR ━━
{history_block}

━━ YOUR TURN (turn {state['round'] + 1}) ━━
Available agents to nominate next:
{availability_block}

Nomination rules:
  • Nominate 1 or more agents whose input would be valuable RIGHT NOW.
  • Do NOT nominate agents with 0 turns left.
  • Do NOT nominate only yourself.
  • Set STATUS: DONE only when there is clear group consensus — not just your preference.
    If done, fill in DECISION with the final outcome in one sentence.

{RESPONSE_FORMAT}"""


# ─────────────────────────────────────────────────────────
# EXTRACTOR PROMPT
# ─────────────────────────────────────────────────────────

def build_extractor_prompt(state: MASState) -> str:
    """Neutral, persona-free prompt used by the extractor node."""

    history = "\n".join(
        f"  {m['agent']}: {m['content']}"
        for m in state["messages"]
    )
    proposals = (
        "\n".join(f"  - {d}" for d in state["raw_decisions"])
        if state["raw_decisions"] else "  (no explicit proposals recorded)"
    )

    return f"""A group of agents held a structured discussion about the following task:

TASK:
{state['task'].strip()}

FULL CONVERSATION:
{history}

DECISION PROPOSALS MADE DURING DISCUSSION:
{proposals}

Based on the conversation above, what is the final collective decision?
Reply in exactly one clear sentence.
If no consensus was reached, say: "No consensus was reached: <brief summary of positions>."
"""