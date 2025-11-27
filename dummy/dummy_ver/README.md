# 피로도 예측 XGBoost 모델 프로젝트

애플워치 생체데이터와 날씨 데이터를 사용하여 피로도를 3단계(좋음/보통/나쁨)로 예측하는 XGBoost 모델 학습 파이프라인입니다.

## 프로젝트 구조

```
lifelog/dummy_ver/
├── config/
│   └── features_config.py          # 피처 설정 및 상수 정의
├── data/
│   ├── student_data.csv            # 학생용 더미 데이터
│   ├── worker_data.csv             # 직장인용 더미 데이터
│   └── general_data.csv            # 일반용 더미 데이터
├── models/
│   ├── student_model.json          # 학생용 학습 모델
│   ├── student_metadata.json       # 학생용 모델 메타데이터
│   ├── student_results.json        # 학생용 모델 평가 결과
│   ├── worker_model.json           # 직장인용 학습 모델
│   ├── worker_metadata.json        # 직장인용 모델 메타데이터
│   ├── worker_results.json         # 직장인용 모델 평가 결과
│   ├── general_model.json          # 일반용 학습 모델
│   ├── general_metadata.json       # 일반용 모델 메타데이터
│   ├── general_results.json        # 일반용 모델 평가 결과
│   └── training_summary.json       # 전체 학습 요약
├── scripts/
│   ├── generate_dummy_data.py      # 더미 데이터 생성 스크립트
│   ├── train_model.py              # 모델 학습 스크립트
│   └── predict.py                  # 예측 스크립트
└── README.md
```

## 모델 개요

### 사용자 유형별 모델
- **학생용 (Student)**: 불규칙한 수면 패턴, 높은 활동량 특성 반영
- **직장인용 (Worker)**: 규칙적인 패턴, 높은 스트레스 특성 반영
- **일반용 (General)**: 평균적인 생활 패턴 특성 반영

### 피처 (Features)

#### 1. 생체 데이터 (Apple Watch)
- `heart_rate_avg`: 평균 심박수
- `heart_rate_min`: 최소 심박수
- `heart_rate_max`: 최대 심박수
- `heart_rate_variability`: 심박변이도 (HRV)
- `resting_heart_rate`: 휴식 시 심박수
- `steps`: 걸음 수
- `active_calories`: 활동 칼로리
- `exercise_minutes`: 운동 시간 (분)
- `stand_hours`: 서있던 시간
- `sleep_hours`: 수면 시간
- `sleep_quality`: 수면 질 (0-100)
- `blood_oxygen`: 혈중 산소포화도

#### 2. 날씨 데이터 (기상청 API)
각 날씨 피처는 4개의 시점(당일, 1일전, 3일전, 7일전)으로 제공됩니다:
- `temperature`: 온도
- `humidity`: 습도
- `precipitation`: 강수량
- `wind_speed`: 풍속
- `atmospheric_pressure`: 기압
- `uv_index`: 자외선 지수

총 피처 수: 12개 생체 데이터 + 24개 날씨 데이터 = 36개

### 타겟 클래스
- **좋음 (0)**: 피로도가 낮은 상태
- **보통 (1)**: 보통 수준의 피로도
- **나쁨 (2)**: 피로도가 높은 상태

## 설치 및 환경 설정

### 1. 가상환경 생성
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 2. 패키지 설치
```bash
pip install xgboost scikit-learn pandas numpy
```

## 사용 방법

### 1. 더미 데이터 생성
```bash
python scripts/generate_dummy_data.py
```

이 스크립트는 다음을 생성합니다:
- `data/student_data.csv`: 학생용 1000개 샘플
- `data/worker_data.csv`: 직장인용 1000개 샘플
- `data/general_data.csv`: 일반용 1000개 샘플

### 2-A. 기본 모델 학습 (단일 XGBoost)
```bash
python scripts/train_model.py
```

학습 프로세스:
- 데이터를 train/validation/test 세트로 분할
- XGBoost 모델 학습 (early stopping 포함)
- 5-fold 교차 검증 수행
- 모델 평가 및 성능 지표 계산
- 피처 중요도 분석
- 모델 및 결과 저장

### 2-B. 앙상블 모델 학습 ⭐ (권장)
```bash
python scripts/train_ensemble_model.py
```

