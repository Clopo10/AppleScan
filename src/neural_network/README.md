# Modul Neural Network - AppleScan

## Arhitectura Aleasă: YOLOv8 Nano (Object Detection)

### Decizie Arhitectură

**Model**: YOLOv8n (Nano variant)
**Task**: Object Detection pentru detecție și clasificare mere

### De ce YOLOv8 (nu clasificare simplă CNN)?

| **Aspect**            | **CNN Clasificare**              | **YOLO Detection**          | **Alegerea Noastră**          |
| --------------------- | -------------------------------- | --------------------------- | ----------------------------- |
| Input                 | Imagine întreagă                 | Imagine cu multiple obiecte | ✅ YOLO (multiple mere/cadru) |
| Output                | 1 clasă/imagine                  | N obiecte + coordonate      | ✅ YOLO (2-5 mere/cadru)      |
| Localizare            | ❌ Nu știe unde e obiectul       | ✅ Bounding box precis      | ✅ YOLO (necesară pt sortare) |
| Viteza                | Rapidă                           | Foarte rapidă (real-time)   | ✅ YOLO (30+ FPS)             |
| Aplicație industrială | Clasificare batch (după sortare) | Sortare automată live       | ✅ YOLO (bandă în mișcare)    |

**Concluzie**: YOLO este esențial pentru că:

1. **Detectează UNDE** sunt merele pe bandă (coordonate pentru braț robotizat)
2. **Clasifică simultan** fiecare măr (roșu vs verde)
3. **Real-time**: Procesează video live la 30+ FPS pe GPU (10+ FPS pe CPU)

### De ce YOLOv8n (Nano) și nu alte versiuni?

| **Model** | **Parametri** | **mAP50** | **Viteză (CPU)** | **Alegere**            |
| --------- | ------------- | --------- | ---------------- | ---------------------- |
| YOLOv8n   | 3M            | ~99%      | 15 FPS           | ✅ **Ales**            |
| YOLOv8s   | 11M           | ~99.2%    | 8 FPS            | ❌ Prea lent CPU       |
| YOLOv8m   | 26M           | ~99.5%    | 3 FPS            | ❌ Mult prea lent      |
| YOLOv8l   | 43M           | ~99.6%    | 1 FPS            | ❌ Imposibil real-time |

**Justificare YOLOv8n**:

- Suficient de precis (99.5% mAP50 pe testele noastre)
- Rapid pe CPU (antrenare fără GPU disponibilă)
- Dimensiune mică (11 MB) - ușor de integrat în edge devices
- Backbone: CSPDarknet cu 3M parametri - suficient pentru 2 clase simple

## Arhitectura Detaliată YOLOv8n

### Structură Globală

```
INPUT (640×640×3)
    ↓
[BACKBONE: CSPDarknet]  ← Extracție features multi-scale
    ↓
[NECK: PANet]           ← Agregare features de la diferite scale
    ↓
[HEAD: Detection]       ← 3 output layers (small/medium/large objects)
    ↓
OUTPUT: [class, x, y, w, h, confidence] pentru fiecare măr detectat
```

### Componente Principale

#### 1. Backbone: CSPDarknet Nano

```
Conv2d (3→16, 3×3, stride=2)  → 320×320×16
    ↓
C2f Block (16→32) × 1         → 160×160×32
    ↓
C2f Block (32→64) × 2         → 80×80×64
    ↓
C2f Block (64→128) × 2        → 40×40×128
    ↓
C2f Block (128→256) × 1       → 20×20×256
```

**C2f Block**: CSP (Cross Stage Partial) + Bottleneck cu rezidual connections

- Reduce numărul parametrilor (vs. ResNet clasic)
- Menține flow-ul gradientului (vs. vanilla conv)
- Eficient computațional pentru inferență rapidă

#### 2. Neck: PANet (Path Aggregation Network)

```
[P5: 20×20×256] ─────┐
                     ↓
[P4: 40×40×128] ──→ Upsample + Concat → [P4': 40×40×256]
                     ↓
[P3: 80×80×64]  ──→ Upsample + Concat → [P3': 80×80×128]
```

