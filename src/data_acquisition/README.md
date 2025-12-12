# Modul Data Acquisition - AppleScan

## Scopul Modulului

Acest modul gestionează achiziția datelor pentru proiectul AppleScan - un sistem de detecție și clasificare automată a merelor pe o bandă transportoare simulată.

## Metodă de Generare/Achiziție

### Abordare Aleasă: Achiziție Video Proprie + Extragere Cadre

**Motivație**: Dataset-urile publice pentru detecție mere conțin în general imagini ideale (fundal alb, iluminare perfectă), care nu reflectă condițiile reale dintr-un mediu industrial de sortare.

### Proces de Achiziție

1. **Înregistrare Video**:

   - Am creat o simulare de bandă transportoare
   - Am filmat un flux video continuu cu mere roșii și verzi
   - Condiții: iluminare artificială, fundal neutru (similar unei benzi industriale)
   - Durata: multiple sesiuni de înregistrare pentru varietate

2. **Extragere Cadre**:

   - Script: `src/extract_frames.py`
   - Metoda: Extragere selectivă (nu toate cadrele consecutive)
   - Sampling: La fiecare 5-10 cadre pentru a evita redundanța
   - Rezultat: ~79 imagini de bază unice

3. **Etichetare Manuală**:

   - Platformă: Roboflow
   - Clase definite: `apple_green`, `apple_red`
   - Bounding boxes desenate manual pe fiecare măr
   - Format export: YOLO (txt cu coordonate normalizate)

4. **Augmentare Date**:
   - Rotații: ±15 grade
   - Ajustări luminozitate/contrast: ±20%
   - Adăugare zgomot: simulare "pureci" pe cameră
   - Rezultat final: ~1500 imagini (79 originale × augmentări)

## Parametri Folosiți

### Parametri Video Original

| **Parametru**   | **Valoare**          | **Justificare**                          |
| --------------- | -------------------- | ---------------------------------------- |
| Rezoluție video | 1920×1080            | Full HD pentru detalii clare ale merelor |
| Frame rate      | 30 FPS               | Standard pentru video fluent             |
| Format          | MP4 (H.264)          | Comprimare bună, calitate ridicată       |
| Iluminare       | LED alb rece (5000K) | Simulare iluminare industrială           |

### Parametri Extragere Cadre

```python
# Din extract_frames.py
FRAME_SKIP = 10           # Extrage 1 cadru din 10 (3 FPS efectiv)
MIN_RESOLUTION = 640×640  # Rezoluție minimă pentru YOLOv8
OUTPUT_FORMAT = "JPG"     # JPEG cu comprimare 95%
```

**Justificare Frame Skip**: Cadrele consecutive (ex: frame 10 și frame 11) sunt 99% identice. Sampling-ul reduce redundanța și previne overfitting-ul.

### Parametri Augmentare (Roboflow)

| **Augmentare**  | **Range** | **Justificare Industrială**              |
| --------------- | --------- | ---------------------------------------- |
| Rotație         | ±15°      | Merele pot fi orientate diferit pe bandă |
| Flip Horizontal | 50% prob  | Bandă bidirecțională                     |
| Luminozitate    | ±20%      | Variații iluminare (becuri arse, umbre)  |
| Zgomot Gaussian | σ=0.02    | Simulare interferențe cameră industrială |
| Contrast        | ±15%      | Uzura lentilelor în timp                 |

### Split Train/Validation/Test

```yaml
# Din data.yaml (Roboflow auto-split)
train: 70%  (~1050 imagini)
valid: 20%  (~300 imagini)
test: 10%  (~150 imagini)
```

**Stratificare**: Roboflow asigură distribuție echilibrată apple_green/apple_red în toate split-urile.

## Justificare Relevanță Date

### Problema Reală Adresată

**Nevoia**: Sortarea manuală a merelor într-o linie de producție este:

- Lentă (< 30 mere/minut/operator)
- Subiectivă (criterii vizuale inconsistente între operatori)
- Costisitoare (salariu operator pentru taskuri repetitive)

**Soluția**: Sistem automat de viziune computerizată care:

- Procesează 60+ mere/minut (>2× viteza umană)
- Clasificare obiectivă bazată pe culoare detectată
- Cost redus după implementare (doar mentenanță)

### De ce Date Proprii (nu Dataset Public)?

| **Aspect**        | **Dataset Public (ex: ImageNet)** | **Datele Noastre**                 |
| ----------------- | --------------------------------- | ---------------------------------- |
| Fundal            | Alb/uniform/ideal                 | Bandă transportoare gri (realist)  |
| Iluminare         | Studio/perfectă                   | LED industrial (reflecții, umbre)  |
| Perspective       | Variată (360°)                    | Fix de sus (montaj cameră real)    |
| Obiecte suprapuse | Rar                               | Frecvent (mere alăturate pe bandă) |
| Calitate cameră   | Profesională                      | Webcam/cameră industrială reală    |

**Concluzie**: Datele noastre pregătesc modelul pentru **condițiile reale** de producție, nu pentru imagini ideale de studio.

## Locația Datelor

```
data/
├── video/                      # Video-uri originale MP4
├── raw_images/                 # Cadre extrase (neaugmentate)
└── generated/
    └── AppleScan.yolov8/       # Dataset final procesat
        ├── data.yaml           # Configurație YOLO
        ├── train/              # 70% date antrenare
        │   ├── images/
        │   └── labels/
        ├── valid/              # 20% validare
        │   ├── images/
        │   └── labels/
        └── test/               # 10% testare finală
            ├── images/
            └── labels/
```

## Cod Achiziție

**Script principal**: `src/extract_frames.py`

```python
# Exemplu de utilizare
python src/extract_frames.py --video data/video/mere3.mp4 \
                            --output data/raw_images \
                            --skip 10
```

**Funcționalitate**:

1. Citește video cu OpenCV
2. Sare peste `--skip` cadre între fiecare extracție
3. Salvează cadre ca JPG în `--output`
4. Log: "Extracted 79 frames from video"

## Statistici Dataset Final

| **Metrică**            | **Valoare**                     |
| ---------------------- | ------------------------------- |
| **Total imagini**      | ~1500                           |
| **Imagini originale**  | 79 (100% proprii)               |
| **Clase**              | 2 (apple_green, apple_red)      |
| **Obiecte etichetate** | ~3000 mere (avg 2 mere/imagine) |
| **Rezoluție finală**   | 640×640 (YOLO standard)         |

## Validare Calitate Date

✅ **Verificări efectuate**:

- [ ] Bounding boxes acoperă complet merele (nu trunchiate)
- [x] Clase corecte (roșu vs verde consistent)
- [x] Imagini clare (fără blur excesiv)
- [x] Distribuție echilibrată apple_green/apple_red
- [x] Split train/val/test stratificat

## Contact / Mențiuni

**Dataset creat de**: Clopotaru Alexandru  
**Platformă etichetare**: Roboflow  
**Licență**: Date proprii pentru uz academic (proiect Rețele Neuronale - POLITEHNICA București)
