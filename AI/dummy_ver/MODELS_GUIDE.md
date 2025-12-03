# 모델 사용 가이드

## 📁 모델 디렉토리 구조

```
models/
├── xgboost_only/              # 단일 XGBoost 모델
│   ├── student_xgboost_model.pkl
│   ├── worker_xgboost_model.pkl
│   └── general_xgboost_model.pkl
│
├── ensemble/                   # 앙상블 모델
│   ├── student_ensemble_model.pkl
│   ├── student_xgb_model.pkl
│   ├── student_rf_model.pkl
│   ├── student_lgb_model.pkl
│   ├── student_ensemble_params.json
│   ├── student_ensemble_metadata.json
│   ├── student_ensemble_results.json
│   └── (worker, general 동일 구조)
│
└── (기존 JSON 모델들)
    ├── student_model.json
    ├── student_metadata.json
    ├── student_results.json
    └── ...
```

---

## 🎯 모델 선택 가이드

### 1. XGBoost 단일 모델 (xgboost_only/)

**사용 시기**:
- 빠른 추론 속도가 필요할 때
- 모델 크기를 작게 유지해야 할 때
- General 사용자 타입 (앙상블보다 6.9% 더 우수)

**성능**:
| User Type | Accuracy | File Size |
|-----------|----------|-----------|
| Student   | 70.5%    | 553 KB    |
| Worker    | 72.0%    | 552 KB    |
| General   | 70.0%    | 528 KB    |

**사용 방법**:
```python
from scripts.predict_with_pkl import PickleFatiguePredictor

# 모델 로드
predictor = PickleFatiguePredictor(user_type='student')

# 예측
result = predictor.predict(features)
print(f"예측: {result['predicted_label']}")
print(f"신뢰도: {result['confidence']:.2%}")
```

**실행**:
```bash
python3 scripts/predict_with_pkl.py
```

---

### 2. 앙상블 모델 (ensemble/)

**사용 시기**:
- 최고 성능이 필요할 때
- Student, Worker 사용자 타입 (2-3% 성능 향상)
- 개별 모델의 예측도 확인하고 싶을 때

**성능**:
| User Type | Accuracy | 개선율 | File Size |
|-----------|----------|--------|-----------|
| Student   | 72.0%    | +2.9%  | 3.2 MB    |
| Worker    | 72.0%    | +2.1%  | 2.8 MB    |
| General   | 67.5%    | -6.9%  | 3.9 MB    |

**구성**:
- XGBoost + Random Forest + LightGBM
- Soft Voting (확률 기반)
- RandomizedSearchCV로 하이퍼파라미터 최적화

**사용 방법**:
```python
from scripts.predict_with_ensemble import EnsembleFatiguePredictor

# 앙상블 모델 로드
predictor = EnsembleFatiguePredictor(user_type='student')

# 예측 (개별 모델 결과 포함)
result = predictor.predict(features, use_individual=True)

print(f"앙상블 예측: {result['predicted_label']}")
print(f"신뢰도: {result['confidence']:.2%}")

# 개별 모델 예측 확인
for model, pred in result['individual_predictions'].items():
    print(f"{model}: {pred['predicted_label']} ({pred['confidence']:.2%})")
```

**실행**:
```bash
python3 scripts/predict_with_ensemble.py
```

---

## 📊 성능 비교표

### Student 모델
| 모델 | Accuracy | F1 Score | 추천도 |
|------|----------|----------|--------|
| **Ensemble** | **72.0%** | **0.699** | ⭐⭐⭐⭐⭐ |
| Random Forest | 72.5% | 0.705 | ⭐⭐⭐⭐ |
| XGBoost (튜닝) | 71.5% | 0.699 | ⭐⭐⭐⭐ |
| XGBoost (pkl) | 70.5% | 0.684 | ⭐⭐⭐ |

### Worker 모델
| 모델 | Accuracy | F1 Score | 추천도 |
|------|----------|----------|--------|
| **Ensemble** | **72.0%** | **0.702** | ⭐⭐⭐⭐⭐ |
| XGBoost (pkl) | 72.0% | 0.687 | ⭐⭐⭐⭐ |
| LightGBM | 71.0% | 0.696 | ⭐⭐⭐⭐ |