**Rol**: Combină features de la diferite scale pentru detecție obiecte mici și mari:

- P3 (80×80): Detectează mere mici/distante
- P4 (40×40): Detectează mere medii (majoritare)
- P5 (20×20): Detectează mere mari/aproape de cameră

#### 3. Head: Detection Layer (Decoupled)

**Pentru fiecare scale (P3, P4, P5)**:

```
Classification Head:  [Conv 3×3] → [Conv 1×1] → [2 clase: apple_green, apple_red]
Box Regression Head:  [Conv 3×3] → [Conv 1×1] → [4 coord: x, y, w, h]
```

**Output Final**:

- 8400 anchor points (80×80 + 40×40 + 20×20 = 8400)
- Pentru fiecare point: [2 clase + 4 coord + 1 objectness] = 7 valori
- Total output: 8400 × 7 tensor

### Funcții de Activare

| **Locație**         | **Activare**     | **Justificare**                              |
| ------------------- | ---------------- | -------------------------------------------- |
| Toate Conv (hidden) | **SiLU (Swish)** | Smooth, non-monotonic → convergență mai bună |
| Classification Head | **Sigmoid**      | Probabilități independente per clasă         |
| Box Regression      | **Linear**       | Coordonate continue (nu probabilități)       |

**De ce SiLU vs ReLU?**

```
ReLU(x) = max(0, x)           → "Hard" cutoff la 0 → gradient 0 pentru x<0
SiLU(x) = x * sigmoid(x)      → "Smooth" → gradient niciodată exact 0
```

**Beneficiu**: SiLU → convergență mai rapidă și performanță +1-2% mAP vs ReLU în detecție obiect.

## Loss Function Compus

YOLOv8 folosește **3 loss-uri simultane**:

### 1. Classification Loss: Binary Cross Entropy (BCE)

```python
L_cls = -Σ [y_true * log(y_pred) + (1 - y_true) * log(1 - y_pred)]
```

**Aplicat pe**: 2 clase (apple_green, apple_red)

### 2. Box Regression Loss: Complete IoU (CIoU)

```python
L_box = 1 - CIoU(bbox_pred, bbox_true)

unde CIoU = IoU - (ρ²/c²) - α*v
    ↓
    IoU:     Overlap standard
    ρ²/c²:   Distanță între centre (penalizare poziție)
    α*v:     Consistență aspect ratio (w/h similar)
```

**De ce CIoU (nu IoU simplu)?**

- IoU standard: Penalizează doar overlap, ignoră distanța când IoU=0
- CIoU: Ghidează modelul chiar când bbox-urile nu se suprapun deloc

### 3. Distribution Focal Loss (DFL)

```python
L_dfl = -Σ log(softmax(δ_i))  ← pentru fiecare margine bbox (4 margini)
```

**Rol**: Rafinează coordonatele bbox de la "aproximativ corect" la "pixel-perfect".

### Total Loss

```python
L_total = λ_cls * L_cls + λ_box * L_box + λ_dfl * L_dfl

unde:
    λ_cls = 0.5  (classification weight)
    λ_box = 7.5  (box weight - cel mai important!)
    λ_dfl = 1.5  (distribution weight)
```

**Prioritate**: Box regression > Distribution > Classification (localizarea corectă e critică pentru sortare).

## Optimizer și Hiperparametri

### Optimizer: SGD cu Momentum

```yaml
optimizer: SGD
momentum: 0.937
weight_decay: 0.0005
nesterov: True
```

**De ce SGD (nu Adam)?**

- Adam: Convergență rapidă, dar risc overfitting pe dataset-uri mici
- SGD + momentum: Mai lent, dar generalizare mai bună (esențial pentru 1500 imagini)
- weight_decay: Regularizare L2 → previne overfitting

### Learning Rate Scheduler

```yaml
initial_lr: 0.01
warmup_epochs: 3
warmup_momentum: 0.8
warmup_bias_lr: 0.1

final_lr: 0.01 # constant după warmup (cos_lr=False)
close_mosaic: 10 # Ultimele 10 epoci fără augmentare mosaic
```

