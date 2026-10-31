"""4단계: 픽셀 추적 결과 -> 경기장 좌표 + 필터 + 팀 분류 (0 ~ LAST_RELIABLE_FRAME)
- 선수 위치: 박스 아래쪽 가운데(발)
- 경기장 밖(사이드라인 밖) 탐지 제거, 사이드라인 근처에서 3야드도 안 움직인 ID(스태프·심판) 제거
- 팀: 상체 영역의 흰색 비율로 BUF(흰 유니폼) / BAL(검정 유니폼), ID 안에서 15프레임 다수결
  (ID가 겹친 선수에게 넘어가는 경우가 있어 ID 단위가 아니라 프레임 단위로 판단)
출력: data/field_tracks_raw.csv"""
import cv2, numpy as np, pandas as pd
from common import VIDEO, TRACKS, H_CAMERA, H_FIELD, FIELD_RAW, LAST_RELIABLE_FRAME as LAST

FIELD_W = 53.33
H_to0, H_f = np.load(H_CAMERA), np.load(H_FIELD)
df = pd.read_csv(TRACKS)
df = df[df.frame <= LAST].copy()

cap, f, white = cv2.VideoCapture(str(VIDEO)), 0, {}
while f <= LAST:
    ok, img = cap.read()
    if not ok:
        break
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for r in df[df.frame == f].itertuples():
        h, w = r.y2 - r.y1, r.x2 - r.x1
        roi = hsv[max(int(r.y1 + .15 * h), 0):int(r.y1 + .45 * h), max(int(r.x1 + .25 * w), 0):int(r.x2 - .25 * w)]
        if roi.size:
            white[r.Index] = float(((roi[..., 2] > 160) & (roi[..., 1] < 70)).mean())
    f += 1
df["white"] = pd.Series(white)

H_all = np.stack([H_f @ H_to0[i] for i in range(LAST + 1)])
foot = np.stack([(df.x1 + df.x2) / 2, df.y2, np.ones(len(df))], axis=1)
P = np.einsum("nij,nj->ni", H_all[df.frame.values], foot)
df["X"], df["Y"] = P[:, 0] / P[:, 2], P[:, 1] / P[:, 2]

n0 = df.id.nunique()
df = df[(df.Y > -1) & (df.Y < FIELD_W + 1)]
g = df.groupby("id").agg(ym=("Y", "median"), xr=("X", lambda s: s.max() - s.min()))
df = df[~df.id.isin(g[(g.ym < 1.5) & (g.xr < 3)].index)]
df = df.sort_values(["id", "frame"])
isw = (df.white > 0.12).astype(float)
df["team"] = np.where(isw.groupby(df.id).transform(lambda s: s.rolling(15, center=True, min_periods=1).mean()) > .5, "BUF", "BAL")
df = df[df.groupby("id").frame.transform("count") >= 8]
df[["X", "Y"]] = df.groupby("id")[["X", "Y"]].transform(lambda s: s.rolling(7, center=True, min_periods=1).median())
df.to_csv(FIELD_RAW, index=False)
print(f"IDs {n0} -> {df.id.nunique()} (경기장 밖·스태프 제거), 프레임당 평균 {df.groupby('frame').size().mean():.1f}명")
