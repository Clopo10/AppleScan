from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO
import cv2
import os
import glob
import numpy as np
from collections import defaultdict
import threading

app = Flask(__name__)

# Global variables for video selection
current_video = 'mere3.mp4'
video_session_id = 0
video_lock = threading.Lock()

# Session-based tracking - each session has its own data
session_data = {}  # {session_id: {'tracks': {}, 'unique_ids': {'green': set(), 'red': set()}, 'next_id': 0}}

def get_session_data(session_id):
    """Get or create data for a specific session"""
    if session_id not in session_data:
        session_data[session_id] = {
            'active_tracks': {},
            'all_unique_ids': {'green': set(), 'red': set()},
            'next_apple_id': 0
        }
    return session_data[session_id]

# Tracking parameters
MAX_DISTANCE = 80  # Maximum distance to consider the same apple between frames
MAX_FRAMES_MISSING = 30  # Remove track if apple not seen for this many frames

# --- CONFIGURARE ---
# Căile trebuie să fie corecte relativ la locul de unde rulăm scriptul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'mar_model', 'weights', 'best.pt')
VIDEO_DIR = os.path.join(BASE_DIR, 'data', 'video')
# -------------------

# Încărcăm modelul antrenat
print(f"[INFO] Incarc modelul de la: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

def calculate_centroid(box):
    """Calculate centroid of a bounding box"""
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return (cx, cy)

def find_matching_track(centroid, class_id, frame_num, active_tracks):
    """Find if this detection matches an existing track"""
    
    best_match_id = None
    best_distance = MAX_DISTANCE
    
    for track_id, track_data in active_tracks.items():
        # Only match same class
        if track_data['class'] != class_id:
            continue
        
        # Calculate distance
        dist = np.sqrt((centroid[0] - track_data['centroid'][0])**2 + 
                      (centroid[1] - track_data['centroid'][1])**2)
        
        if dist < best_distance:
            best_distance = dist
            best_match_id = track_id
    
    return best_match_id

def generate_frames():
    # Capture the current session ID and video at the start
    with video_lock:
        my_session_id = video_session_id
        video_to_play = current_video
    
    print(f"[INFO] Starting generator for session {my_session_id}, video: {video_to_play}")
    
    # Get session-specific data
    session = get_session_data(my_session_id)
    active_tracks = session['active_tracks']
    all_unique_ids = session['all_unique_ids']
    
    video_path = os.path.join(VIDEO_DIR, video_to_play)
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}.")
        return
    
    frame_num = 0

    while True:
        # Check if this generator should stop (video changed)
        with video_lock:
            if my_session_id != video_session_id:
                print(f"[INFO] Generator stopped - video changed (session {my_session_id} -> {video_session_id})")
                cap.release()
                break
        
        success, frame = cap.read()
        if not success:
            # Video s-a terminat
            print(f"[INFO] Video terminat (session {my_session_id}).")
            print(f"[INFO] Total mere verzi unice: {len(all_unique_ids['green'])}")
            print(f"[INFO] Total mere roșii unice: {len(all_unique_ids['red'])}")
            print(f"[INFO] Total mere: {len(all_unique_ids['green']) + len(all_unique_ids['red'])}")
            cap.release()
            break

        frame_num += 1
        
        # Run YOLOv8 inference on the frame
        results = model(frame)

        # Current frame detections
        current_detections = []
        
        detections = results[0].boxes
        
        if detections is not None and len(detections) > 0:
            for box in detections:
                class_id = int(box.cls[0])
                centroid = calculate_centroid(box)
                current_detections.append({'centroid': centroid, 'class': class_id})
        
        # Match detections with existing tracks
        matched_track_ids = set()
        
        for detection in current_detections:
            centroid = detection['centroid']
            class_id = detection['class']
            
            # Try to find matching track
            track_id = find_matching_track(centroid, class_id, frame_num, active_tracks)
            
            if track_id is not None:
                # Update existing track
                active_tracks[track_id]['centroid'] = centroid
                active_tracks[track_id]['last_seen'] = frame_num
                matched_track_ids.add(track_id)
            else:
                # Create new track
                new_id = session['next_apple_id']
                session['next_apple_id'] += 1
                
                active_tracks[new_id] = {
                    'centroid': centroid,
                    'class': class_id,
                    'last_seen': frame_num
                }
                
                # Add to unique IDs
                if class_id == 0:  # green
                    all_unique_ids['green'].add(new_id)
                else:  # red
                    all_unique_ids['red'].add(new_id)
                
                matched_track_ids.add(new_id)
        
        # Remove old tracks that haven't been seen recently
        tracks_to_remove = []
        for track_id, track_data in active_tracks.items():
            if frame_num - track_data['last_seen'] > MAX_FRAMES_MISSING:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del active_tracks[track_id]

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
    # Get list of available videos
    videos = [os.path.basename(f) for f in glob.glob(os.path.join(VIDEO_DIR, '*.mp4'))]
    videos.sort()
    return render_template('index.html', videos=videos, current_video=current_video)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def get_stats():
    # Return stats for the current session only
    with video_lock:
        current_session_id = video_session_id
    
    session = get_session_data(current_session_id)
    all_unique_ids = session['all_unique_ids']
    
    return jsonify({
        'green_apples': len(all_unique_ids['green']),
        'red_apples': len(all_unique_ids['red']),
        'total_apples': len(all_unique_ids['green']) + len(all_unique_ids['red'])
    })

@app.route('/select_video', methods=['POST'])
def select_video():
    global current_video, video_session_id
    data = request.get_json()
    new_video = data.get('video')
    
    if new_video and os.path.exists(os.path.join(VIDEO_DIR, new_video)):
        with video_lock:
            current_video = new_video
            # Increment session ID to stop old generators
            video_session_id += 1
            # Clean up old session data to prevent memory leaks (keep last 3 sessions)
            if len(session_data) > 3:
                old_sessions = sorted(session_data.keys())[:-3]
                for old_session in old_sessions:
                    del session_data[old_session]
        
        print(f"[INFO] Video changed to {new_video}, new session ID: {video_session_id}")
        return jsonify({'success': True, 'video': current_video})
    return jsonify({'success': False, 'error': 'Video not found'}), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)