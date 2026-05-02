"""import_regression_pack_gt.py — GT/label ingestion for expanded regression pack.

Reads configs/regression_pack.csv and generates canonical GT JSON files in
configs/ground_truth/regression_pack/<stem>_gt.json.

Canonical format (same as Anti-UAV-RGBT originals):
    {"exist": [0|1, ...], "gt_rect": [[x, y, w, h], ...]}

Sources handled:
  1. Anti-UAV-RGBT clips  — copy exist/gt_rect from Desktop JSON directly.
  2. Noise clips (V_BIRD_001, V_AIRPLANE_001) — synthesise target-absent GT.
  3. V_DRONE_001  — MATLAB MCOS .mat file, not parseable without matlab;
                    skipped, limitation documented in report.
  4. All other clips — no GT available, skipped.

Usage:
    python python_scripts/import_regression_pack_gt.py [--pack-file configs/regression_pack.csv]
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2

# ---------------------------------------------------------------------------
# Desktop source paths
# ---------------------------------------------------------------------------

_DESKTOP_ANTIUAV = Path('/Users/bround/Desktop/Датасеты/Anti-UAV-RGBT/test')

_ANTIUAV_MAP: dict[str, Path] = {
    'antiuav_rgbt_20190925_193610_1_1_visible':
        _DESKTOP_ANTIUAV / '20190925_193610_1_1' / 'visible.json',
    'antiuav_rgbt_20190925_200805_1_2_visible':
        _DESKTOP_ANTIUAV / '20190925_200805_1_2' / 'visible.json',
    'antiuav_rgbt_20190925_200805_1_2_infrared':
        _DESKTOP_ANTIUAV / '20190925_200805_1_2' / 'infrared.json',
    'antiuav_rgbt_train_20190925_205804_1_1_visible':
        _DESKTOP_ANTIUAV.parent / 'train' / '20190925_205804_1_1' / 'visible.json',
    'antiuav_rgbt_train_20190925_210802_1_2_visible':
        _DESKTOP_ANTIUAV.parent / 'train' / '20190925_210802_1_2' / 'visible.json',
    'antiuav_rgbt_train_20190925_210802_1_7_infrared':
        _DESKTOP_ANTIUAV.parent / 'train' / '20190925_210802_1_7' / 'infrared.json',
    'antiuav_rgbt_train_20190925_205804_1_2_infrared':
        _DESKTOP_ANTIUAV.parent / 'train' / '20190925_205804_1_2' / 'infrared.json',
}

# Noise clips: no drone target — target-absent GT
_NOISE_ABSENT_CLIPS = {
    'drone_detection_V_BIRD_001',
    'drone_detection_V_AIRPLANE_001',
}

# Clips whose labels exist but are not parseable (MCOS .mat)
_SKIPPED_WITH_REASON: dict[str, str] = {
    'drone_detection_V_DRONE_001': (
        'V_DRONE_001_LABELS.mat is a MATLAB MCOS groundTruth object '
        '(Opaque class) and cannot be parsed with scipy.io without a '
        'full MATLAB runtime. Skipped — no GT generated.'
    ),
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_frame_count(video_path: Path) -> int:
    """Return frame count via OpenCV, or 0 on failure."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return n


def import_antiuav(stem: str, src_json: Path, out_dir: Path) -> dict:
    """Copy Anti-UAV JSON directly — format is already canonical."""
    if not src_json.exists():
        return {'status': 'error', 'reason': f'Source not found: {src_json}'}
    try:
        data = json.loads(src_json.read_text(encoding='utf-8'))
        exist = list(data.get('exist', []))
        gt_rect = list(data.get('gt_rect', []))
        if not exist:
            return {'status': 'error', 'reason': 'Source JSON has empty exist list'}
        out = {'exist': exist, 'gt_rect': gt_rect}
        out_path = out_dir / f'{stem}_gt.json'
        out_path.write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
        gt_frames = sum(1 for e in exist if int(e) == 1)
        return {
            'status': 'ok',
            'path': str(out_path),
            'total_frames': len(exist),
            'gt_frames': gt_frames,
            'source': str(src_json),
        }
    except Exception as exc:
        return {'status': 'error', 'reason': str(exc)}


def synthesise_absent(stem: str, video_path: Path, out_dir: Path) -> dict:
    """Generate target-absent GT (exist=0 for every frame)."""
    n = _get_frame_count(video_path)
    if n <= 0:
        return {'status': 'error', 'reason': f'Cannot open video to get frame count: {video_path}'}
    out = {
        'exist': [0] * n,
        'gt_rect': [[0, 0, 0, 0]] * n,
    }
    out_path = out_dir / f'{stem}_gt.json'
    out_path.write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
    return {
        'status': 'ok',
        'path': str(out_path),
        'total_frames': n,
        'gt_frames': 0,
        'note': 'target-absent (noise/distractor clip)',
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(pack_file: str = 'configs/regression_pack.csv') -> None:
    pack_path = Path(pack_file)
    if not pack_path.exists():
        print(f'ERROR: pack file not found: {pack_file}', file=sys.stderr)
        sys.exit(1)

    out_dir = Path('configs/ground_truth/regression_pack')
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    skips: list[dict] = []

    # Read clip stems from pack CSV
    with open(pack_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().startswith('#'):
                continue
            source_str = row[0].strip()
            video_path = Path(source_str)
            stem = video_path.stem  # e.g. antiuav_rgbt_20190925_193610_1_1_visible

            if stem in _ANTIUAV_MAP:
                src_json = _ANTIUAV_MAP[stem]
                res = import_antiuav(stem, src_json, out_dir)
                res['clip'] = stem
                results.append(res)

            elif stem in _NOISE_ABSENT_CLIPS:
                res = synthesise_absent(stem, video_path, out_dir)
                res['clip'] = stem
                results.append(res)

            elif stem in _SKIPPED_WITH_REASON:
                skips.append({'clip': stem, 'reason': _SKIPPED_WITH_REASON[stem]})

            else:
                skips.append({'clip': stem, 'reason': 'No GT source available'})

    # Summary
    print('\n=== GT Ingestion Results ===\n')
    ok_count = 0
    for r in results:
        status = r.get('status', '?')
        clip = r.get('clip', '?')
        if status == 'ok':
            ok_count += 1
            gt_f = r.get('gt_frames', 0)
            total = r.get('total_frames', 0)
            note = r.get('note', '')
            print(f'  OK   {clip}: {gt_f}/{total} gt_frames  {note}')
        else:
            print(f'  ERR  {clip}: {r.get("reason", "?")}')

    print()
    for s in skips:
        print(f'  SKIP {s["clip"]}: {s["reason"]}')

    total_clips = len(results) + len(skips)
    print(f'\nDone: {ok_count}/{total_clips} clips have GT generated.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import GT labels for regression pack clips')
    parser.add_argument('--pack-file', default='configs/regression_pack.csv',
                        help='Path to regression pack CSV')
    args = parser.parse_args()
    main(pack_file=args.pack_file)
