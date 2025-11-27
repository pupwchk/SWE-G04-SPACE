# 실전 배포 가이드: Apple Watch → 서버 → 스트레스 감지

## 시스템 아키텍처

```
┌─────────────────┐
│  Apple Watch    │
│  (HealthKit)    │
└────────┬────────┘
         │ 심박수 데이터
         ↓ (HTTP/WebSocket)
┌─────────────────┐
│   iOS App       │
│  (SwiftUI)      │
└────────┬────────┘
         │ API 요청
         ↓
┌─────────────────┐
│  FastAPI 서버   │
│  (Python)       │
│  ├─ 스트레스     │
│  │  감지 모듈    │
│  ├─ PostgreSQL  │
│  └─ WebSocket   │
└────────┬────────┘
         │ 스트레스 이벤트
         ↓
┌─────────────────┐
│  스마트홈       │
│  자동화         │
└─────────────────┘
```

---

## 1단계: FastAPI 백엔드 구축

### 1.1 의존성 설치

기존 `requirements.txt`에 추가:

```bash
cd /Users/eojunho/HYU/25-2/SWE
source venv/bin/activate

# 추가 패키지 설치
pip install fastapi uvicorn websockets asyncpg redis python-multipart
pip freeze > requirements.txt
```

### 1.2 스트레스 감지 API 엔드포인트 작성

`BackEnd/fastapi-starter/app/api/stress.py` 파일 생성:

```python
"""
스트레스 감지 API
Apple Watch에서 심박수 데이터를 받아 실시간으로 스트레스를 계산
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import asyncio
import sys
sys.path.append('../../../Model')

from Stress import RealtimeStressMonitor, StressLevel

router = APIRouter(prefix="/stress", tags=["Stress Detection"])

# 사용자별 모니터 인스턴스 저장
user_monitors = {}


class HeartRateData(BaseModel):
    """심박수 데이터 모델"""
    user_id: int
    heart_rate: float  # BPM
    timestamp: datetime
    device_id: Optional[str] = None


class StressResponse(BaseModel):
    """스트레스 평가 응답 모델"""
    user_id: int
    stress_level: str
    stress_level_kr: str
    stress_score: float
    confidence: float
    timestamp: datetime
    hrv_metrics: dict
    recommendations: List[str]


def get_or_create_monitor(user_id: int) -> RealtimeStressMonitor:
    """사용자별 스트레스 모니터 가져오기 또는 생성"""
    if user_id not in user_monitors:
        monitor = RealtimeStressMonitor(
            window_size=60,
            update_interval=10,
            on_high_stress_alert=lambda assessment: handle_high_stress(user_id, assessment)
        )
        user_monitors[user_id] = monitor
    return user_monitors[user_id]


async def handle_high_stress(user_id: int, assessment):
    """고 스트레스 감지 시 처리"""
    # 스마트홈 자동화 트리거
    await trigger_stress_relief_scenario(user_id, assessment)

    # 알림 전송
    await send_push_notification(
        user_id,
        f"높은 스트레스가 감지되었습니다 ({assessment.stress_score:.0f}/100). 휴식을 취하세요."
    )


@router.post("/heart-rate", response_model=Optional[StressResponse])
async def receive_heart_rate(data: HeartRateData):
    """
    Apple Watch에서 심박수 데이터 수신

    - **user_id**: 사용자 ID
    - **heart_rate**: 심박수 (BPM)
    - **timestamp**: 측정 시간
    - **device_id**: 기기 ID (선택)
    """
    try:
        # 모니터 가져오기
        monitor = get_or_create_monitor(data.user_id)

        # 심박수 추가 및 스트레스 계산
        assessment = monitor.add_heart_rate(data.heart_rate, data.timestamp)

        # 아직 충분한 데이터가 없으면 None 반환
        if assessment is None:
            return None

        # 스트레스 평가 결과 반환
        from Stress import StressDetector
        detector = StressDetector()
        recommendations = detector.get_stress_recommendations(assessment)

        return StressResponse(
            user_id=data.user_id,
            stress_level=str(assessment.stress_level),
            stress_level_kr=assessment.stress_level.to_korean(),
            stress_score=assessment.stress_score,
            confidence=assessment.confidence,
            timestamp=assessment.timestamp,
            hrv_metrics=assessment.hrv_metrics.to_dict(),
            recommendations=recommendations['korean']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트레스 계산 오류: {str(e)}")


@router.get("/current/{user_id}")
async def get_current_stress(user_id: int):
    """현재 스트레스 수준 조회"""
    monitor = user_monitors.get(user_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="모니터링 데이터가 없습니다")

    current = monitor.get_current_stress()
    if current is None:
        raise HTTPException(status_code=404, detail="충분한 데이터가 수집되지 않았습니다")

    return current.to_dict()


@router.get("/trend/{user_id}")
async def get_stress_trend(user_id: int, duration_minutes: int = 60):
    """스트레스 트렌드 조회"""
    monitor = user_monitors.get(user_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="모니터링 데이터가 없습니다")

    trend = monitor.get_stress_trend(duration_minutes)
    if not trend:
        return {"trend": [], "summary": None}

    avg_score = sum(a.stress_score for a in trend) / len(trend)

    return {
        "trend": [a.to_dict() for a in trend],
        "summary": {
            "average_stress": avg_score,
            "count": len(trend),
            "duration_minutes": duration_minutes,
            "is_increasing": monitor.is_stress_increasing()
        }
    }


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    실시간 스트레스 모니터링용 WebSocket
    Apple Watch에서 심박수를 실시간 스트리밍
    """
    await websocket.accept()
    monitor = get_or_create_monitor(user_id)

    try:
        while True:
            # 클라이언트로부터 심박수 데이터 수신
            data = await websocket.receive_json()
            hr = data.get("heart_rate")
            timestamp = datetime.fromisoformat(data.get("timestamp"))

            # 스트레스 계산
            assessment = monitor.add_heart_rate(hr, timestamp)

            # 결과 전송
            if assessment:
                await websocket.send_json({
                    "type": "stress_update",
                    "data": {
                        "stress_level": str(assessment.stress_level),
                        "stress_level_kr": assessment.stress_level.to_korean(),
                        "stress_score": assessment.stress_score,
                        "heart_rate": hr,
                        "timestamp": assessment.timestamp.isoformat()
                    }
                })
            else:
                await websocket.send_json({
                    "type": "buffering",
                    "message": "데이터 수집 중..."
                })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user_id}")


# 스마트홈 자동화 함수들
async def trigger_stress_relief_scenario(user_id: int, assessment):
    """스트레스 완화 시나리오 실행"""
    # TODO: 실제 스마트홈 API 호출
    print(f"[User {user_id}] 스트레스 완화 시나리오 실행")
    print(f"  - 조명 어둡게 (30%)")
    print(f"  - 이완 음악 재생")
    print(f"  - 온도 조절 (22°C)")


async def send_push_notification(user_id: int, message: str):
    """푸시 알림 전송"""
    # TODO: FCM 또는 APNs를 통한 푸시 알림
    print(f"[User {user_id}] 알림: {message}")
```