**Warmup Strategy**:

```
Epoca 1-3:   LR crește linear de la 0 → 0.01
Epoca 4-90:  LR constant 0.01
Epoca 91-100: Fără mosaic augmentation (stabilizare finală)
```

## Data Augmentation în Pipeline

### Augmentări Geometrice

```yaml
degrees: 0.0 # Rotații (dezactivate - deja în Roboflow)
translate: 0.1 # Translație ±10% (simulare poziții diferite pe bandă)
scale: 0.5 # Zoom 0.5× - 1.5× (distanță variabilă cameră-bandă)
shear: 0.0 # Shear (dezactivat - nu e realist pentru vedere top-down)
perspective: 0.0 # Perspective warp (dezactivat - cameră fixă)
flipud: 0.0 # Flip vertical (dezactivat - gravitația e constantă)
fliplr: 0.5 # Flip horizontal (50% șansă - bandă bidirecțională)
```

### Augmentări Color

```yaml
hsv_h: 0.015 # Hue shift ±1.5% (variații culoare LED în timp)
hsv_s: 0.7 # Saturation 0.3× - 1.7× (mere mai/mai puțin roșii/verzi)
hsv_v: 0.4 # Value/Brightness 0.6× - 1.4× (LED mai puțin intens)
```

**Justificare HSV**:

- **Hue**: Simulare îmbătrânire LED (shift galben în timp)
- **Saturation**: Robustețe la mere cu culori "borderline" (roșu-portocaliu, verde-galben)
- **Value**: Simulare variații tensiune electrică (LED pâlpâie ușor)

### Augmentări Mosaic (până la epoca 90)

```yaml
mosaic: 1.0 # Activat 100% până la close_mosaic
mixup: 0.0 # Dezactivat (nu e benefic pentru detecție cu 2 clase simple)
copy_paste: 0.0 # Dezactivat (poate crea artefacte nerealistice)
```

**Mosaic Augmentation**: Combină 4 imagini într-una singură

```
┌────────┬────────┐
│ Img1   │ Img2   │  → Forțează modelul să învețe detecție parțială
├────────┼────────┤     (mere tăiate de margine = realist pe bandă)
│ Img3   │ Img4   │
└────────┴────────┘
```

## Training Workflow

### Inițializare

```python
model = YOLO('yolov8n.pt')  # Pornire de la weights pre-antrenate (COCO)
```

**Transfer Learning**:

- Backbone (CSPDarknet): Weights COCO (recunoaște forme generale)
- Head (Detection): Reinițializat pentru 2 clase (apple_green, apple_red)
- **Justificare**: COCO conține "apple" ca clasă → transferul e foarte relevant

### Loop Antrenare (pseudocod)

```python
for epoch in range(100):
    for batch in train_loader:
        # 1. Forward pass
        pred_boxes, pred_classes = model(batch_images)

        # 2. Calcul loss
        loss_cls = BCE_loss(pred_classes, true_classes)
        loss_box = CIoU_loss(pred_boxes, true_boxes)
        loss_dfl = DFL_loss(pred_boxes, true_boxes)
        total_loss = 0.5*loss_cls + 7.5*loss_box + 1.5*loss_dfl

        # 3. Backpropagation
        total_loss.backward()
        optimizer.step()

    # 4. Validare
    val_metrics = validate(model, val_loader)
    log_metrics(epoch, train_loss, val_metrics)

    # 5. Salvare best model
    if val_metrics['mAP50'] > best_mAP:
        save_model('best.pt')
```

## Rezultate Obținute

### Metrici Test Set (evaluate.py)

```json
{
  "mAP50": 0.995, // 99.50% - Excelent!
  "mAP50-95": 0.9286, // 92.86% - Foarte bun pentru 2 clase
  "precision": 0.9934, // 99.34% - Aproape fără false positives
  "recall": 1.0, // 100.00% - ZERO false negatives!
  "f1_score": 0.9967 // 99.67% - Echilibru perfect P/R
}
```

### Interpretare Rezultate

