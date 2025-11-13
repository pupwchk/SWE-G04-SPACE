# SPACE 스트레스 감지 모듈

지능형 스마트홈 자동화를 위한 실시간 HRV(심박 변이도) 기반 스트레스 모니터링 시스템

## 개요

이 모듈은 Apple Watch의 심박수 데이터를 사용하여 실시간으로 스트레스를 감지합니다. HRV 지표를 계산하고 스트레스 수준을 평가하여 개인화된 스마트홈 자동화 반응을 가능하게 합니다.

## 주요 기능

- ✅ **HRV 계산**: 심박수 데이터로부터 SDNN, RMSSD, pNN50 계산
- ✅ **스트레스 감지**: 5단계 스트레스 분류 (매우 낮음 → 매우 높음)
- ✅ **실시간 모니터링**: 콜백 기능을 통한 연속 스트레스 평가
- ✅ **Apple Watch 통합**: HealthKit 심박수 데이터용으로 설계
- ✅ **스마트홈 자동화**: 스트레스 수준에 따른 시나리오 트리거

## 시스템 구조

```
Apple Watch (HealthKit)
         ↓
   심박수 스트림
         ↓
   HRV 계산기
         ↓
    HRV 지표
  (SDNN, RMSSD, pNN50)
         ↓
   스트레스 감지기
         ↓
   스트레스 평가
 (레벨 1-5, 점수 0-100)
         ↓
  스마트홈 제어
```

## 모듈 구성

### 1. `hrv_calculator.py` - HRV 계산기

심박수 또는 RR 간격 데이터로부터 HRV 지표를 계산합니다.

**클래스:**
- `HRVCalculator`: 정적 HRV 계산
- `RollingHRVCalculator`: 실시간 롤링 윈도우 계산
- `HRVMetrics`: HRV 지표 데이터 컨테이너

**HRV 지표:**
- **SDNN**: NN 간격의 표준편차 (전체 HRV)
- **RMSSD**: 연속 차이의 제곱근 평균 제곱 (단기 HRV)
- **pNN50**: 50ms 이상 차이나는 연속 간격 비율 (부교감신경 활동)

### 2. `stress_detector.py` - 스트레스 감지기

연구 기반 임계값을 사용하여 HRV 지표로부터 스트레스 수준을 감지합니다.

**클래스:**
- `StressDetector`: 스트레스 수준 감지
- `StressLevel`: 5단계 스트레스 레벨 열거형
- `StressAssessment`: 평가 결과 컨테이너

**스트레스 레벨:**
1. **매우 낮음** (1): 최적의 이완 상태
2. **낮음** (2): 건강하고 낮은 스트레스
3. **보통** (3): 일상적인 스트레스
4. **높음** (4): 스트레스 상승, 개입 권장
5. **매우 높음** (5): 극심한 스트레스, 즉각 조치 필요

**임계값:**
- 동료 심사 연구 기반 (Kim et al., 2018; Thayer et al., 2012)
- 성인 연령 조정 (조정 가능)
- RMSSD(40%), SDNN(35%), pNN50(25%)의 가중 조합

### 3. `realtime_monitor.py` - 실시간 모니터

콜백과 트렌드 분석 기능을 갖춘 실시간 스트레스 모니터링을 제공합니다.

**클래스:**
- `RealtimeStressMonitor`: 콜백 기능을 갖춘 실시간 모니터링
- `StressMonitorSession`: 모니터링 세션용 컨텍스트 매니저

**기능:**
- 설정 가능한 업데이트 간격
- 스트레스 변화 콜백
- 고 스트레스 알림
- 트렌드 분석 (증가/감소)
- 세션 요약 통계

## 설치

```bash
# 필수 의존성 설치
pip install numpy

# Python 경로에 모듈 추가
export PYTHONPATH="${PYTHONPATH}:/path/to/SWEG04/SWE-G04-SPACE/Model"
```

## 빠른 시작

### 기본 HRV 계산

