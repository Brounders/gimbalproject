"""
train_drone.py
Дообучение YOLO11n на датасете Drone vs Bird (Mendeley).
Запуск: python train_drone.py
"""

from ultralytics import YOLO
import yaml, os, shutil, random
from pathlib import Path

# ─────────────────────────────────────────────
# КОНФИГУРАЦИЯ — меняй только здесь
# ─────────────────────────────────────────────
PROJECT_ROOT = Path("/Users/bround/Documents/Projects/GimbalProject")
DATASET_RAW  = PROJECT_ROOT / "datasets" / "drone_bird_raw"   # куда распаковал датасет
DATASET_OUT  = PROJECT_ROOT / "datasets" / "drone_bird_yolo"  # итоговая структура для YOLO
RUNS_DIR     = PROJECT_ROOT / "runs"

EPOCHS      = 100
BATCH       = 16      # уменьши до 8 если не хватает памяти
IMG_SIZE    = 640
LR0         = 0.01    # начальный learning rate
LRF         = 0.001   # финальный lr = LR0 * LRF
PATIENCE    = 20      # early stopping: стоп если нет улучшений N эпох
WORKERS     = 4       # потоки загрузки данных
DEVICE      = "mps"   # MPS для Mac M1/M2; "cpu" если проблемы; "0" для NVIDIA
VAL_SPLIT   = 0.15    # 15% данных → валидация
SEED        = 42
# ─────────────────────────────────────────────


def prepare_dataset():
    """
    Датасет с Mendeley уже в YOLO-формате, но нам нужно разбить его
    на train/val если этого ещё не сделано.
    
    Ожидаемая структура DATASET_RAW:
        drone_bird_raw/
            images/   ← все .jpg/.png
            labels/   ← все .txt (YOLO-формат)
    
    Или уже готовая структура train/val — тогда эта функция пропустит разбивку.
    """
    
    # Проверяем — может уже готово
    if (DATASET_OUT / "images" / "train").exists():
        print("✅ Датасет уже подготовлен, пропускаем разбивку.")
        return

    print("📂 Подготовка структуры датасета...")
    
    # Собираем все изображения
    img_dir = DATASET_RAW / "images"
    lbl_dir = DATASET_RAW / "labels"
    
    # Поддерживаем вложенные папки (датасет может быть разбит по классам)
    images = sorted(list(img_dir.rglob("*.jpg")) + 
                    list(img_dir.rglob("*.png")) +
                    list(img_dir.rglob("*.JPG")))
    
    print(f"   Найдено изображений: {len(images)}")
    
    # Оставляем только те, у кого есть разметка
    valid = []
    for img in images:
        # Ищем соответствующий .txt
        rel = img.relative_to(img_dir)
        lbl = lbl_dir / rel.with_suffix(".txt")
        if lbl.exists():
            valid.append((img, lbl))
    
    print(f"   С разметкой: {len(valid)}")
    
    # Перемешиваем и делим
    random.seed(SEED)
    random.shuffle(valid)
    split = int(len(valid) * (1 - VAL_SPLIT))
    train_pairs = valid[:split]
    val_pairs   = valid[split:]
    
    print(f"   Train: {len(train_pairs)} | Val: {len(val_pairs)}")
    
    # Создаём папки и копируем
    for subset, pairs in [("train", train_pairs), ("val", val_pairs)]:
        (DATASET_OUT / "images" / subset).mkdir(parents=True, exist_ok=True)
        (DATASET_OUT / "labels" / subset).mkdir(parents=True, exist_ok=True)
        for img, lbl in pairs:
            shutil.copy2(img, DATASET_OUT / "images" / subset / img.name)
            shutil.copy2(lbl, DATASET_OUT / "labels" / subset / lbl.name)
    
    print("✅ Датасет подготовлен.")


def create_yaml():
    """Создаём dataset.yaml для YOLO."""
    
    # Определяем классы — датасет Mendeley использует:
    # 0 = drone, 1 = bird  (проверь в своих .txt файлах!)
    data = {
        "path": str(DATASET_OUT),
        "train": "images/train",
        "val":   "images/val",
        "nc": 2,
        "names": {0: "drone", 1: "bird"}
    }
    
    yaml_path = DATASET_OUT / "dataset.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    
    print(f"✅ Создан {yaml_path}")
    return yaml_path


def train(yaml_path):
    """Запуск дообучения."""
    
    print("\n🚀 Начинаем дообучение YOLO11n...")
    print(f"   Device: {DEVICE} | Epochs: {EPOCHS} | Batch: {BATCH} | ImgSize: {IMG_SIZE}")
    
    model = YOLO("yolo11n.pt")  # загружает предобученные веса автоматически
    
    results = model.train(
        data       = str(yaml_path),
        epochs     = EPOCHS,
        batch      = BATCH,
        imgsz      = IMG_SIZE,
        device     = DEVICE,
        lr0        = LR0,
        lrf        = LRF,
        patience   = PATIENCE,  # early stopping
        workers    = WORKERS,
        project    = str(RUNS_DIR),
        name       = "drone_bird_v1",
        exist_ok   = True,
        
        # Аугментации — важны для ночных маленьких целей
        hsv_h      = 0.01,   # минимальный сдвиг оттенка (ночью не нужен)
        hsv_s      = 0.3,    # насыщенность
        hsv_v      = 0.5,    # яркость — важно! имитирует разную освещённость
        degrees    = 10.0,   # поворот
        translate  = 0.1,    # сдвиг
        scale      = 0.5,    # масштаб
        fliplr     = 0.5,    # горизонтальное отражение
        mosaic     = 1.0,    # мозаика (помогает с маленькими объектами)
        mixup      = 0.1,    # mixup аугментация
        copy_paste = 0.1,    # copy-paste (хорошо для маленьких объектов)
        
        # Настройки для маленьких объектов
        overlap_mask = True,
        val        = True,
        plots      = True,   # графики loss/mAP
        save       = True,
        save_period= 10,     # сохранять чекпоинт каждые 10 эпох
        
        # Оптимизатор
        optimizer  = "AdamW",
        weight_decay = 0.0005,
        warmup_epochs = 3.0,
    )
    
    best_model = RUNS_DIR / "drone_bird_v1" / "weights" / "best.pt"
    print(f"\n✅ Обучение завершено!")
    print(f"   Лучшая модель: {best_model}")
    return best_model


def validate(best_model_path, yaml_path):
    """Быстрая проверка качества модели после обучения."""
    print("\n🔍 Валидация модели...")
    model = YOLO(str(best_model_path))
    metrics = model.val(data=str(yaml_path), device=DEVICE, imgsz=IMG_SIZE)
    
    print(f"\n📊 Результаты:")
    print(f"   mAP50:    {metrics.box.map50:.3f}")
    print(f"   mAP50-95: {metrics.box.map:.3f}")
    print(f"   Precision:{metrics.box.mp:.3f}")
    print(f"   Recall:   {metrics.box.mr:.3f}")


if __name__ == "__main__":
    prepare_dataset()
    yaml_path = create_yaml()
    best_model = train(yaml_path)
    validate(best_model, yaml_path)
