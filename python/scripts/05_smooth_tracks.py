"""5단계: 궤적 다듬기 -> Unity 입력
1) 10프레임 이하 공백은 선형 보간  2) Savitzky-Golay 필터(창 21, 2차)로 떨림 제거
3) 0.5초(15프레임) 미만 구간 제거  4) 팀 라벨 15프레임 다수결로 정리
출력: data/field_tracks.csv (frame, id, team, X, Y)"""
import numpy as np, pandas as pd
from scipy.signal import savgol_filter
from common import FIELD_RAW, FIELD

df = pd.read_csv(FIELD_RAW)[["frame", "id", "team", "X", "Y"]]

def jitter(d):   # 프레임 간 가속도 크기 평균 (야드/프레임^2)
    v = []
    for _, g in d.sort_values("frame").groupby("id"):
        g = g[g.frame.diff().fillna(1) == 1]
        if len(g) > 3:
            v.append(np.hypot(np.diff(g.X, 2), np.diff(g.Y, 2)))
    return np.concatenate(v).mean()

rows = []
for pid, g in df.sort_values("frame").groupby("id"):
    full = g.set_index("frame").reindex(range(g.frame.min(), g.frame.max() + 1))
    gap = full.X.isna()
    keep = ~gap | (gap.groupby((gap != gap.shift()).cumsum()).transform("sum") <= 10)
    full[["X", "Y"]] = full[["X", "Y"]].interpolate(limit_area="inside")
    full["team"] = full.team.ffill()
    full = full[keep]
    for _, s in full.groupby((full.index.to_series().diff() != 1).cumsum()):
        if len(s) < 15:
            continue
        w = min(21, len(s) - (1 - len(s) % 2))
        s = s.copy()
        s["X"], s["Y"] = savgol_filter(s.X, w, 2), savgol_filter(s.Y, w, 2)
        isbuf = (s.team == "BUF").astype(float).rolling(15, center=True, min_periods=1).mean()
        s["team"], s["id"] = np.where(isbuf > .5, "BUF", "BAL"), pid
        rows.append(s.reset_index().rename(columns={"index": "frame"}))
res = pd.concat(rows)[["frame", "id", "team", "X", "Y"]].sort_values(["frame", "id"]).round(3)
res.to_csv(FIELD, index=False)
m = df.merge(res, on=["frame", "id"], suffixes=("_r", "_s"))
d = np.hypot(m.X_r - m.X_s, m.Y_r - m.Y_s)
print(f"떨림 {jitter(df):.3f} -> {jitter(res):.3f} 야드/프레임^2, 원래 위치와 차이 평균 {d.mean():.2f}야드 (95%: {d.quantile(.95):.2f})")
