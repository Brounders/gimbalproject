#!/usr/bin/env python3
"""Validate consistency between active_plan and orchestration state indexes."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TASK_RE = re.compile(r"\bTASK-\d{8}-\d{3}\b")
TRAIN_RE = re.compile(r"\bTRAIN-\d{8}-\d{3}\b")
REQUIRED_HEADINGS = [
    "## Plan ID",
    "## Status",
    "## Active Claude Tasks (execution allowed now)",
    "## Active RTX Tasks (execution allowed now)",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_ids(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def _extract_section_ids(text: str, heading: str, pattern: re.Pattern[str]) -> set[str]:
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == heading
            continue
        if in_section:
            section_lines.append(line)
    return _extract_ids("\n".join(section_lines), pattern)


def _extract_section_text(text: str, heading: str) -> str:
    lines = text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == heading
            continue
        if in_section:
            section_lines.append(line)
    return "\n".join(section_lines).strip()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    state_dir = repo_root / "orchestrator" / "state"

    active_plan = _read(state_dir / "active_plan.md")
    open_tasks = _read(state_dir / "open_tasks.md")
    completed_tasks = _read(state_dir / "completed_tasks.md")
    open_training = _read(state_dir / "open_training.md")

    active_task_ids = _extract_section_ids(
        active_plan, "## Active Claude Tasks (execution allowed now)", TASK_RE
    )
    active_train_ids = _extract_section_ids(
        active_plan, "## Active RTX Tasks (execution allowed now)", TRAIN_RE
    )
    active_status_text = _extract_section_text(active_plan, "## Status").lower()
    open_task_ids = _extract_ids(open_tasks, TASK_RE)
    completed_task_ids = _extract_ids(completed_tasks, TASK_RE)
    open_train_ids = _extract_ids(open_training, TRAIN_RE)

    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in active_plan:
            errors.append(f"active_plan format error: missing required heading `{heading}`.")

    for task_id in sorted(active_task_ids):
        if task_id in completed_task_ids:
            errors.append(f"{task_id}: listed in active_plan but already completed.")
        if task_id not in open_task_ids:
            errors.append(f"{task_id}: listed in active_plan but missing in open_tasks.")

    for train_id in sorted(active_train_ids):
        if train_id not in open_train_ids:
            errors.append(
                f"{train_id}: listed in active_plan but missing in open_training."
            )

    if "active" in active_status_text and not (active_task_ids or active_train_ids):
        errors.append("active_plan status is Active but no active Claude/RTX tasks are listed.")

    if errors:
        print("orchestrator_state_check=FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("orchestrator_state_check=OK")
    print(
        f"active_tasks={len(active_task_ids)} open_tasks={len(open_task_ids)} completed_tasks={len(completed_task_ids)}"
    )
    print(f"active_training={len(active_train_ids)} open_training={len(open_train_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
