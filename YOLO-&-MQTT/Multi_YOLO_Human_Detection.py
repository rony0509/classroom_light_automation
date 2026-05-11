import cv2
import paho.mqtt.client as mqtt
from ultralytics import YOLO
import threading
import time
import json
import os

# ==========================================
# 1. CONFIGURATION LOAD
# ==========================================
CONFIG_FILE = "cameras.json"

if not os.path.exists(CONFIG_FILE):
    print(f"Error: {CONFIG_FILE} not found! Please create it.")
    exit()

with open(CONFIG_FILE, "r") as f:
    CONFIG_DATA = json.load(f)

# Extract global settings with defaults
GLOBAL_CONFIG = CONFIG_DATA.get("settings", {})
MODEL_PATH = GLOBAL_CONFIG.get("model", "yolov8n.pt")
CONFIDENCE_THRESHOLD = GLOBAL_CONFIG.get("confidence_threshold", 0.5)
DETECTION_CLASS = GLOBAL_CONFIG.get("detection_class", 0)  # 0 = human in COCO
FRAME_WIDTH = GLOBAL_CONFIG.get("frame_width", 640)
FRAME_HEIGHT = GLOBAL_CONFIG.get("frame_height", 480)
FRAME_READ_DELAY = GLOBAL_CONFIG.get("frame_read_delay", 0.01)
MAIN_LOOP_DELAY = GLOBAL_CONFIG.get("main_loop_delay", 0.1)

CAMERA_CONFIGS = CONFIG_DATA.get("cameras", [])

print(f"Model: {MODEL_PATH}")
print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
print(f"Detection Class: {DETECTION_CLASS}")
print(f"Frame Size: {FRAME_WIDTH}x{FRAME_HEIGHT}")
print(f"Loaded {len(CAMERA_CONFIGS)} cameras from config.")

# ==========================================
# 2. MQTT SETUP
# ==========================================
client = mqtt.Client()
try:
    client.connect("broker.hivemq.com", 1883, 60)
    client.loop_start()
    print("Connected to MQTT Broker!")
except Exception as e:
    print(f"Failed to connect to MQTT: {e}")

# ==========================================
# 3. MULTI-THREADED CAMERA CLASS
# ==========================================
class CameraStream:
    def __init__(self, cam_id, source, topic, model):
        self.cam_id = cam_id
        self.source = source
        self.topic = topic
        self.model = model
        
        # Open video capture
        self.cap = cv2.VideoCapture(self.source)
        self.ret = False
        self.frame = None
        self.running = True
        self.prev_count = -1
        self.lock = threading.Lock()
        
        # Start a background thread to read frames
        # This prevents RTSP buffer lag (which causes delay/freezing)
        self.read_thread = threading.Thread(target=self._update_frames, daemon=True)
        self.read_thread.start()
        
        # Start a separate thread for YOLO detection
        # This allows multiple cameras to run detection in parallel
        self.detect_thread = threading.Thread(target=self._detect_objects, daemon=True)
        self.detect_thread.start()

    def _update_frames(self):
        """Continuously read frames from camera"""
        while self.running:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.ret = ret
                        self.frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            time.sleep(FRAME_READ_DELAY)

    def _detect_objects(self):
        """Run YOLO detection on latest frame"""
        while self.running:
            with self.lock:
                if self.ret and self.frame is not None:
                    frame = self.frame.copy()
                else:
                    frame = None
            
            if frame is not None:
                try:
                    results = self.model(frame, verbose=False)
                    count = 0
                    for r in results:
                        for box in r.boxes:
                            cls = int(box.cls[0])
                            conf = float(box.conf[0])
                            if cls == DETECTION_CLASS and conf > CONFIDENCE_THRESHOLD:
                                count += 1
                    
                    # Send only if count changed
                    if count != self.prev_count:
                        client.publish(self.topic, str(count))
                        print(f"[{self.cam_id}] Human Count: {count} -> {self.topic}")
                        self.prev_count = count
                except Exception as e:
                    print(f"[{self.cam_id}] Detection error: {e}")
            
            time.sleep(0.05)  # Detection loop delay

    def stop(self):
        self.running = False
        self.read_thread.join(timeout=2)
        self.detect_thread.join(timeout=2)
        self.cap.release()

# ==========================================
# 4. INITIALIZE CAMERAS & YOLO
# ==========================================
model = YOLO(MODEL_PATH)

cameras = []
for cfg in CAMERA_CONFIGS:
    cam = CameraStream(cfg["id"], cfg["source"], cfg["topic"], model)
    cameras.append(cam)
    print(f"Started stream for {cfg['id']} -> Topic: {cfg['topic']}")

print("All cameras initialized. Detection threads running...")

# ==========================================
# 5. MAIN LOOP - Keep program running
# ==========================================
try:
    while True:
        time.sleep(1)  # Keep main thread alive
        # Optional: Add health checks here
        # active_cameras = sum(1 for cam in cameras if cam.running)
        # print(f"Active cameras: {active_cameras}/{len(cameras)}")

except KeyboardInterrupt:
    print("\nStopping all cameras...")
finally:
    for cam in cameras:
        cam.stop()
    client.loop_stop()
    print("Stopped successfully.")