### General 모델
| 모델 | Accuracy | F1 Score | 추천도 |
|------|----------|----------|--------|
| **XGBoost (단일)** | **70.0%** | **0.686** | ⭐⭐⭐⭐⭐ |
| XGBoost (튜닝) | 69.0% | 0.682 | ⭐⭐⭐⭐ |
| Ensemble | 67.5% | 0.656 | ⚠️ 비추천 |

---

## 🚀 권장 배포 전략

### 시나리오별 모델 선택

```python
def select_model(user_type, priority='performance'):
    """
    사용자 타입과 우선순위에 따라 최적 모델 선택

    Args:
        user_type: 'student', 'worker', 'general'
        priority: 'performance' (성능) 또는 'speed' (속도)
    """
    if priority == 'speed':
        # 빠른 추론이 필요한 경우 - 단일 XGBoost
        return f'xgboost_only/{user_type}_xgboost_model.pkl'

    elif user_type in ['student', 'worker']:
        # Student, Worker는 앙상블 권장 (2-3% 성능 향상)
        return f'ensemble/{user_type}_ensemble_model.pkl'

    else:  # general
        # General은 단일 XGBoost 권장 (앙상블보다 6.9% 우수)
        return f'xgboost_only/{user_type}_xgboost_model.pkl'

# 사용 예
model_path = select_model('student', priority='performance')
# → 'ensemble/student_ensemble_model.pkl'

model_path = select_model('general', priority='performance')
# → 'xgboost_only/general_xgboost_model.pkl'
```

---

## 📝 모델 재학습

### XGBoost 단일 모델
```bash
# 기존 JSON 모델을 pkl로 변환
python3 scripts/convert_models_to_pkl.py

# 또는 직접 학습
python3 scripts/train_model.py
```

### 앙상블 모델
```bash
# 전체 사용자 타입 학습 (약 10-15분 소요)
python3 scripts/train_ensemble_model.py

# 단일 사용자 타입 테스트 (약 3-5분 소요)
python3 scripts/train_ensemble_single.py
```

---

## 🔧 모델 로드 예제

### 1. pickle로 직접 로드
```python
import pickle

# XGBoost 단일 모델
with open('models/xgboost_only/student_xgboost_model.pkl', 'rb') as f:
    model = pickle.load(f)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)
```

### 2. 예측 클래스 사용
```python
# XGBoost
from scripts.predict_with_pkl import PickleFatiguePredictor
predictor = PickleFatiguePredictor(user_type='student')

# Ensemble
from scripts.predict_with_ensemble import EnsembleFatiguePredictor
predictor = EnsembleFatiguePredictor(user_type='worker')

result = predictor.predict(features_dict)
```

---

## 💾 파일 크기 및 속도 비교

| 모델 타입 | 파일 크기 | 추론 속도 | 메모리 사용량 |
|----------|----------|----------|-------------|
| XGBoost (pkl) | ~550 KB | 빠름 (1x) | 낮음 (1x) |
| Ensemble | ~3-4 MB | 보통 (3x) | 높음 (3x) |
| XGBoost (json) | ~570 KB | 빠름 (1x) | 낮음 (1x) |

**결론**:
- 실시간 서비스: XGBoost pkl 권장
- 배치 처리: Ensemble 권장 (Student/Worker만)
- 모바일/임베디드: XGBoost pkl 필수

---

## 🎓 요약

### XGBoost 단일 모델 (xgboost_only/)
- ✅ 빠른 속도
- ✅ 작은 파일 크기
- ✅ General 사용자에게 최적
- ⚠️ Student/Worker는 앙상블보다 성능 낮음

### 앙상블 모델 (ensemble/)
- ✅ 최고 성능 (Student/Worker)
- ✅ 개별 모델 예측 확인 가능
- ✅ 안정적인 예측
- ⚠️ 느린 속도 (3배)
- ⚠️ 큰 파일 크기 (3배)
- ⚠️ General 사용자에게 비추천

### 추천 사용법
```
Student 사용자  → ensemble/student_ensemble_model.pkl
Worker 사용자   → ensemble/worker_ensemble_model.pkl
General 사용자  → xgboost_only/general_xgboost_model.pkl
속도 우선      → xgboost_only/*.pkl
```

---

**작성일**: 2025-11-23
**버전**: 1.0
