from typing import Optional

import cv2
import numpy as np

from uav_tracker.config import Config
from uav_tracker.tracking.target_manager import TargetManager, TrackedTarget


def _draw_target(
    frame: np.ndarray,
    manager: TargetManager,
    target: TrackedTarget,
    cfg: Config,
    *,
    compact: bool = False,
):
    tid = target.track_id
    is_active = tid == manager.active_id
    x1, y1, x2, y2 = target.bbox
    color_map = {
        'yolo': (48, 204, 92),
        'roi': (30, 180, 255),
        'local': (0, 210, 255),
        'lock': (255, 215, 0),
        'night': (255, 170, 50),
    }
    color_active = (0, 70, 255)

    base_color = color_map.get(target.source, (200, 200, 200))
    color = color_active if is_active else base_color
    thickness = 2 if is_active else 1
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    if compact:
        label = f"{'[LOCK] ' if is_active else ''}ID:{tid}"
    elif target.source in {'yolo', 'roi', 'local', 'lock'} and target.cls_id >= 0:
        label = (
            f"{'[LOCK] ' if is_active else ''}ID:{tid} {target.source[0].upper()} "
            f"c{target.cls_id} d:{target.drone_score:.2f} conf:{target.conf:.2f} spd:{target.speed:.1f}"
        )
    else:
        label = f"{'[LOCK] ' if is_active else ''}ID:{tid} {target.source[0].upper()} conf:{target.conf:.2f} spd:{target.speed:.1f}"
    cv2.putText(frame, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    if cfg.SHOW_TRAILS and not compact and len(target.trail) > 1:
        pts = list(target.trail)
        for idx in range(1, len(pts)):
            alpha = idx / len(pts)
            trail_color = tuple(int(v * alpha) for v in color)
            cv2.line(frame, pts[idx - 1], pts[idx], trail_color, 1)


def _target_class_label(target: Optional[TrackedTarget], cfg: Config) -> str:
    if target is None:
        return 'NO TARGET'
    if target.cls_id < 0:
        return 'UNKNOWN'
    if target.cls_id == int(cfg.PREFER_CLASS_ID):
        return 'UAV'
    if target.cls_id == 1:
        return 'BIRD'
    return f'OBJ c{target.cls_id}'


def _draw_active_lock_box(
    frame: np.ndarray,
    track_id: int,
    bbox: tuple[int, int, int, int],
    center: Optional[tuple[int, int]],
) -> None:
    x1, y1, x2, y2 = bbox
    bw = max(8, int(x2 - x1))
    bh = max(8, int(y2 - y1))

    # Slightly larger than target bbox, while staying proportional to the object size.
    pad_x = max(2, int(bw * 0.08))
    pad_y = max(2, int(bh * 0.08))
    box_w = bw + 2 * pad_x
    box_h = bh + 2 * pad_y

    if center is not None:
        cx, cy = center
    else:
        cx = int((x1 + x2) * 0.5)
        cy = int((y1 + y2) * 0.5)

    fx1 = int(cx - box_w * 0.5)
    fy1 = int(cy - box_h * 0.5)
    fx2 = fx1 + box_w
    fy2 = fy1 + box_h

    h, w = frame.shape[:2]
    fx1 = max(0, min(w - 2, fx1))
    fy1 = max(0, min(h - 2, fy1))
    fx2 = max(fx1 + 1, min(w - 1, fx2))
    fy2 = max(fy1 + 1, min(h - 1, fy2))

    red = (0, 0, 255)
    cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), red, 2)
    cv2.putText(
        frame,
        f'ID={track_id}',
        (fx1, max(14, fy1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        red,
        2,
    )


def draw_frame(
    frame: np.ndarray,
    manager: TargetManager,
    fps: float,
    cfg: Config,
    frame_index: int,
    scan_strategy: str,
    tracking_mode: str,
    lock_confirmed: bool,
    gt_bbox: Optional[tuple[int, int, int, int]] = None,
    gt_iou: float = 0.0,
    timings_ms: Optional[dict[str, float]] = None,
    focus_roi: Optional[tuple[int, int, int, int]] = None,
    lock_search_roi: Optional[tuple[int, int, int, int]] = None,
    lock_score: float = 0.0,
    display_confidence: float = 0.0,
    lock_switches_per_min: float = 0.0,
    lock_switch_count: int = 0,
    budget_level: int = 0,
    budget_load: float = 1.0,
    roi_budget_candidates: int = 0,
    night_skip: int = 1,
    reticle_center: Optional[tuple[int, int]] = None,
    display_lock_box: Optional[tuple[int, int, int, int]] = None,
):
    active = manager.get_active_target()
    compact_overlay = bool(cfg.OPERATOR_MINIMAL_OVERLAY and cfg.RUNTIME_MODE in {'operator', 'embedded'})
    use_reticle_overlay = bool(cfg.RETICLE_OVERLAY_ENABLED)
    all_visible_targets = manager.display_targets()
    visible = len(all_visible_targets)

    if (
        not use_reticle_overlay
        and not compact_overlay
        and cfg.SHOW_FOCUS_WINDOW
        and focus_roi is not None
        and manager.is_focus_mode()
    ):
        fx1, fy1, fx2, fy2 = focus_roi
        cv2.rectangle(frame, (fx1, fy1), (fx2, fy2), (0, 180, 255), 1)
        cv2.putText(frame, 'focus ROI', (fx1, max(18, fy1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 180, 255), 1)

    if not use_reticle_overlay and not compact_overlay and cfg.SHOW_LOCK_SEARCH_WINDOW and lock_search_roi is not None:
        sx1, sy1, sx2, sy2 = lock_search_roi
        cv2.rectangle(frame, (sx1, sy1), (sx2, sy2), (120, 120, 255), 1)

    if not use_reticle_overlay and not compact_overlay and cfg.SHOW_GT_OVERLAY and gt_bbox is not None:
        gx1, gy1, gx2, gy2 = gt_bbox
        cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (80, 220, 255), 2)
        cv2.putText(frame, 'GT', (gx1, max(18, gy1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 220, 255), 1)

    if use_reticle_overlay:
        if active is not None:
            _draw_active_lock_box(frame, active.track_id, display_lock_box or active.bbox, reticle_center)

        background_targets = max(0, visible - (1 if active is not None else 0))
        background_total = max(0, len(manager.targets) - (1 if active is not None else 0))
        track_id = '-' if active is None else str(active.track_id)
        class_label = _target_class_label(active, cfg)
        reliability = int(round(max(0.0, min(1.0, float(display_confidence))) * 100.0))
        if tracking_mode == 'TRACK':
            tracking_state = 'LOCK_CONFIRMED' if lock_confirmed else 'TRACK_CANDIDATE'
        else:
            tracking_state = tracking_mode

        cv2.putText(frame, f'FPS: {fps:.1f}', (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
        cv2.putText(
            frame,
            f'BG targets: {background_targets} vis / {background_total} total',
            (10, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (210, 210, 210),
            1,
        )
        cv2.putText(
            frame,
            f'ID:{track_id} - {class_label}',
            (10, 74),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (235, 235, 235),
            2,
        )
        cv2.putText(
            frame,
            f'{tracking_state} | Confidence: {reliability}%',
            (10, 99),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (200, 220, 255),
            1,
        )
        return frame

    visible_targets = all_visible_targets
    if compact_overlay and active is not None:
        visible_targets = [active]

    for target in visible_targets:
        _draw_target(frame, manager, target, cfg, compact=compact_overlay)

    active_source = active.source if active is not None else '-'
    visible_now = len(visible_targets)

    if compact_overlay:
        if tracking_mode == 'TRACK':
            status = 'LOCK' if lock_confirmed else 'TRACK*'
        else:
            status = tracking_mode
        active_text = '-' if manager.active_id is None else f'ID {manager.active_id}'
        cv2.putText(frame, f'FPS: {fps:.1f}  {status}  {active_text}', (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    else:
        cv2.putText(frame, f'FPS: {fps:.1f}  Frame: {frame_index + 1}', (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        if tracking_mode == 'TRACK':
            mode_label = 'LOCK_CONFIRMED' if lock_confirmed else 'TRACK_CANDIDATE'
        else:
            mode_label = tracking_mode
        cv2.putText(frame, f'Mode: {mode_label}  Plan: {scan_strategy}', (10, 49), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)
        gt_text = f'GT IoU: {gt_iou:.3f}' if gt_bbox is not None else 'GT IoU: -'
        cv2.putText(
            frame,
            (
                f'Targets: {visible_now}/{len(manager.targets)}  Active: {manager.active_id} ({active_source})  {gt_text}  '
                f'Lock:{lock_score:.2f}  Sw/min:{lock_switches_per_min:.2f} ({lock_switch_count})'
            ),
            (10, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (210, 210, 210),
            1,
        )

    if not compact_overlay and cfg.SHOW_DEBUG_TIMINGS and timings_ms is not None:
        timing_text = ' '.join(
            [
                f"G:{timings_ms.get('global', 0.0):.1f}ms",
                f"K:{timings_ms.get('lock', 0.0):.1f}ms",
                f"L:{timings_ms.get('local', 0.0):.1f}ms",
                f"ROI:{timings_ms.get('roi', 0.0):.1f}ms",
                f"N:{timings_ms.get('night', 0.0):.1f}ms",
                f"D:{timings_ms.get('draw', 0.0):.1f}ms",
                f"B:L{int(budget_level)} load:{budget_load:.2f} roi:{int(roi_budget_candidates)} nskip:{int(night_skip)}",
            ]
        )
        cv2.putText(frame, timing_text, (10, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (150, 190, 210), 1)

    if not compact_overlay:
        cv2.putText(frame, 'Q=quit  N=next  R=reset', (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    return frame
