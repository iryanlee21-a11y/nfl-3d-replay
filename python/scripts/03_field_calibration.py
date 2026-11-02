"""3단계: 0번 프레임 -> 경기장 좌표(야드)
0번 프레임에서 경기장 표시를 자동으로 찾아 호모그래피를 계산한다.
  1) 흰색 픽셀에서 허프 변환으로 긴 직선(야드 라인) 5개를 찾는다: 골라인, 5, 10, 15, 20야드
  2) 선수 박스와 야드 라인을 지운 뒤 남은 작은 흰 조각(해시마크)을 RANSAC으로 두 줄로 묶는다
  3) 야드 라인 5개 x 해시 2줄 = 교점 10개로 호모그래피를 구한다
좌표:
  X: 골라인에서의 거리(야드), 골라인 = 0, 엔드존 방향이 음수
  Y: 먼 쪽 사이드라인에서의 거리(야드)
NFL 규격: 야드 라인 5야드 간격, 해시마크는 사이드라인에서 70'9" = 23.58야드, 두 해시 사이 18'6" = 6.17야드
검증: 기준점에 쓰지 않은 1야드 간격 해시마크들이 정수 야드 위치로 변환되는지 확인한다."""
import cv2, numpy as np
from ultralytics import YOLO
from common import VIDEO, H_FIELD

HASH_FAR = 23.58
HASH_NEAR = HASH_FAR + 6.17
YARDS = [0, 5, 10, 15, 20]                                 # 화면 오른쪽(엔드존)부터 왼쪽으로

ok, img = cv2.VideoCapture(str(VIDEO)).read()
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
white = ((hsv[..., 2] > 190) & (hsv[..., 1] < 60)).astype(np.uint8) * 255
for x1, y1, x2, y2 in YOLO("yolov8m.pt").predict(img, classes=[0], imgsz=1280, conf=0.2, verbose=False)[0].boxes.xyxy.int().tolist():
    white[max(y1 - 5, 0):y2 + 5, max(x1 - 5, 0):x2 + 5] = 0

# 1) 야드 라인: 화면 위(y=0)와 아래(y=h)에서의 x 위치로 표현하고, 가까운 직선끼리 묶어 평균
segs = cv2.HoughLinesP(white, 1, np.pi / 720, 200, minLineLength=300, maxLineGap=40)[:, 0]
segs = [s for s in segs if abs(s[3] - s[1]) > 1]
ends = sorted((x1 + (0 - y1) * (x2 - x1) / (y2 - y1), x1 + (h - y1) * (x2 - x1) / (y2 - y1)) for x1, y1, x2, y2 in segs)
groups = []
for a, b in ends:
    if groups and a - groups[-1][-1][0] < 40:
        groups[-1].append((a, b))
    else:
        groups.append([(a, b)])
lines = [np.mean(g, axis=0) for g in groups][::-1]        # 오른쪽(골라인)부터
assert len(lines) == len(YARDS), f"야드 라인 {len(lines)}개 검출 (5개 필요)"

# 2) 해시마크 두 줄
m = white.copy()
for a, b in lines:
    cv2.line(m, (int(a), 0), (int(b), h), 0, 22)
n, _, st, cen = cv2.connectedComponentsWithStats(m)
marks = np.float32([cen[i] for i in range(1, n) if 40 < st[i][4] < 600 and max(st[i][2], st[i][3]) < 45])
rng, rem, rows = np.random.default_rng(0), marks.copy(), []
for _ in range(2):
    best = None
    for _ in range(3000):
        p, q = rem[rng.choice(len(rem), 2, replace=False)]
        d = q - p
        if abs(d[1]) > 0.5 * abs(d[0]):                    # 해시 줄은 화면에서 거의 가로 방향
            continue
        inl = np.abs((rem - p) @ (np.array([-d[1], d[0]]) / np.linalg.norm(d))) < 6
        if best is None or inl.sum() > best.sum():
            best = inl
    rows.append(np.polyfit(rem[best, 0], rem[best, 1], 1))  # y = k x + c
    rem = rem[~best]
rows.sort(key=lambda r: r[1])                              # 위쪽 줄 = 먼 쪽 해시

# 3) 교점 10개 -> 호모그래피
img_pts, fld_pts = [], []
for (a, b), X in zip(lines, YARDS):
    s = (b - a) / h
    for (k, c), Y in zip(rows, (HASH_FAR, HASH_NEAR)):
        y = (k * a + c) / (1 - k * s)
        img_pts.append((a + s * y, y)); fld_pts.append((X, Y))
img_pts, fld_pts = np.float32(img_pts), np.float32(fld_pts)
H, _ = cv2.findHomography(img_pts, fld_pts, 0)
np.save(H_FIELD, H)

proj = cv2.perspectiveTransform(img_pts.reshape(-1, 1, 2), H).reshape(-1, 2)
print("기준점 재투영 오차(야드): 최대", np.linalg.norm(proj - fld_pts, axis=1).max().round(3))
F = cv2.perspectiveTransform(marks.reshape(-1, 1, 2), H).reshape(-1, 2)
on = (np.abs(F[:, 1] - HASH_FAR) < .6) | (np.abs(F[:, 1] - HASH_NEAR) < .6)
err = np.abs(F[on, 0] - np.round(F[on, 0]))
print(f"검증: 해시마크 {on.sum()}개가 정수 야드에서 벗어난 정도 평균 {err.mean():.2f}야드, 최대 {err.max():.2f}야드")
