from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class UIState(str, Enum):
    IDLE = 'idle'
    CHECKING = 'checking'
    RUNNING = 'running'
    LOCK = 'lock'
    LOST = 'lost'
    EVALUATION = 'evaluation'
    ERROR = 'error'


@dataclass
class UIStateMachine:
    state: UIState = UIState.IDLE
    history: list[UIState] = field(default_factory=list)

    def set(self, state: UIState) -> None:
        if self.state != state:
            self.history.append(self.state)
            self.state = state

    def can_start(self) -> bool:
        return self.state in {UIState.IDLE, UIState.LOST, UIState.ERROR}

    def can_stop(self) -> bool:
        return self.state in {UIState.CHECKING, UIState.RUNNING, UIState.LOCK, UIState.LOST, UIState.EVALUATION}

    def can_evaluate(self) -> bool:
        return self.state in {UIState.IDLE, UIState.LOST, UIState.ERROR}

    def panel_allowed(self, panel_key: str) -> bool:
        # Panels are context-aware; pinned panels can still be forced visible by PanelManager.
        policy = {
            'monitoring': {UIState.CHECKING, UIState.RUNNING, UIState.LOCK, UIState.LOST, UIState.EVALUATION, UIState.ERROR},
            'target': {UIState.RUNNING, UIState.LOCK, UIState.LOST},
            'events': {UIState.CHECKING, UIState.RUNNING, UIState.LOCK, UIState.LOST, UIState.EVALUATION, UIState.ERROR},
            'params': {UIState.IDLE, UIState.CHECKING, UIState.RUNNING, UIState.LOCK, UIState.LOST, UIState.EVALUATION, UIState.ERROR},
            'expert': {UIState.IDLE, UIState.CHECKING, UIState.RUNNING, UIState.LOCK, UIState.LOST, UIState.EVALUATION, UIState.ERROR},
        }
        allowed = policy.get(panel_key)
        if not allowed:
            return True
        return self.state in allowed
