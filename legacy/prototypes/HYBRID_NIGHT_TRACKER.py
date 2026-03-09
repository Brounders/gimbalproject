#!/usr/bin/env python3
# SANE_TRACKER.py - Без ебаного ночного режима

import cv2
import time
import torch
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque

# ===== НАСТРОЙКИ =====
MODEL_PATH = "models/yolo11n.pt"
FRAME_SIZE = (640, 480)
CONF_THRESH = 0.5
IOU_THRESH = 0.5
TARGET_CLASS = 0

# Параметры трекинга
MIN_SPEED = 10
LOST_FRAMES_MAX = 30
SMOOTHING_FACTOR = 0.7
MAX_TRACK_STALE = 120

# ===== ЗАГРУЗКА =====
device = "mps" if torch.backends.mps.is_available() else "cpu"
use_half = device == "cuda"
print(f"Устройство: {device}, FP16: {'on' if use_half else 'off'}")
model = YOLO(MODEL_PATH)
model.to(device)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
if not cap.isOpened():
    raise RuntimeError("Не удалось открыть камеру (index 0)")

# Данные
track_history = defaultdict(lambda: deque(maxlen=5))
track_speeds = defaultdict(float)
track_colors = {}
last_seen_frame = {}

target_id = None
lost_counter = 0
prev_center = None

# FPS
fps_counter = 0
fps_timer = time.time()
fps = 0
frame_idx = 0

print("Запуск... ESC выход")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # Инференс
        results = model.track(
            frame,
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            classes=[TARGET_CLASS],
            persist=True,
            verbose=False,
            half=use_half,
        )

        current_ids = set()

        if results[0].boxes is not None and results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)

            for box, obj_id in zip(boxes, ids):
                current_ids.add(obj_id)
                last_seen_frame[obj_id] = frame_idx

                x1, y1, x2, y2 = map(int, box[:4])
                center = ((x1 + x2) // 2, (y1 + y2) // 2)

                track_history[obj_id].append(center)

                # Скорость
                if len(track_history[obj_id]) >= 2:
                    p0, p1 = track_history[obj_id][-2], track_history[obj_id][-1]
                    speed = np.hypot(p1[0] - p0[0], p1[1] - p0[1]) * fps if fps > 0 else 0
                    track_speeds[obj_id] = speed

                # Цвет
                if obj_id not in track_colors:
                    track_colors[obj_id] = (
                        int(np.random.randint(0, 255)),
                        int(np.random.randint(0, 255)),
                        int(np.random.randint(0, 255)),
                    )
                color = track_colors[obj_id]

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    f"ID:{obj_id}",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )

        # Логика цели должна работать даже если current_ids пустой
        if target_id is not None:
            if target_id in current_ids:
                lost_counter = 0
            else:
                lost_counter += 1
                if lost_counter > LOST_FRAMES_MAX:
                    target_id = None
                    lost_counter = 0
                    prev_center = None

        if target_id is None and current_ids:
            best_id = None
            best_speed = MIN_SPEED
            for obj_id in current_ids:
                if track_speeds.get(obj_id, 0) > best_speed:
                    best_speed = track_speeds[obj_id]
                    best_id = obj_id
            if best_id is not None:
                target_id = best_id
                prev_center = None
                print(f"Новая цель: ID {target_id}")

        # Рисуем цель
        if target_id in current_ids:
            for box, obj_id in zip(boxes, ids):
                if obj_id == target_id:
                    x1, y1, x2, y2 = map(int, box[:4])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(
                        frame,
                        "TARGET",
                        (x1, y1 - 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )

                    # Сглаженный центр
                    center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    alpha = SMOOTHING_FACTOR
                    if prev_center is None:
                        smooth_center = center
                    else:
                        smooth_center = (
                            int(prev_center[0] * alpha + center[0] * (1 - alpha)),
                            int(prev_center[1] * alpha + center[1] * (1 - alpha)),
                        )
                    prev_center = smooth_center
                    cv2.circle(frame, smooth_center, 5, (255, 255, 0), -1)
                    break

        # Очистка старых треков
        stale_ids = [
            obj_id
            for obj_id, seen_at in last_seen_frame.items()
            if frame_idx - seen_at > MAX_TRACK_STALE
        ]
        for obj_id in stale_ids:
            last_seen_frame.pop(obj_id, None)
            track_history.pop(obj_id, None)
            track_speeds.pop(obj_id, None)
            track_colors.pop(obj_id, None)

        # FPS
        fps_counter += 1
        now = time.time()
        if now - fps_timer >= 1:
            fps = fps_counter
            fps_counter = 0
            fps_timer = now
            print(f"FPS: {fps}, Объектов: {len(current_ids)}")

        cv2.putText(frame, f"FPS: {fps}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"Objects: {len(current_ids)}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        cv2.imshow("SANE TRACKER", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
finally:
    cap.release()
    cv2.destroyAllWindows()
