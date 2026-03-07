#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import RUNTIME_MODES, apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source
from uav_tracker.profile_io import available_presets, load_preset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Scenario sweep for tracker presets')
    parser.add_argument('--source', type=str, required=True, help='Видео файл, папка кадров или индекс камеры')
    parser.add_argument('--presets', type=str, default='default,small_target,night,antiuav_thermal', help='Список preset через запятую')
    parser.add_argument('--max-frames', type=int, default=300, help='Лимит кадров на один сценарий')
    parser.add_argument('--report-dir', type=Path, default=Path('runs/evaluations/sweeps'), help='Папка с отчетами')
    parser.add_argument('--tag', type=str, default='', help='Префикс имени файла отчета')
    parser.add_argument('--mode', type=str, default='', choices=[''] + list(RUNTIME_MODES), help='Принудительный runtime mode')
    parser.add_argument('--device', type=str, default='', help='Принудительное устройство (mps/cpu/hailo)')
    parser.add_argument('--imgsz', type=int, default=0, help='Принудительный размер входа')
    parser.add_argument('--conf', type=float, default=0.0, help='Принудительный conf threshold')
    parser.add_argument('--small-target', type=str, default='auto', choices=['auto', 'on', 'off'], help='Режим small target')
    parser.add_argument('--sort', type=str, default='score', choices=['score', 'lock_rate', 'fps', 'swpm'], help='Ключ сортировки сводки')
    return parser.parse_args()


def _resolve_small_target(mode: str, preset_data: dict) -> bool:
    if mode == 'on':
        return True
    if mode == 'off':
        return False
    return bool(preset_data.get('small_target_mode', False))


def _score_row(row: dict) -> float:
    lock_rate = float(row['lock_rate'])
    fps = float(row['avg_fps'])
    switch_rate = float(row['lock_switches_per_min'])
    false_rate = float(row['false_alarm_rate'])
    false_lock_rate = float(row.get('false_lock_rate', 0.0))
    continuity = float(row.get('continuity_score', 0.0))
    avg_budget_level = float(row['avg_budget_level'])
    fps_term = min(fps / 30.0, 1.0)
    return (
        lock_rate * 55.0
        + continuity * 20.0
        + fps_term * 20.0
        - switch_rate * 4.0
        - false_rate * 15.0
        - false_lock_rate * 18.0
        - avg_budget_level * 2.0
    )


def _sort_rows(rows: list[dict], key: str) -> list[dict]:
    if key == 'lock_rate':
        return sorted(rows, key=lambda r: (r['lock_rate'], r['avg_fps']), reverse=True)
    if key == 'fps':
        return sorted(rows, key=lambda r: r['avg_fps'], reverse=True)
    if key == 'swpm':
        return sorted(rows, key=lambda r: (r['lock_switches_per_min'], -r['lock_rate']))
    return sorted(rows, key=lambda r: r['score'], reverse=True)


def _to_row(preset: str, report: dict, report_path: Path) -> dict:
    total = max(1, int(report['total_frames']))
    lock_rate = float(report['lock_frames']) / total
    false_alarm_rate = float(report['false_alarm_frames']) / total
    false_lock_rate = float(report.get('false_lock_frames', 0)) / total
    row = {
        'preset': preset,
        'report_path': str(report_path),
        'total_frames': int(report['total_frames']),
        'lock_frames': int(report['lock_frames']),
        'lock_rate': lock_rate,
        'false_alarm_rate': false_alarm_rate,
        'false_lock_rate': false_lock_rate,
        'avg_fps': float(report['avg_fps']),
        'avg_lock_score': float(report['avg_lock_score']),
        'continuity_score': float(report.get('continuity_score', 0.0)),
        'active_presence_rate': float(report.get('active_presence_rate', 0.0)),
        'active_id_changes': int(report.get('active_id_changes', 0)),
        'median_reacquire_frames': float(report.get('median_reacquire_frames', 0.0)),
        'lock_switches': int(report.get('lock_switches', 0)),
        'lock_switches_per_min': float(report.get('lock_switches_per_min', 0.0)),
        'avg_budget_level': float(report.get('avg_budget_level', 0.0)),
        'avg_budget_load': float(report.get('avg_budget_load', 0.0)),
        'avg_budget_frame_ms': float(report.get('avg_budget_frame_ms', 0.0)),
        'time_to_first_lock': report.get('time_to_first_lock'),
    }
    row['score'] = _score_row(row)
    return row