```python
from hrv_calculator import HRVCalculator

# Apple Watch의 심박수 데이터 (BPM)
heart_rates = [72, 75, 73, 76, 74, 77, 75, 73, 71, 74]

# HRV 지표 계산
calculator = HRVCalculator()
hrv_metrics = calculator.calculate_hrv_from_heart_rates(heart_rates)

print(f"SDNN: {hrv_metrics.sdnn:.2f} ms")
print(f"RMSSD: {hrv_metrics.rmssd:.2f} ms")
print(f"pNN50: {hrv_metrics.pnn50:.2f} %")
```

### 스트레스 감지

```python
from stress_detector import StressDetector

# HRV 지표로부터 스트레스 감지
detector = StressDetector()
assessment = detector.detect_stress(hrv_metrics)

print(f"스트레스 레벨: {assessment.stress_level}")  # 예: StressLevel.MODERATE
print(f"스트레스 점수: {assessment.stress_score:.1f}/100")
print(f"한글: {assessment.stress_level.to_korean()}")  # "보통"

# 권장사항 가져오기
recommendations = detector.get_stress_recommendations(assessment)
for rec in recommendations['korean']:
    print(f"- {rec}")
```

### 실시간 모니터링

```python
from realtime_monitor import RealtimeStressMonitor

# 콜백 함수를 갖춘 모니터 생성
def on_high_stress(assessment):
    print(f"⚠️ 고 스트레스 감지: {assessment.stress_score:.0f}/100")
    # 스마트홈 자동화 트리거
    trigger_stress_relief_scenario()

monitor = RealtimeStressMonitor(
    window_size=60,         # HRV 계산용 60개의 RR 간격
    update_interval=10,     # 10초마다 업데이트
    on_high_stress_alert=on_high_stress
)

# 심박수 측정값이 들어올 때마다 추가
while True:
    hr = get_heart_rate_from_apple_watch()  # 사용자 구현
    assessment = monitor.add_heart_rate(hr)

    if assessment:
        print(f"현재 스트레스: {assessment.stress_level}")
```

### 세션 모니터링

```python
from realtime_monitor import RealtimeStressMonitor, StressMonitorSession

monitor = RealtimeStressMonitor(window_size=60, update_interval=5)

with StressMonitorSession(monitor) as session:
    # 활동 중 스트레스 모니터링
    for hr in heart_rate_stream:
        monitor.add_heart_rate(hr)

# 세션 요약 가져오기
summary = session.get_session_summary()
print(f"평균 스트레스: {summary['average_stress_score']:.1f}/100")
print(f"고 스트레스 에피소드: {summary['high_stress_episodes']}")
```

## Apple Watch 통합

### iOS Swift (HealthKit)

```swift
import HealthKit

let healthStore = HKHealthStore()

// 심박수 권한 요청
let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!

healthStore.requestAuthorization(toShare: nil, read: [heartRateType]) { success, error in
    if success {
        startHeartRateMonitoring()
    }
}

// 백그라운드 심박수 업데이트 시작
func startHeartRateMonitoring() {
    let query = HKAnchoredObjectQuery(
        type: heartRateType,
        predicate: nil,
        anchor: nil,
        limit: HKObjectQueryNoLimit
    ) { query, samples, deletedObjects, anchor, error in
        guard let samples = samples as? [HKQuantitySample] else { return }

        for sample in samples {
            let hr = sample.quantity.doubleValue(for: HKUnit(from: "count/min"))
            sendToBackend(heartRate: hr, timestamp: sample.startDate)
        }
    }

    healthStore.execute(query)
}
```

### 백엔드 API (FastAPI)

