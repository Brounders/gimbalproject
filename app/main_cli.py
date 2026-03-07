import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uav_tracker.config import Config
from uav_tracker.evaluation import evaluate_source
from uav_tracker.modes import RUNTIME_MODES, apply_runtime_mode
from uav_tracker.pipeline import apply_runtime_preset, parse_video_source, run_tracker
from uav_tracker.profile_io import apply_overrides, available_presets, load_preset, load_profile


def build_parser(defaults: Config) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='YOLO + Night hybrid tracker')
    parser.add_argument('--preset', type=str, default='', choices=[''] + available_presets(), help='Имя YAML preset из configs/')
    parser.add_argument('--profile', type=str, default='', help='Путь к YAML профилю')
    parser.add_argument('--mode', type=str, default=None, choices=list(RUNTIME_MODES), help='Research / operator / embedded runtime policy')
    parser.add_argument('--source', type=str, default=None, help='0/1... для камеры или путь к видео/папке кадров')
    parser.add_argument('--model', type=str, default=None, help='Путь к .pt модели')
    parser.add_argument('--device', type=str, default=None, help='mps/cpu/hailo/0')
    parser.add_argument('--imgsz', type=int, default=None, help='Размер входа YOLO')
    parser.add_argument('--conf', type=float, default=None, help='Порог уверенности YOLO')
    parser.add_argument('--small-target-mode', action='store_true', help='Пресет для маленьких целей: imgsz↑ conf↓')
    parser.add_argument('--max-frames', type=int, default=0, help='Ограничить число кадров для тестового прогона (0 = весь поток)')
    parser.add_argument('--no-display', action='store_true', help='Не открывать окно OpenCV')
    parser.add_argument('--output', type=str, default='', help='Путь для сохранения размеченного видео')
    parser.add_argument('--no-adaptive-scan', action='store_true', help='Всегда выполнять полный full-frame scan')
    parser.add_argument('--rescan-interval', type=int, default=None, help='Интервал кадров между глобальными пересканами в режиме lock')
    parser.add_argument('--lock-log', type=str, default='', help='Путь к JSONL логу lock-событий')
    parser.add_argument('--show-gt', dest='show_gt', action='store_true', default=None, help='Показывать ground truth overlay, если доступен')
    parser.add_argument('--hide-gt', dest='show_gt', action='store_false', help='Скрыть ground truth overlay')
    parser.add_argument('--evaluate', action='store_true', help='Запустить evaluation mode вместо live tracking')
    parser.add_argument('--report', type=str, default='', help='Куда сохранить evaluation report JSON')
    return parser


def main() -> None:
    cfg = Config()
    parser = build_parser(cfg)
    args = parser.parse_args()

    source = cfg.VIDEO_SOURCE
    small_target_mode = bool(args.small_target_mode)
    output_path = args.output
    lock_log_path = args.lock_log
    imgsz = cfg.IMG_SIZE
    conf = cfg.CONF_THRESH

    if args.profile:
        profile = load_profile(args.profile)
        cfg = apply_overrides(cfg, profile)
        source = parse_video_source(str(profile.get('source', source)))
        small_target_mode = bool(profile.get('small_target_mode', small_target_mode))
        output_path = args.output or str(profile.get('output_path', output_path))
        lock_log_path = args.lock_log or str(profile.get('lock_event_log_path', lock_log_path))
        imgsz = int(profile.get('imgsz', cfg.IMG_SIZE))
        conf = float(profile.get('conf_thresh', cfg.CONF_THRESH))
    else:
        if args.preset:
            cfg, _ = load_preset(args.preset, cfg)
        imgsz = cfg.IMG_SIZE
        conf = cfg.CONF_THRESH

    if args.mode:
        cfg = apply_runtime_mode(cfg, args.mode)
    if args.source is not None:
        source = parse_video_source(args.source)
    if args.model:
        cfg.MODEL_PATH = args.model
    if args.device:
        cfg.DEVICE = args.device
    if args.imgsz is not None:
        imgsz = args.imgsz
    if args.conf is not None:
        conf = args.conf

    cfg = apply_runtime_preset(cfg, small_target_mode=small_target_mode, imgsz=imgsz, conf=conf)
    cfg.VIDEO_SOURCE = source
    if args.no_adaptive_scan:
        cfg.ADAPTIVE_SCAN_ENABLED = False
    if args.rescan_interval is not None:
        cfg.GLOBAL_SCAN_INTERVAL = max(1, args.rescan_interval)
    if args.show_gt is not None:
        cfg.SHOW_GT_OVERLAY = args.show_gt
    if lock_log_path:
        cfg.LOCK_EVENT_LOG_ENABLED = True
        cfg.LOCK_EVENT_LOG_PATH = lock_log_path

    if args.evaluate:
        report_path = args.report or str(ROOT / 'runs' / 'evaluations' / f'{Path(str(source)).stem or "camera"}_report.json')
        report = evaluate_source(
            cfg,
            source=cfg.VIDEO_SOURCE,
            small_target_mode=small_target_mode,
            max_frames=args.max_frames,
            report_path=report_path,
        )
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        print(f'Отчёт сохранён: {report_path}')
        return

    print(
        f'Запуск трекера | Источник: {cfg.VIDEO_SOURCE} | Режим: {cfg.RUNTIME_MODE} | Устройство: {cfg.DEVICE} '
        f'| imgsz: {cfg.IMG_SIZE} | conf: {cfg.CONF_THRESH:.2f} '
        f'| adaptive: {cfg.ADAPTIVE_SCAN_ENABLED} | rescan: {cfg.GLOBAL_SCAN_INTERVAL}'
    )
    run_tracker(
        cfg,
        source=cfg.VIDEO_SOURCE,
        output_path=output_path,
        lock_log_path=lock_log_path,
        no_display=args.no_display,
        max_frames=args.max_frames,
        small_target_mode=small_target_mode,
    )


if __name__ == '__main__':
    main()
