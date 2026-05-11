
from ultralytics import YOLO
import cv2
import paho.mqtt.client as mqtt
import time

# 🔥 MQTT setup
client = mqtt.Client()
client.connect("broker.hivemq.com", 1883, 60)
client.loop_start()

topic = "classroom/human_count"

# YOLO
model = YOLO("yolov8n.pt")
url = "http://10.227.121.201:4747/video"
cap = cv2.VideoCapture(url)

frame_count = 0
prev_count = -1

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))

    frame_count += 1
    if frame_count % 4 != 0:
        continue

    results = model(frame)

    count = 0

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if cls == 0 and conf > 0.5:
                count += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)

    print("Human:", count)

    # 🔥 MQTT send only if changed
    if count != prev_count:
        client.publish(topic, str(count))
        print("Sent to ESP:", count)
        prev_count = count

    cv2.imshow("Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()