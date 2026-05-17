from __future__ import annotations

from app.dts_training_loop import TrainingLoopSnapshot, training_loop_state


def test_training_loop_starts_with_collect_when_no_ready_frames() -> None:
    state = training_loop_state(TrainingLoopSnapshot(ready_frames=0))

    assert state.stage == "COLLECT"
    assert "клик" in state.next_action.lower()


def test_training_loop_requires_pack_after_ready_frames() -> None:
    state = training_loop_state(TrainingLoopSnapshot(ready_frames=5))

    assert state.stage == "PACK_REQUIRED"
    assert "собрать" in state.next_action.lower()


def test_training_loop_requires_training_after_pack() -> None:
    state = training_loop_state(TrainingLoopSnapshot(ready_frames=5, pack_ok=5, pack_dir="runs/pack"))

    assert state.stage == "TRAIN_REQUIRED"
    assert "обучить" in state.next_action.lower()


def test_training_loop_waits_for_best_after_job_created() -> None:
    state = training_loop_state(
        TrainingLoopSnapshot(
            ready_frames=5,
            pack_ok=5,
            pack_dir="runs/pack",
            training_job_dir="runs/job",
        )
    )

    assert state.stage == "WAITING_BEST"
    assert "best.pt" in state.next_action


def test_training_loop_requires_compare_when_candidate_model_exists() -> None:
    state = training_loop_state(
        TrainingLoopSnapshot(
            ready_frames=5,
            pack_ok=5,
            pack_dir="runs/pack",
            training_job_dir="runs/job",
            candidate_model_path="runs/train/weights/best.pt",
        )
    )

    assert state.stage == "COMPARE_REQUIRED"
    assert "сравнить" in state.next_action.lower()


def test_training_loop_requires_accept_after_smoke_pass() -> None:
    state = training_loop_state(
        TrainingLoopSnapshot(
            ready_frames=5,
            pack_ok=5,
            pack_dir="runs/pack",
            candidate_model_path="runs/train/weights/best.pt",
            compare_status="PASS",
            compare_result_dir="runs/compare",
        )
    )

    assert state.stage == "ACCEPT_REQUIRED"
    assert "принять" in state.next_action.lower()


def test_training_loop_marks_safe_accepted_candidate_as_done_for_dts() -> None:
    state = training_loop_state(
        TrainingLoopSnapshot(
            ready_frames=5,
            pack_ok=5,
            pack_dir="runs/pack",
            candidate_model_path="runs/train/weights/best.pt",
            compare_status="PASS",
            compare_result_dir="runs/compare",
            accepted_candidate_dir="models/candidates/accepted/a",
        )
    )

    assert state.stage == "ACCEPTED_SAFE"
    assert "full gate" in state.next_action.lower()
