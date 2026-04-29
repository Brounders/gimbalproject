"""RuntimeConfigView — read-only proxy over Config with per-session overrides.

Solves BUG-001: auto-scene previously mutated the shared Config object directly,
creating a race condition between the GUI thread (reading cfg) and TrackerWorker
(writing cfg). RuntimeConfigView stores overrides in a separate dict, leaving
the base Config object intact.

Usage::

    view = RuntimeConfigView(base_cfg)
    view = view.with_overrides(CONF_THRESH=0.12, NIGHT_MOT_THRESH=12)
    value = view.CONF_THRESH  # returns override or falls back to base
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeConfigView:
    """Immutable-safe proxy: reads overrides first, falls back to base Config.

    The base Config is never mutated. Use ``with_overrides()`` to produce a new
    view with updated values — the original view remains unchanged.
    """

    _base: Any  # Config instance (typed as Any to avoid circular import)
    _overrides: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails (i.e. not _base/_overrides)
        if name.startswith("_"):
            raise AttributeError(name)
        overrides = object.__getattribute__(self, "_overrides")
        if name in overrides:
            return overrides[name]
        base = object.__getattribute__(self, "_base")
        return getattr(base, name)

    def with_overrides(self, **kwargs: Any) -> "RuntimeConfigView":
        """Return a new view with merged overrides. Original is unchanged."""
        base = object.__getattribute__(self, "_base")
        existing = object.__getattribute__(self, "_overrides")
        return RuntimeConfigView(base, {**existing, **kwargs})

    def active_overrides(self) -> dict[str, Any]:
        """Return a copy of the current override dict (for inspection/logging)."""
        return dict(object.__getattribute__(self, "_overrides"))