앙상블 학습 프로세스:
- XGBoost + Random Forest + LightGBM 결합
- RandomizedSearchCV를 통한 하이퍼파라미터 자동 튜닝 (각 모델 20회)
- Soft Voting 기법으로 예측 결합
- 5-fold 교차 검증
- 개별 모델 및 앙상블 모델 비교 평가
- Student/Worker 모델: 약 2-3% 성능 향상

**단일 사용자 타입 테스트**:
```bash
python scripts/train_ensemble_single.py
```

### 3. 예측
```bash
python scripts/predict.py
```

또는 Python 코드에서 사용:

```python
from scripts.predict import FatiguePredictor

# 예측기 초기화
predictor = FatiguePredictor(user_type='student')

# 피처 준비
features = {
    'heart_rate_avg': 75,
    'sleep_hours': 6.5,
    'sleep_quality': 70,
    # ... 나머지 피처들
}

# 예측 수행
result = predictor.predict(features)

print(f"예측 결과: {result['predicted_label']}")
print(f"신뢰도: {result['confidence']:.2%}")
```

## 모델 성능

### 전체 성능 비교

| User Type | Accuracy | F1 (Macro) | F1 (Weighted) |
|-----------|----------|------------|---------------|
| Student   | 0.7000   | 0.5792     | 0.6680        |
| Worker    | 0.7050   | 0.5431     | 0.6692        |
| General   | 0.7250   | 0.6369     | 0.7170        |

### 주요 피처 중요도

#### Student 모델
1. sleep_hours (수면 시간)
2. sleep_quality (수면 질)
3. exercise_minutes (운동 시간)
4. heart_rate_variability (심박변이도)
5. steps (걸음 수)

#### Worker 모델
1. sleep_hours (수면 시간)
2. sleep_quality (수면 질)
3. exercise_minutes (운동 시간)
4. heart_rate_variability (심박변이도)
5. stand_hours (서있던 시간)

#### General 모델
1. sleep_hours (수면 시간)
2. sleep_quality (수면 질)
3. heart_rate_variability (심박변이도)
4. exercise_minutes (운동 시간)
5. active_calories (활동 칼로리)

## 모델 파라미터

```python
params = {
    'objective': 'multi:softprob',  # 다중 클래스 분류
    'num_class': 3,                  # 3개 클래스
    'max_depth': 6,                  # 최대 트리 깊이
    'learning_rate': 0.1,            # 학습률
    'n_estimators': 100,             # 부스팅 라운드
    'subsample': 0.8,                # 샘플링 비율
    'colsample_bytree': 0.8,         # 피처 샘플링 비율
    'min_child_weight': 3,           # 최소 자식 가중치
    'gamma': 0.1,                    # 분할 최소 손실 감소
    'eval_metric': 'mlogloss'        # 평가 지표
}
```

## 데이터 생성 로직

더미 데이터는 실제 생리학적 패턴을 반영하여 생성됩니다:

1. **생체 데이터**: 사용자 유형별로 다른 분포 사용
   - 학생: 낮은 수면 시간, 높은 활동량
   - 직장인: 규칙적 패턴, 낮은 활동량
   - 일반: 평균적 패턴

2. **날씨 데이터**: 시간적 상관관계 반영
   - 과거로 갈수록 현재 날씨와의 차이 증가

3. **피로도 라벨**: 규칙 기반 생성
   - 수면 시간/질
   - 운동량
   - 심박변이도
   - 날씨 조건
   - 사용자 유형별 특성

## 확장 가능성

### 실제 데이터 적용
1. `generate_dummy_data.py` 대신 실제 데이터 로더 구현
2. Apple Watch API 연동
3. 기상청 API 또는 Open-Meteo API 연동

### 모델 개선
1. 하이퍼파라미터 튜닝 (GridSearch, RandomSearch)
2. 앙상블 모델 (여러 모델 결합)
3. 딥러닝 모델 시도 (LSTM, Transformer)
4. 피처 엔지니어링 (상호작용 피처, 시계열 피처)

### 배포
1. REST API 서버 구축 (Flask, FastAPI)
2. 모바일 앱 통합
3. 실시간 예측 시스템
4. 모델 모니터링 및 재학습 파이프라인

## 라이센스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
