"""4단계: 픽셀 추적 결과 -> 경기장 좌표 + 필터 + 팀 분류 (0 ~ LAST_RELIABLE_FRAME)
- 선수 위치: 박스 아래쪽 가운데(발)
- 경기장 밖(사이드라인 밖, 엔드라인 뒤) 탐지 제거, 사이드라인 근처에서 3야드도 안 움직인 ID(스태프·심판) 제거
- 팀: 상체 영역의 빨간색 비율로 SF(49ers, 빨강) / LAR(Rams, 흰색), ID 안에서 31프레임(1초) 다수결
  (ID가 겹친 선수에게 넘어가는 경우가 있어 ID 단위가 아니라 프레임 단위로 판단)
출력: data/field_tracks_raw.csv"""
import cv2, numpy as np, pandas as pd
from common import VIDEO, TRACKS, H_CAMERA, H_FIELD, FIELD_RAW, LAST_RELIABLE_FRAME as LAST

FIELD_W = 53.33
END_LINE = -10                     # 엔드존 뒤쪽 끝
H_to0, H_f = np.load(H_CAMERA), np.load(H_FIELD)
df = pd.read_csv(TRACKS)
df = df[df.frame <= LAST].copy()

cap, f, red = cv2.VideoCapture(str(VIDEO)), 0, {}
while f <= LAST:
    ok, img = cap.read()
    if not ok:
        break
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for r in df[df.frame == f].itertuples():
        h, w = r.y2 - r.y1, r.x2 - r.x1
        roi = hsv[max(int(r.y1 + .15 * h), 0):int(r.y1 + .45 * h), max(int(r.x1 + .25 * w), 0):int(r.x2 - .25 * w)]
        if roi.size:
            # 그늘진 진한 빨강(버건디)도 잡도록 밝기 기준을 낮춤 (V>70이면 몸을 돌릴 때 SF를 LAR로 잘못 분류)
            red[r.Index] = float((((roi[..., 0] < 12) | (roi[..., 0] > 160)) & (roi[..., 1] > 60) & (roi[..., 2] > 30)).mean())
    f += 1
df["red"] = pd.Series(red)

H_all = np.stack([H_f @ H_to0[i] for i in range(LAST + 1)])
foot = np.stack([(df.x1 + df.x2) / 2, df.y2, np.ones(len(df))], axis=1)
P = np.einsum("nij,nj->ni", H_all[df.frame.values], foot)
df["X"], df["Y"] = P[:, 0] / P[:, 2], P[:, 1] / P[:, 2]

n0 = df.id.nunique()
df = df[(df.Y > -1) & (df.Y < FIELD_W + 1) & (df.X > END_LINE - 1)]
g = df.groupby("id").agg(ym=("Y", "median"), xr=("X", lambda s: s.max() - s.min()))
df = df[~df.id.isin(g[(g.ym < 2.5) & (g.xr < 3)].index)]
df = df.sort_values(["id", "frame"])
isr = (df.red > 0.10).astype(float)
df["team"] = np.where(isr.groupby(df.id).transform(lambda s: s.rolling(31, center=True, min_periods=1).mean()) > .5, "SF", "LAR")
df = df[df.groupby("id").frame.transform("count") >= 8]
df[["X", "Y"]] = df.groupby("id")[["X", "Y"]].transform(lambda s: s.rolling(7, center=True, min_periods=1).median())
df.to_csv(FIELD_RAW, index=False)
print(f"IDs {n0} -> {df.id.nunique()} (경기장 밖·스태프 제거), 프레임당 평균 {df.groupby('frame').size().mean():.1f}명")
