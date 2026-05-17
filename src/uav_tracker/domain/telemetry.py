from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, TextIO

from .types import FrameResult


class JsonlTelemetryWriter:
    """Buffered JSONL writer for frame-level telemetry.

    The writer is deliberately small and optional.  If it is not constructed,
    the pipeline behavior is unchanged.
    """

    def __init__(self, path: str | Path, *, flush_every: int = 30) -> None:
        self.path = Path(path)
        self.flush_every = max(1, int(flush_every))
        self._handle: TextIO | None = None
        self._pending = 0

    def __enter__(self) -> "JsonlTelemetryWriter":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def open(self) -> None:
        if self._handle is not None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def write_frame(self, result: FrameResult) -> None:
        if self._handle is None:
            self.open()
        assert self._handle is not None
        self._handle.write(json.dumps({"event": "frame_result", **result.to_dict()}, ensure_ascii=False) + "\n")
        self._pending += 1
        if self._pending >= self.flush_every:
            self.flush()

    def write_event(self, event: str, payload: dict) -> None:
        if self._handle is None:
            self.open()
        assert self._handle is not None
        self._handle.write(json.dumps({"event": event, **payload}, ensure_ascii=False) + "\n")
        self._pending += 1
        if self._pending >= self.flush_every:
            self.flush()

    def flush(self) -> None:
        if self._handle is None:
            return
        self._handle.flush()
        self._pending = 0

    def close(self) -> None:
        if self._handle is None:
            return
        self.flush()
        self._handle.close()
        self._handle = None


class JsonlTelemetryReader:
    """Read-only iterator over frame_result events in a JSONL telemetry file."""

    def __init__(self, path: str | Path, *, strict: bool = False) -> None:
        self._path = Path(path)
        self._strict = strict

    def __iter__(self) -> Iterator[FrameResult]:
        with self._path.open("r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    if self._strict:
                        raise ValueError(f"JSON decode error at line {lineno}: {line[:80]!r}")
                    continue
                if not isinstance(obj, dict) or obj.get("event") != "frame_result":
                    continue
                try:
                    yield FrameResult.from_dict(obj)
                except Exception as exc:
                    if self._strict:
                        raise ValueError(f"FrameResult parse error at line {lineno}: {exc}") from exc
                    continue
