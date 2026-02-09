# 📘 README – Etapa 4: Arhitectura Completă a Aplicației SIA bazată pe Rețele Neuronale

**Disciplina:** Rețele Neuronale  
**Instituție:** POLITEHNICA București – FIIR  
**Student:** Clopotaru Alexandru  
**Link Repository GitHub** https://github.com/Clopo10/AppleScan
**Data:** 5.12.2025

---

## Scopul Etapei 4

Această etapă corespunde punctului **5. Dezvoltarea arhitecturii aplicației software bazată pe RN** din lista de 9 etape - slide 2 **RN Specificatii proiect.pdf**.

**Trebuie să livrați un SCHELET COMPLET și FUNCȚIONAL al întregului Sistem cu Inteligență Artificială (SIA). In acest stadiu modelul RN este doar definit și compilat (fără antrenare serioasă).**

### IMPORTANT - Ce înseamnă "schelet funcțional":

**CE TREBUIE SĂ FUNCȚIONEZE:**

- Toate modulele pornesc fără erori
- Pipeline-ul complet rulează end-to-end (de la date → până la output UI)
- Modelul RN este definit și compilat (arhitectura există)
- Web Service/UI primește input și returnează output

  **CE NU E NECESAR ÎN ETAPA 4:**

- Model RN antrenat cu performanță bună
- Hiperparametri optimizați
- Acuratețe mare pe test set
- Web Service/UI cu funcționalități avansate

**Scopul anti-plagiat:** Nu puteți copia un notebook + model pre-antrenat de pe internet, pentru că modelul vostru este NEANTRENAT în această etapă. Demonstrați că înțelegeți arhitectura și că ați construit sistemul de la zero.

---

## Livrabile Obligatorii

### 1. Tabelul Nevoie Reală → Soluție SIA → Modul Software (max ½ pagină)

Completați in acest readme tabelul următor cu **minimum 2-3 rânduri** care leagă nevoia identificată în Etapa 1-2 cu modulele software pe care le construiți (metrici măsurabile obligatoriu):

| **Nevoie reală concretă**                                   | **Cum o rezolvă SIA-ul vostru**                                                                       | **Modul software responsabil** |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------ |
| Sortarea manuală a merelor este lentă și subiectivă         | Detecție automată defecte vizuale (lovituri, pete) cu model YOLOv8 în timp real (<70ms/cadru)         | RN + Web Service               |
| Monitorizarea calității loturilor de producție în timp real | Dashboard Web care numără automat merele bune vs. defecte și afișează statistici live (95% acuratețe) | Data Logging + RN + UI         |

**Instrucțiuni:**

- Fiți concreti (nu vagi): "detectare fisuri sudură" ✓, "îmbunătățire proces" ✗
- Specificați metrici măsurabile: "< 2 secunde", "> 95% acuratețe", "reducere 20%"
- Legați fiecare nevoie de modulele software pe care le dezvoltați

---

### 2. Contribuția Voastră Originală la Setul de Date – MINIM 40% din Totalul Observațiilor Finale

**Regula generală:** Din totalul de **N observații finale** în `data/processed/`, **minimum 40%** trebuie să fie **contribuția voastră originală**.

#### Cum se calculează 40%:

**Exemplu 1 - Dataset DOAR public în Etapa 3:**

```
Etapa 3: Ați folosit 10,000 samples dintr-o sursa externa (ex: Kaggle)
Etapa 4: Trebuie să generați/achiziționați date astfel încât:

Opțiune A: Adăugați 6,666 samples noi → Total 16,666 (6,666/16,666 = 40%)
Opțiune B: Păstrați 6,000 publice + 4,000 generate → Total 10,000 (4,000/10,000 = 40%)
```

**Exemplu 2 - Dataset parțial original în Etapa 3:**

```
Etapa 3: Ați avut deja 3,000 samples generate + 7,000 publice = 10,000 total
Etapa 4: 3,000 samples existente numără ca "originale"
        Dacă 3,000/10,000 = 30% < 40% → trebuie să generați încă ~1,700 samples
        pentru a ajunge la 4,700/10,000 = 47% > 40% ✓
```

