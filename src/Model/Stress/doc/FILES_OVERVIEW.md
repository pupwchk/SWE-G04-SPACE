# Stress 폴더 파일 구조 및 기능 설명

## 📂 전체 구조

```
Stress/
├── 📘 문서 파일
│   ├── README.md                   # 영문 전체 문서
│   ├── README_KR.md               # 한글 전체 문서
│   ├── QUICKSTART.md              # 빠른 시작 가이드
│   ├── DEPLOYMENT_GUIDE.md        # 실전 배포 가이드
│   └── FILES_OVERVIEW.md          # 이 파일
│
├── 🔧 핵심 모듈 (실제 사용)
│   ├── __init__.py                # 패키지 초기화
│   ├── hrv_calculator.py          # HRV 계산 모듈
│   ├── stress_detector.py         # 스트레스 감지 모듈
│   └── realtime_monitor.py        # 실시간 모니터링 모듈
│
├── 🎮 데모 및 예제 (학습/테스트용)
│   ├── demo.py                    # 자동 실행 데모
│   ├── example_usage.py           # 상세 예제 (5가지)
│   ├── test_realtime.py           # 실시간 모니터 테스트
│   └── test_api.py                # API 테스트
│
└── 🗂️ 기타
    └── __pycache__/               # Python 캐시 (자동 생성)
```

---

## 📘 문서 파일

### 1. `README.md` (영문 전체 문서)
**목적**: 모듈의 완전한 영문 기술 문서

**내용**:
- 모듈 개요 및 아키텍처
- 각 클래스 및 함수 상세 설명
- HRV 지표 설명 (SDNN, RMSSD, pNN50)
- 스트레스 레벨 임계값
- Apple Watch HealthKit 통합 방법
- FastAPI 백엔드 예제
- 연구 배경 및 참고문헌
- 성능 및 정확도 정보

**대상**: 영어권 개발자, 기술 문서

---

### 2. `README_KR.md` (한글 전체 문서)
**목적**: 한국어 사용자를 위한 완전한 문서

**내용**: README.md와 동일하지만 한글로 작성
- 모든 기술 용어 한글화
- 한국어 권장사항
- 한글 코드 주석 및 설명

**대상**: 한국인 개발자, 프로젝트 발표

---

### 3. `QUICKSTART.md` (빠른 시작 가이드)
**목적**: 5분 안에 시작할 수 있는 간단한 가이드

**내용**:
- 3가지 실행 방법 (터미널, VSCode, 직접 실행)
- 기본 사용 예제
- 트러블슈팅 (자주 발생하는 오류 해결)
- 파일 목록 및 설명

**대상**: 처음 사용하는 개발자

**사용 시기**: 프로젝트를 처음 받았을 때

---

### 4. `DEPLOYMENT_GUIDE.md` (실전 배포 가이드)
**목적**: Apple Watch 데이터를 서버로 받아 실제 운영하는 방법

**내용**:
- 전체 시스템 아키텍처
- FastAPI 백엔드 구축 (완전한 코드)
- iOS 앱 구현 (Swift/SwiftUI 코드)
- HealthKit 연동 방법
- WebSocket 실시간 스트리밍
- Docker 배포 설정
- 프로덕션 체크리스트

**대상**: 실제 서비스 구축하는 개발자

**사용 시기**: 프로토타입을 실제 서비스로 만들 때

---

### 5. `FILES_OVERVIEW.md` (이 파일)
**목적**: 폴더 내 모든 파일의 역할과 관계 설명

**내용**: 각 파일의 기능, 사용 시기, 관계도

**대상**: 프로젝트 구조를 파악하고 싶은 개발자

---

## 🔧 핵심 모듈 (실제 사용)

### 6. `__init__.py` (패키지 초기화)
**목적**: Stress 폴더를 Python 패키지로 만들기

**내용**:
```python
from .hrv_calculator import HRVCalculator, RollingHRVCalculator, HRVMetrics
from .stress_detector import StressDetector, StressLevel, StressAssessment
from .realtime_monitor import RealtimeStressMonitor, StressMonitorSession

__all__ = [...]  # 내보낼 클래스 목록
__version__ = '1.0.0'
```

**기능**:
- 다른 파일에서 `from Stress import ...` 형식으로 import 가능
- 외부에 노출할 클래스/함수 정의

