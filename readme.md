# agent-society

A text-based multi-agent simulation framework built with LangGraph. Agents know each other, communicate freely, and reach collective decisions through emergent conversation.

---

## How It Works

Each agent is given an identity and personality. They take turns speaking, choosing who to address next, and collectively signal when a decision has been reached — no hardcoded turn order or voting phases.

```
Alice speaks → nominates Bob and Carol
Bob responds → nominates Alice
Carol challenges → nominates everyone
...
Agent signals DONE → extractor summarises the decision
```

---

## Project Structure

```
├── config/
│   ├── agents.yaml       ← define agents here
│   └── settings.yaml     ← task, LLM, turn limits
├── agents/
│   ├── base.py           ← Agent dataclass + registry
│   └── prompts.py        ← prompt builders
├── graph/
│   ├── state.py          ← shared simulation state
│   ├── nodes.py          ← agent, logger, queue_manager, extractor
│   ├── routing.py        ← conditional edge logic
│   └── builder.py        ← assembles the LangGraph
├── utils/
│   ├── logger.py         ← logging setup + session folder
│   ├── parser.py         ← parses LLM responses
│   └── io.py             ← JSONL writer
└── main.py               ← entrypoint
```

---

## Setup

```bash
conda create -n mas_env python=3.11
conda activate mas_env
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
```

---

## Configure

**Add or edit agents** in `config/agents.yaml`:
```yaml
agents:
  - name: Alice
    personality: Bold and visionary. Tends to take charge.
    role: Initiator
    first_speaker: true

  - name: Bob
    personality: Diplomatic. Builds consensus.
    role: Mediator
```

**Change the task** in `config/settings.yaml`:
```yaml
simulation:
  task: >
    Your group must elect one leader for an upcoming mission.
    Discuss and reach a collective decision.
```

---

## Run

```bash
python main.py
```

---

## Logs

Each run creates a timestamped folder:

```
logs/
└── session_20260227_222011/
    ├── session.txt     ← full conversation log
    ├── session.jsonl   ← structured JSON records
    └── config.yaml     ← exact config used for this run
```

---

## Switch to Claude

In `config/settings.yaml`:
```yaml
llm:
  provider: anthropic
  model: claude-opus-4-5
```

```bash
pip install langchain-anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```