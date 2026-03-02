from __future__ import annotations

import json
import pathlib
import threading
from datetime import datetime, timezone
from typing import Any


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_lines(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as fh:
        return sum(1 for _ in fh)


class EventSpoolWriter:
    """Append-only NDJSON writer with monotonic per-file sequence."""

    def __init__(self, run_id: str, spool_path: pathlib.Path) -> None:
        self.run_id = run_id
        self.spool_path = spool_path
        self.spool_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq_state_path = self.spool_path.parent / "seq.state"
        self._seq = self._load_seq()
        self._fh = self.spool_path.open("a", encoding="utf-8")

    def _load_seq(self) -> int:
        if self._seq_state_path.exists():
            try:
                return int(self._seq_state_path.read_text(encoding="utf-8").strip() or "0")
            except ValueError:
                return 0
        # Fallback for first run before seq.state exists.
        return _count_lines(self.spool_path)

    def _persist_seq(self, seq: int) -> None:
        self._seq_state_path.write_text(str(seq), encoding="utf-8")

    def emit(self, source: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._seq += 1
            seq = self._seq
            evt = {
                "schema_version": "1.0",
                "event_id": f"{self.run_id}-{seq:08d}",
                "ts": _utc_iso(),
                "run_id": self.run_id,
                "source": source,
                "event_type": event_type,
                "idempotency_key": f"run:{self.run_id}:src:{source}:seq:{seq:08d}",
                "payload": payload,
            }
            self._fh.write(json.dumps(evt, ensure_ascii=False) + "\n")
            self._fh.flush()
            self._persist_seq(seq)
            return evt

    def close(self) -> None:
        self._fh.close()