### 1.3 FastAPI 앱에 라우터 추가

`BackEnd/fastapi-starter/app/main.py` 수정:

```python
from fastapi import FastAPI
from app.api import users, tracking
from app.api import stress  # 추가

app = FastAPI(title="SPACE API")

# 라우터 등록
app.include_router(users.router)
app.include_router(tracking.router)
app.include_router(stress.router, prefix="/api")  # 추가

@app.get("/")
def root():
    return {"message": "SPACE API Server"}
```

---

## 2단계: iOS 앱 구현 (SwiftUI)

### 2.1 HealthKit 권한 요청

`Info.plist`에 추가:

```xml
<key>NSHealthShareUsageDescription</key>
<string>심박수 데이터를 사용하여 스트레스를 모니터링합니다.</string>

<key>NSHealthUpdateUsageDescription</key>
<string>건강 데이터를 저장합니다.</string>
```

### 2.2 HealthKit Manager 생성

`HealthKitManager.swift`:

```swift
import HealthKit

class HealthKitManager: ObservableObject {
    let healthStore = HKHealthStore()

    @Published var isAuthorized = false
    @Published var currentHeartRate: Double = 0

    // HealthKit 권한 요청
    func requestAuthorization() async throws {
        guard HKHealthStore.isHealthDataAvailable() else {
            throw HealthKitError.notAvailable
        }

        let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let typesToRead: Set = [heartRateType]

        try await healthStore.requestAuthorization(toShare: nil, read: typesToRead)

        await MainActor.run {
            self.isAuthorized = true
        }
    }

    // 실시간 심박수 모니터링 시작
    func startHeartRateMonitoring(completion: @escaping (Double, Date) -> Void) {
        let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!

        let query = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: nil,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { [weak self] query, samples, deletedObjects, anchor, error in

            guard let samples = samples as? [HKQuantitySample] else { return }

            for sample in samples {
                let heartRate = sample.quantity.doubleValue(
                    for: HKUnit(from: "count/min")
                )

                DispatchQueue.main.async {
                    self?.currentHeartRate = heartRate
                }

                // 서버로 전송
                completion(heartRate, sample.startDate)
            }
        }

        query.updateHandler = { [weak self] query, samples, deletedObjects, anchor, error in
            guard let samples = samples as? [HKQuantitySample] else { return }

            for sample in samples {
                let heartRate = sample.quantity.doubleValue(
                    for: HKUnit(from: "count/min")
                )

                DispatchQueue.main.async {
                    self?.currentHeartRate = heartRate
                }

                completion(heartRate, sample.startDate)
            }
        }

        healthStore.execute(query)
    }
}

enum HealthKitError: Error {
    case notAvailable
}
```

