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
MIN_CONFIDENCE_FOR_CLASSIFICATION = 0.42  # Minimum confidence to trust classification
MIN_CONSISTENT_FRAMES = 3  # Minimum frames with same class before finalizing
MAX_RECLASSIFY_FRAME = 20  # Only allow reclassification in first N frames
MIN_FRAMES_FOR_FINALIZATION = 2  # Minimum frames to finalize a track on removal
MIN_AREA_FOR_TRACKING = 1000  # Minimum area to consider valid detection

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
    area = (x2 - x1) * (y2 - y1)
    return (cx, cy, area)

def find_matching_track(centroid, class_id, confidence, frame_num, active_tracks):
    """Find if this detection matches an existing track"""
    
    best_match_id = None
    best_distance = MAX_DISTANCE
    
    for track_id, track_data in active_tracks.items():
        # Skip tracks that haven't been seen recently - they might be different apples
        if frame_num - track_data['last_seen'] > 3:
            continue
            
        # Calculate distance
        track_centroid = track_data['centroid']
        dist = np.sqrt((centroid[0] - track_centroid[0])**2 + 
                      (centroid[1] - track_centroid[1])**2)
        
        # Match by proximity, regardless of class (to handle misclassification)
        if dist < best_distance:
            best_distance = dist
            best_match_id = track_id
    
    return best_match_id

