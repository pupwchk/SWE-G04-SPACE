# Fatigue Prediction Model

Apple Watch 호환 데이터를 사용한 피로도 예측 XGBoost 분류 모델

## 프로젝트 개요

- **목적**: Fitbit pmdata를 활용하여 사용자의 피로도(1-5점) 예측
- **모델**: XGBoost Classifier
- **하이퍼파라미터 탐색**: RandomizedSearchCV (50회 반복)
- **교차 검증**: Leave-One-Participant-Out CV (16-fold)
- **피처**: Apple Watch에서 수집 가능한 데이터만 사용

## 디렉토리 구조

```
Fatigue/
├── config.py                    # 설정 파일
├── utils.py                     # 유틸리티 함수
├── 1_data_loader.py             # Step 1: JSON → 일일 집계 DataFrame
├── 2_feature_engineering.py     # Step 2: 피처 생성 (이동 평균, 파생 피처)
├── 3_train_xgboost.py           # Step 3: XGBoost 학습 + RandomSearch
├── 4_evaluate.py                # Step 4: 평가 및 시각화
├── run_pipeline.py              # 전체 파이프라인 실행
├── output/                      # 출력 디렉토리
│   ├── daily_aggregated.csv     # 일일 집계 데이터
│   ├── features_engineered.csv  # 피처 엔지니어링 완료 데이터
│   ├── feature_list.txt         # 피처 목록
│   ├── models/                  # 학습된 모델
│   │   ├── xgboost_best_model.pkl
│   │   └── random_search_results.pkl
│   ├── results/                 # 평가 결과
│   │   ├── cv_results.csv
│   │   ├── feature_importance.csv
│   │   ├── best_parameters.txt
│   │   ├── leave_one_out_results.csv
│   │   └── evaluation_summary.txt
│   └── plots/                   # 시각화
│       ├── confusion_matrix.png
│       ├── feature_importance.png
│       ├── cv_results.png
│       └── participant_performance.png
└── README.md
```

## 사용법

### 1. 환경 설정

```bash
# 가상환경 활성화
source /Users/eojunho/HYU/25-2/SWE/venv/bin/activate

# 의존성 설치
pip install pandas numpy scikit-learn xgboost matplotlib seaborn scipy
```

### 2. 전체 파이프라인 실행 (권장)

```bash
cd /Users/eojunho/HYU/25-2/SWE/SWEG04/SWE-G04-SPACE/Model/Fatigue
python run_pipeline.py
```

**예상 시간**: 30-40분 (RandomSearch 50회)

### 3. 단계별 실행

```bash
# Step 1: 데이터 로드 (5분)
python 1_data_loader.py

# Step 2: 피처 엔지니어링 (2분)
python 2_feature_engineering.py

# Step 3: 모델 학습 (30분)
python 3_train_xgboost.py

# Step 4: 평가 및 시각화 (5분)
python 4_evaluate.py
```

## 파이프라인 상세

### Step 1: Data Loader

**입력**: `pmdata/p01-p16/fitbit/*.json`, `pmsys/wellness.csv`

**처리**:
- 7개 Apple Watch 호환 JSON 파일 로드
  - calories.json, distance.json, exercise.json
  - heart_rate.json, resting_heart_rate.json
  - sleep.json, steps.json
- 일일 집계 수행
  - 심박수: 평균/최대/최소/표준편차
  - 수면: 총 시간/깊은 수면/REM/얕은 수면
  - 운동: 세션 수/총 시간/칼로리
- wellness.csv와 병합 (타겟 변수)

**출력**: `output/daily_aggregated.csv` (~1763 rows)

### Step 2: Feature Engineering

**입력**: `output/daily_aggregated.csv`

**처리**:
1. **파생 피처 생성** (10개)
   - 수면 효율성, 수면의 질 점수
   - 깊은 수면/REM 비율
   - 활동-수면 균형
   - 심박수 범위, 안정시 심박수 비율
   - 칼로리/걸음수 효율, 보폭, 운동 강도

2. **시계열 피처** (40개)
   - 7일/3일 이동 평균 (10개 피처 × 2)
   - 전날 대비 변화량 (4개 피처)
   - 요일, 주말, 월 중 날짜

3. **결측치 처리**
   - Forward fill → Backward fill → 0

**출력**: `output/features_engineered.csv` (~70 features)

### Step 3: XGBoost Training

**입력**: `output/features_engineered.csv`

**모델**: XGBoost Multi-class Classifier

**하이퍼파라미터 탐색**:
```python
RandomizedSearchCV(
    n_iter=50,
    cv=LeaveOneGroupOut(),  # 16-fold
    scoring='f1_macro'
)
```

**탐색 파라미터**:
- n_estimators: 100-500
- max_depth: 3-10
- learning_rate: 0.01-0.3
- subsample, colsample_bytree: 0.6-1.0
- gamma, reg_alpha, reg_lambda

**출력**:
- `models/xgboost_best_model.pkl`
- `results/best_parameters.txt`
- `results/cv_results.csv`
- `results/feature_importance.csv`

### Step 4: Evaluation

**평가 방법**: Leave-One-Participant-Out CV

**메트릭**:
- Accuracy
- F1-score (macro, weighted)
- Confusion Matrix
- 참가자별 성능

**시각화**:
1. **Confusion Matrix**: 피로도 예측 정확도
2. **Feature Importance**: 상위 20개 중요 피처
3. **CV Results**: RandomSearch 점수 분포
4. **Participant Performance**: 참가자별 성능 비교

**출력**:
- `results/evaluation_summary.txt`
- `results/leave_one_out_results.csv`
- `plots/*.png` (4개 그래프)

## 주요 피처 (예상 상위 10개)

1. `sleep_duration_7d_avg` - 7일 평균 수면시간
2. `resting_hr_7d_avg` - 7일 평균 안정시 심박수
3. `sleep_deep` - 깊은 수면 시간
4. `hr_std` - 심박수 변동성 (스트레스)
5. `total_steps_7d_avg` - 7일 평균 걸음수
6. `exercise_duration` - 운동 시간
7. `sleep_quality_score` - 수면의 질
8. `resting_hr_diff_1d` - 안정시 심박수 변화
9. `sleep_rem` - REM 수면 시간
10. `day_of_week` - 요일 효과

## 예상 성능

```
Accuracy:       0.70 - 0.80
F1 (macro):     0.65 - 0.75
F1 (weighted):  0.68 - 0.78
```

**주의**: 데이터 불균형 (대부분 Fatigue 2-3)으로 인해 F1-score가 중요

## Apple Watch 실전 배포

학습된 모델을 실전 배포할 때:

1. **데이터 수집** (iOS HealthKit)
   - 7개 JSON 파일 데이터 수집
   - 일일 집계 수행

2. **피처 계산**
   - 이동 평균, 변화량 계산
   - 파생 피처 생성

3. **모델 추론**
   ```python
   import pickle

   # 모델 로드
   with open('xgboost_best_model.pkl', 'rb') as f:
       model = pickle.load(f)

   # 예측
   fatigue_level = model.predict(features)[0] + 1  # 0-4 → 1-5
   ```

4. **스마트홈 자동화**
   - Fatigue ≥ 4: 조명 밝기 낮춤, 온도 조절
   - Fatigue ≤ 2: 활동 권장 알림

## 문의

- Junho Uh (djwnsgh0248@hanyang.ac.kr)
