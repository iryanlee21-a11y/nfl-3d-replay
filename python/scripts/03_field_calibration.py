"""3단계: 0번 프레임 -> 경기장 좌표(야드)
0번 프레임에서 위치를 알 수 있는 경기장 표시 6개를 직접 찾아 호모그래피를 계산한다.
  X: 경기장 길이 방향(야드), 야드 라인 A = 0
  Y: 먼 쪽 사이드라인에서의 거리(야드)
NFL 규격: 야드 라인 5야드 간격, 해시마크는 사이드라인에서 70'9" = 23.58야드, 두 해시 사이 18'6" = 6.17야드
검증: 기준점에 쓰지 않은 해시 눈금이 규격 위치로 변환되는지 확인한다."""
import cv2, numpy as np
from common import H_FIELD

HASH_FAR = 23.58
HASH_NEAR = HASH_FAR + 6.17
img_pts = np.float32([[15, 62], [420, 55], [817, 45],      # 야드 라인 A, B, C x 사이드라인
                      [778, 405],                          # 야드 라인 B x 먼 쪽 해시
                      [362, 555], [918, 537]])             # 야드 라인 A, B x 가까운 쪽 해시
fld_pts = np.float32([[0, 0], [5, 0], [10, 0], [5, HASH_FAR], [0, HASH_NEAR], [5, HASH_NEAR]])
H, _ = cv2.findHomography(img_pts, fld_pts, 0)
np.save(H_FIELD, H)

proj = cv2.perspectiveTransform(img_pts.reshape(-1, 1, 2), H).reshape(-1, 2)
print("기준점 재투영 오차(야드):", np.round(np.linalg.norm(proj - fld_pts, axis=1), 2))
checks = {"먼 쪽 해시 (862,395)": ((862, 395), HASH_FAR), "먼 쪽 해시 (1067,390)": ((1067, 390), HASH_FAR),
          "가까운 해시 (245,565)": ((245, 565), HASH_NEAR), "가까운 해시 (685,550)": ((685, 550), HASH_NEAR),
          "가까운 해시 (1012,537)": ((1012, 537), HASH_NEAR)}
for name, (p, y_true) in checks.items():
    x, y = cv2.perspectiveTransform(np.float32([[p]]), H)[0, 0]
    print(f"검증 {name}: X={x:.2f} (1야드 눈금 {round(x)}), Y={y:.2f} (규격 {y_true:.2f})")
