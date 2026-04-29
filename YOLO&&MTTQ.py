# pip install ultralytics opencv-python paho-mqtt
# Step 1: Broker setup (Laptop pe)

# Install:
# 👉 Mosquitto

# Install (Windows):
# Google: “Mosquitto download”
# Install normally
# Start broker:
# mosquitto

from ultralytics import YOLO
import cv2
import paho.mqtt.publish as publish

BROKER = "192.168.1.100"

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    person_detected = False

    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0:  # person
                person_detected = True

    if person_detected:
        publish.single("classroom/light", "ON", hostname=BROKER)
        print("Human detected → ON")
    else:
        publish.single("classroom/light", "OFF", hostname=BROKER)
        print("No human → OFF")

    cv2.imshow("YOLO", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()