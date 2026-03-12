import tkinter as tk
import cv2
import pathlib
import time
import pyautogui
from PIL import Image
import threading

# ====================== MediaPipe ======================
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import (
    HandLandmarker, HandLandmarkerOptions,
    FaceLandmarker, FaceLandmarkerOptions,
    RunningMode
)
from mediapipe.tasks.python.core.base_options import BaseOptions

# Models directory
MODELS_DIR = pathlib.Path.cwd() / 'models'

def check_models():
    hand_path = MODELS_DIR / 'hand_landmarker.task'
    face_path = MODELS_DIR / 'face_landmarker.task'
    
    if not hand_path.exists() or not face_path.exists():
        print("❌ Model files not found!")
        print(f"   Expected in: {MODELS_DIR}")
        return False
    
    hand_size = hand_path.stat().st_size / (1024*1024)
    face_size = face_path.stat().st_size / (1024*1024)
    
    print(f"✅ Hand model: {hand_size:.1f} MB")
    print(f"✅ Face model: {face_size:.1f} MB")
    
    if hand_size < 1 or face_size < 1:
        print("❌ Model files are corrupted (too small). Please re-download using the PowerShell commands.")
        return False
    return True

# Custom drawing
def draw_landmarks(image, landmarks, color=(0, 255, 0), thickness=2):
    h, w = image.shape[:2]
    connections = [
        (0,1),(1,2),(2,3),(3,4), (0,5),(5,6),(6,7),(7,8),
        (0,9),(9,10),(10,11),(11,12), (0,13),(13,14),(14,15),(15,16),
        (0,17),(17,18),(18,19),(19,20), (5,9),(9,13),(13,17)
    ]
    for start, end in connections:
        if start < len(landmarks) and end < len(landmarks):
            s = landmarks[start]
            e = landmarks[end]
            cv2.line(image, (int(s.x*w), int(s.y*h)), (int(e.x*w), int(e.y*h)), color, thickness)
    for lm in landmarks:
        cv2.circle(image, (int(lm.x*w), int(lm.y*h)), 4, color, -1)

