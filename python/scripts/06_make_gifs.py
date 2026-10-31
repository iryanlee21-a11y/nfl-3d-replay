"""6단계: README용 결과 이미지
media/topdown.gif  : 원본 영상 + 위에서 본 경기장 (0 ~ LAST_RELIABLE_FRAME)
media/tracking.gif : 전체 플레이 추적 결과 (ID 박스, 흰 박스 = BUF, 보라 박스 = BAL)"""
import cv2, numpy as np, pandas as pd
from PIL import Image
from common import VIDEO, TRACKS, FIELD, DOCS, LAST_RELIABLE_FRAME as LAST

field_df, tracks = pd.read_csv(FIELD), pd.read_csv(TRACKS)
XMIN, XMAX, W, S = -30, 12, 53.33, 14          # 1야드 = 14px
fx = lambda x: int((XMAX - x) * S)              # 공격 방향(X 감소)이 오른쪽
fy = lambda y: int(y * S)

def field_img():
    im = np.zeros((int(W * S) + 1, int((XMAX - XMIN) * S) + 1, 3), np.uint8); im[:] = (60, 120, 40)
    for x in range(XMIN, XMAX + 1):
        if x % 5 == 0:
            cv2.line(im, (fx(x), 0), (fx(x), im.shape[0]), (230, 230, 230), 2)
        for yh in (23.58, 29.75):
            cv2.line(im, (fx(x), fy(yh) - 4), (fx(x), fy(yh) + 4), (230, 230, 230), 1)
    cv2.line(im, (fx(2.1), 0), (fx(2.1), im.shape[0]), (200, 60, 40), 2)   # 스크리미지 라인
    return im

def topdown(f):
    im = field_img()
    for _, g in field_df[(field_df.frame <= f) & (field_df.frame > f - 45)].groupby("id"):
        pts = np.array([[fx(x), fy(y)] for x, y in zip(g.X, g.Y)], np.int32)
        if len(pts) > 1:
            cv2.polylines(im, [pts], False, (200, 200, 200), 1)
    for r in field_df[field_df.frame == f].itertuples():
        buf = r.team == "BUF"
        cv2.circle(im, (fx(r.X), fy(r.Y)), 8, (255, 255, 255) if buf else (30, 30, 30), -1)
        cv2.circle(im, (fx(r.X), fy(r.Y)), 8, (0, 0, 255) if buf else (180, 60, 160), 2)
    cv2.putText(im, f"{f / 29.97:.1f}s", (8, 24), 0, 0.7, (255, 255, 255), 2)
    return im

def is_white(img, r):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); h, w = r.y2 - r.y1, r.x2 - r.x1
    roi = hsv[max(int(r.y1 + .15 * h), 0):int(r.y1 + .45 * h), max(int(r.x1 + .25 * w), 0):int(r.x2 - .25 * w)]
    return roi.size and ((roi[..., 2] > 160) & (roi[..., 1] < 70)).mean() > 0.12

def pil(bgr, width):
    h = int(bgr.shape[0] * width / bgr.shape[1])
    return Image.fromarray(cv2.cvtColor(cv2.resize(bgr, (width, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))

def save(frames, path):
    frames = [f.quantize(colors=96, method=Image.Quantize.MEDIANCUT) for f in frames]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)

cap, frames = cv2.VideoCapture(str(VIDEO)), []
while True:
    ok, img = cap.read()
    if not ok:
        break
    frames.append(img)
DOCS.mkdir(exist_ok=True)
td = []
for i in range(0, LAST + 1, 3):
    t = topdown(i); v = cv2.resize(frames[i], (t.shape[0], t.shape[0]))
    td.append(pil(np.hstack([v, t]), 640))
save(td, DOCS / "topdown.gif")
tr = []
for i in range(0, len(frames), 4):
    img = frames[i].copy()
    for r in tracks[tracks.frame == i].itertuples():
        col = (255, 255, 255) if is_white(img, r) else (180, 60, 160)
        cv2.rectangle(img, (int(r.x1), int(r.y1)), (int(r.x2), int(r.y2)), col, 3)
        cv2.putText(img, str(r.id), (int(r.x1), int(r.y1) - 6), 0, 1.0, (0, 255, 255), 3)
    tr.append(pil(img, 360))
save(tr, DOCS / "tracking.gif")
print("saved media/topdown.gif, media/tracking.gif")
