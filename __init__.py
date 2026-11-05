"""Hermes lifecycle plugin that backs up locally authored Agent Skills."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TIMER: threading.Timer | None = None
_LOCK = threading.Lock()
_RUNNING = False
_PENDING: dict[str, str] | None = None


def _hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        return Path(local) / "hermes" if local else Path.home() / "AppData" / "Local" / "hermes"
    return Path.home() / ".hermes"


def _log(entry: dict[str, Any]) -> None:
    try:
        log_path = _hermes_home() / "logs" / "agent-skills-publisher.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        # The lifecycle observer must never break a Hermes session.
        pass


def _schedule(delay: float = 1.5) -> None:
    global _TIMER
    with _LOCK:
        if _RUNNING:
            return
        if _TIMER is not None:
            _TIMER.cancel()
        _TIMER = threading.Timer(delay, _publish_pending)
        _TIMER.daemon = False
        _TIMER.start()


def _publish_pending() -> None:
    global _TIMER, _RUNNING, _PENDING
    with _LOCK:
        _TIMER = None
        if _RUNNING or _PENDING is None:
            return
        event = _PENDING
        _PENDING = None
        _RUNNING = True

    try:
        repo = Path(__file__).resolve().parent
        script = repo / "scripts" / "publish_skills.py"
        if not script.is_file():
            raise FileNotFoundError(f"publisher script missing: {script}")
        home = _hermes_home()
        command = [
            sys.executable,
            str(script),
            "--repo", str(repo),
            "--home", str(home),
            "--event-action", event["action"],
            "--skill-name", event["skill_name"],
        ]
        environment = os.environ.copy()
        environment["HERMES_HOME"] = str(home)
        result = subprocess.run(
            command,
            cwd=str(repo),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            check=False,
        )
        _log({
            "action": event["action"],
            "skill_name": event["skill_name"],
            "provenance": event["provenance"],
            "returncode": result.returncode,
            "stdout": result.stdout.strip()[-12000:],
            "stderr": result.stderr.strip()[-4000:],
        })
    except Exception as exc:
        _log({"error": str(exc), "event": event})
    finally:
        with _LOCK:
            _RUNNING = False
            pending = _PENDING is not None
        if pending:
            _schedule(0.2)


def on_skill_lifecycle(
    action: str = "",
    skill_name: str = "",
    provenance: str = "",
    **_: Any,
) -> None:
    """Queue a debounced publish after a skill is authored or edited."""
    if action not in {"created", "patched", "edited"}:
        return
    global _PENDING
    with _LOCK:
        _PENDING = {
            "action": str(action),
            "skill_name": str(skill_name),
            "provenance": str(provenance),
        }
        running = _RUNNING
    if not running:
        _schedule()


def register(ctx: Any) -> None:
    ctx.register_hook("on_skill_lifecycle", on_skill_lifecycle)
