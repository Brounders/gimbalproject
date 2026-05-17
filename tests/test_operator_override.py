"""Operator target override backend tests.

The UI will eventually convert mouse input into OperatorTargetOverride.
These tests keep the first iteration GUI-free: a command enters the pipeline,
TargetManager creates/selects an operator-confirmed target, and telemetry
records what happened.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from uav_tracker.config import Config
from uav_tracker.detection_source import DetectionSource
from uav_tracker.pipeline import TrackerPipeline
from uav_tracker.tracking.operator_override import OperatorTargetOverride
from uav_tracker.tracking.target_manager import TargetManager
from uav_tracker.tracking.tracked_target import TrackedTarget


class _FakeLockTracker:
    def __init__(self):
        self.reset_count = 0
        self.sync_calls = []

    def reset(self):
        self.reset_count += 1

    def sync_from_bbox(self, frame, bbox):
        self.sync_calls.append((frame.shape, bbox))


def _target(tid: int, bbox: tuple[int, int, int, int]) -> TrackedTarget:
    x1, y1, x2, y2 = bbox
    return TrackedTarget(
        track_id=tid,
        bbox=bbox,
        raw_bbox=bbox,
        cx=(x1 + x2) / 2.0,
        cy=(y1 + y2) / 2.0,
        conf=0.4,
        cls_id=0,
        drone_score=0.7,
        hit_streak=2,
        source=DetectionSource.YOLO,
        trail=deque(maxlen=30),
    )


class TestOperatorTargetOverride:
    def test_click_expands_to_clipped_bbox(self):
        override = OperatorTargetOverride.from_click(5, 5, box_size=20)

        assert override.to_bbox((100, 200, 3)) == (0, 0, 15, 15)
        assert override.kind == 'click'

    def test_invalid_bbox_is_rejected(self):
        override = OperatorTargetOverride.from_bbox((30, 30, 20, 40))

        assert override.to_bbox((100, 100, 3)) is None


class TestTargetManagerOperatorOverride:
    def test_operator_override_creates_confirmed_active_target(self):
        cfg = Config(OPERATOR_OVERRIDE_ENABLED=True, LOCK_CONFIRM_FRAMES=5)
        mgr = TargetManager(cfg)

        result = mgr.apply_operator_override(
            OperatorTargetOverride.from_bbox((10, 20, 50, 70)),
            frame_shape=(100, 120, 3),
        )

        active = mgr.get_active_target()
        assert result.applied is True
        assert active is not None
        assert active.source == DetectionSource.OPERATOR
        assert active.raw_bbox == (10, 20, 50, 70)
        assert active.hit_streak == 5
        assert active.drone_score == 1.0
        assert mgr.active_id == result.active_id
        assert mgr.is_focus_mode() is True

    def test_operator_override_can_enter_verifying_without_instant_lock(self):
        cfg = Config(
            OPERATOR_OVERRIDE_ENABLED=True,
            OPERATOR_OVERRIDE_INSTANT_LOCK=False,
            LOCK_CONFIRM_FRAMES=5,
        )
        mgr = TargetManager(cfg)

        result = mgr.apply_operator_override(
            OperatorTargetOverride.from_bbox((10, 20, 50, 70)),
            frame_shape=(100, 120, 3),
        )

        active = mgr.get_active_target()
        assert result.applied is True
        assert result.status == 'verifying'
        assert active is not None
        assert active.source == DetectionSource.OPERATOR
        assert active.hit_streak < cfg.LOCK_CONFIRM_FRAMES
        assert mgr.active_id == result.active_id
        assert mgr.is_focus_mode() is False

    def test_operator_override_prefers_existing_target_inside_bbox(self):
        cfg = Config(OPERATOR_OVERRIDE_ENABLED=True, LOCK_CONFIRM_FRAMES=4)
        mgr = TargetManager(cfg)
        mgr.targets[42] = _target(42, (80, 80, 120, 120))

        result = mgr.apply_operator_override(
            OperatorTargetOverride.from_bbox((70, 70, 130, 130)),
            frame_shape=(200, 200, 3),
        )

        assert result.applied is True
        assert result.active_id == 42
        assert len(mgr.targets) == 1
        assert mgr.active_id == 42
        assert mgr.targets[42].source == DetectionSource.OPERATOR

    def test_confirm_active_as_operator_marks_existing_target(self):
        mgr = TargetManager(Config(LOCK_CONFIRM_FRAMES=3))
        mgr.targets[7] = _target(7, (10, 10, 30, 30))
        mgr.active_id = 7

        assert mgr.confirm_active_as_operator() is True

        active = mgr.get_active_target()
        assert active.source == DetectionSource.OPERATOR
        assert active.conf == 1.0
        assert active.drone_score == 1.0
        assert active.hit_streak == 3
        assert mgr.is_focus_mode() is True

    def test_operator_target_survives_lost_frames_until_operator_grace(self):
        cfg = Config(YOLO_LOST_MAX=2, OPERATOR_HOLD_GRACE_FRAMES=5)
        mgr = TargetManager(cfg)
        mgr.apply_operator_override(
            OperatorTargetOverride.from_bbox((10, 10, 30, 30)),
            frame_shape=(80, 80, 3),
        )
        tid = mgr.active_id

        for _ in range(5):
            mgr.age_targets(set())

        assert tid in mgr.targets
        mgr.age_targets(set())
        assert tid not in mgr.targets


class TestPipelineOperatorOverride:
    def _pipeline(self, enabled: bool) -> TrackerPipeline:
        pipe = TrackerPipeline.__new__(TrackerPipeline)
        pipe.cfg = Config(OPERATOR_OVERRIDE_ENABLED=enabled)
        pipe.manager = TargetManager(pipe.cfg)
        pipe.lock_tracker = _FakeLockTracker()
        pipe._pending_operator_override = None
        pipe._last_operator_override_status = 'none'
        pipe._last_operator_override_bbox = None
        pipe._operator_override_count = 0
        pipe.frame_counter = 1
        pipe.budget = type('Budget', (), {'effective_global_scan_interval': lambda self, frame_counter: 6})()
        return pipe

    def test_pipeline_queues_override_until_frame_shape_is_available(self):
        pipe = self._pipeline(enabled=True)
        override = OperatorTargetOverride.from_click(40, 50, box_size=30)

        assert pipe.request_operator_target(override) is True
        assert pipe._pending_operator_override is override

    def test_pipeline_ignores_override_when_feature_flag_is_off(self):
        pipe = self._pipeline(enabled=False)
        pipe.request_operator_target(OperatorTargetOverride.from_bbox((10, 10, 30, 30)))

        status = pipe._apply_operator_override_if_pending(np.zeros((80, 80, 3), dtype=np.uint8))

        assert status == 'disabled'
        assert pipe.manager.get_active_target() is None
        assert pipe.lock_tracker.reset_count == 0

    def test_pipeline_applies_override_and_seeds_template_lock(self):
        pipe = self._pipeline(enabled=True)
        pipe.request_operator_target(OperatorTargetOverride.from_bbox((10, 10, 30, 30)))
        frame = np.zeros((80, 80, 3), dtype=np.uint8)

        status = pipe._apply_operator_override_if_pending(frame)

        assert status == 'applied'
        assert pipe.manager.get_active_target() is not None
        assert pipe.manager.get_active_target().source == DetectionSource.OPERATOR
        assert pipe.lock_tracker.reset_count == 0
        assert pipe.lock_tracker.sync_calls == [((80, 80, 3), (10, 10, 30, 30))]
        assert pipe._operator_override_count == 1
        assert pipe._last_operator_override_bbox == (10, 10, 30, 30)

    def test_pipeline_release_operator_target_clears_lock(self):
        pipe = self._pipeline(enabled=True)
        pipe.request_operator_target(OperatorTargetOverride.from_bbox((10, 10, 30, 30)))
        pipe._apply_operator_override_if_pending(np.zeros((80, 80, 3), dtype=np.uint8))

        assert pipe.request_operator_release() is True

        assert pipe.manager.active_id is None
        assert pipe.lock_tracker.reset_count == 1

    def test_pipeline_confirm_operator_target_marks_existing_active(self):
        pipe = self._pipeline(enabled=True)
        pipe.manager.targets[9] = _target(9, (20, 20, 50, 50))
        pipe.manager.active_id = 9

        assert pipe.request_operator_confirm() is True

        assert pipe.manager.targets[9].source == DetectionSource.OPERATOR

    def test_operator_target_prefers_lock_tracking_over_global_scan(self):
        pipe = self._pipeline(enabled=True)
        pipe.request_operator_target(OperatorTargetOverride.from_bbox((10, 10, 30, 30)))
        pipe._apply_operator_override_if_pending(np.zeros((80, 80, 3), dtype=np.uint8))

        run_global, strategy = pipe._should_run_global_scan()

        assert run_global is False
        assert strategy == 'OPERATOR-LOCK'

    def test_verifying_operator_target_uses_local_search_around_click(self):
        pipe = self._pipeline(enabled=True)
        pipe.cfg.OPERATOR_OVERRIDE_INSTANT_LOCK = False
        pipe.request_operator_target(OperatorTargetOverride.from_click(40, 50, box_size=30))
        pipe._apply_operator_override_if_pending(np.zeros((80, 80, 3), dtype=np.uint8))

        run_global, strategy = pipe._should_run_global_scan()

        assert run_global is False
        assert strategy == 'OPERATOR-VERIFY'
