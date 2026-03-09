import cv2
import time
import torch
from ultralytics import YOLO
from collections import deque

# ===== НАСТРОЙКИ =====
MODEL_PATH = "models/yolo11n.pt"
FRAME_SIZE = (640, 480)  # оптимально
CONF_THRESH = 0.4
TARGET_CLASS = 2  # car

# ===== ЗАГРУЗКА =====
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Устройство: {device}")
model = YOLO(MODEL_PATH)
model.to(device)

# ===== КАМЕРА =====
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
cap.set(cv2.CAP_PROP_FPS, 30)

# ===== ТРЕКИНГ =====
history = {}
prev_centers = {}
target_id = None

# ===== FPS =====
fps_counter = 0
fps_timer = time.time()
fps = 0

print("Запуск... ESC выход")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Инференс
    results = model.track(
        frame, 
        conf=CONF_THRESH,
        classes=[TARGET_CLASS],
        persist=True,
        verbose=False,
        half=True
    )
    
    # Обработка результатов
    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy().astype(int)
        
        for box, obj_id in zip(boxes, ids):
            x1, y1, x2, y2 = map(int, box[:4])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{obj_id}", (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    
    # FPS
    fps_counter += 1
    if time.time() - fps_timer >= 1:
        fps = fps_counter
        fps_counter = 0
        fps_timer = time.time()
    
    cv2.putText(frame, f"FPS: {fps}", (20, 40), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow("Tracker", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()