**사용 예시**:
```python
# 다른 파일에서
from Stress import HRVCalculator, StressDetector
```

**수정 필요**: ❌ (변경하지 않아도 됨)

---

### 7. `hrv_calculator.py` (HRV 계산 모듈) ⭐
**목적**: 심박수 데이터로부터 HRV 지표 계산

**핵심 클래스**:

#### `HRVCalculator` (정적 계산)
- 한 번에 여러 심박수 데이터를 받아 HRV 계산
- 배치 처리에 적합

**주요 메서드**:
```python
# 심박수 → RR 간격 변환
heart_rate_to_rr_intervals(heart_rates: List[float]) -> List[float]

# SDNN 계산 (전체 HRV)
calculate_sdnn(rr_intervals: List[float]) -> float

# RMSSD 계산 (단기 HRV, 스트레스 민감)
calculate_rmssd(rr_intervals: List[float]) -> float

# pNN50 계산 (부교감신경 활동)
calculate_pnn50(rr_intervals: List[float]) -> float

# 모든 HRV 지표 한 번에 계산
calculate_hrv_metrics(rr_intervals: List[float]) -> HRVMetrics
```

#### `RollingHRVCalculator` (실시간 계산)
- 심박수 데이터를 하나씩 받아 실시간으로 계산
- 롤링 윈도우 방식 (최근 N개만 사용)

**주요 메서드**:
```python
# 심박수 추가 (실시간)
add_heart_rate(heart_rate: float) -> Optional[HRVMetrics]

# 현재 HRV 가져오기
get_current_hrv() -> Optional[HRVMetrics]

# 버퍼 초기화
reset()
```

**사용 시기**:
- `HRVCalculator`: 과거 데이터 분석, 배치 처리
- `RollingHRVCalculator`: 실시간 모니터링

---

### 8. `stress_detector.py` (스트레스 감지 모듈) ⭐
**목적**: HRV 지표로부터 스트레스 수준 판정

**핵심 클래스**:

#### `StressLevel` (열거형)
5단계 스트레스 레벨:
```python
VERY_LOW = 1    # 매우 낮음
LOW = 2         # 낮음
MODERATE = 3    # 보통
HIGH = 4        # 높음
VERY_HIGH = 5   # 매우 높음
```

**메서드**:
```python
stress_level.to_korean()  # "매우 낮음", "높음" 등
str(stress_level)         # "Very Low", "High" 등
```

#### `StressDetector`
**주요 메서드**:
```python
# 스트레스 감지
detect_stress(hrv_metrics: HRVMetrics) -> StressAssessment

# 권장사항 가져오기
get_stress_recommendations(assessment: StressAssessment) -> Dict
```

**임계값** (연구 기반):
```python
RMSSD_THRESHOLDS = {
    'very_high': 15,   # < 15ms → 매우 높은 스트레스
    'high': 25,        # < 25ms → 높은 스트레스
    'moderate': 35,    # < 35ms → 보통 스트레스
    'low': 50,         # < 50ms → 낮은 스트레스
}
```

**StressAssessment** (결과 객체):
```python
assessment.stress_level     # StressLevel 열거형
assessment.stress_score     # 0-100 점수
assessment.confidence       # 0-1 신뢰도
assessment.hrv_metrics      # 원본 HRV 지표
assessment.reasoning        # 판단 근거
assessment.timestamp        # 평가 시간
```

---

### 9. `realtime_monitor.py` (실시간 모니터링 모듈) ⭐
**목적**: 연속적인 심박수 스트림을 모니터링하고 스트레스 추적

**핵심 클래스**:

#### `RealtimeStressMonitor`
**초기화 파라미터**:
```python
RealtimeStressMonitor(
    window_size=60,          # HRV 계산용 RR 간격 개수
    update_interval=10,      # 스트레스 업데이트 주기 (초)
    on_stress_change=callback,    # 스트레스 변화 시 호출
    on_high_stress_alert=callback # 고 스트레스 감지 시 호출
)
```

**주요 메서드**:
```python
# 심박수 추가 (실시간)
add_heart_rate(hr: float, timestamp: datetime) -> Optional[StressAssessment]

# 현재 스트레스 조회
get_current_stress() -> Optional[StressAssessment]

# 스트레스 트렌드 분석 (최근 N분)
get_stress_trend(duration_minutes: int) -> List[StressAssessment]

# 평균 스트레스 점수
get_average_stress_score(duration_minutes: int) -> Optional[float]

# 스트레스 증가 중인지 확인
is_stress_increasing(duration_minutes: int) -> bool

# 초기화
reset()
```

