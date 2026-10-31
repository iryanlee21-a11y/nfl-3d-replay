"""1단계: 선수 탐지 + 추적
YOLOv8m(COCO 사전학습)으로 사람을 탐지하고 ByteTrack으로 프레임 간 ID를 유지한다.
작은 선수까지 잡기 위해 입력 해상도를 960으로 올렸다.
출력: data/tracks.csv (frame, id, x1, y1, x2, y2, conf)"""
import cv2, pandas as pd
from ultralytics import YOLO
from common import VIDEO, TRACKS

model = YOLO("yolov8m.pt")              # 없으면 자동으로 내려받는다
cap = cv2.VideoCapture(str(VIDEO))
rows, f = [], 0
while True:
    ok, frame = cap.read()
    if not ok:
        break
    r = model.track(frame, persist=True, classes=[0], imgsz=960, conf=0.25,
                    tracker="bytetrack.yaml", verbose=False)[0]
    if r.boxes.id is not None:
        for (x1, y1, x2, y2), tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.conf.tolist()):
            rows.append(dict(frame=f, id=tid, x1=x1, y1=y1, x2=x2, y2=y2, conf=c))
    f += 1
df = pd.DataFrame(rows)
df.to_csv(TRACKS, index=False)
life = df.groupby("id").frame.count()
print(f"frames={f} detections={len(df)} ids={df.id.nunique()} ids>=2s={(life >= 60).sum()}")
