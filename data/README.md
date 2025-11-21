## 2. Descrierea Setului de Date

### 2.1 Sursa datelor

- **Origine:** Date proprii (înregistrări video cu banda transportoare simulată) + Dataset public
- **Modul de achiziție:** Fișier extern (Video .mp4 convertit în cadre)
- **Perioada / condițiile colectării:** Noiembrie 2024 - Ianuarie 2025, condiții de iluminare artificială (interior), fundal neutru (bandă transportoare).

### 2.2 Caracteristicile dataset-ului

- **Număr total de observații:** ~1,500 imagini (extrase din video + surse externe).
- **Număr de caracteristici (features):** Rezoluție pixeli (W x H x 3) + 5 atribute per etichetă (YOLO format).
- **Tipuri de date:** Imagini (RGB) + Text (Adnotări)
- **Format fișiere:** JPG/PNG (Imagini) / TXT (Etichete YOLO)

### 2.3 Descrierea fiecărei caracteristici

| **Caracteristică** | **Tip** | **Unitate**  | **Descriere**                              | **Domeniu valori**                 |
| ------------------ | ------- | ------------ | ------------------------------------------ | ---------------------------------- |
| class_id           | numeric | -            | ID-ul clasei obiectului                    | {0: Măr_Bun, 1: Măr_Defect, ...}   |
| x_center           | numeric | raport (0-1) | Coordonata X a centrului bounding box-ului | 0.0 – 1.0 (normalizat la lățime)   |
| y_center           | numeric | raport (0-1) | Coordonata Y a centrului bounding box-ului | 0.0 – 1.0 (normalizat la înălțime) |
| width              | numeric | raport (0-1) | Lățimea bounding box-ului                  | 0.0 – 1.0                          |
| height             | numeric | raport (0-1) | Înălțimea bounding box-ului                | 0.0 – 1.0                          |

---

## 3. Analiza Exploratorie a Datelor (EDA) – Sintetic

### 3.1 Statistici descriptive aplicate

- **Distributia claselor** Histograme pentru a vedea raportul dintre "Mere Bune" vs. "Mere Defecte".
- **Dimensiunea obiectelor** Analiza ariei bounding box-urilor (mici vs. mari) pentru a vedea dacă merele sunt filmate prea de departe sau prea de aproape.
- **Heatmap pozitional** Unde apar merele cel mai des în cadru? (De obicei pe centrul benzii).
- **Raportul de aspect** Dacă merele sunt deformate sau alungite în imagini.

### 3.2 Analiza calității datelor

- **Imagini neclare** Identificarea cadrelor extrase din video în momente de mișcare rapidă (motion blur).
- **Etichete lipsa (Background images)** Verificarea imaginilor care nu au fișier .txt asociat (acestea sunt folosite ca "negative samples" - fundal gol).
- **Suprapuneri (Occlusions)** Identificarea vizuală a cadrelor unde merele se acoperă reciproc (dificil pentru model).

### 3.3 Probleme identificate

- Dezechilibru de clasă (Class Imbalance): Avem 1000 de mere bune și doar 200 de mere defecte (modelul va tinde să ignore defectele).
- Iluminare variabilă: Umbre puternice în unele cadre video care pot fi confundate cu pete (defecte).
- Redundanță: Cadrele extrase consecutiv din video (ex: cadrul 10 și cadrul 11) sunt 99% identice, ceea ce duce la overfitting.

---

## 4. Preprocesarea Datelor

### 4.1 Curățarea datelor

- **Eliminare duplicatelor** Ștergerea cadrelor consecutive foarte similare (Sampling la fiecare 5 sau 10 cadre din video).
- **Filtrare** Eliminarea manuală a imaginilor extrem de neclare.
- **Corectare Etichete** Verificarea în Roboflow/CVAT dacă bounding box-urile sunt strânse pe măr.

### 4.2 Transformarea caracteristicilor

- **Redimensionare (Resizing)** Toate imaginile aduse la 640x640 pixeli (standard YOLOv8).
- **Normalizare** Pixelii (0-255) sunt împărțiți la 255 de către model intern (0.0 - 1.0).
- **Augmentare:**
  - Flip Horizontal / Vertical: Simularea merelor în alte poziții.
  - Rotație: +/- 15 grade.
  - Ajustare Luminozitate/Contrast: +/- 20% pentru a face modelul robust la schimbări de lumină.
  - Noise: Adăugarea de zgomot digital ("pureci") pentru robustețe.

### 4.3 Structurarea seturilor de date

**Împărțire recomandată:**

- 70% – train
- 20% – validation
- 10% – test

**Principii respectate:**

- Stratificare pentru clasificare
- Fără scurgere de informație (data leakage)
- Statistici calculate DOAR pe train și aplicate pe celelalte seturi

### 4.4 Salvarea rezultatelor preprocesării

- Date preprocesate în `data/processed/`
- Seturi train/val/test în foldere dedicate
- Parametrii de preprocesare în `config/preprocessing_config.*` (opțional)

---

## 5. Fișiere Generate în Această Etapă

- `data/raw_video/` – fișierele video originale (.mp4).
- `dataset/train/, dataset/valid/` – imaginile și etichetele gata de antrenare.
- `data/data.yaml/` – fișierul de configurare pentru YOLOv8.
- `src/preprocessing/frame_extractor.py` – scriptul care scoate pozele din video.

---

## 6. Stare Etapă (de completat de student)

- [x] Structură repository configurată
- [ ] Dataset analizat (EDA realizată)
- [ ] Date preprocesate
- [ ] Seturi train/val/test generate
- [x] Documentație actualizată în README
