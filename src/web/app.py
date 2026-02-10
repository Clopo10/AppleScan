# Flask web server and helpers for templates, streaming, and JSON responses
from flask import Flask, render_template, Response, jsonify, request
# YOLO model inference
from ultralytics import YOLO
# OpenCV for video capture and JPEG encoding
import cv2
# Path and filesystem utilities
import os
# File discovery using wildcard patterns
import glob
# Numeric operations (distance computations)
import numpy as np
# Enum for streaming state machine
from enum import Enum, auto
# Thread-safe access to shared video/session data
import threading

# Flask app instance
app = Flask(__name__)


# State machine for the streaming pipeline
class StreamState(Enum):
    IDLE = auto()
    ACQUIRE_DATA = auto()
    PREPROCESS = auto()
    INFERENCE = auto()
    DECISION = auto()
    OUTPUT = auto()
    ERROR = auto()


# Global variables for the selected video
current_video = "mere3.mp4"
video_session_id = 0
video_lock = threading.Lock()

# Session-based tracking data (per video session)
session_data = {}


def get_session_data(session_id):
    # Create or return tracking data for a session.
    if session_id not in session_data:
        session_data[session_id] = {
            "active_tracks": {},
            "all_unique_ids": {"green": set(), "red": set()},
            "next_apple_id": 0
        }
    return session_data[session_id]


# Tracking parameters
MAX_DISTANCE = 80
MAX_FRAMES_MISSING = 30
MIN_CONFIDENCE_FOR_CLASSIFICATION = 0.42
MIN_CONSISTENT_FRAMES = 3
MAX_RECLASSIFY_FRAME = 20
MIN_FRAMES_FOR_FINALIZATION = 2
MIN_AREA_FOR_TRACKING = 1000

# --- CONFIG ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "models", "mar_model_nou", "weights", "best.pt")
VIDEO_DIR = os.path.join(BASE_DIR, "data", "video")
# -------------

# Load YOLO model once at startup
print(f"[INFO] Incarc modelul de la: {MODEL_PATH}")
model = YOLO(MODEL_PATH)


def calculate_centroid(box):
    # Return (center x, center y, area) for one YOLO box.
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    area = (x2 - x1) * (y2 - y1)
    return (cx, cy, area)


def find_matching_track(centroid, frame_num, active_tracks):
    # Match detection to the nearest recent track
    best_match_id = None
    best_distance = MAX_DISTANCE

    for track_id, track_data in active_tracks.items():
        # Ignore very old tracks
        if frame_num - track_data["last_seen"] > 3:
            continue

        track_centroid = track_data["centroid"]
        dist = np.sqrt((centroid[0] - track_centroid[0]) ** 2 +
                   (centroid[1] - track_centroid[1]) ** 2)

        if dist < best_distance:
            best_distance = dist
            best_match_id = track_id

    return best_match_id


def get_best_classification(class_history, confidence_history, area_history):
    # Pick the best class using confidence and area as a simple score.
    if not class_history:
        return None

    best_score = -1
    best_class = None

    for cls, conf, area in zip(class_history, confidence_history, area_history):
        score = conf * (area ** 0.5)
        if score > best_score:
            best_score = score
            best_class = cls

    return best_class


