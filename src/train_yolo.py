from ultralytics import YOLO
import os

def train_model():
    # 1. Obținem calea către folderul principal al proiectului (AppleScan)
    # Mergem 2 niveluri mai sus de la acest script (src -> AppleScan)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 2. Definim calea EXACTA către data.yaml
    # ATENȚIE: Aici am adăugat folderul 'AppleScan.yolov8' conform pozei tale
    yaml_path = os.path.join(base_dir, 'data', 'AppleScan.yolov8', 'data.yaml')

    # Verificare de siguranță: vedem dacă fișierul există înainte să pornim
    if not os.path.exists(yaml_path):
        print(f"[EROARE] Nu găsesc fișierul la: {yaml_path}")
        return

    print(f"[INFO] Fisier de configurare gasit: {yaml_path}")

    # 3. Încărcăm modelul Nano (cel mai rapid pentru teste)
    model = YOLO('yolov8n.pt') 

    print("[INFO] Incep antrenarea... (Poate dura cateva minute)")

    # 4. Start Antrenare
    results = model.train(
        data=yaml_path, 
        epochs=100,        # 100 de epoci e ok pentru setul tau
        imgsz=640,         # Mărimea standard
        plots=True,        # Generează grafice
        name='mar_model',  # Numele folderului unde se salvează rezultatul
        project='data/models' # Salvăm modelele antrenate organizat
    )

    print("[GATA] Antrenare completa!")
    
    # 5. Exportăm modelul final în format ONNX (bun pentru compatibilitate)
    success = model.export(format='onnx')

if __name__ == '__main__':
    train_model()