def _write_csv(path: Path, rows: list[dict]) -> None:
    headers = [
        'preset',
        'score',
        'lock_rate',
        'avg_fps',
        'continuity_score',
        'active_presence_rate',
        'active_id_changes',
        'median_reacquire_frames',
        'lock_switches_per_min',
        'lock_switches',
        'avg_lock_score',
        'false_alarm_rate',
        'false_lock_rate',
        'avg_budget_level',
        'avg_budget_load',
        'avg_budget_frame_ms',
        'time_to_first_lock',
        'total_frames',
        'report_path',
    ]
    lines = [','.join(headers)]
    for row in rows:
        values = []
        for h in headers:
            v = row.get(h, '')
            values.append(str(v))
        lines.append(','.join(values))
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    args = parse_args()
    source = parse_video_source(args.source)
    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    preset_names = [p.strip() for p in args.presets.split(',') if p.strip()]
    if not preset_names:
        print('Пустой список preset.', file=sys.stderr)
        return 2

    known = set(available_presets())
    rows: list[dict] = []
    source_stem = Path(str(source)).stem if isinstance(source, str) else f'camera_{source}'
    source_stem = source_stem or 'source'

    print(f'Источник: {source}')
    for preset in preset_names:
        if preset not in known:
            print(f'[skip] preset не найден: {preset}')
            continue

        cfg = Config()
        cfg, preset_data = load_preset(preset, cfg)
        if args.mode:
            cfg = apply_runtime_mode(cfg, args.mode)
        if args.device:
            cfg.DEVICE = args.device

        small_target_mode = _resolve_small_target(args.small_target, preset_data)
        imgsz = int(args.imgsz) if args.imgsz > 0 else int(cfg.IMG_SIZE)
        conf = float(args.conf) if args.conf > 0 else float(cfg.CONF_THRESH)
        cfg = apply_runtime_preset(cfg, small_target_mode=small_target_mode, imgsz=imgsz, conf=conf)

        report_path = report_dir / f'{args.tag}{preset}_{source_stem}.json'
        print(
            f"[run] {preset}: mode={cfg.RUNTIME_MODE} device={cfg.DEVICE} "
            f"imgsz={cfg.IMG_SIZE} conf={cfg.CONF_THRESH:.2f} small={small_target_mode}"
        )
        report = evaluate_source(
            cfg,
            source=source,
            small_target_mode=small_target_mode,
            max_frames=max(0, int(args.max_frames)),
            report_path=str(report_path),
        )
        row = _to_row(preset, report.to_dict(), report_path)
        rows.append(row)
        print(
            f"[done] {preset}: score={row['score']:.2f} lock_rate={row['lock_rate']:.3f} "
            f"cont={row['continuity_score']:.3f} sw/min={row['lock_switches_per_min']:.2f} "
            f"false_lock={row['false_lock_rate']:.3f} fps={row['avg_fps']:.1f}"
        )

    if not rows:
        print('Нет валидных прогонов.', file=sys.stderr)
        return 3

    rows = _sort_rows(rows, args.sort)
    generated_at = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    summary = {
        'generated_at_utc': generated_at,
        'source': str(source),
        'sort': args.sort,
        'rows': rows,
    }
    summary_json = report_dir / f'{args.tag}summary_{source_stem}.json'
    summary_csv = report_dir / f'{args.tag}summary_{source_stem}.csv'
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    _write_csv(summary_csv, rows)

    print('\nРейтинг сценариев:')
    print('preset | score | lock_rate | continuity | sw/min | fps | budget')
    for row in rows:
        print(
            f"{row['preset']} | {row['score']:.2f} | {row['lock_rate']:.3f} | {row['continuity_score']:.3f} | "
            f"{row['lock_switches_per_min']:.2f} | {row['avg_fps']:.1f} | {row['avg_budget_level']:.2f}"
        )
    print(f'\nСводка JSON: {summary_json}')
    print(f'Сводка CSV:  {summary_csv}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