def generate_frames():
    # Stream frames with detections and tracking.
    with video_lock:
        my_session_id = video_session_id
        video_to_play = current_video

    print(f"[INFO] Starting generator for session {my_session_id}, video: {video_to_play}")

    # Per-session tracking state
    session = get_session_data(my_session_id)
    active_tracks = session["active_tracks"]
    all_unique_ids = session["all_unique_ids"]

    # Open the selected video file
    video_path = os.path.join(VIDEO_DIR, video_to_play)
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}.")
        return

    # Initialize state machine variables
    frame_num = 0
    state = StreamState.ACQUIRE_DATA
    frame = None
    results = None
    annotated_frame = None

    while True:
        # Stop if the video changed
        with video_lock:
            if my_session_id != video_session_id:
                print(f"[INFO] Generator stopped - video changed (session {my_session_id} -> {video_session_id})")
                cap.release()
                break

        try:
            if state == StreamState.ACQUIRE_DATA:
                # Read next frame from video
                success, frame = cap.read()
                if not success:
                    # End of video; print final counts
                    print(f"[INFO] Video terminat (session {my_session_id}).")
                    print(f"[INFO] Total mere verzi unice: {len(all_unique_ids['green'])}")
                    print(f"[INFO] Total mere roșii unice: {len(all_unique_ids['red'])}")
                    print(f"[INFO] Total mere: {len(all_unique_ids['green']) + len(all_unique_ids['red'])}")
                    cap.release()
                    break

                frame_num += 1
                state = StreamState.PREPROCESS

            if state == StreamState.PREPROCESS:
                # Placeholder for preprocessing
                state = StreamState.INFERENCE

            if state == StreamState.INFERENCE:
                # Run model inference on the current frame
                results = model(frame)
                state = StreamState.DECISION

            if state == StreamState.DECISION:
                # Build detection list and update tracks
                current_detections = []
                detections = results[0].boxes

                # Build detection list with centroid + area
                if detections is not None and len(detections) > 0:
                    for box in detections:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        cx, cy, area = calculate_centroid(box)

                        if area >= MIN_AREA_FOR_TRACKING:
                            current_detections.append({
                                "centroid": (cx, cy),
                                "area": area,
                                "class": class_id,
                                "confidence": confidence
                            })

                for detection in current_detections:
                    # Try to match the detection to an existing track
                    centroid = detection["centroid"]
                    area = detection["area"]
                    class_id = detection["class"]
                    confidence = detection["confidence"]

                    track_id = find_matching_track(centroid, frame_num, active_tracks)

                    if track_id is not None:
                        # Update existing track with new observation
                        track = active_tracks[track_id]
                        track["centroid"] = centroid
                        track["last_seen"] = frame_num
                        track["max_area"] = max(track.get("max_area", 0), area)

                        if "class_history" not in track:
                            # Initialize per-track history buffers
                            track["class_history"] = []
                            track["confidence_history"] = []
                            track["area_history"] = []
                            track["first_seen"] = frame_num
                            track["is_locked"] = False

                        track["class_history"].append(class_id)
                        track["confidence_history"].append(confidence)
                        track["area_history"].append(area)

                        if len(track["class_history"]) > 10:
                            # Keep only the most recent observations
                            track["class_history"] = track["class_history"][-10:]
                            track["confidence_history"] = track["confidence_history"][-10:]
                            track["area_history"] = track["area_history"][-10:]

                        is_locked = track.get("is_locked", False)
                        old_class = track.get("final_class")
                        frames_tracked = len(track["class_history"])
                        frames_since_first = frame_num - track.get("first_seen", frame_num)

                        if not is_locked and len(track["class_history"]) >= MIN_CONSISTENT_FRAMES:
                            # Decide best class once we have enough history
                            best_class = get_best_classification(
                                track["class_history"],
                                track["confidence_history"],
                                track["area_history"]
                            )
                            max_confidence = max(track["confidence_history"])

                            if max_confidence >= MIN_CONFIDENCE_FOR_CLASSIFICATION:
                                # Update unique counts and track class if confident
                                if old_class != best_class:
                                    if old_class is not None:
                                        if frames_since_first <= MAX_RECLASSIFY_FRAME:
                                            print(
                                                f"[INFO] Reclassifying apple {track_id}: {old_class} -> {best_class} "
                                                f"(frames: {frames_tracked})"
                                            )
                                            old_class_name = "green" if old_class == 0 else "red"
                                            new_class_name = "green" if best_class == 0 else "red"
                                            all_unique_ids[old_class_name].discard(track_id)
                                            all_unique_ids[new_class_name].add(track_id)

                                            track["final_class"] = best_class
                                            track["class"] = best_class
                                    else:
                                        class_name = "green" if best_class == 0 else "red"
                                        all_unique_ids[class_name].add(track_id)
                                        track["final_class"] = best_class
                                        track["class"] = best_class

                                if frames_since_first > MAX_RECLASSIFY_FRAME:
                                    # Lock class after reclassify window
                                    track["is_locked"] = True
                    else:
                        # Create a new track for an unmatched detection
                        new_id = session["next_apple_id"]
                        session["next_apple_id"] += 1

                        active_tracks[new_id] = {
                            "centroid": centroid,
                            "class": class_id,
                            "final_class": None,
                            "is_locked": False,
                            "first_seen": frame_num,
                            "last_seen": frame_num,
                            "max_area": area,
                            "class_history": [class_id],
                            "confidence_history": [confidence],
                            "area_history": [area]
                        }

                # Clean up old tracks
                tracks_to_remove = []
                for track_id, track_data in active_tracks.items():
                    frames_missing = frame_num - track_data["last_seen"]

                    if frames_missing > MAX_FRAMES_MISSING:
                        # Finalize and remove tracks missing for too long
                        if track_data.get("final_class") is None and len(track_data.get("class_history", [])) >= 5:
                            best_class = get_best_classification(
                                track_data["class_history"],
                                track_data["confidence_history"],
                                track_data.get("area_history", track_data["class_history"])
                            )
                            max_conf = max(track_data["confidence_history"])
                            max_area = track_data.get("max_area", 0)

                            if max_conf >= MIN_CONFIDENCE_FOR_CLASSIFICATION and max_area >= MIN_AREA_FOR_TRACKING:
                                # Persist final class and unique counts
                                class_name = "green" if best_class == 0 else "red"

                                if track_data.get("final_class") is not None and track_data["final_class"] != best_class:
                                    old_class_name = "green" if track_data["final_class"] == 0 else "red"
                                    all_unique_ids[old_class_name].discard(track_id)
                                    print(
                                        f"[INFO] Correcting track {track_id} from {old_class_name} to {class_name} "
                                        "on removal"
                                    )

                                all_unique_ids[class_name].add(track_id)
                                track_data["final_class"] = best_class
                                track_data["is_locked"] = True
                                print(
                                    f"[INFO] Finalizing track {track_id} as {class_name} "
                                    f"(frames: {len(track_data['class_history'])}, conf: {max_conf:.2f}, "
                                    f"area: {max_area:.0f})"
                                )

                        tracks_to_remove.append(track_id)
                    elif frames_missing > 5 and track_data.get("final_class") is None:
                        # Pre-finalize tracks that have gone briefly missing
                        if len(track_data.get("class_history", [])) >= 5:
                            best_class = get_best_classification(
                                track_data["class_history"],
                                track_data["confidence_history"],
                                track_data.get("area_history", track_data["class_history"])
                            )
                            max_conf = max(track_data["confidence_history"])
                            max_area = track_data.get("max_area", 0)

                            if max_conf >= MIN_CONFIDENCE_FOR_CLASSIFICATION and max_area >= MIN_AREA_FOR_TRACKING:
                                # Persist pre-finalized class and unique counts
                                class_name = "green" if best_class == 0 else "red"

                                if track_data.get("final_class") is not None and track_data["final_class"] != best_class:
                                    old_class_name = "green" if track_data["final_class"] == 0 else "red"
                                    all_unique_ids[old_class_name].discard(track_id)
                                    print(
                                        f"[INFO] Correcting track {track_id} from {old_class_name} to {class_name} "
                                        f"(missing {frames_missing} frames)"
                                    )

                                all_unique_ids[class_name].add(track_id)
                                track_data["final_class"] = best_class
                                track_data["is_locked"] = True
                                print(
                                    f"[INFO] Pre-finalizing track {track_id} as {class_name} "
                                    f"(missing {frames_missing} frames)"
                                )

                for track_id in tracks_to_remove:
                    del active_tracks[track_id]

                # Render detections on the frame
                annotated_frame = results[0].plot()
                state = StreamState.OUTPUT

            if state == StreamState.OUTPUT:
                # Encode frame as JPEG and stream as MJPEG
                ret, buffer = cv2.imencode(".jpg", annotated_frame)
                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
                state = StreamState.ACQUIRE_DATA

        except Exception as exc:
            # Any error moves the pipeline to ERROR state
            print(f"[ERROR] State machine failed: {exc}")
            state = StreamState.ERROR

        if state == StreamState.ERROR:
            # Release resources on error
            cap.release()
            break