```python
from fastapi import FastAPI
from datetime import datetime
from realtime_monitor import RealtimeStressMonitor, StressLevel

app = FastAPI()
monitor = RealtimeStressMonitor(window_size=60, update_interval=10)

@app.post("/api/health/heart-rate")
async def receive_heart_rate(hr: float, timestamp: datetime):
    """Apple Watch에서 심박수 수신"""
    assessment = monitor.add_heart_rate(hr, timestamp)

    if assessment:
        # 고 스트레스 확인
        if assessment.stress_level in [StressLevel.HIGH, StressLevel.VERY_HIGH]:
            # 스마트홈 자동화 트리거
            await trigger_stress_relief()

        return assessment.to_dict()

    return {"status": "buffering"}

async def trigger_stress_relief():
    """스트레스 완화를 위한 스마트홈 액션 트리거"""
    # 조명 어둡게
    await control_lights(brightness=30, color="warm")

    # 이완 음악 재생
    await play_music(playlist="relaxation")

    # 온도 조절
    await set_temperature(target=22)

    # 알림 전송
    await send_notification(
        "고 스트레스가 감지되었습니다. 잠시 휴식을 취하세요."
    )
```

## 실행 예제

데모 파일을 실행하여 모든 기능을 확인하세요:

```bash
cd SWEG04/SWE-G04-SPACE/Model/Stress
python demo.py
```

### 예제 출력

```
╔══════════════════════════════════════════════════════════╗
║          SPACE 스트레스 감지 데모                          ║
╚══════════════════════════════════════════════════════════╝

Demo 1: 기본 HRV 계산
============================================================
심박수 데이터: 30회 측정
평균 심박수: 74.5 BPM

HRV 지표:
  SDNN:  18.45 ms
  RMSSD: 24.32 ms
  pNN50: 12.50 %

Demo 2: 스트레스 감지
============================================================

이완 상태:
----------------------------------------
  평균 심박수: 61.8 BPM
  RMSSD: 45.23 ms
  스트레스 레벨: 낮음
  스트레스 점수: 25.3/100
  신뢰도: 0.87
  권장사항:
    - 스트레스 수준이 낮고 건강합니다.
    - 현재의 스트레스 관리 방법을 계속 유지하세요.

고 스트레스 상태:
----------------------------------------
  평균 심박수: 96.2 BPM
  RMSSD: 12.45 ms
  스트레스 레벨: 매우 높음
  스트레스 점수: 92.1/100
  신뢰도: 0.91
  권장사항:
    - 스트레스 수준이 매우 높습니다.
    - 즉시 긴장을 풀기 위한 조치를 취하세요.

[실시간 모니터링 예제 계속...]
```

## 스마트홈 통합

### 스트레스 기반 자동화 시나리오

```python
# 예제: 스트레스 수준에 따른 적응형 홈 환경

async def handle_stress_level(assessment: StressAssessment):
    """스트레스 수준에 따라 홈 환경 조정"""

    if assessment.stress_level == StressLevel.VERY_LOW:
        # 최적 상태 - 현재 설정 유지
        pass

    elif assessment.stress_level == StressLevel.LOW:
        # 일반 모드
        await set_scene("normal")

    elif assessment.stress_level == StressLevel.MODERATE:
        # 편안함 모드
        await set_scene("comfort")
        await play_ambient_sound("nature")

    elif assessment.stress_level == StressLevel.HIGH:
        # 적극적 스트레스 완화
        await set_scene("relaxation")
        await play_music("meditation")
        await diffuse_aromatherapy("lavender")
        await send_notification("높은 스트레스가 감지되었습니다. 휴식 모드를 활성화했습니다.")

    elif assessment.stress_level == StressLevel.VERY_HIGH:
        # 긴급 스트레스 개입
        await set_scene("deep_relaxation")
        await play_guided_meditation()
        await dim_all_screens()
        await notify_emergency_contact()
        await send_notification("매우 높은 스트레스! 즉시 휴식을 취하세요.")
```

## 연구 배경

### HRV와 스트레스의 관계

심박 변이도(HRV)는 스트레스를 나타내는 잘 확립된 생체 지표입니다:

- **높은 HRV** → 더 나은 스트레스 회복력, 이완 상태
- **낮은 HRV** → 적응력 감소, 스트레스 상태

### 주요 연구

