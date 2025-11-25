from flask import Flask, render_template, Response
from ultralytics import YOLO
import cv2
import os

app = Flask(__name__)

# --- CONFIGURARE ---
# Căile trebuie să fie corecte relativ la locul de unde rulăm scriptul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'models', 'mar_model', 'weights', 'best.pt')
VIDEO_PATH = os.path.join(BASE_DIR, 'data', 'video', 'mere3.mp4') 
# -------------------

# Încărcăm modelul antrenat
print(f"[INFO] Incarc modelul de la: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

def generate_frames():
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            # Dacă s-a terminat video-ul, îl luăm de la capăt (loop)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # --- AICI SE INTAMPLA MAGIA AI ---
        # Run YOLOv8 inference on the frame
        results = model(frame)

        # Visualize the results on the frame
        annotated_frame = results[0].plot()
        # ---------------------------------

        # Codificăm imaginea ca JPEG pentru a o trimite în browser
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        # Generatorul care trimite fluxul video (MJPEG)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)