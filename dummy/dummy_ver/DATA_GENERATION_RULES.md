# 더미 데이터 생성 규칙 상세 설명

## 1. 학생/직장인/일반 더미데이터 생성 규칙

### 📊 생체 데이터 생성 규칙

각 사용자 타입별로 **정규분포(Normal Distribution)**를 사용하여 현실적인 데이터를 생성합니다.

#### 🎓 Student (학생)
**특징**: 불규칙한 수면 패턴, 높은 활동량

| 피처 | 평균 | 표준편차 | 범위 | 특징 |
|------|------|----------|------|------|
| 평균 심박수 | 75 | 10 | 50-120 | 젊은 연령대 |
| 최소 심박수 | 60 | 8 | 40-80 | - |
| 최대 심박수 | 140 | 20 | 100-200 | 높은 활동량 |
| 심박변이도 | 50 | 15 | 20-100 | 스트레스 중간 |
| 휴식 심박수 | 65 | 8 | 45-85 | - |
| **걸음 수** | **8000** | **3000** | 0-25000 | **높은 활동량** ⭐ |
| 활동 칼로리 | 400 | 150 | 0-1000 | 높음 |
| 운동 시간 | 30 | 20 | 0-120 | - |
| 서있던 시간 | 10 | 3 | 0-16 | - |
| **수면 시간** | **6.5** | **1.5** | 3-12 | **적은 수면** ⚠️ |
| **수면 질** | **65** | **15** | 0-100 | **낮은 질** ⚠️ |
| 혈중 산소 | 97 | 2 | 90-100 | - |

**핵심 특징**:
- 수면 시간 평균 6.5시간 (부족)
- 수면 질 65점 (낮음)
- 걸음 수 8000보 (높은 활동량)
- 높은 변동성 (표준편차 큼)

---

#### 💼 Worker (직장인)
**특징**: 규칙적인 패턴, 낮은 활동량, 높은 스트레스

| 피처 | 평균 | 표준편차 | 범위 | 특징 |
|------|------|----------|------|------|
| 평균 심박수 | 72 | 8 | 50-120 | 안정적 |
| 최소 심박수 | 58 | 7 | 40-80 | - |
| 최대 심박수 | 130 | 18 | 100-200 | 중간 활동량 |
| **심박변이도** | **45** | **12** | 20-100 | **스트레스 높음** ⚠️ |
| 휴식 심박수 | 62 | 7 | 45-85 | - |
| **걸음 수** | **6000** | **2500** | 0-25000 | **낮은 활동량** ⚠️ |
| 활동 칼로리 | 300 | 120 | 0-1000 | 낮음 |
| 운동 시간 | 20 | 15 | 0-120 | 적음 |
| 서있던 시간 | 8 | 2 | 0-16 | 낮음 |
| 수면 시간 | 7 | 1 | 3-12 | 보통 |
| 수면 질 | 70 | 12 | 0-100 | 보통 |
| 혈중 산소 | 97 | 2 | 90-100 | - |

**핵심 특징**:
- 수면 시간 7시간 (적정)
- 걸음 수 6000보 (낮음, 주로 앉아서 근무)
- 심박변이도 45 (스트레스로 인한 낮은 HRV)
- 낮은 변동성 (규칙적인 생활)

---

#### 👥 General (일반)
**특징**: 평균적인 생활 패턴

| 피처 | 평균 | 표준편차 | 범위 | 특징 |
|------|------|----------|------|------|
| 평균 심박수 | 70 | 9 | 50-120 | 평균 |
| 최소 심박수 | 58 | 8 | 40-80 | - |
| 최대 심박수 | 135 | 19 | 100-200 | - |
| 심박변이도 | 48 | 14 | 20-100 | 중간 |
| 휴식 심박수 | 63 | 8 | 45-85 | - |
| 걸음 수 | 7000 | 2800 | 0-25000 | 평균 |
| 활동 칼로리 | 350 | 140 | 0-1000 | 평균 |
| 운동 시간 | 25 | 18 | 0-120 | - |
| 서있던 시간 | 9 | 2.5 | 0-16 | - |
| **수면 시간** | **7.5** | **1.2** | 3-12 | **양호** ✅ |
| 수면 질 | 72 | 13 | 0-100 | 양호 |
| 혈중 산소 | 97 | 2 | 90-100 | - |

