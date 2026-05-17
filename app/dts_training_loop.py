from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainingLoopSnapshot:
    ready_frames: int = 0
    pack_ok: int = 0
    pack_dir: str = ""
    training_job_dir: str = ""
    candidate_model_path: str = ""
    compare_status: str = "NOT_RUN"
    compare_result_dir: str = ""
    accepted_candidate_dir: str = ""


@dataclass(frozen=True)
class TrainingLoopState:
    stage: str
    next_action: str


def training_loop_state(snapshot: TrainingLoopSnapshot) -> TrainingLoopState:
    ready = max(0, int(snapshot.ready_frames))
    pack_ok = max(0, int(snapshot.pack_ok))
    compare_status = str(snapshot.compare_status or "NOT_RUN")

    if snapshot.accepted_candidate_dir:
        return TrainingLoopState(
            "ACCEPTED_SAFE",
            "Candidate сохранен безопасно. Следующий шаг: full gate отдельно, затем production promotion вручную.",
        )
    if compare_status == "PASS" and snapshot.compare_result_dir:
        return TrainingLoopState(
            "ACCEPT_REQUIRED",
            "Smoke gate PASS. Нажмите ПРИНЯТЬ, чтобы сохранить candidate без замены текущей модели.",
        )
    if compare_status in {"FAIL", "RETUNE"}:
        return TrainingLoopState(
            "RETUNE_REQUIRED",
            "Candidate не прошел сравнение. Вернитесь к DTS-разметке или обучите новый candidate.",
        )
    if snapshot.candidate_model_path:
        return TrainingLoopState(
            "COMPARE_REQUIRED",
            "best.pt найден. Нажмите СРАВНИТЬ для smoke gate baseline vs candidate.",
        )
    if snapshot.training_job_dir:
        return TrainingLoopState(
            "WAITING_BEST",
            "Training job создан. Запустите job и дождитесь weights/best.pt.",
        )
    if pack_ok > 0 and snapshot.pack_dir:
        return TrainingLoopState(
            "TRAIN_REQUIRED",
            "Pack готов. Нажмите ОБУЧИТЬ, чтобы создать воспроизводимый training job.",
        )
    if ready > 0:
        return TrainingLoopState(
            "PACK_REQUIRED",
            "Есть готовые DTS-кадры. Нажмите СОБРАТЬ, чтобы создать training pack.",
        )
    return TrainingLoopState(
        "COLLECT",
        "Кликните цель на видео, затем примите записи в DTS для набора training candidate.",
    )
