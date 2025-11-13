"""
Configuration for Fatigue Prediction Model
"""

from pathlib import Path

# 경로 설정
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent.parent.parent.parent
PMDATA_DIR = PROJECT_ROOT / "lifelog" / "pmdata"

# 데이터 파일명
FITBIT_FILES = [
    "calories.json",
    "distance.json",
    "exercise.json",
    "heart_rate.json",
    "resting_heart_rate.json",
    "sleep.json",
    "steps.json"
]

WELLNESS_FILE = "pmsys/wellness.csv"

# 참가자 목록
PARTICIPANTS = [f"p{i:02d}" for i in range(1, 17)]  # p01 ~ p16

# 피처 엔지니어링 설정
ROLLING_WINDOW_DAYS = 7  # 7일 이동 평균
SEQUENCE_LENGTH = 7      # LSTM용 시퀀스 길이 (현재 XGBoost라 미사용)

# 모델 설정
TARGET_COLUMN = "fatigue"
NUM_CLASSES = 3  # 피로도 Low(1-2), Medium(3), High(4-5)
CLASS_MAPPING = {
    1: 0,  # Low
    2: 0,  # Low
    3: 1,  # Medium
    4: 2,  # High
    5: 2   # High
}
CLASS_NAMES = ["Low", "Medium", "High"]

# XGBoost RandomSearch 설정
RANDOM_SEARCH_ITERATIONS = 50
CV_FOLDS = None  # Leave-One-Participant-Out 사용
RANDOM_STATE = 42

# 평가 메트릭
SCORING_METRIC = "f1_macro"

# 저장 경로
OUTPUT_DIR = BASE_DIR / "output"
MODEL_DIR = OUTPUT_DIR / "models"
RESULTS_DIR = OUTPUT_DIR / "results"
PLOTS_DIR = OUTPUT_DIR / "plots"

# 디렉토리 생성
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

print(f"✓ Config loaded")
print(f"  PMDATA_DIR: {PMDATA_DIR}")
print(f"  OUTPUT_DIR: {OUTPUT_DIR}")