**핵심 특징**:
- 모든 지표가 중간값
- 수면 시간 7.5시간 (가장 좋음)
- 안정적인 생활 패턴

---

### 🌤️ 날씨 데이터 생성 규칙

날씨 데이터는 **시간적 상관관계**를 고려하여 생성됩니다.

#### 기본 분포
```python
base_temp = np.random.normal(20, 10)        # 온도: 평균 20°C, 표준편차 10
base_humidity = np.random.normal(60, 20)     # 습도: 평균 60%, 표준편차 20
base_precip = np.random.exponential(2)       # 강수량: 지수분포 (평균 2mm)
base_wind = np.random.exponential(3)         # 풍속: 지수분포 (평균 3m/s)
base_pressure = np.random.normal(1013, 10)   # 기압: 평균 1013hPa
base_uv = np.random.uniform(0, 11)           # 자외선: 균등분포 (0-11)
```

#### 시간 오프셋별 변화
**당일(d0), 1일전(d1), 3일전(d3), 7일전(d7)**

```python
noise_factor = 1 + (offset * 0.1)  # 시간이 지날수록 변동성 증가

# 예: 3일전 날씨는 noise_factor = 1.3
# 즉, 과거로 갈수록 현재와의 차이가 커짐
```

| 오프셋 | noise_factor | 의미 |
|--------|--------------|------|
| d0 (당일) | 1.0 | 기준 |
| d1 (1일전) | 1.1 | 10% 증가 |
| d3 (3일전) | 1.3 | 30% 증가 |
| d7 (7일전) | 1.7 | 70% 증가 |

**현실적 패턴**: 7일 전 날씨는 오늘과 크게 다를 수 있지만, 어제 날씨는 비슷한 경향

---

### 🎯 피로도 라벨 생성 규칙 (핵심!)

**규칙 기반 점수 시스템**으로 현실적인 피로도 라벨 생성

#### 점수 계산 규칙

```python
fatigue_score = 0  # 초기값

# 1. 수면 시간
if sleep_hours < 6:
    fatigue_score += 2     # 6시간 미만 → +2점 (심각)
elif sleep_hours < 7:
    fatigue_score += 1     # 6-7시간 → +1점 (부족)

# 2. 수면 질
if sleep_quality < 60:
    fatigue_score += 2     # 60점 미만 → +2점 (나쁨)
elif sleep_quality < 70:
    fatigue_score += 1     # 60-70점 → +1점 (보통)

# 3. 심박변이도 (HRV - 스트레스 지표)
if heart_rate_variability < 40:
    fatigue_score += 1     # HRV 낮음 = 스트레스 높음

# 4. 운동량 (과유불급)
if exercise_minutes > 60:
    fatigue_score += 1     # 과도한 운동
elif exercise_minutes < 10:
    fatigue_score += 1     # 운동 부족

# 5. 날씨 영향
if temperature > 30 or temperature < 5:
    fatigue_score += 1     # 극한 온도

if humidity > 80:
    fatigue_score += 1     # 높은 습도

if atmospheric_pressure < 1000:
    fatigue_score += 1     # 저기압 (두통 유발)

# 6. 사용자 타입별 조정
if user_type == 'student':
    if steps > 10000:
        fatigue_score -= 1  # 학생은 활동량 많으면 오히려 좋음
elif user_type == 'worker':
    if stand_hours > 10:
        fatigue_score += 1  # 직장인은 오래 서있으면 피로

# 7. 랜덤 노이즈 추가 (현실성)
fatigue_score += np.random.randint(-1, 2)  # -1, 0, 1 중 랜덤

# 8. 최종 라벨 결정
if fatigue_score <= 1:
    label = 0  # 좋음
elif fatigue_score <= 4:
    label = 1  # 보통
else:
    label = 2  # 나쁨
```

