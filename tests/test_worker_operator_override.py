"""TrackerWorker operator override request contract."""
from __future__ import annotations

from app.workers import TrackerWorker
from uav_tracker.config import Config


class TestTrackerWorkerOperatorOverride:
    def test_request_operator_target_queues_click_command(self):
        cfg = Config(OPERATOR_OVERRIDE_BOX_SIZE=32)
        worker = TrackerWorker(cfg, source=0, output_path='', small_target_mode=False)

        worker.request_operator_target(100, 120)
        override = worker._pop_operator_override()

        assert override is not None
        assert override.kind == 'click'
        assert override.point == (100, 120)
        assert override.box_size == 32

    def test_pop_operator_override_is_single_shot(self):
        worker = TrackerWorker(Config(), source=0, output_path='', small_target_mode=False)

        worker.request_operator_target(1, 2)

        assert worker._pop_operator_override() is not None
        assert worker._pop_operator_override() is None

    def test_request_operator_bbox_queues_bbox_command(self):
        worker = TrackerWorker(Config(), source=0, output_path='', small_target_mode=False)

        worker.request_operator_bbox((10, 20, 40, 60))
        override = worker._pop_operator_override()

        assert override is not None
        assert override.kind == 'bbox'
        assert override.bbox == (10, 20, 40, 60)

    def test_operator_control_events_are_single_shot(self):
        worker = TrackerWorker(Config(), source=0, output_path='', small_target_mode=False)

        worker.request_operator_confirm()
        worker.request_operator_release()

        assert worker._pop_operator_confirm() is True
        assert worker._pop_operator_confirm() is False
        assert worker._pop_operator_release() is True
        assert worker._pop_operator_release() is False