1. **Kim et al. (2018)**: "Stress and Heart Rate Variability: A Meta-Analysis and Review of the Literature"
   - 36개 연구의 메타 분석
   - 스트레스와 HRV 간의 강한 음의 상관관계
   - RMSSD가 급성 스트레스에 가장 민감

2. **Thayer et al. (2012)**: "A meta-analysis of heart rate variability and neuroimaging studies"
   - HRV는 전전두엽 피질 조절을 반영
   - 낮은 HRV는 불안과 우울증과 연관

3. **Task Force (1996)**: "Heart rate variability: standards of measurement"
   - HRV 측정 표준 확립
   - HRV 지표의 임상적 의미

### 임계값

성인(20-60세)의 표준 데이터 기반:

| 지표 | 매우 낮은 스트레스 | 낮은 스트레스 | 보통 | 높은 스트레스 | 매우 높은 스트레스 |
|------|-------------------|--------------|------|--------------|-------------------|
| RMSSD | ≥50 ms | 35-50 ms | 25-35 ms | 15-25 ms | <15 ms |
| SDNN | ≥100 ms | 70-100 ms | 50-70 ms | 30-50 ms | <30 ms |
| pNN50 | ≥15% | 7-15% | 3-7% | 1-3% | <1% |

## 성능 고려사항

### 실시간 처리

- **윈도우 크기**: 60개의 RR 간격 (~1분의 데이터)
- **업데이트 간격**: 5-10초 (설정 가능)
- **지연 시간**: HRV 계산에 <100ms
- **메모리**: 모니터링 세션당 ~10KB

### 정확도

- **최소 데이터**: 기본 평가를 위한 30개의 RR 간격
- **최적 데이터**: 신뢰할 수 있는 HRV를 위한 60개 이상의 RR 간격
- **이상치 필터링**: 아티팩트 제거 (>20% 연속 변화)
- **신뢰도 점수**: 신뢰성 표시 (0-1)

## 향후 개선사항

- [ ] 연령 조정 임계값
- [ ] 주파수 영역 HRV (LF/HF 비율)
- [ ] 개인화된 기준선 학습
- [ ] 다중 모달 스트레스 감지 (HR + HRV + 활동)
- [ ] 장기 스트레스 트렌드 분석
- [ ] 수면 데이터와의 통합
- [ ] HRV로부터 호흡수 추출 (Series 8+)

## 파일 구조

```
Stress/
├── hrv_calculator.py       # HRV 계산 모듈
├── stress_detector.py      # 스트레스 감지 모듈
├── realtime_monitor.py     # 실시간 모니터링
├── demo.py                 # 자동 실행 데모
├── example_usage.py        # 상세 예제
├── README.md               # 영문 문서
├── README_KR.md            # 한글 문서 (이 파일)
├── QUICKSTART.md           # 빠른 시작 가이드
└── __init__.py             # 패키지 초기화
```

## 라이선스

SPACE (Smart home PersonAlized Control Environment) 프로젝트의 일부입니다.
한양대학교 소프트웨어공학 과목 2025-2학기

## 팀원

- 어준호 - 정보시스템학과 (djwnsgh0248@hanyang.ac.kr)
- 신연성 - 데이터사이언스학과 (dustjd2651@gmail.com)
- 김도겸 - 컴퓨터소프트웨어학부 (dogyeom74@hanyang.ac.kr)
- 임동현 - 컴퓨터소프트웨어학부 (limdongxian1207@gmail.com)

## 참고 문헌

- Task Force of the European Society of Cardiology (1996). Heart rate variability: standards of measurement
- Kim, H. G., et al. (2018). Stress and Heart Rate Variability: A Meta-Analysis
- Thayer, J. F., et al. (2012). A meta-analysis of heart rate variability and neuroimaging studies
- Apple HealthKit 문서: https://developer.apple.com/documentation/healthkit

## 문의

프로젝트 관련 문의사항은 팀 이메일로 연락주시기 바랍니다.

---

**마지막 업데이트**: 2025년 11월 13일
