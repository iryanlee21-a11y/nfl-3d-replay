from ultralytics import YOLO
import cv2
import pandas as pd

# 모델 불러오기 (기본: YOLOv8n)
model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture("data/nfl_sample.mp4")

frame_idx = 0
all_detections = []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    results = model(frame)
    annotated = results[0].plot()

    # 사람(person) 탐지 결과만 저장
    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf)
        cls = int(box.cls)
        label = model.names[cls]
        if label == "person":
            all_detections.append({
                "frame": frame_idx,
                "x1": x1.item(),
                "y1": y1.item(),
                "x2": x2.item(),
                "y2": y2.item(),
                "conf": conf
            })

    # 실시간 시각화
    cv2.namedWindow("NFL Player Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("NFL Player Detection", 1280, 720)
    cv2.imshow("NFL Player Detection", annotated)
    if cv2.waitKey(1) == 27:  # ESC로 종료
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()

# CSV로 저장
df = pd.DataFrame(all_detections)
df.to_csv("data/detections.csv", index=False)
print(f"Saved {len(df)} detections to data/detections.csv")