def get_best_classification(class_history, confidence_history, area_history):
    """Get the most likely class from the single best observation"""
    if not class_history:
        return None
    
    # Find the observation with highest confidence * area (best clear view)
    best_score = -1
    best_class = None
    
    for cls, conf, area in zip(class_history, confidence_history, area_history):
        score = conf * (area ** 0.5)  # Weight by sqrt of area to avoid over-weighting
        if score > best_score:
            best_score = score
            best_class = cls
    
    return best_class

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
                confidence = float(box.conf[0])
                cx, cy, area = calculate_centroid(box)
                
                # Only track detections with sufficient size
                if area >= MIN_AREA_FOR_TRACKING:
                    current_detections.append({
                        'centroid': (cx, cy),
                        'area': area,
                        'class': class_id, 
                        'confidence': confidence
                    })
        
        # Match detections with existing tracks
        matched_track_ids = set()
        
        for detection in current_detections:
            centroid = detection['centroid']
            area = detection['area']
            class_id = detection['class']
            confidence = detection['confidence']
            
            # Try to find matching track
            track_id = find_matching_track(centroid, class_id, confidence, frame_num, active_tracks)
            
            if track_id is not None:
                # Update existing track
                track = active_tracks[track_id]
                track['centroid'] = centroid
                track['last_seen'] = frame_num
                track['max_area'] = max(track.get('max_area', 0), area)
                
                # Update class history for this track
                if 'class_history' not in track:
                    track['class_history'] = []
                    track['confidence_history'] = []
                    track['area_history'] = []
                    track['first_seen'] = frame_num
                    track['is_locked'] = False
                
                track['class_history'].append(class_id)
                track['confidence_history'].append(confidence)
                track['area_history'].append(area)
                
                # Keep only recent history (last 10 frames)
                if len(track['class_history']) > 10:
                    track['class_history'] = track['class_history'][-10:]
                    track['confidence_history'] = track['confidence_history'][-10:]
                    track['area_history'] = track['area_history'][-10:]
                
                # Determine if we should update the class
                is_locked = track.get('is_locked', False)
                old_class = track.get('final_class')
                frames_tracked = len(track['class_history'])
                frames_since_first = frame_num - track.get('first_seen', frame_num)
                
                # Only update classification if not locked
                if not is_locked:
                    # Require minimum observations for reliable classification
                    required_frames = 5
                    
                    if len(track['class_history']) >= required_frames:
                        # Get best classification from clearest observation
                        best_class = get_best_classification(
                            track['class_history'],
                            track['confidence_history'],
                            track['area_history']
                        )
                        
                        # Check if best observation meets confidence threshold
                        max_confidence = max(track['confidence_history'])
                        
                        if max_confidence >= MIN_CONFIDENCE_FOR_CLASSIFICATION:
                            if old_class != best_class:
                                # Classification changed or being set for first time
                                if old_class is not None:
                                    # Only allow reclassification early in tracking
                                    if frames_since_first <= MAX_RECLASSIFY_FRAME:
                                        print(f"[INFO] Reclassifying apple {track_id}: {old_class} -> {best_class} (frames: {frames_tracked})") 
                                        old_class_name = 'green' if old_class == 0 else 'red'
                                        new_class_name = 'green' if best_class == 0 else 'red'
                                        
                                        # Remove from old set and add to new set
                                        all_unique_ids[old_class_name].discard(track_id)
                                        all_unique_ids[new_class_name].add(track_id)
                                        
                                        track['final_class'] = best_class
                                        track['class'] = best_class
                                    # else: too late to reclassify, keep old class
                                else:
                                    # First time finalizing
                                    class_name = 'green' if best_class == 0 else 'red'
                                    all_unique_ids[class_name].add(track_id)
                                    track['final_class'] = best_class
                                    track['class'] = best_class
                            
                            # Don't lock immediately - only lock after reclassification window
                            if frames_since_first > MAX_RECLASSIFY_FRAME:
                                track['is_locked'] = True
                
                matched_track_ids.add(track_id)
            else:
                # Create new track
                new_id = session['next_apple_id']
                session['next_apple_id'] += 1
                
                active_tracks[new_id] = {
                    'centroid': centroid,
                    'class': class_id,
                    'final_class': None,  # Not finalized yet
                    'is_locked': False,
                    'first_seen': frame_num,
                    'last_seen': frame_num,
                    'max_area': area,
                    'class_history': [class_id],
                    'confidence_history': [confidence],
                    'area_history': [area]
                }
                
                matched_track_ids.add(new_id)
        
        # Remove old tracks that haven't been seen recently
        # But first, finalize any unfinalized tracks that are about to be removed
        tracks_to_remove = []
        for track_id, track_data in active_tracks.items():
            frames_missing = frame_num - track_data['last_seen']
            
            if frames_missing > MAX_FRAMES_MISSING:
                # If track is being removed and not yet finalized, try to finalize it
                # Only finalize if we have enough evidence
                if track_data.get('final_class') is None and len(track_data.get('class_history', [])) >= 5:
                    best_class = get_best_classification(
                        track_data['class_history'], 
                        track_data['confidence_history'],
                        track_data.get('area_history', track_data['class_history'])  # Fallback to class_history length
                    )
                    max_conf = max(track_data['confidence_history'])
                    max_area = track_data.get('max_area', 0)
                    
                    # Finalize only if we have good confidence and size
                    if max_conf >= MIN_CONFIDENCE_FOR_CLASSIFICATION and max_area >= MIN_AREA_FOR_TRACKING:
                        class_name = 'green' if best_class == 0 else 'red'
                        
                        # If already finalized with different class, update the sets
                        if track_data.get('final_class') is not None and track_data['final_class'] != best_class:
                            old_class_name = 'green' if track_data['final_class'] == 0 else 'red'
                            all_unique_ids[old_class_name].discard(track_id)
                            print(f"[INFO] Correcting track {track_id} from {old_class_name} to {class_name} on removal")
                        
                        all_unique_ids[class_name].add(track_id)
                        track_data['final_class'] = best_class
                        track_data['is_locked'] = True
                        print(f"[INFO] Finalizing track {track_id} as {class_name} (frames: {len(track_data['class_history'])}, conf: {max_conf:.2f}, area: {max_area:.0f})")
                
                tracks_to_remove.append(track_id)
            elif frames_missing > 5 and track_data.get('final_class') is None:
                # Track hasn't been seen in a while but not dead yet - try to finalize if possible
                if len(track_data.get('class_history', [])) >= 5:
                    best_class = get_best_classification(
                        track_data['class_history'], 
                        track_data['confidence_history'],
                        track_data.get('area_history', track_data['class_history'])
                    )
                    max_conf = max(track_data['confidence_history'])
                    max_area = track_data.get('max_area', 0)
                    
                    if max_conf >= MIN_CONFIDENCE_FOR_CLASSIFICATION and max_area >= MIN_AREA_FOR_TRACKING:
                        class_name = 'green' if best_class == 0 else 'red'
                        
                        # If already finalized with different class, update the sets
                        if track_data.get('final_class') is not None and track_data['final_class'] != best_class:
                            old_class_name = 'green' if track_data['final_class'] == 0 else 'red'
                            all_unique_ids[old_class_name].discard(track_id)
                            print(f"[INFO] Correcting track {track_id} from {old_class_name} to {class_name} (missing {frames_missing} frames)")
                        
                        all_unique_ids[class_name].add(track_id)
                        track_data['final_class'] = best_class
                        track_data['is_locked'] = True
                        print(f"[INFO] Pre-finalizing track {track_id} as {class_name} (missing {frames_missing} frames)")
        
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