# ====================== OPTIMIZED VIRTUAL MOUSE ======================
def virtual_mouse():
    if not check_models(): return
    print("🚀 Starting Virtual Mouse **(Optimized - Fast & Smooth)**...")
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Load model as bytes (fastest on Windows)
    with open(MODELS_DIR / 'hand_landmarker.task', 'rb') as f:
        model_bytes = f.read()
    base_options = BaseOptions(model_asset_buffer=model_bytes)
    
    options = HandLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.VIDEO,
        num_hands=1
    )
    detector = HandLandmarker.create_from_options(options)

    screen_w, screen_h = pyautogui.size()
    pyautogui.PAUSE = 0          # Remove built-in delay
    pyautogui.FAILSAFE = False   # Disable corner failsafe for speed

    frame_count = 0
    smoothed_x = smoothed_y = screen_w // 2
    alpha = 0.65                 # Smoothing (0.6-0.8 works best)
    last_move = time.time()

    start_time = time.time()
    fps = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        frame_count += 1

        # Calculate & display FPS
        if frame_count % 30 == 0:
            fps = 30 / (time.time() - start_time)
            start_time = time.time()
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Detect only every 2nd frame (big speed boost)
        if frame_count % 2 == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timestamp = int(frame_count * 33.33)
            result = detector.detect_for_video(mp_image, timestamp)

            if result.hand_landmarks:
                for landmarks in result.hand_landmarks:
                    draw_landmarks(frame, landmarks)

                    # Index finger = mouse move
                    idx = landmarks[8]
                    target_x = screen_w * idx.x
                    target_y = screen_h * idx.y

                    # Exponential smoothing → buttery smooth cursor
                    smoothed_x = alpha * target_x + (1 - alpha) * smoothed_x
                    smoothed_y = alpha * target_y + (1 - alpha) * smoothed_y

                    # Move mouse only when needed
                    if time.time() - last_move > 0.016:   # max ~60 moves/sec
                        pyautogui.moveTo(smoothed_x, smoothed_y, duration=0.008)
                        last_move = time.time()

                    # Thumb + Index close = click
                    thb = landmarks[4]
                    if abs(idx.y - thb.y) < 0.085:   # relative threshold (better than pixels)
                        pyautogui.click()
                        cv2.putText(frame, "CLICK!", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                        time.sleep(0.18)   # debounce

        cv2.imshow("Virtual Mouse (Optimized - Fast) - ESC to stop", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

def volume_control():
    if not check_models(): return
    print("🔊 Starting Volume Control with Hand Gestures...")
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    with open(MODELS_DIR / 'hand_landmarker.task', 'rb') as f:
        model_bytes = f.read()
    base_options = BaseOptions(model_asset_buffer=model_bytes)
    
    options = HandLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.VIDEO,
        num_hands=1
    )
    detector = HandLandmarker.create_from_options(options)

    frame_count = 0
    prev_distance = 0
    volume_level = 50

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        frame_count += 1

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        timestamp = int(frame_count * 33.33)
        result = detector.detect_for_video(mp_image, timestamp)

        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                draw_landmarks(frame, landmarks, color=(255, 0, 0), thickness=1)

                # Thumb and Index finger for volume control
                thumb = landmarks[4]
                index = landmarks[8]

                # Calculate distance between thumb and index
                dist = ((index.x - thumb.x)**2 + (index.y - thumb.y)**2)**0.5
                
                # Scale distance to volume (0-100)
                distance_to_volume = int(dist * 300)
                distance_to_volume = max(0, min(100, distance_to_volume))
                volume_level = distance_to_volume

                # Draw volume indicator
                cv2.putText(frame, f"Volume: {volume_level}%", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                
                # Draw volume bar
                bar_width = int(volume_level * 2)
                cv2.rectangle(frame, (10, 80), (10 + bar_width, 100), (0, 255, 0), -1)
                cv2.rectangle(frame, (10, 80), (210, 100), (255, 255, 255), 2)

                # Draw thumb and index circles
                cv2.circle(frame, (int(thumb.x*w), int(thumb.y*h)), 8, (0, 255, 255), -1)
                cv2.circle(frame, (int(index.x*w), int(index.y*h)), 8, (255, 0, 0), -1)
                cv2.line(frame, (int(thumb.x*w), int(thumb.y*h)), (int(index.x*w), int(index.y*h)), (0, 255, 255), 2)

        cv2.imshow("Volume Control (Pinch to adjust) - ESC to stop", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

def eye_controlled_mouse():
    if not check_models(): return
    print("🚀 Starting Eye Controlled Mouse...")
    cap = cv2.VideoCapture(0)
    
    with open(MODELS_DIR / 'face_landmarker.task', 'rb') as f:
        model_bytes = f.read()
    base_options = BaseOptions(model_asset_buffer=model_bytes)
    
    options = FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=RunningMode.VIDEO,
        output_face_blendshapes=False,
        num_faces=1
    )
    detector = FaceLandmarker.create_from_options(options)

    screen_w, screen_h = pyautogui.size()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)   # ← FIXED

        timestamp = int(frame_count * 33.33)
        frame_count += 1

        result = detector.detect_for_video(mp_image, timestamp)

        if result.face_landmarks:
            for landmarks in result.face_landmarks:
                for lm in landmarks:
                    x = int(lm.x * w)
                    y = int(lm.y * h)
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                eye = landmarks[474]
                screen_x = screen_w * eye.x
                screen_y = screen_h * eye.y
                pyautogui.moveTo(screen_x, screen_y, duration=0.05)

                cv2.circle(frame, (int(eye.x*w), int(eye.y*h)), 10, (0, 255, 255), 2)

                top = landmarks[159].y
                bot = landmarks[145].y
                if abs(top - bot) < 0.015:
                    pyautogui.click()
                    cv2.putText(frame, "BLINK CLICK!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                    time.sleep(0.3)

        cv2.imshow("Eye Controlled Mouse - ESC to stop", frame)
        if cv2.waitKey(1) & 0xFF == 27: break

    cap.release()
    cv2.destroyAllWindows()

def capture_photo():
    print("📸 Capturing photo...")
    cap = cv2.VideoCapture(0)
    for _ in range(30): cap.read()
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("captured_photo.jpg", frame)
        print("✅ Photo saved!")
        try: Image.open("captured_photo.jpg").show()
        except: pass
    cap.release()
    cv2.destroyAllWindows()

# ====================== GUI ======================
if __name__ == "__main__":
    window = tk.Tk()
    window.title("Virtual & Hand Controlled Mouse - Team 4")
    window.geometry("520x420")

    tk.Label(window, text="Virtual & Hand Controlled Mouse", font=("Arial", 16, "bold")).pack(pady=20)

    for text, cmd in [
        ("1. Volume Control (Hand)", lambda: threading.Thread(target=volume_control, daemon=True).start()),
        ("2. Virtual Mouse (Hand)", lambda: threading.Thread(target=virtual_mouse, daemon=True).start()),
        ("3. Eye Controlled Mouse", lambda: threading.Thread(target=eye_controlled_mouse, daemon=True).start()),
        ("4. Capture Photo", capture_photo)
    ]:
        tk.Button(window, text=text, command=cmd, width=35, height=2, font=("Arial", 10)).pack(pady=8)

    tk.Label(window, text="Press ESC in the OpenCV window to stop", fg="red", font=("Arial", 9)).pack(pady=10)
    window.mainloop()