**Exemplu 3 - Dataset complet original:**

```
Etapa 3-4: Generați toate datele (simulare, senzori proprii, etichetare manuală - varianta recomandata)
           → 100% original ✓ (depășește cu mult 40% - FOARTE BINE!)
```

#### Tipuri de contribuții acceptate (exemple din inginerie):

Alegeți UNA sau MAI MULTE dintre variantele de mai jos și **demonstrați clar în repository**:

| **Tip contribuție** | **Exemple concrete din inginerie** | **Dovada minimă cerută** |
| ------------------- | ---------------------------------- | ------------------------ |

| **Date achiziționate cu senzori proprii** | Am realizat o achiziție de date proprie prin filmarea unui flux video cu mere. Din acest video, am utilizat scriptul extract_frames.py pentru a extrage cadre relevante. | data/video (video-uri proprii) & data/raw_images (poze proprii) & src/extract_frames.py (script extragere poze) |
| **Etichetare/adnotare manuală** | Am realizat etichetarea manuală folosind platforma Roboflow, definind clasele "apple_green" și "apple_red" și am aplicat tehnici de augmentare (rotire, modificare luminozitate) pentru a crește robustețea modelului la variații de lumină. | data/AppleScan.yolov8 (datele etichetate manual), in README.roboflow.txt se poate vedea nr. total de poze (79) si tipurile de augmentari folosite |

#### Declarație obligatorie în README:

Scrieți clar în acest README (Secțiunea 2):

```markdown
### Contribuția originală la setul de date:

**Total observații finale:** ~100 imagini (după Etapa 3 + Etapa 4 - augmentate din video propriu)
**Observații originale:** 100 (100%)

**Tipul contribuției:**
[ ] Date generate prin simulare fizică  
[X] Date achiziționate cu senzori proprii  
[X] Etichetare/adnotare manuală  
[ ] Date sintetice prin metode avansate

**Descriere detaliată:**
Pentru acest proiect, nu am utilizat dataset-uri publice generice, deoarece acestea conțin adesea imagini ideale, pe fundal alb, care nu reflectă realitatea de pe o bandă transportoare. Am realizat o achiziție de date proprie prin filmarea unui flux video cu mere (roșii și verzi). Din acest video, am utilizat scriptul extract_frames.py pentru a extrage cadre relevante. Ulterior, am realizat etichetarea manuală a acestora folosind platforma Roboflow, definind clasele mar_bun și mar_defect și am aplicat tehnici de augmentare (rotire, modificare luminozitate) pentru a crește robustețea modelului la variații de lumină.

**Locația codului:** `src/extract_frames.py`
**Locația datelor:** `data/raw_images` (sursele) si `data/AppleScan.yolov8/` (procesate)

**Dovezi:**

- Setul de date structurat în folderul `data/`
- Fișierul `data/AppleScan.yolov8/data.yaml` care atestă structura custom.
```

#### Exemple pentru "contribuție originală":

-Simulări fizice realiste cu ecuații și parametri justificați  
-Date reale achiziționate cu senzori proprii (setup documentat)  
-Augmentări avansate cu justificare fizică (ex: simulare perspective camera industrială)

#### Atenție - Ce NU este considerat "contribuție originală":

- Augmentări simple (rotații, flips, crop) pe date publice
- Aplicare filtre standard (Gaussian blur, contrast) pe imagini publice
- Normalizare/standardizare (aceasta e preprocesare, nu generare)
- Subset dintr-un dataset public (ex: selectat 40% din ImageNet)

---

### 3. Diagrama State Machine a Întregului Sistem (OBLIGATORIE)

**Cerințe:**

- **Minimum 4-6 stări clare** cu tranziții între ele
- **Formate acceptate:** PNG/SVG, pptx, draw.io
- **Locație:** `docs/state_machine.*` (orice extensie)
- **Legendă obligatorie:** 1-2 paragrafe în acest README: "De ce ați ales acest State Machine pentru nevoia voastră?"

**Stări tipice pentru un SIA:**

