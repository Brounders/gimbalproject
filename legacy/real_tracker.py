import cv2
import time
import torch
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque

# ===== НАСТРОЙКИ =====
MODEL_PATH = "models/yolo11n.pt"
FRAME_SIZE = (640, 480)
CONF_THRESH = 0.4
TARGET_CLASS = 0  # person
MIN_SPEED = 30     # пикс/сек (подбери под свое видео)
HISTORY_LEN = 5    # кадров для усреднения скорости
LOST_FRAMES_MAX = 30  # сколько кадров ждать потерянную цель

# ===== ЗАГРУЗКА =====
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Устройство: {device}")
model = YOLO(MODEL_PATH)
model.to(device)

# ===== КАМЕРА =====
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])

# ===== ТРЕКИНГ =====
track_history = defaultdict(lambda: deque(maxlen=HISTORY_LEN))
track_speeds = defaultdict(float)
track_colors = {}
target_id = None
lost_counter = 0

# ===== FPS =====
fps_counter = 0
fps_timer = time.time()
fps = 0

print("Запуск... ESC выход")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Инференс с трекингом
    results = model.track(
        frame, 
        conf=CONF_THRESH,
        classes=[TARGET_CLASS],
        persist=True,
        verbose=False,
        half=True
    )
    
    # Обработка результатов
    current_ids = set()
    
    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        current_ids = set(track_ids)
        
        # Сначала обновляем скорости для всех объектов
        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box[:4])
            center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            # Добавляем в историю
            track_history[track_id].append(center)
            
            # Вычисляем скорость (пикс/сек)
            if len(track_history[track_id]) >= 2:
                points = list(track_history[track_id])
                dx = points[-1][0] - points[-2][0]
                dy = points[-1][1] - points[-2][1]
                speed = np.sqrt(dx*dx + dy*dy) * fps if fps > 0 else 0
                track_speeds[track_id] = speed
        
        # Рисуем все объекты
        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box[:4])
            
            # Цвет
            if track_id not in track_colors:
                track_colors[track_id] = (
                    np.random.randint(0, 255),
                    np.random.randint(0, 255),
                    np.random.randint(0, 255)
                )
            color = track_colors[track_id]
            
            # Рамка
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID:{track_id}", (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Скорость
            if track_id in track_speeds:
                cv2.putText(frame, f"{track_speeds[track_id]:.0f}px/s", 
                           (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # ===== ЛОГИКА ВЫБОРА ЦЕЛИ ПО СКОРОСТИ =====
        # Если есть цель, проверяем видна ли она
        if target_id is not None:
            if target_id in current_ids:
                lost_counter = 0  # цель видна, сбрасываем счетчик
            else:
                lost_counter += 1
                if lost_counter > LOST_FRAMES_MAX:
                    print(f"Цель {target_id} потеряна, ищем новую...")
                    target_id = None
                    lost_counter = 0
        
        # Если нет цели, ищем самую быструю
        if target_id is None:
            best_id = None
            best_speed = MIN_SPEED
            
            for track_id in current_ids:
                if track_id in track_speeds and track_speeds[track_id] > best_speed:
                    best_speed = track_speeds[track_id]
                    best_id = track_id
            
            if best_id is not None:
                target_id = best_id
                print(f"Новая цель: ID {target_id}, скорость {best_speed:.0f} px/s")
        
        # Рисуем цель
        if target_id is not None and target_id in current_ids:
            for box, track_id in zip(boxes, track_ids):
                if track_id == target_id:
                    x1, y1, x2, y2 = map(int, box[:4])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(frame, "TARGET", (x1, y1-25), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    break
    
    # FPS
    fps_counter += 1
    if time.time() - fps_timer >= 1:
        fps = fps_counter
        fps_counter = 0
        fps_timer = time.time()
        print(f"FPS: {fps}, Объектов: {len(track_history)}")
    
    # Инфо на экране
    cv2.putText(frame, f"FPS: {fps}", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Objects: {len(track_history)}", (20, 80), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    if target_id:
        cv2.putText(frame, f"Target: ID {target_id}", (20, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow("TRACKER FINAL", frame)
    
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()