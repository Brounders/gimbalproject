"""Integration tests for guarded ActionPolicy behavior wiring (ALG-001 v1.1).

These tests verify the actual side-effect of `_apply_action_policy_behavior`
on a TrackerPipeline-like object without constructing the full pipeline
(which would require a YOLO model + cv2 capture).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from uav_tracker.tracking.action_policy import (
    BEHAVIOR_FORCE_DROP,
    BEHAVIOR_OBSERVE,
    BEHAVIOR_TELEMETRY_ONLY,
    TrackingAction,
)
from uav_tracker.tracking.evidence import TargetBelief

# Pull the bound method without instantiating TrackerPipeline (avoids cv2/YOLO).
from uav_tracker.pipeline import TrackerPipeline


class _FakeManager:
    """Mimics the public TargetManager release API used by the guard."""
    def __init__(self, active_id=None):
        self.active_id = active_id
        self._release_calls = 0

    def release_active(self) -> bool:
        if self.active_id is None:
            return False
        self.active_id = None
        self._release_calls += 1
        return True


class _FakeLockTracker:
    def __init__(self):
        self.reset_calls = 0

    def reset(self):
        self.reset_calls += 1


class _FakeCfg:
    def __init__(self, behavior_enabled=False):
        self.ACTION_POLICY_BEHAVIOR_ENABLED = bool(behavior_enabled)


def _make_pipeline_stub(behavior_enabled=False, active_id=42):
    """Build a minimal pipeline-like object with the bound _apply_action_policy_behavior."""
    stub = SimpleNamespace()
    stub.cfg = _FakeCfg(behavior_enabled=behavior_enabled)
    stub.manager = _FakeManager(active_id=active_id)
    stub.lock_tracker = _FakeLockTracker()
    stub._behavior_drop_count = 0
    # Bind the unbound function.
    stub._apply_action_policy_behavior = (
        TrackerPipeline._apply_action_policy_behavior.__get__(stub, type(stub))
    )
    return stub


# ---------------------------------------------------------------------------
# Default OFF — telemetry-only path.
# ---------------------------------------------------------------------------


class TestBehaviorOffDefaultPath:
    def test_drop_lock_does_not_clear_active_when_disabled(self):
        stub = _make_pipeline_stub(behavior_enabled=False, active_id=7)
        path = stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        assert path == BEHAVIOR_TELEMETRY_ONLY
        # Critical: pipeline must NOT touch existing TemplateLockTracker / TargetManager.
        assert stub.manager.active_id == 7
        assert stub.manager._release_calls == 0
        assert stub.lock_tracker.reset_calls == 0
        assert stub._behavior_drop_count == 0

    def test_keep_lock_disabled_no_effect(self):
        stub = _make_pipeline_stub(behavior_enabled=False, active_id=7)
        path = stub._apply_action_policy_behavior(TrackingAction.KEEP_LOCK)
        assert path == BEHAVIOR_TELEMETRY_ONLY
        assert stub.manager.active_id == 7

    def test_all_actions_disabled_have_no_side_effect(self):
        for action in TrackingAction:
            stub = _make_pipeline_stub(behavior_enabled=False, active_id=11)
            path = stub._apply_action_policy_behavior(action)
            assert path == BEHAVIOR_TELEMETRY_ONLY
            assert stub.manager.active_id == 11
            assert stub.lock_tracker.reset_calls == 0


# ---------------------------------------------------------------------------
# Enabled — guarded behavior, drop-only effect.
# ---------------------------------------------------------------------------


class TestBehaviorEnabledGuardedPath:
    def test_enabled_drop_lock_clears_active_and_resets_tracker(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=7)
        path = stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        assert path == BEHAVIOR_FORCE_DROP
        assert stub.manager.active_id is None
        assert stub.lock_tracker.reset_calls == 1
        assert stub._behavior_drop_count == 1

    def test_enabled_drop_lock_with_no_active_target_still_resets_lock(self):
        """Lock tracker must be reset even if active_id is already None."""
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=None)
        path = stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        assert path == BEHAVIOR_FORCE_DROP
        # release_active returned False (no active id) but lock_tracker was reset.
        assert stub.manager._release_calls == 0
        assert stub.lock_tracker.reset_calls == 1
        assert stub._behavior_drop_count == 1

    def test_enabled_keep_lock_does_not_extend_hold(self):
        """Critical guarantee: enabling behavior must never extend hold."""
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=7)
        path = stub._apply_action_policy_behavior(TrackingAction.KEEP_LOCK)
        assert path == BEHAVIOR_OBSERVE
        # No clears, no resets — pre-existing TargetManager/LockTracker path runs.
        assert stub.manager.active_id == 7
        assert stub.manager._release_calls == 0
        assert stub.lock_tracker.reset_calls == 0

    def test_enabled_local_validate_observe(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=3)
        assert stub._apply_action_policy_behavior(TrackingAction.LOCAL_VALIDATE) == BEHAVIOR_OBSERVE
        assert stub.manager.active_id == 3

    def test_enabled_expand_roi_observe(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=3)
        assert stub._apply_action_policy_behavior(TrackingAction.EXPAND_ROI) == BEHAVIOR_OBSERVE

    def test_enabled_global_rescan_observe(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=3)
        assert stub._apply_action_policy_behavior(TrackingAction.GLOBAL_RESCAN) == BEHAVIOR_OBSERVE

    def test_enabled_redetect_observe(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=3)
        assert stub._apply_action_policy_behavior(TrackingAction.REDETECT) == BEHAVIOR_OBSERVE

    def test_drop_count_accumulates(self):
        stub = _make_pipeline_stub(behavior_enabled=True, active_id=7)
        stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        stub._apply_action_policy_behavior(TrackingAction.DROP_LOCK)
        assert stub._behavior_drop_count == 3


# ---------------------------------------------------------------------------
# TargetBelief modality (sensor-aware) — backward compat + IR-first semantics.
# ---------------------------------------------------------------------------


class TestTargetBeliefModality:
    def test_default_modality_is_rgb(self):
        belief = TargetBelief.empty()
        assert belief.modality == 'rgb'

    def test_explicit_ir_modality_preserved(self):
        belief = TargetBelief(
            active_id=1,
            bbox=(0, 0, 10, 10),
            last_good_bbox=(0, 0, 10, 10),
            velocity=(0.0, 0.0),
            scale=1.0,
            p_present=0.9,
            p_same_target=0.9,
            reliability=0.8,
            lost_age=0,
            source='lock',
            modality='ir',
        )
        assert belief.modality == 'ir'

    def test_night_diagnostic_modality_preserved(self):
        """RGB-night is diagnostic-only per IR-first night gate decision."""
        belief = TargetBelief(
            active_id=1,
            bbox=(0, 0, 10, 10),
            last_good_bbox=(0, 0, 10, 10),
            velocity=(0.0, 0.0),
            scale=1.0,
            p_present=0.5,
            p_same_target=0.5,
            reliability=0.4,
            lost_age=2,
            source='night',
            modality='night',
        )
        assert belief.modality == 'night'

    def test_modality_field_defaults_when_omitted(self):
        """Backward compatibility: existing call sites without modality still work."""
        belief = TargetBelief(
            active_id=1,
            bbox=(0, 0, 10, 10),
            last_good_bbox=(0, 0, 10, 10),
            velocity=(0.0, 0.0),
            scale=1.0,
            p_present=0.9,
            p_same_target=0.9,
            reliability=0.8,
            lost_age=0,
            source='yolo',
        )
        assert belief.modality == 'rgb'


# ---------------------------------------------------------------------------
# FrameOutput backward compatibility — new fields default-safe.
# ---------------------------------------------------------------------------


class TestFrameOutputBackwardCompat:
    def test_frame_output_constructs_with_old_kwargs(self):
        """Existing FrameOutput(...) call sites without new fields still work."""
        from uav_tracker.display.frame_result import FrameOutput
        fo = FrameOutput(
            frame=None,
            fps=30.0,
            active_id=None,
            active_source='-',
            active_bbox=None,
            target_count=0,
            visible_target_count=0,
            mode='SCAN',
            frame_index=0,
            scan_strategy='GLOBAL-SCAN',
            gt_visible=False,
            gt_iou=0.0,
            lock_score=0.0,
            display_confidence=0.0,
            continuity_score=0.0,
            active_presence_rate=0.0,
            active_id_changes=0,
            median_reacquire_frames=0.0,
            lock_events=[],
            lock_switch_count=0,
            lock_switches_per_min=0.0,
            lock_event_counts={},
            budget_level=0,
            budget_load=0.0,
            budget_frame_ms=0.0,
            roi_budget_candidates=0,
            night_skip=0,
            timings_ms={},
        )
        # New fields must default safely.
        assert fo.target_modality == 'rgb'
        assert fo.decision_path == 'telemetry_only'
        assert fo.tracking_action == 'global_rescan'
        assert fo.behavior_drop_count == 0

    def test_frame_output_accepts_new_fields(self):
        from uav_tracker.display.frame_result import FrameOutput
        fo = FrameOutput(
            frame=None,
            fps=30.0,
            active_id=None,
            active_source='-',
            active_bbox=None,
            target_count=0,
            visible_target_count=0,
            mode='SCAN',
            frame_index=0,
            scan_strategy='GLOBAL-SCAN',
            gt_visible=False,
            gt_iou=0.0,
            lock_score=0.0,
            display_confidence=0.0,
            continuity_score=0.0,
            active_presence_rate=0.0,
            active_id_changes=0,
            median_reacquire_frames=0.0,
            lock_events=[],
            lock_switch_count=0,
            lock_switches_per_min=0.0,
            lock_event_counts={},
            budget_level=0,
            budget_load=0.0,
            budget_frame_ms=0.0,
            roi_budget_candidates=0,
            night_skip=0,
            timings_ms={},
            target_modality='ir',
            decision_path='behavior_guarded:observe',
            behavior_drop_count=3,
        )
        assert fo.target_modality == 'ir'
        assert fo.decision_path == 'behavior_guarded:observe'
        assert fo.behavior_drop_count == 3