### 2.3 API Service 생성

`StressAPIService.swift`:

```swift
import Foundation

class StressAPIService {
    static let shared = StressAPIService()

    private let baseURL = "http://your-server.com/api/stress"
    // 개발용: "http://localhost:11325/api/stress"

    struct HeartRateData: Codable {
        let user_id: Int
        let heart_rate: Double
        let timestamp: String
        let device_id: String?
    }

    struct StressResponse: Codable {
        let user_id: Int
        let stress_level: String
        let stress_level_kr: String
        let stress_score: Double
        let confidence: Double
        let timestamp: String
        let recommendations: [String]
    }

    // 심박수 데이터 전송
    func sendHeartRate(
        userId: Int,
        heartRate: Double,
        timestamp: Date
    ) async throws -> StressResponse? {

        let url = URL(string: "\(baseURL)/heart-rate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let data = HeartRateData(
            user_id: userId,
            heart_rate: heartRate,
            timestamp: ISO8601DateFormatter().string(from: timestamp),
            device_id: UIDevice.current.identifierForVendor?.uuidString
        )

        request.httpBody = try JSONEncoder().encode(data)

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.serverError
        }

        // 응답이 null일 수 있음 (충분한 데이터가 아직 없는 경우)
        if responseData.isEmpty || String(data: responseData, encoding: .utf8) == "null" {
            return nil
        }

        return try JSONDecoder().decode(StressResponse.self, from: responseData)
    }

    // WebSocket 연결 (실시간 모니터링)
    func connectWebSocket(userId: Int) -> URLSessionWebSocketTask {
        let url = URL(string: "ws://your-server.com/api/stress/ws/\(userId)")!
        let task = URLSession.shared.webSocketTask(with: url)
        task.resume()
        return task
    }
}

enum APIError: Error {
    case serverError
    case decodingError
}
```

### 2.4 스트레스 모니터링 뷰

`StressMonitorView.swift`:

```swift
import SwiftUI

struct StressMonitorView: View {
    @StateObject private var healthKitManager = HealthKitManager()
    @State private var currentStress: StressAPIService.StressResponse?
    @State private var isMonitoring = false

    let userId = 1  // 실제 사용자 ID

    var body: some View {
        VStack(spacing: 20) {
            // 현재 심박수
            VStack {
                Text("현재 심박수")
                    .font(.headline)
                Text("\(Int(healthKitManager.currentHeartRate))")
                    .font(.system(size: 60, weight: .bold))
                    .foregroundColor(.red)
                Text("BPM")
                    .font(.caption)
            }
            .padding()
            .background(Color.gray.opacity(0.1))
            .cornerRadius(15)

            // 스트레스 레벨
            if let stress = currentStress {
                VStack(spacing: 15) {
                    Text("스트레스 레벨")
                        .font(.headline)

                    Text(stress.stress_level_kr)
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(stressColor(for: stress.stress_score))

                    Text("\(Int(stress.stress_score))/100")
                        .font(.title3)
                        .foregroundColor(.secondary)

                    // 신뢰도
                    HStack {
                        Text("신뢰도:")
                        ProgressView(value: stress.confidence)
                            .frame(width: 100)
                        Text("\(Int(stress.confidence * 100))%")
                            .font(.caption)
                    }

                    // 권장사항
                    VStack(alignment: .leading, spacing: 5) {
                        Text("권장사항:")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        ForEach(stress.recommendations.prefix(2), id: \.self) { rec in
                            Text("• \(rec)")
                                .font(.caption)
                        }
                    }
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(10)
                }
                .padding()
                .background(Color.white)
                .cornerRadius(15)
                .shadow(radius: 5)
            }

            // 모니터링 시작/중지 버튼
            Button(action: toggleMonitoring) {
                Text(isMonitoring ? "모니터링 중지" : "모니터링 시작")
                    .font(.headline)
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(isMonitoring ? Color.red : Color.blue)
                    .cornerRadius(10)
            }
            .padding(.horizontal)

            Spacer()
        }
        .padding()
        .onAppear {
            requestHealthKitPermission()
        }
    }

    // HealthKit 권한 요청
    func requestHealthKitPermission() {
        Task {
            try? await healthKitManager.requestAuthorization()
        }
    }

    // 모니터링 토글
    func toggleMonitoring() {
        isMonitoring.toggle()

        if isMonitoring {
            startMonitoring()
        }
    }

    // 모니터링 시작
    func startMonitoring() {
        healthKitManager.startHeartRateMonitoring { heartRate, timestamp in
            Task {
                do {
                    let response = try await StressAPIService.shared.sendHeartRate(
                        userId: userId,
                        heartRate: heartRate,
                        timestamp: timestamp
                    )

                    if let response = response {
                        await MainActor.run {
                            self.currentStress = response
                        }
                    }
                } catch {
                    print("Error sending heart rate: \(error)")
                }
            }
        }
    }

    // 스트레스 점수에 따른 색상
    func stressColor(for score: Double) -> Color {
        switch score {
        case 0..<20: return .green
        case 20..<40: return .blue
        case 40..<60: return .yellow
        case 60..<80: return .orange
        default: return .red
        }
    }
}
```