#### `StressMonitorSession` (컨텍스트 매니저)
**사용법**:
```python
with StressMonitorSession(monitor) as session:
    # 모니터링 수행
    for hr in heart_rate_stream:
        monitor.add_heart_rate(hr)

# 세션 종료 후 요약
summary = session.get_session_summary()
```

**세션 요약 정보**:
- 세션 시작/종료 시간
- 평균/최소/최대 스트레스
- 스트레스 레벨 분포
- 고 스트레스 에피소드 수

---

## 🎮 데모 및 예제 (학습/테스트용)

### 10. `demo.py` (자동 실행 데모) ⭐ **추천**
**목적**: 사용자 입력 없이 자동으로 실행되는 데모

**3가지 데모**:
1. **기본 HRV 계산**: 심박수 → HRV 지표
2. **스트레스 감지**: 다양한 시나리오 (이완/보통/고 스트레스)
3. **실시간 모니터링**: 10초간 점진적 스트레스 증가

**실행 방법**:
```bash
python demo.py
```

**특징**:
- ✅ 자동 실행 (input() 없음)
- ✅ 10초 만에 완료
- ✅ 모든 기능 시연

**사용 시기**:
- 프로젝트 시연
- 빠른 동작 확인
- 프레젠테이션

---

### 11. `example_usage.py` (상세 예제)
**목적**: 5가지 상세한 사용 예제와 설명

**5가지 예제**:
1. **기본 HRV 계산**: 간단한 계산 예제
2. **스트레스 감지**: 4가지 시나리오 비교
3. **실시간 모니터링**: 콜백 함수 사용
4. **세션 관리**: 컨텍스트 매니저 사용
5. **Apple Watch 통합**: 실제 통합 시뮬레이션

**실행 방법**:
```bash
python example_usage.py
```

**특징**:
- ✅ 모든 기능 상세 설명
- ✅ 코드 주석 포함
- ✅ 단계별 진행 (Enter 키로 이동)

**사용 시기**:
- 모듈 사용법 학습
- 각 클래스/메서드 이해
- 코드 복사하여 사용

---

### 12. `test_realtime.py` (실시간 모니터 테스트)
**목적**: `realtime_monitor.py`의 기능만 집중 테스트

**테스트 내용**:
- 콜백 함수 동작 확인
- 30초간 스트레스 점진적 증가
- 트렌드 분석 결과 표시

**실행 방법**:
```bash
python test_realtime.py
```

**사용 시기**:
- 실시간 모니터링 기능만 테스트
- 콜백 로직 확인
- 트렌드 분석 검증

---

### 13. `test_api.py` (API 테스트) ⭐
**목적**: FastAPI 서버가 실행 중일 때 API 엔드포인트 테스트

**테스트 기능**:
- `/heart-rate` POST - 심박수 전송
- `/current/{user_id}` GET - 현재 스트레스 조회
- `/trend/{user_id}` GET - 트렌드 조회
- `/reset/{user_id}` DELETE - 모니터 초기화

**실행 방법**:
```bash
# 터미널 1: 서버 시작
cd BackEnd/fastapi-starter
uvicorn app.main:app --reload --port 11325

# 터미널 2: 테스트 실행
cd Model/Stress
python test_api.py
```

**특징**:
- ✅ 실제 HTTP 요청 전송
- ✅ 80회 심박수 데이터 시뮬레이션
- ✅ 결과 요약 자동 표시

**사용 시기**:
- 백엔드 API 개발 후 테스트
- 서버-클라이언트 통신 검증
- iOS 앱 개발 전 API 확인

---

## 📊 파일 간 관계도