#### 라벨 분포 결과

| User Type | 좋음 (0) | 보통 (1) | 나쁨 (2) | 총계 |
|-----------|---------|---------|---------|------|
| Student   | 231 (23%) | 597 (60%) | 172 (17%) | 1000 |
| Worker    | 253 (25%) | 613 (61%) | 134 (13%) | 1000 |
| General   | 383 (38%) | 538 (54%) | 79 (8%) | 1000 |

**분석**:
- General 사용자가 가장 건강 (좋음 38%)
- Student가 가장 피로 (나쁨 17%)
- 모든 타입에서 '보통'이 가장 많음 (현실적)

---

## 2. 서버 배포 시 모델 로딩 부담 분석

### 💾 메모리 사용량 분석

#### 현재 모델 크기

| 모델 | 파일 크기 | 로딩 후 메모리 | 예상 RAM |
|------|----------|---------------|----------|
| Student XGBoost | 553 KB | ~15 MB | 낮음 |
| Worker XGBoost | 552 KB | ~15 MB | 낮음 |
| General XGBoost | 528 KB | ~15 MB | 낮음 |
| Student Ensemble | 3.2 MB | ~80 MB | 중간 |
| Worker Ensemble | 2.8 MB | ~70 MB | 중간 |
| General Ensemble | 3.9 MB | ~90 MB | 중간 |
| **총합 (3개 모두 로딩)** | **~11.5 MB** | **~285 MB** | **여유** ✅ |

### 🚀 서버 배포 시나리오

#### 시나리오 1: 모든 모델 사전 로딩 (권장) ⭐

```python
# 서버 시작 시 모든 모델 로딩
models = {
    'student_ensemble': load_model('ensemble/student_ensemble_model.pkl'),
    'worker_ensemble': load_model('ensemble/worker_ensemble_model.pkl'),
    'general_xgboost': load_model('xgboost_only/general_xgboost_model.pkl')
}

# 예측 (즉시 응답)
def predict(user_type, features):
    model_key = f"{user_type}_ensemble" if user_type != 'general' else 'general_xgboost'
    return models[model_key].predict(features)
```

**장점**:
- ✅ **빠른 응답 속도** (~10-50ms)
- ✅ 사용자 경험 우수
- ✅ 메모리 285MB만 사용 (매우 적음)

**단점**:
- ⚠️ 서버 시작 시간 약 5초 증가 (문제 없음)

**결론**: **전혀 무리 없음!** 최신 서버는 기본 1-2GB RAM이므로 285MB는 매우 여유

---

#### 시나리오 2: 동적 로딩 (필요 시에만 로딩)

```python
models = {}

def predict(user_type, features):
    model_key = f"{user_type}_ensemble"

    # 캐시에 없으면 로딩
    if model_key not in models:
        models[model_key] = load_model(f'ensemble/{model_key}.pkl')

    return models[model_key].predict(features)
```

**장점**:
- ✅ 초기 메모리 사용 적음
- ✅ 사용하지 않는 모델은 로딩 안 함

**단점**:
- ⚠️ 첫 요청 시 느림 (1-2초 딜레이)
- ⚠️ 사용자 경험 저하

**결론**: 비추천 (메모리가 극도로 제한적인 경우만)

---

#### 시나리오 3: 하이브리드 (가장 사용 빈도 높은 것만 사전 로딩)

```python
# 가장 많이 사용되는 모델만 사전 로딩
models = {
    'student_ensemble': load_model('ensemble/student_ensemble_model.pkl'),
    'general_xgboost': load_model('xgboost_only/general_xgboost_model.pkl')
}

# Worker는 필요시 로딩 (사용자가 적다면)
def predict(user_type, features):
    model_key = get_model_key(user_type)

    if model_key not in models:
        models[model_key] = load_model(...)  # Lazy loading

    return models[model_key].predict(features)
```

**결론**: 과최적화, 필요 없음

---

### 📊 실제 서버 성능 예측