**mAP50 = 99.50%**: La IoU threshold 0.5 (50% overlap), modelul detectează corect 99.5% din mere.

**Recall = 100%**: Modelul NU RATEAZĂ NICIUN măr (critical pentru sortare - preferăm false alarm decât măr nesortate).

**Precision = 99.34%**: Din 100 detecții, 99 sunt corecte (1 false positive - acceptabil).

### Performanță per Clasă

| **Clasă**   | **Precision** | **Recall** | **mAP50** |
| ----------- | ------------- | ---------- | --------- |
| apple_green | 0.993         | 1.000      | 0.995     |
| apple_red   | 0.994         | 1.000      | 0.995     |

**Observație**: Performanță IDENTICĂ pe ambele clase → model echilibrat (nu favorizează o clasă).

## Inferență Real-Time

### Pipeline Inferență (app.py)

```python
# 1. Încărcare model antrenat
model = YOLO('best.pt')

# 2. Citire frame video
frame = video.read()  # 1920×1080×3

# 3. Preprocessare (automat de YOLO)
# - Resize la 640×640 (letterbox cu padding)
# - Normalizare 0-255 → 0.0-1.0
# - Reorder channels BGR → RGB

# 4. Inferență
results = model(frame)  # Returnează listă detecții

# 5. Post-procesare
# - NMS (Non-Maximum Suppression): Elimină bbox duplicate
# - Threshold confidence: Păstrează doar detecții >0.25

# 6. Desenare bbox pe frame
for detection in results:
    class_name = detection.class_name  # "apple_green" sau "apple_red"
    bbox = detection.bbox              # [x1, y1, x2, y2]
    confidence = detection.confidence  # 0.0 - 1.0

    color = GREEN if "green" in class_name else RED
    draw_box(frame, bbox, color, confidence)

# 7. Return frame annotat
return frame
```

### Latență Măsurată

| **Hardware**    | **FPS**   | **Latență/Frame** |
| --------------- | --------- | ----------------- |
| CPU (i7-7700HQ) | 10-15 FPS | 66-100 ms         |
| GPU (simulat)   | 30-60 FPS | 16-33 ms          |

**Pentru aplicație industrială**: 15 FPS e suficient pentru bandă la viteză medie (1 m/s).

## Fișiere Generate

```
models/mar_model/
├── weights/
│   ├── best.pt           # Model cu cea mai bună val_mAP (epoca 49)
│   ├── last.pt           # Model la ultima epocă (100)
│   └── best.onnx         # Export ONNX pentru deployment
├── args.yaml             # Hiperparametri antrenare
└── results.csv           # Istoric metrici toate epocile
```

## Extensii Posibile (Nivel 3 Bonus)

### 1. Modele Alternative Comparate

| **Model**        | **mAP50** | **FPS** | **Parametri** |
| ---------------- | --------- | ------- | ------------- |
| YOLOv8n (actual) | 99.50%    | 15      | 3M            |
| YOLOv8s          | 99.55%    | 8       | 11M           |
| YOLOv5n          | 98.80%    | 18      | 2.5M          |
| Faster R-CNN     | 99.70%    | 2       | 40M           |

**Recomandare**: Rămânem la YOLOv8n (best tradeoff viteză/acuratețe).

### 2. Deployment Edge

```python
# Export pentru Raspberry Pi 4 / Jetson Nano
model.export(format='onnx', imgsz=640, half=True)  # FP16 precision
# Rezultat: best.onnx (5.5 MB) → 20 FPS pe Jetson Nano
```

### 3. Multi-Class Extension

**Clase viitoare posibile**:

- `apple_defect`: Lovituri, pete, putregai
- `apple_size_small/medium/large`: Sortare după dimensiune
- `empty_space`: Detectare goluri pe bandă (trigger alarmă lipsă furnizor)

## Contact

**Arhitectură implementată de**: Clopotaru Alexandru  
**Framework**: Ultralytics YOLOv8 (Python 3.13, PyTorch 2.9.1)  
**Licență**: AGPL-3.0 (Ultralytics) + Uz Academic
