#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = ROOT / "python_scripts" / "train_yolo_from_yaml.py"


@dataclass
class DatasetStep:
    step_id: str
    data: Path
    enabled: bool = True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sequential training over dataset queue: each step continues from previous best.pt."
    )
    p.add_argument("--plan", type=Path, default=Path("configs/training_curriculum.yaml"))
    p.add_argument("--python-bin", type=str, default=sys.executable)
    p.add_argument("--max-steps", type=int, default=0, help="0 = all remaining steps")
    p.add_argument("--continue-on-error", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"plan not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("plan must be a YAML mapping")
    return payload


def _resolve(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (root / p)


def _validate_steps(raw_steps: Any, root: Path) -> list[DatasetStep]:
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("plan.datasets must be a non-empty list")
    steps: list[DatasetStep] = []
    seen: set[str] = set()
    for idx, item in enumerate(raw_steps, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"datasets[{idx}] must be a mapping")
        step_id = str(item.get("id", "")).strip()
        data = str(item.get("data", "")).strip()
        if not step_id:
            raise ValueError(f"datasets[{idx}].id is required")
        if step_id in seen:
            raise ValueError(f"duplicate datasets id: {step_id}")
        if not data:
            raise ValueError(f"datasets[{idx}].data is required")
        seen.add(step_id)
        steps.append(
            DatasetStep(
                step_id=step_id,
                data=_resolve(root, data),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return steps


def _default_state_path(plan_name: str) -> Path:
    return ROOT / "runs" / "curriculum_state" / f"{plan_name}.json"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"completed": [], "failed": [], "latest_best": ""}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"completed": [], "failed": [], "latest_best": ""}


def _save_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _build_train_cmd(
    py_bin: str,
    data_path: Path,
    model_path: Path,
    run_name: str,
    train_cfg: dict[str, Any],
    project_dir: Path,
    resume: bool,
) -> list[str]:
    cmd = [
        py_bin,
        str(TRAIN_SCRIPT),
        "--data",
        str(data_path),
        "--model",
        str(model_path),
        "--project",
        str(project_dir),
        "--name",
        run_name,
        "--device",
        str(train_cfg.get("device", "cuda")),
        "--imgsz",
        str(int(train_cfg.get("imgsz", 640))),
        "--batch",
        str(int(train_cfg.get("batch", 6))),
        "--workers",
        str(int(train_cfg.get("workers", 2))),
        "--epochs",
        str(int(train_cfg.get("epochs", 2000))),
        "--time-hours",
        str(float(train_cfg.get("time_hours", 12))),
        "--patience",
        str(int(train_cfg.get("patience", 120))),
        "--cache",
        str(train_cfg.get("cache", "none")),
        "--lr0",
        str(float(train_cfg.get("lr0", 0.0018))),
        "--lrf",
        str(float(train_cfg.get("lrf", 0.01))),
        "--max-det",
        str(int(train_cfg.get("max_det", 80))),
        "--conf",
        str(float(train_cfg.get("conf", 0.35))),
        "--save-period",
        str(int(train_cfg.get("save_period", 1))),
    ]
    if bool(train_cfg.get("val", False)):
        cmd.append("--val")
    else:
        cmd.append("--no-val")
    if bool(train_cfg.get("plots", False)):
        cmd.append("--plots")
    else:
        cmd.append("--no-plots")
    if resume:
        cmd.append("--resume")
    return cmd


def main() -> int:
    args = parse_args()
    plan = _load_yaml(args.plan)

    plan_name = str(plan.get("name", "training_curriculum")).strip() or "training_curriculum"
    project_dir = _resolve(ROOT, str(plan.get("project_dir", "runs/detect/runs")))
    base_model = _resolve(ROOT, str(plan.get("base_model", "models/yolo11n.pt")))
    state_path = _resolve(ROOT, str(plan.get("state_file", _default_state_path(plan_name))))
    run_prefix = str(plan.get("run_prefix", plan_name)).strip() or plan_name
    train_cfg = dict(plan.get("train", {}))
    steps = _validate_steps(plan.get("datasets", []), ROOT)

    state = _load_state(state_path)
    completed = set(state.get("completed", []))
    failed = set(state.get("failed", []))
    latest_best_raw = str(state.get("latest_best", "")).strip()
    latest_best = Path(latest_best_raw) if latest_best_raw else base_model
    if not latest_best.is_absolute():
        latest_best = _resolve(ROOT, str(latest_best))

    if not latest_best.exists():
        raise FileNotFoundError(f"initial model not found: {latest_best}")

    queued: list[DatasetStep] = [s for s in steps if s.enabled and s.step_id not in completed]
    if args.max_steps > 0:
        queued = queued[: int(args.max_steps)]

    print(f"[plan] name={plan_name}")
    print(f"[plan] state={state_path}")
    print(f"[plan] base_model={base_model}")
    print(f"[plan] latest_best={latest_best}")
    print(f"[plan] total_steps={len(steps)} pending={len(queued)} completed={len(completed)} failed={len(failed)}")

    if not queued:
        print("[summary] nothing to run (queue is empty)")
        return 0

    for idx, step in enumerate(queued, start=1):
        run_name = f"{run_prefix}_{step.step_id}"
        run_dir = project_dir / run_name
        last_ckpt = run_dir / "weights" / "last.pt"
        best_ckpt = run_dir / "weights" / "best.pt"

        if not step.data.exists():
            print(f"[error] missing dataset yaml: {step.data}")
            failed.add(step.step_id)
            state["failed"] = sorted(failed)
            _save_state(state_path, state)
            if not args.continue_on_error:
                return 2
            continue

        model_input = latest_best if latest_best.exists() else base_model
        resume = last_ckpt.exists()
        if resume:
            model_input = last_ckpt

        cmd = _build_train_cmd(
            py_bin=args.python_bin,
            data_path=step.data,
            model_path=model_input,
            run_name=run_name,
            train_cfg=train_cfg,
            project_dir=project_dir,
            resume=resume,
        )

        print(
            f"[{idx}/{len(queued)}] step={step.step_id} run={run_name} "
            f"resume={resume} model={model_input}"
        )
        if args.dry_run:
            print("[dry-run]", " ".join(cmd))
            continue

        rc = subprocess.run(cmd, cwd=ROOT).returncode
        if rc != 0:
            print(f"[error] train failed step={step.step_id} rc={rc}")
            failed.add(step.step_id)
            state["failed"] = sorted(failed)
            _save_state(state_path, state)
            if not args.continue_on_error:
                return rc
            continue

        if not best_ckpt.exists():
            print(f"[error] best checkpoint missing after success: {best_ckpt}")
            failed.add(step.step_id)
            state["failed"] = sorted(failed)
            _save_state(state_path, state)
            if not args.continue_on_error:
                return 3
            continue

        latest_best = best_ckpt
        completed.add(step.step_id)
        if step.step_id in failed:
            failed.remove(step.step_id)
        state["completed"] = sorted(completed)
        state["failed"] = sorted(failed)
        state["latest_best"] = str(latest_best.resolve())
        state["last_run_name"] = run_name
        _save_state(state_path, state)
        print(f"[ok] step={step.step_id} latest_best={latest_best}")

    print(f"[summary] completed={len(completed)} failed={len(failed)} latest_best={latest_best}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
