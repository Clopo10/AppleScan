# Web UI - AppleScan

## Descriere

Interfață web Flask pentru vizualizarea în timp real a detecției și clasificării merelor pe banda transportoare.

## Tehnologii

- **Backend**: Flask (Python)
- **Frontend**: HTML5 + MJPEG streaming
- **Model**: YOLOv8n (încărcat la pornire)
- **Video Processing**: OpenCV

## Structură

```
src/web/
├── app.py              # Server Flask principal
└── templates/
    └── index.html      # Pagină HTML cu video stream
```

## Instrucțiuni Lansare

### 1. Instalare Dependențe (dacă nu ați făcut deja)

```powershell
pip install flask opencv-python ultralytics
```

### 2. Pornire Server

```powershell
# Din folderul rădăcină AppleScan/
python src\web\app.py
```

**Output așteptat**:

```
[INFO] Incarc modelul de la: C:\Users\...\AppleScan\data\models\mar_model\weights\best.pt
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.X:5000
Press CTRL+C to quit
```

### 3. Accesare în Browser

Deschideți browser la una din adresele:

- **Local**: http://localhost:5000
- **LAN**: http://192.168.1.X:5000 (pentru acces de pe telefon/laptop în aceeași rețea)

### 4. Utilizare UI

**Interfață**:

- Video stream live cu mere detectate
- Bounding boxes colorate:
  - **Verde**: `apple_green` (mere verzi)
  - **Roșu**: `apple_red` (mere roșii)
- Label-uri cu clasă + confidence score (ex: "apple_green 0.98")

**Video Loop**:

- Video-ul se repetă automat la final (simulare bandă continuă)
- Pentru schimbare video: modificați `VIDEO_PATH` în `app.py`

### 5. Oprire Server

În terminalul PowerShell unde rulează serverul:

```
Ctrl + C
```

## Configurare Avansată

### Schimbare Sursă Video

**Editați în `app.py`**:

```python
# Linia 11
VIDEO_PATH = os.path.join(BASE_DIR, 'data', 'video', 'NUMELE_FISIER.mp4')
```

**Opțiuni sursă**:

```python
# Pentru webcam live
cap = cv2.VideoCapture(0)  # 0 = webcam implicită

# Pentru fișier video
cap = cv2.VideoCapture('data/video/mere3.mp4')

# Pentru stream IP camera
cap = cv2.VideoCapture('rtsp://192.168.1.100:554/stream')
```

### Rezoluție Video

**Editați în `app.py` înainte de loop-ul `while True`**:

```python
# După linia 20
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

## Arhitectura Aplicației

### Flow Procesare

```
[Video Source]
    ↓ read()
[Frame 1920×1080×3]
    ↓ model(frame)
[YOLOv8 Inference]
    ↓ results
[Detections: [(class, bbox, conf), ...]]
    ↓ plot()
[Annotated Frame cu bbox]
    ↓ imencode('.jpg')
[JPEG Bytes]
    ↓ yield
[MJPEG Stream HTTP]
    ↓
[Browser: <img src="/video_feed">]
```

### Endpoints Flask

| **Route**     | **Metodă** | **Descriere**                                   |
| ------------- | ---------- | ----------------------------------------------- |
| `/`           | GET        | Pagină HTML principală (index.html)             |
| `/video_feed` | GET        | Stream MJPEG continuu (generare frame-by-frame) |

### Template HTML

**Fișier**: `templates/index.html`

## Troubleshooting

### Eroare: "Could not open video"

**Cauză**: Fișier video lipsă sau cale incorectă.

**Soluție**:

```powershell
# Verificare existență fișier
Test-Path "data\video\mere3.mp4"  # Trebuie: True

# Verificare format video (MP4, AVI, MKV suportate)
ffprobe data\video\mere3.mp4
```

### Eroare: "Model not found"

**Cauză**: Model `best.pt` nu există sau cale greșită.

**Soluție**:

```powershell
# Verificare model antrenat
Test-Path "data\models\mar_model\weights\best.pt"  # Trebuie: True

# Dacă lipsește → antrenați modelul
python src\train_yolo.py
```

### Video se blochează/laggy

**Cauză**: CPU prea încărcat cu inferență.

**Soluții**:

1. Reduceți rezoluție: `model(frame, imgsz=320)`
2. Skip frames: procesați doar 1 din 2 frame-uri
3. Folosiți GPU: instalați `torch` cu CUDA

### Browser nu se conectează

**Cauză**: Firewall blochează portul 5000.

**Soluție Windows**:

```powershell
# Adăugare regulă firewall
New-NetFirewallRule -DisplayName "Flask 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

## Screenshot Demo

**Locație**: `docs/screenshots/inference_real.png`

**Framework**: Flask 3.0  
**Streaming Protocol**: MJPEG (Motion JPEG over HTTP)
