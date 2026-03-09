#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "tracker_env" / "bin" / "python"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest RTX export zip on Mac, update latest checkpoint, run stable cycle benchmark+quality-gate."
    )
    p.add_argument("--url", type=str, required=True, help="HTTP URL of RTX export zip")
    p.add_argument("--tag", type=str, default="", help="Optional artifact tag (default: from zip filename)")
    p.add_argument("--candidate-preset", type=str, default="night_rtx_candidate")
    p.add_argument("--pack-file", type=Path, default=Path("configs/regression_pack.csv"))
    p.add_argument("--mode", type=str, default="operator")
    p.add_argument("--device", type=str, default="mps")
    p.add_argument("--max-frames", type=int, default=240)
    p.add_argument("--run-ab", action="store_true", help="Run profile A/B before gate")
    p.add_argument("--skip-cycle", action="store_true", help="Only ingest artifact, skip benchmark/gate")
    return p.parse_args()


def _safe_tag(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._-")
    return value or f"rtx_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_payload_root(unpack_root: Path) -> Path:
    candidates = []
    for best in unpack_root.rglob("best.pt"):
        parent = best.parent
        if (parent / "last.pt").exists():
            candidates.append(parent)
    if not candidates:
        raise FileNotFoundError("best.pt/last.pt not found in unpacked artifact")
    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


def _safe_extract_cross_platform(zip_path: Path, out_dir: Path) -> None:
    with ZipFile(zip_path) as zf:
        for info in zf.infolist():
            raw_name = info.filename.replace("\\", "/").lstrip("/")
            if not raw_name:
                continue
            target = (out_dir / raw_name).resolve()
            if not str(target).startswith(str(out_dir.resolve())):
                raise RuntimeError(f"unsafe zip path: {info.filename}")
            if info.is_dir() or raw_name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def _run(cmd: list[str]) -> None:
    print("[exec]", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT, check=False)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def main() -> int:
    args = parse_args()

    incoming = ROOT / "imports" / "rtx" / "incoming"
    unpacked = ROOT / "imports" / "rtx" / "unpacked"
    checkpoints = ROOT / "models" / "checkpoints"
    incoming.mkdir(parents=True, exist_ok=True)
    unpacked.mkdir(parents=True, exist_ok=True)
    checkpoints.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(args.url)
    zip_name = Path(parsed.path).name or "rtx_artifact.zip"
    tag = _safe_tag(args.tag or Path(zip_name).stem)
    zip_path = incoming / f"{tag}.zip"
    unpack_root = unpacked / tag
    if unpack_root.exists():
        shutil.rmtree(unpack_root)
    unpack_root.mkdir(parents=True, exist_ok=True)

    print(f"[info] download: {args.url}")
    urlretrieve(args.url, zip_path)
    zip_sha = _sha256(zip_path)
    print(f"[info] zip: {zip_path} sha256={zip_sha}")

    _safe_extract_cross_platform(zip_path, unpack_root)
    payload = _find_payload_root(unpack_root)
    print(f"[info] payload: {payload}")

    mapped = {
        "best.pt": f"{tag}_best.pt",
        "last.pt": f"{tag}_last.pt",
        "args.yaml": f"{tag}_args.yaml",
        "results.csv": f"{tag}_results.csv",
        "summary.txt": f"{tag}_summary.txt",
        "tail_log.txt": f"{tag}_tail_log.txt",
        "source_log.log": f"{tag}_source_log.log",
    }
    written: dict[str, str] = {}
    for src_name, dst_name in mapped.items():
        src = payload / src_name
        if not src.exists():
            continue
        dst = checkpoints / dst_name
        shutil.copy2(src, dst)
        written[src_name] = str(dst)

    # Canonical "latest" pointers as plain files for stable config paths.
    shutil.copy2(payload / "best.pt", checkpoints / "rtx_latest_best.pt")
    shutil.copy2(payload / "last.pt", checkpoints / "rtx_latest_last.pt")
    if (payload / "args.yaml").exists():
        shutil.copy2(payload / "args.yaml", checkpoints / "rtx_latest_args.yaml")
    if (payload / "summary.txt").exists():
        shutil.copy2(payload / "summary.txt", checkpoints / "rtx_latest_summary.txt")

    meta = {
        "ingested_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "tag": tag,
        "url": args.url,
        "zip_path": str(zip_path),
        "zip_sha256": zip_sha,
        "payload_root": str(payload),
        "written_files": written,
        "latest_best": str(checkpoints / "rtx_latest_best.pt"),
        "latest_last": str(checkpoints / "rtx_latest_last.pt"),
    }
    meta_path = checkpoints / f"{tag}_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[info] meta: {meta_path}")

    if args.skip_cycle:
        print("[summary] cycle skipped by --skip-cycle")
        return 0

    stable_tag = f"{tag}_"
    cmd = [
        str(PY),
        "python_scripts/run_stable_cycle.py",
        "--rtx-model",
        "models/checkpoints/rtx_latest_best.pt",
        "--candidate-preset",
        args.candidate_preset,
        "--pack-file",
        str(args.pack_file),
        "--mode",
        args.mode,
        "--device",
        args.device,
        "--max-frames",
        str(args.max_frames),
        "--tag",
        stable_tag,
    ]
    if args.run_ab:
        cmd.append("--run-ab")
    _run(cmd)

    decision_glob = f"runs/evaluations/stable_cycle/{stable_tag}stable_*_stable_cycle_decision.json"
    matches = sorted(ROOT.glob(decision_glob), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        print("[error] stable cycle decision json not found")
        return 3
    decision_path = matches[0]
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    print(f"[summary] decision={payload.get('release_decision')}")
    print(f"[summary] gate_passed={payload.get('quality_gate_passed')}")
    print(f"[summary] score={payload.get('quality_gate_mean_score')}")
    print(f"[summary] decision_json={decision_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
