"""초기 시도: YOLOv8m + DeepSORT 추적, 화면 안정화, 경기장 영역(ROI) 필터.
이후 ByteTrack + 카메라 보정 + 경기장 좌표 변환(scripts/01~05)으로 대체했다. 기록용으로 남겨둔다."""
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import os

# --- 경로 설정 ---
video_path = "data/nfl_sample.mp4"
output_csv = "data/tracked_players_stable.csv"

# --- YOLO 모델 로드 ---
model = YOLO("yolov8m.pt")

# --- DeepSORT 초기화 ---
tracker = DeepSort(max_age=30, n_init=3)

# --- ROI (필드 영역 다각형) 정의 ---
# 실제 영상에 맞춰서 대략적인 필드 위치 설정 (필요시 조정)
roi_polygon = np.array([
    [120, 380],
    [950, 380],
    [1000, 920],
    [80, 920]
], np.int32)

# --- 비디오 로드 ---
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("❌ Video not found or cannot be opened.")
    exit()

# --- 안정화용 피처 포인트 설정 ---
prev_gray = None
prev_pts = None
transform_matrix = np.eye(3)

# --- 결과 저장용 ---
results = []

frame_idx = 0
print("🚀 Processing with stabilization + ROI filtering...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_idx += 1
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ---- (1) 카메라 움직임 보정 ----
    if prev_gray is not None:
        prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, prev_pts, None)

        good_old = prev_pts[status == 1]
        good_new = next_pts[status == 1]

        if len(good_old) > 10:
            H, _ = cv2.findHomography(good_new, good_old, cv2.RANSAC, 5.0)
            if H is not None:
                transform_matrix = H @ transform_matrix
                frame = cv2.warpPerspective(frame, transform_matrix, (frame.shape[1], frame.shape[0]))

    prev_gray = frame_gray.copy()

    # ---- (2) ROI 마스크 적용 ----
    mask = np.zeros_like(frame[:, :, 0])
    cv2.fillPoly(mask, [roi_polygon], 255)
    frame = cv2.bitwise_and(frame, frame, mask=mask)

    # ---- (3) YOLO 탐지 ----
    detections = model(frame, conf=0.4, classes=[0])  # person class only

    det_array = []
    for det in detections[0].boxes.data.cpu().numpy():
        x1, y1, x2, y2, conf, cls = det
        # 중심이 ROI 안에 있는 경우만 유지
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if cv2.pointPolygonTest(roi_polygon, (cx, cy), False) >= 0:
            det_array.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))

    # ---- (4) DeepSORT 업데이트 ----
    tracks = tracker.update_tracks(det_array, frame=frame)
    for track in tracks:
        if not track.is_confirmed():
            continue
        x1, y1, x2, y2 = track.to_ltrb()
        results.append([frame_idx, track.track_id, x1, y1, x2, y2])

    if frame_idx % 20 == 0:
        print(f"🟩 Frame {frame_idx}: {len(tracks)} active tracks")

cap.release()

# --- (5) 결과 저장 ---
df = pd.DataFrame(results, columns=["frame", "id", "x1", "y1", "x2", "y2"])
os.makedirs(os.path.dirname(output_csv), exist_ok=True)
df.to_csv(output_csv, index=False)
print(f"✅ Tracking stabilized. {len(df)} detections saved to {output_csv}")