```
IDLE → ACQUIRE_DATA → PREPROCESS → INFERENCE → DISPLAY/ACT → LOG → [ERROR] → STOP
                ↑______________________________________________|
```

**Exemple concrete per domeniu de inginerie:**

#### A. Monitorizare continuă proces industrial (vibrații motor, temperaturi, presiuni):

```
IDLE → START_ACQUISITION → COLLECT_SENSOR_DATA → BUFFER_CHECK →
PREPROCESS (filtrare, FFT) → RN_INFERENCE → THRESHOLD_CHECK →
  ├─ [Normal] → LOG_RESULT → UPDATE_DASHBOARD → COLLECT_SENSOR_DATA (loop)
  └─ [Anomalie] → TRIGGER_ALERT → NOTIFY_OPERATOR → LOG_INCIDENT →
                  COLLECT_SENSOR_DATA (loop)
       ↓ [User stop / Emergency]
     SAFE_SHUTDOWN → STOP
```

#### B. Clasificare imagini defecte producție (suduri, suprafețe, piese):

```
IDLE → WAIT_TRIGGER (senzor trecere piesă) → CAPTURE_IMAGE →
VALIDATE_IMAGE (blur check, brightness) →
  ├─ [Valid] → PREPROCESS (resize, normalize) → RN_INFERENCE →
              CLASSIFY_DEFECT →
                ├─ [OK] → LOG_OK → CONVEYOR_PASS → IDLE
                └─ [DEFECT] → LOG_DEFECT → TRIGGER_REJECTION → IDLE
  └─ [Invalid] → ERROR_IMAGE_QUALITY → RETRY_CAPTURE (max 3×) → IDLE
       ↓ [Shift end]
     GENERATE_REPORT → STOP
```

#### C. Predicție traiectorii robot mobil (AGV, AMR în depozit):

```
IDLE → LOAD_MAP → RECEIVE_TARGET → PLAN_PATH →
VALIDATE_PATH (obstacle check) →
  ├─ [Clear] → EXECUTE_SEGMENT → ACQUIRE_SENSORS (LIDAR, IMU) →
              RN_PREDICT_NEXT_STATE → UPDATE_TRAJECTORY →
                ├─ [Target reached] → STOP_AT_TARGET → LOG_MISSION → IDLE
                └─ [In progress] → EXECUTE_SEGMENT (loop)
  └─ [Obstacle detected] → REPLAN_PATH → VALIDATE_PATH
       ↓ [Emergency stop / Battery low]
     SAFE_STOP → LOG_STATUS → STOP
```

#### D. Predicție consum energetic (turbine eoliene, procese batch):

```
IDLE → LOAD_HISTORICAL_DATA → ACQUIRE_CURRENT_CONDITIONS
(vânt, temperatură, demand) → PREPROCESS_FEATURES →
RN_FORECAST (24h ahead) → VALIDATE_FORECAST (sanity checks) →
  ├─ [Valid] → DISPLAY_FORECAST → UPDATE_CONTROL_STRATEGY →
              LOG_PREDICTION → WAIT_INTERVAL (1h) →
              ACQUIRE_CURRENT_CONDITIONS (loop)
  └─ [Invalid] → ERROR_FORECAST → USE_FALLBACK_MODEL → LOG_ERROR →
                ACQUIRE_CURRENT_CONDITIONS (loop)
       ↓ [User request report]
     GENERATE_DAILY_REPORT → STOP
```

**Notă pentru proiecte simple:**
Chiar dacă aplicația voastră este o clasificare simplă (user upload → classify → display), trebuie să modelați fluxul ca un State Machine. Acest exercițiu vă învață să gândiți modular și să anticipați toate stările posibile (inclusiv erori).

**Legendă obligatorie (scrieți în README):**