---

## 3단계: 서버 배포

### 3.1 Docker를 사용한 배포

`Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 복사
COPY SWEG04/SWE-G04-SPACE/Model/Stress /app/Stress
COPY BackEnd/fastapi-starter /app/api

WORKDIR /app/api

# 환경 변수
ENV PYTHONPATH=/app

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`docker-compose.yml` 수정:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "11325:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      - db
    volumes:
      - ./BackEnd/fastapi-starter/app:/app/api/app
      - ./SWEG04/SWE-G04-SPACE/Model/Stress:/app/Stress

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

volumes:
  postgres_data:
```

### 3.2 배포 명령어

```bash
# 1. 서버로 코드 배포 (예: AWS EC2)
scp -r SWEG04 BackEnd requirements.txt user@your-server:/path/to/app

# 2. 서버에서 Docker 실행
ssh user@your-server
cd /path/to/app
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f api
```

---

## 4단계: 테스트

### 4.1 로컬 테스트

```bash
# 백엔드 서버 시작
cd BackEnd/fastapi-starter
uvicorn app.main:app --reload --port 11325

# 다른 터미널에서 테스트
curl -X POST "http://localhost:11325/api/stress/heart-rate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "heart_rate": 75,
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

### 4.2 iOS 시뮬레이터에서 테스트

1. Xcode에서 프로젝트 열기
2. 시뮬레이터 실행
3. Health 앱에서 심박수 데이터 수동 추가
4. 앱에서 모니터링 시작

---

## 5단계: 프로덕션 배포

### 체크리스트

- [ ] HTTPS 설정 (Let's Encrypt)
- [ ] 환경 변수 설정 (`.env` 파일)
- [ ] 데이터베이스 백업 설정
- [ ] 모니터링 및 로깅 (Sentry, DataDog)
- [ ] Rate Limiting 설정
- [ ] CORS 설정
- [ ] iOS 앱 App Store 배포
- [ ] 푸시 알림 설정 (APNs)

### 보안 고려사항

```python
# app/main.py에 추가

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host 설정
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-server.com", "*.your-server.com"]
)
```

---

## 요약

### 데이터 흐름

1. **Apple Watch** → 심박수 측정 (HealthKit)
2. **iOS 앱** → 심박수 데이터를 서버로 전송 (HTTP POST)
3. **FastAPI 서버** → 스트레스 계산 (Stress 모듈)
4. **서버** → 스트레스 결과 응답
5. **iOS 앱** → 결과 표시 + 스마트홈 자동화

### 다음 단계

1. `BackEnd/fastapi-starter/app/api/stress.py` 파일 생성
2. iOS 앱에 HealthKit 및 API 연동 코드 추가
3. 로컬 테스트
4. 서버 배포
5. iOS 앱 테스트
6. 프로덕션 배포

더 자세한 도움이 필요하시면 말씀해주세요!
