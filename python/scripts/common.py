"""공통 경로 설정. 모든 스크립트는 python/ 폴더에서 실행한다: python scripts/01_track_players.py"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT.parent / "media"
VIDEO = DATA / "nfl_sample.mp4"          # 원본 영상 (저작권 때문에 레포에는 없음, README 참고)
TRACKS = DATA / "tracks.csv"             # 01: 픽셀 좌표 추적 결과
H_CAMERA = DATA / "camera_H_to0.npy"     # 02: 각 프레임 -> 0번 프레임 호모그래피
H_FIELD = DATA / "H_field_from0.npy"     # 03: 0번 프레임 -> 경기장(야드) 호모그래피
FIELD_RAW = DATA / "field_tracks_raw.csv"  # 04: 경기장 좌표 (필터 전)
FIELD = DATA / "field_tracks.csv"        # 05: 경기장 좌표 (평활화) -> Unity 입력
LAST_RELIABLE_FRAME = 200                # 카메라 보정이 믿을 만한 마지막 프레임 (README '한계' 참고)