```markdown
### Justificarea State Machine-ului ales:

Am ales o arhitectură de tip Monitorizare Continuă (Pipeline de Inspecție Video) deoarece proiectul simulează o bandă transportoare industrială unde fluxul de date este constant.

Stările principale sunt:

1. IDLE: Sistemul așteaptă încărcarea fluxului video sau pornirea serverului Flask.
2. ACQUIRE_FRAME: Extragerea unui cadru individual din buffer-ul video (folosind OpenCV).
3. PREPROCESS: Redimensionarea imaginii la 640x640 (format YOLO) și normalizarea pixelilor.
4. INFERENCE (YOLOv8): Rularea modelului neural pentru a obține coordonatele (Bounding Boxes) și clasele.
5. DECISION & DRAW: Verificarea pragului de încredere (Confidence Score > 0.5). Dacă este valid, se desenează conturul (Verde = Bun, Roșu = Defect).
6. UPDATE_UI: Trimiterea cadrului procesat către interfața Web prin protocol MJPEG.
7. ERROR: Gestionarea cazurilor în care video-ul se termină (se face loop) sau camera nu răspunde.

Tranzițiile critice sunt:

- ACQUIRE_FRAME → ERROR: Dacă cap.read() returnează False (video terminat sau eroare citire).
- INFERENCE → DECISION: Realizată automat de biblioteca Ultralytics.

Starea ERROR este esențială pentru că în contextul unei benzi de sortare industriale, pot apărea defecțiuni critice care ar compromite calitatea lotului. De exemplu: camera video se poate deconecta sau bloca din cauza supraîncălzirii, iluminarea artificială se poate defecta, sau fișierul video sursă se poate corupe/termina brusc. Sistemul trebuie să gestioneze aceste erori prin intrarea într-o stare de siguranță (oprirea procesării și alertarea operatorului) pentru a nu permite trecerea merelor nesortate.

Bucla de feedback funcționează astfel: În stadiul actual, sistemul oferă un feedback vizual în timp real operatorului prin actualizarea dashboard-ului.
```

---

### 4. Scheletul Complet al celor 3 Module Cerute la Curs (slide 7)

Toate cele 3 module trebuie să **pornească și să ruleze fără erori** la predare. Nu trebuie să fie perfecte, dar trebuie să demonstreze că înțelegeți arhitectura.

| **Modul**                         | **Python (exemple tehnologii)**                  | **LabVIEW**                         | **Cerință minimă funcțională (la predare)**                                                                                                               |
| --------------------------------- | ------------------------------------------------ | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Data Logging / Acquisition** | `src/data_acquisition/`                          | LLB cu VI-uri de generare/achiziție | **MUST:** Produce CSV cu datele voastre (inclusiv cele 40% originale). Cod rulează fără erori și generează minimum 100 samples demonstrative.             |
| **2. Neural Network Module**      | `src/neural_network/model.py` sau folder dedicat | LLB cu VI-uri RN                    | **MUST:** Modelul RN definit, compilat, poate fi încărcat. **NOT required:** Model antrenat cu performanță bună (poate avea weights random/inițializați). |
| **3. Web Service / UI**           | Streamlit, Gradio, FastAPI, Flask, Dash          | WebVI sau Web Publishing Tool       | **MUST:** Primește input de la user și afișează un output. **NOT required:** UI frumos, funcționalități avansate.                                         |

#### Detalii per modul:

#### **Modul 1: Data Logging / Acquisition**

**Funcționalități obligatorii:**

- [ ] Cod rulează fără erori: `python src/data_acquisition/generate.py` sau echivalent LabVIEW
- [ ] Generează CSV în format compatibil cu preprocesarea din Etapa 3
- [ ] Include minimum 40% date originale în dataset-ul final
- [ ] Documentație în cod: ce date generează, cu ce parametri

#### **Modul 2: Neural Network Module**

**Funcționalități obligatorii:**

- [ ] Arhitectură RN definită și compilată fără erori
- [ ] Model poate fi salvat și reîncărcat
- [ ] Include justificare pentru arhitectura aleasă (în docstring sau README)
- [ ] **NU trebuie antrenat** cu performanță bună (weights pot fi random)

#### **Modul 3: Web Service / UI**

**Funcționalități MINIME obligatorii:**

