import cv2
import os

# --- CONFIGURARE ---
VIDEO_PATH = 'data/video/mere3.mp4'  # Asigură-te că numele e corect
OUTPUT_FOLDER = 'data/raw_images'         # Unde salvăm pozele
FRAME_RATE = 10                           # Salvăm 1 cadru la fiecare 10 cadre (pentru diversitate)
# -------------------

def extract_frames():
    # 1. Verificăm dacă există folderul de output, dacă nu, îl creăm
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"[INFO] Folder creat: {OUTPUT_FOLDER}")

    # 2. Încărcăm video-ul
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    if not cap.isOpened():
        print(f"[EROARE] Nu pot deschide video-ul: {VIDEO_PATH}")
        return

    count = 0
    saved_count = 0

    print("[INFO] Încep extragerea cadrelor...")

    while True:
        success, frame = cap.read()
        
        if not success:
            break # S-a terminat video-ul

        # 3. Salvăm doar dacă numărul cadrului se împarte exact la FRAME_RATE
        if count % FRAME_RATE == 0:
            # Generăm un nume unic: frame_001.jpg, frame_002.jpg...
            filename = f"{OUTPUT_FOLDER}/frame_{saved_count:04d}.jpg"
            cv2.imwrite(filename, frame)
            saved_count += 1
        
        count += 1

    cap.release()
    print(f"[GATA] Am extras {saved_count} imagini în folderul '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    extract_frames()