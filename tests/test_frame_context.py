"""Tests for FrameContext dataclass."""
import pytest
from uav_tracker.frame_context import FrameContext


class TestFrameContext:
    def test_fields_accessible(self):
        ctx = FrameContext(frame_id=5, timestamp=1.23, scene_mode="night", budget_ok=True)
        assert ctx.frame_id == 5
        assert ctx.timestamp == 1.23
        assert ctx.scene_mode == "night"
        assert ctx.budget_ok is True

    def test_frozen_immutable(self):
        ctx = FrameContext(frame_id=0, timestamp=0.0, scene_mode="day", budget_ok=False)
        with pytest.raises((AttributeError, TypeError)):
            ctx.frame_id = 1  # type: ignore[misc]

    def test_equality(self):
        a = FrameContext(frame_id=1, timestamp=0.5, scene_mode="ir", budget_ok=True)
        b = FrameContext(frame_id=1, timestamp=0.5, scene_mode="ir", budget_ok=True)
        assert a == b

    def test_scene_modes(self):
        for mode in ("day", "night", "ir", "auto"):
            ctx = FrameContext(frame_id=0, timestamp=0.0, scene_mode=mode, budget_ok=True)
            assert ctx.scene_mode == mode