@app.route("/")
def index():
    # Pagina principala.
    # List available videos and render the main page
    videos = [os.path.basename(f) for f in glob.glob(os.path.join(VIDEO_DIR, "*.mp4"))]
    videos.sort()
    return render_template("index.html", videos=videos, current_video=current_video)


@app.route("/video_feed")
def video_feed():
    # Stream MJPEG cu video + bounding boxes from generator
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stats")
def get_stats():
    # Returneaza numarul unic de mere pe sesiunea curenta.
    # Read current session stats safely
    with video_lock:
        current_session_id = video_session_id

    session = get_session_data(current_session_id)
    all_unique_ids = session["all_unique_ids"]

    return jsonify({
        "green_apples": len(all_unique_ids["green"]),
        "red_apples": len(all_unique_ids["red"]),
        "total_apples": len(all_unique_ids["green"]) + len(all_unique_ids["red"])
    })


@app.route("/select_video", methods=["POST"])
def select_video():
    # Schimba video-ul si reseteaza sesiunea
    global current_video, video_session_id
    data = request.get_json()
    new_video = data.get("video")

    if new_video and os.path.exists(os.path.join(VIDEO_DIR, new_video)):
        with video_lock:
            current_video = new_video
            video_session_id += 1

            # Pastreaza doar ultimele 3 sesiuni
            if len(session_data) > 3:
                old_sessions = sorted(session_data.keys())[:-3]
                for old_session in old_sessions:
                    del session_data[old_session]

        print(f"[INFO] Video changed to {new_video}, new session ID: {video_session_id}")
        return jsonify({"success": True, "video": current_video})

    return jsonify({"success": False, "error": "Video not found"}), 404


if __name__ == "__main__":
    # Run Flask in debug mode for local development
    app.run(debug=True, host="0.0.0.0", port=5000)