- [ ] Propunere Interfață ce primește input de la user (formular, file upload, sau API endpoint)
- [ ] Includeți un screenshot demonstrativ în `docs/screenshots/`

**Ce NU e necesar în Etapa 4:**

- UI frumos/profesionist cu grafică avansată
- Funcționalități multiple (istorice, comparații, statistici)
- Predicții corecte (modelul e neantrenat, e normal să fie incorect)
- Deployment în cloud sau server de producție

**Scop:** Prima demonstrație că pipeline-ul end-to-end funcționează: input user → preprocess → model → output.

## Structura Repository-ului la Finalul Etapei 4 (OBLIGATORIE)

**Verificare consistență cu Etapa 3:**

```
proiect-rn-Clopotaru_Alexandru/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── generated/  # Date originale
│   ├── train/
│   ├── validation/
│   └── test/
├── src/
│   ├── data_acquisition/
│   ├── preprocessing/  # Din Etapa 3
│   ├── neural_network/
│   └── app/  # UI schelet
├── docs/
│   ├── state_machine.*           #(state_machine.png sau state_machine.pptx sau state_machine.drawio)
│   └── [alte dovezi]
├── models/  # Untrained model
├── config/
├── README.md
├── README_Etapa3.md              # (deja existent)
├── README_Etapa4_Arhitectura_SIA.md              # ← acest fișier completat (în rădăcină)
└── requirements.txt  # Sau .lvproj
```

**Diferențe față de Etapa 3:**

- Adăugat `data/generated/` pentru contribuția dvs originală
- Adăugat `src/data_acquisition/` - MODUL 1
- Adăugat `src/neural_network/` - MODUL 2
- Adăugat `src/app/` - MODUL 3
- Adăugat `models/` pentru model neantrenat
- Adăugat `docs/state_machine.png` - OBLIGATORIU
- Adăugat `docs/screenshots/` pentru demonstrație UI

---

## Checklist Final – Bifați Totul Înainte de Predare

### Documentație și Structură

- [x] Tabelul Nevoie → Soluție → Modul complet (minimum 2 rânduri cu exemple concrete completate in README_Etapa4_Arhitectura_SIA.md)
- [x] Declarație contribuție 40% date originale completată în README_Etapa4_Arhitectura_SIA.md
- [x] Cod generare/achiziție date funcțional și documentat
- [x] Dovezi contribuție originală: grafice + log + statistici în `docs/`
- [x] Diagrama State Machine creată și salvată în `docs/state_machine.*`
- [x] Legendă State Machine scrisă în README_Etapa4_Arhitectura_SIA.md (minimum 1-2 paragrafe cu justificare)
- [x] Repository structurat conform modelului de mai sus (verificat consistență cu Etapa 3)

### Modul 1: Data Logging / Acquisition

- [x] Cod rulează fără erori (`python src/extract_frames.py` pentru extragere cadre video)
- [x] Produce minimum 40% date originale din dataset-ul final (100% originale!)
- [x] Dataset generat în format YOLO compatibil cu antrenarea
- [x] Documentație în `src/data_acquisition/README.md` cu:
  - [x] Metodă de generare/achiziție explicată (video propriu + Roboflow)
  - [x] Parametri folosiți (frame skip, rezoluție, augmentări)
  - [x] Justificare relevanță date pentru problema industrială
- [x] Fișiere în `data/generated/AppleScan.yolov8/` conform structurii

### Modul 2: Neural Network

- [x] Arhitectură RN definită și documentată în cod (YOLOv8n)
- [x] README în `src/neural_network/README.md` cu detalii arhitectură completă

### Modul 3: Web Service / UI

- [x] Interfață Flask pornește fără erori (comandă `python src\web\app.py`)
- [x] Screenshot demonstrativ în `docs/screenshots/inference_real.png`
- [x] README în `src/web/README.md` cu instrucțiuni lansare complete

---

**Predarea se face prin commit pe GitHub cu mesajul:**  
`"Etapa 4 completă - Arhitectură SIA funcțională"`

**Tag obligatoriu:**  
`git tag -a v0.4-architecture -m "Etapa 4 - Skeleton complet SIA"`
