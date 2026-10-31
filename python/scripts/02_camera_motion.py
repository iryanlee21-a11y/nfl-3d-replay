"""2단계: 카메라 움직임 추정
중계 카메라는 고정 위치에서 회전·줌만 하므로, 연속한 두 프레임의 관계를 호모그래피 하나로 표현할 수 있다.
배경 특징점(선수 박스와 스코어보드 제외)을 광류로 따라가 프레임 간 호모그래피를 구하고,
이를 누적해 모든 프레임을 0번 프레임 좌표계로 맞춘다.
출력: data/camera_H_to0.npy (N x 3 x 3), --panorama 옵션 시 media/panorama.jpg"""
import sys, cv2, numpy as np, pandas as pd
from common import VIDEO, TRACKS, H_CAMERA, DOCS, LAST_RELIABLE_FRAME

df = pd.read_csv(TRACKS)
cap = cv2.VideoCapture(str(VIDEO))
H_to0, prev, f, frames = [np.eye(3)], None, 0, []
while True:
    ok, img = cap.read()
    if not ok:
        break
    frames.append(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.full((h, w), 255, np.uint8)
    mask[int(h * 0.80):, :] = 0                                   # 스코어보드
    for r in df[df.frame == f].itertuples():                       # 사람(움직이는 물체)
        mask[max(0, int(r.y1) - 10):int(r.y2) + 10, max(0, int(r.x1) - 10):int(r.x2) + 10] = 0
    if prev is not None:
        pg, pm = prev
        p0 = cv2.goodFeaturesToTrack(pg, 800, 0.01, 8, mask=pm)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(pg, gray, p0, None, winSize=(21, 21), maxLevel=4)
        good = st.ravel() == 1
        H, _ = cv2.findHomography(p1[good].reshape(-1, 2), p0[good].reshape(-1, 2), cv2.RANSAC, 2.0)
        H_to0.append(H_to0[-1] @ H)                                # 현재 -> 이전 -> ... -> 0
    prev = (gray, mask)
    f += 1
np.save(H_CAMERA, np.array(H_to0))
print(f"saved {len(H_to0)} homographies -> {H_CAMERA.name}")

if "--panorama" in sys.argv:   # 검증용: 보정 구간 프레임들을 0번 좌표계로 이어 붙인다
    H = np.array(H_to0); idx = range(0, LAST_RELIABLE_FRAME + 1, 10)
    h, w = int(frames[0].shape[0] * 0.8), frames[0].shape[1]
    c = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    allc = np.concatenate([cv2.perspectiveTransform(c, H[i]) for i in idx])
    (x0, y0), (x1, y1) = allc.min(axis=(0, 1)), allc.max(axis=(0, 1))
    s = 2400 / (x1 - x0); M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s], [0, 0, 1]])
    canvas = np.zeros((int((y1 - y0) * s) + 1, 2401, 3), np.uint8)
    for i in idx:
        wp = cv2.warpPerspective(frames[i][:h], M @ H[i], (canvas.shape[1], canvas.shape[0]))
        m = wp.sum(2) > 0; canvas[m] = wp[m]
    DOCS.mkdir(exist_ok=True); cv2.imwrite(str(DOCS / "panorama.jpg"), canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print("saved media/panorama.jpg")