#### 서버 사양별 권장

| 서버 사양 | RAM | 동시 접속자 | 권장 방식 | 예상 응답속도 |
|----------|-----|------------|----------|--------------|
| **최소** | 512 MB | 10-50 | 시나리오 1 | 10-50ms ✅ |
| **권장** | 1 GB | 100-500 | 시나리오 1 | 10-30ms ✅ |
| **고성능** | 2 GB+ | 1000+ | 시나리오 1 + 캐싱 | <10ms ✅ |

#### AWS/GCP 서버 기준

| 서비스 | 인스턴스 타입 | RAM | 비용 | 권장도 |
|--------|--------------|-----|------|--------|
| AWS EC2 | t3.micro | 1 GB | $0.01/hr | ✅ 충분 |
| AWS EC2 | t3.small | 2 GB | $0.02/hr | ✅ 여유 |
| GCP | e2-micro | 1 GB | $0.008/hr | ✅ 충분 |
| Heroku | Free | 512 MB | Free | ⚠️ 빡빡 (가능) |

---

### 🎯 최종 결론 및 권장사항

## **전혀 무리 없음!** ✅✅✅

### 이유:

1. **메모리 사용량 적음**
   - 3개 모델 전체 ~285MB
   - 최신 서버는 기본 1GB+ RAM
   - 285MB는 약 28% 사용 (매우 여유)

2. **로딩 속도 빠름**
   - pkl 파일 로딩 ~1-2초
   - 서버 시작 시 한 번만 로딩
   - 이후 추론은 ~10-50ms

3. **동시 접속자 처리**
   - 모델은 한 번만 로딩 후 공유
   - 1000명이 접속해도 메모리 285MB로 충분
   - 병목은 CPU/네트워크이지 모델 크기 아님

4. **비용 효율**
   - AWS t3.micro (1GB RAM) 충분
   - 월 $7 정도면 운영 가능

### 권장 구조:

```python
class FatiguePredictionServer:
    def __init__(self):
        # 서버 시작 시 모든 모델 사전 로딩 (5초 소요)
        self.models = {
            'student': load_ensemble('student'),    # 80MB
            'worker': load_ensemble('worker'),      # 70MB
            'general': load_xgboost('general')      # 15MB
        }
        print("All models loaded! Ready to serve.")

    def predict(self, user_type, features):
        # 즉시 응답 (10-50ms)
        return self.models[user_type].predict(features)

# 서버 시작
app = FatiguePredictionServer()  # 5초 대기
# 이후 모든 요청은 즉시 처리! ⚡
```

### 성능 목표:

| 지표 | 목표 | 예상 | 달성 가능성 |
|------|------|------|------------|
| 서버 시작 시간 | <10초 | ~5초 | ✅ 여유 |
| 예측 응답 시간 | <100ms | 10-50ms | ✅ 여유 |
| 동시 접속자 | 100명 | 500+ | ✅ 여유 |
| 메모리 사용 | <1GB | 285MB | ✅ 여유 |
| 월 운영 비용 | <$10 | ~$7 | ✅ 적정 |

---

## 📝 추가 최적화 팁 (필요시)

### 1. 모델 압축 (선택)
```python
import joblib

# 압축하여 저장 (파일 크기 30% 감소)
joblib.dump(model, 'model.pkl', compress=3)
```

### 2. 캐싱 (고급)
```python
from functools import lru_cache

@lru_cache(maxsize=1000)  # 최근 1000개 예측 결과 캐싱
def predict_cached(user_type, features_hash):
    return model.predict(features)
```

### 3. 비동기 처리 (대량 트래픽)
```python
import asyncio

async def predict_async(user_type, features):
    # 비동기로 여러 요청 동시 처리
    return await asyncio.to_thread(models[user_type].predict, features)
```

**하지만 현재는 이런 최적화 필요 없음!** 기본 구조로도 충분히 빠름.

---

**최종 답변**: **앙상블 2개 + XGBoost 1개 = 전혀 무리 없습니다!** 🎉