```
┌─────────────────────────────────────────────────┐
│                   사용자                          │
└────────────┬────────────────────────────────────┘
             │
             ├─ 학습: README_KR.md, QUICKSTART.md
             ├─ 테스트: demo.py, example_usage.py
             └─ 배포: DEPLOYMENT_GUIDE.md
             │
             ↓
┌─────────────────────────────────────────────────┐
│              핵심 모듈 (실제 사용)                │
├─────────────────────────────────────────────────┤
│  hrv_calculator.py                              │
│    ↓ (HRVMetrics)                              │
│  stress_detector.py                             │
│    ↓ (StressAssessment)                        │
│  realtime_monitor.py                            │
│    ↓                                            │
│  __init__.py (패키지화)                         │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│          테스트/데모 (개발 및 검증)               │
├─────────────────────────────────────────────────┤
│  demo.py          - 로컬 테스트                 │
│  test_realtime.py - 모듈 단위 테스트            │
│  test_api.py      - API 통합 테스트             │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│        실제 배포 (프로덕션)                       │
├─────────────────────────────────────────────────┤
│  BackEnd/fastapi-starter/app/api/stress.py     │
│    └─ FastAPI 엔드포인트                        │
│  iOS App (HealthKit + SwiftUI)                 │
│    └─ Apple Watch 연동                          │
└─────────────────────────────────────────────────┘
```

---

## 🎯 상황별 사용 파일 가이드

### 1️⃣ 처음 프로젝트를 받았을 때
1. `README_KR.md` 읽기 (전체 개요 파악)
2. `QUICKSTART.md` 읽기 (빠른 시작)
3. `demo.py` 실행 (동작 확인)

### 2️⃣ 모듈 사용법을 배우고 싶을 때
1. `example_usage.py` 실행 (5가지 예제)
2. 각 핵심 모듈 파일 읽기:
   - `hrv_calculator.py`
   - `stress_detector.py`
   - `realtime_monitor.py`

### 3️⃣ 백엔드 API 개발할 때
1. `DEPLOYMENT_GUIDE.md` 읽기
2. `BackEnd/.../api/stress.py` 생성 (가이드에 코드 있음)
3. `test_api.py` 실행 (API 테스트)

### 4️⃣ iOS 앱 개발할 때
1. `DEPLOYMENT_GUIDE.md`의 iOS 섹션 읽기
2. Swift 코드 복사하여 사용:
   - `HealthKitManager.swift`
   - `StressAPIService.swift`
   - `StressMonitorView.swift`

### 5️⃣ 프레젠테이션/데모 할 때
1. `demo.py` 실행 (자동 데모)
2. 또는 `test_api.py` 실행 (실제 서버 연동 시연)

### 6️⃣ 논문/보고서 작성할 때
1. `README_KR.md`의 "연구 배경" 섹션 참조
2. HRV 임계값 표 사용
3. 참고문헌 인용

---

## ⚡ 빠른 참조

### 핵심 3개 파일 (반드시 알아야 함)
1. **`hrv_calculator.py`** - HRV 계산
2. **`stress_detector.py`** - 스트레스 감지
3. **`realtime_monitor.py`** - 실시간 모니터링

### 문서 2개 (읽어야 함)
1. **`README_KR.md`** - 전체 이해
2. **`DEPLOYMENT_GUIDE.md`** - 실제 구현

### 테스트 2개 (실행 추천)
1. **`demo.py`** - 빠른 동작 확인
2. **`test_api.py`** - API 테스트

---

## 📝 요약

| 파일 | 유형 | 중요도 | 용도 |
|------|------|--------|------|
| `README_KR.md` | 문서 | ⭐⭐⭐⭐⭐ | 전체 이해 |
| `DEPLOYMENT_GUIDE.md` | 문서 | ⭐⭐⭐⭐⭐ | 실제 배포 |
| `hrv_calculator.py` | 모듈 | ⭐⭐⭐⭐⭐ | HRV 계산 |
| `stress_detector.py` | 모듈 | ⭐⭐⭐⭐⭐ | 스트레스 감지 |
| `realtime_monitor.py` | 모듈 | ⭐⭐⭐⭐⭐ | 실시간 모니터링 |
| `demo.py` | 데모 | ⭐⭐⭐⭐ | 빠른 확인 |
| `test_api.py` | 테스트 | ⭐⭐⭐⭐ | API 검증 |
| `example_usage.py` | 예제 | ⭐⭐⭐ | 학습용 |
| `QUICKSTART.md` | 문서 | ⭐⭐⭐ | 빠른 시작 |
| `test_realtime.py` | 테스트 | ⭐⭐ | 모듈 테스트 |
| `README.md` | 문서 | ⭐⭐ | 영문 문서 |
| `__init__.py` | 설정 | ⭐ | 패키지화 |

---

**마지막 업데이트**: 2025년 11월 13일
