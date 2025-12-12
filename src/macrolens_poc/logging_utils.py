from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RunContext:
    run_id: str
    started_at_utc: datetime


def new_run_context() -> RunContext:
    return RunContext(run_id=str(uuid.uuid4()), started_at_utc=datetime.now(timezone.utc))


def default_log_path(logs_dir: Path, now_utc: Optional[datetime] = None) -> Path:
    ts = now_utc or datetime.now(timezone.utc)
    return logs_dir / f"run-{ts.strftime('%Y%m%d')}.jsonl"


class JsonlLogger:
    """Minimal JSONL logger.

    Writes one JSON object per line.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def run_summary_event(*, ctx: RunContext, status_counts: Dict[str, int]) -> Dict[str, Any]:
    ended_at_utc = datetime.now(timezone.utc)
    duration_s = (ended_at_utc - ctx.started_at_utc).total_seconds()

    return {
        "event": "run_summary",
        "run_id": ctx.run_id,
        "started_at": ctx.started_at_utc.isoformat(),
        "ended_at": ended_at_utc.isoformat(),
        "duration_s": duration_s,
        "status_counts": status_counts,
    }
