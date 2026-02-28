"""
utils/logger.py
Centralised logging setup — call setup_logging() once at startup.
Returns the session ID and log file paths for use by other modules.
Creates a dedicated folder per simulation session:
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LogPaths:
    session_id:  str
    session_dir: Path   # logs/session_YYYYMMDD_HHMMSS/
    txt:         Path   # session.txt
    jsonl:       Path   # session.jsonl
    config_snap: Path   # config.yaml snapshot


def setup_logging(
    log_dir:       str = "logs",
    console_level: str = "INFO",
    file_level:    str = "DEBUG",
    agents_path:   Path = Path("config/agents.yaml"),
    settings_path: Path = Path("config/settings.yaml"),
) -> LogPaths:
    """
    Creates logs/session_<timestamp>/ and sets up handlers.
    Also copies agents.yaml + settings.yaml into the session folder
    so every run is fully reproducible.
    """
    session_id  = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = Path(log_dir) / f"session_{session_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    txt_path    = session_dir / "session.txt"
    jsonl_path  = session_dir / "session.jsonl"
    config_snap = session_dir / "config.yaml"

    # ── Snapshot the config files used for this run ──────
    _snapshot_configs(agents_path, settings_path, config_snap)

    # ── Logging handlers ──────────────────────────────────
    _console = logging.StreamHandler()
    _console.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    _console.setFormatter(logging.Formatter(
        "%(asctime)s | %(message)s", datefmt="%H:%M:%S"
    ))

    _file = logging.FileHandler(txt_path, encoding="utf-8")
    _file.setLevel(getattr(logging, file_level.upper(), logging.DEBUG))
    _file.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
    ))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(_console)
    root.addHandler(_file)

    return LogPaths(
        session_id  = session_id,
        session_dir = session_dir,
        txt         = txt_path,
        jsonl       = jsonl_path,
        config_snap = config_snap,
    )


def _snapshot_configs(
    agents_path:   Path,
    settings_path: Path,
    output_path:   Path,
) -> None:
    """
    Merge agents.yaml + settings.yaml into a single config.yaml snapshot
    inside the session folder so every run is self-contained.
    """
    lines = ["# ── agents.yaml ──────────────────────────\n"]
    if agents_path.exists():
        lines.append(agents_path.read_text(encoding="utf-8"))
    else:
        lines.append("# (file not found)\n")

    lines.append("\n# ── settings.yaml ────────────────────────\n")
    if settings_path.exists():
        lines.append(settings_path.read_text(encoding="utf-8"))
    else:
        lines.append("# (file not found)\n")

    output_path.write_text("".join(lines), encoding="utf-8")
