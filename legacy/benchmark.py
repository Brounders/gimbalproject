import time
import torch
import numpy as np
from ultralytics import YOLO

print("="*50)
print("БЕНЧМАРК ПРОИЗВОДИТЕЛЬНОСТИ M1")
print("="*50)

# Проверка MPS
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

# Тест матричного умножения (ядро нейросетей)
print("\n📊 Тест матричного умножения 4096x4096:")
for device in ['cpu', 'mps'] if torch.backends.mps.is_available() else ['cpu']:
    print(f"\nУстройство: {device.upper()}")
    
    # Создаем случайные матрицы
    a = torch.randn(4096, 4096).to(device)
    b = torch.randn(4096, 4096).to(device)
    
    # Прогрев
    for _ in range(3):
        c = a @ b
    
    # Замер
    torch.mps.synchronize() if device == 'mps' else None
    start = time.time()
    
    for _ in range(10):
        c = a @ b
    
    torch.mps.synchronize() if device == 'mps' else None
    elapsed = time.time() - start
    
    print(f"  10 умножений: {elapsed:.3f} сек")
    print(f"  1 умножение: {elapsed/10:.3f} сек")
    print(f"  TFLOP/s: {2*4096**3*10 / elapsed / 1e12:.2f}")

# Тест YOLO
print("\n📊 Тест инференса YOLO:")

# Загружаем модель (принудительно на нужное устройство)
device = 'mps' if torch.backends.mps.is_available() else 'cpu'
model = YOLO('models/yolo11n.pt')
model.to(device)

# Создаем тестовое изображение
test_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

# Прогрев
for _ in range(5):
    results = model(test_img, verbose=False)

# Замер
torch.mps.synchronize() if device == 'mps' else None
start = time.time()

for _ in range(20):
    results = model(test_img, verbose=False)

torch.mps.synchronize() if device == 'mps' else None
elapsed = time.time() - start

print(f"  Устройство: {device}")
print(f"  20 инференсов: {elapsed:.3f} сек")
print(f"  Средний: {elapsed/20*1000:.1f} мс")
print(f"  Макс. FPS: {20/elapsed:.1f}")