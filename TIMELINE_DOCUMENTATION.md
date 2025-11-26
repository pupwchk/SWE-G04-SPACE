# 타임라인 기능 전체 문서화

## 목차
1. [개요](#개요)
2. [데이터 모델](#데이터-모델)
3. [핵심 매니저](#핵심-매니저)
4. [뷰 컴포넌트](#뷰-컴포넌트)
5. [iPhone-Watch 통신](#iphone-watch-통신)
6. [위치 추적](#위치-추적)
7. [헬스 데이터 통합](#헬스-데이터-통합)

---

## 개요

타임라인 기능은 사용자의 이동 경로를 GPS로 추적하고, Apple Watch에서 수집된 건강 데이터와 결합하여 체크포인트를 자동 생성하는 시스템입니다.

### 주요 기능
- 📍 **GPS 기반 경로 추적** (iPhone & Watch 모두 지원)
- 🗺️ **실시간 지도 시각화** (MapKit 사용)
- 📊 **체크포인트 자동 생성** (정지 지점 감지)
- ❤️ **건강 데이터 통합** (심박수, 칼로리, 걸음수, HRV, 스트레스)
- 📱⌚ **iPhone-Watch 실시간 동기화** (WatchConnectivity)
- 💾 **타임라인 저장 및 기록 관리** (UserDefaults)

---

## 데이터 모델

### 1. TimelineRecord
**파일**: [TimelineDataModel.swift:13-81](swift_app_demo/space/TimelineDataModel.swift#L13-L81)

타임라인의 전체 기록을 저장하는 메인 데이터 구조입니다.

```swift
struct TimelineRecord: Identifiable, Codable, Equatable {
    let id: UUID
    let startTime: Date
    let endTime: Date
    let coordinates: [CoordinateData]
    let totalDistance: Double      // meters
    let averageSpeed: Double        // km/h
    let maxSpeed: Double            // km/h
    let duration: TimeInterval      // seconds
    var checkpoints: [Checkpoint]   // 경로 상의 체크포인트
}
```

**핵심 계산 프로퍼티**:
- `durationFormatted`: 시간을 "Xh Ym Zs" 형식으로 포맷
- `distanceFormatted`: 거리를 "X.XX km" 또는 "XXX m" 형식으로 포맷
- `centerCoordinate`: 경로의 중심 좌표 계산
- `region`: 지도에 표시할 영역 계산 (1.5배 패딩 포함)

---

### 2. CoordinateData
**파일**: [TimelineDataModel.swift:84-98](swift_app_demo/space/TimelineDataModel.swift#L84-L98)

GPS 좌표와 타임스탬프를 저장하는 구조체입니다.

```swift
struct CoordinateData: Codable, Equatable {
    let latitude: Double
    let longitude: Double
    let timestamp: Date

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}
```

**역할**:
- CLLocationCoordinate2D를 Codable하게 만들기 위한 래퍼
- 각 좌표에 타임스탬프 추가로 시간순 정렬 가능

---

### 3. Checkpoint
**파일**: [TimelineDataModel.swift:173-230](swift_app_demo/space/TimelineDataModel.swift#L173-L230)

경로 상의 특정 지점에 대한 상세 정보를 저장합니다.

```swift
struct Checkpoint: Identifiable, Codable, Equatable {
    let id: UUID
    let coordinate: CoordinateData
    let mood: CheckpointMood            // 사용자 기분
    let stayDuration: TimeInterval      // 체류 시간 (초)
    let stressChange: StressChange      // 스트레스 변화
    let note: String?                   // 사용자 노트
    let timestamp: Date

    // Watch에서 수집한 건강 데이터
    let heartRate: Double?              // bpm
    let calories: Double?               // kcal
    let steps: Int?                     // 걸음수
    let distance: Double?               // meters
    let hrv: Double?                    // ms (심박변이도)
    let stressLevel: Int?               // 0-100
}
```

**특징**:
- 자동 생성 (정지 감지 시) 또는 수동 생성 가능
- 건강 데이터와 위치 데이터의 결합
- 스트레스 변화 추적 (이전 체크포인트와 비교)

---

### 4. CheckpointMood (Enum)
**파일**: [TimelineDataModel.swift:103-139](swift_app_demo/space/TimelineDataModel.swift#L103-L139)

사용자의 기분을 5단계로 분류합니다.

```swift
enum CheckpointMood: String, Codable, CaseIterable {
    case veryHappy = "very_happy"    // 😄 매우 행복
    case happy = "happy"             // 🙂 행복
    case neutral = "neutral"         // 😐 보통
    case sad = "sad"                 // 😔 슬픔
    case verySad = "very_sad"        // 😢 매우 슬픔
}
```

**제공 프로퍼티**:
- `emoji`: 이모지 아이콘
- `label`: 한글 라벨
- `color`: 16진수 색상 코드

**색상 매핑**:
- veryHappy: Green (#4CAF50)
- happy: Light Green (#8BC34A)
- neutral: Amber (#FFC107)
- sad: Orange (#FF9800)
- verySad: Red (#F44336)

---

### 5. StressChange (Enum)
**파일**: [TimelineDataModel.swift:142-170](swift_app_demo/space/TimelineDataModel.swift#L142-L170)

체크포인트 간 스트레스 변화를 추적합니다.

```swift
enum StressChange: String, Codable, CaseIterable {
    case increased = "increased"     // 증가
    case unchanged = "unchanged"     // 변화 없음
    case decreased = "decreased"     // 감소
}
```

**제공 프로퍼티**:
- `icon`: SF Symbol 아이콘 이름
- `label`: 한글 라벨
- `color`: 16진수 색상 코드

---

## 핵심 매니저

### 1. TimelineManager
**파일**: [TimelineDataModel.swift:233-525](swift_app_demo/space/TimelineDataModel.swift#L233-L525)

타임라인 생성, 저장, 체크포인트 관리를 담당하는 싱글톤 매니저입니다.

#### 주요 프로퍼티

```swift
class TimelineManager: ObservableObject {
    static let shared = TimelineManager()

    @Published var timelines: [TimelineRecord] = []
    @Published var currentTimeline: TimelineRecord?

    private let userDefaultsKey = "saved_timelines"
}
```

#### 핵심 함수

##### 1.1 saveTimeline(_:)
**위치**: [TimelineDataModel.swift:247-251](swift_app_demo/space/TimelineDataModel.swift#L247-L251)

타임라인을 저장하고 UserDefaults에 영구 저장합니다.

```swift
func saveTimeline(_ timeline: TimelineRecord) {
    timelines.insert(timeline, at: 0) // 최신 기록이 맨 앞
    saveToUserDefaults()
}
```

##### 1.2 createTimeline(...)
**위치**: [TimelineDataModel.swift:282-324](swift_app_demo/space/TimelineDataModel.swift#L282-L324)

GPS 데이터로부터 타임라인 레코드를 생성합니다.

```swift
func createTimeline(
    startTime: Date,
    endTime: Date,
    coordinates: [CLLocationCoordinate2D],
    timestamps: [Date],
    speeds: [Double],
    checkpoints: [Checkpoint] = []
) -> TimelineRecord?
```

**처리 과정**:
1. 좌표 데이터를 CoordinateData로 변환
2. 총 이동 거리 계산 (점 간 거리 누적)
3. 평균 속도 및 최고 속도 계산
4. TimelineRecord 객체 생성 및 반환

##### 1.3 generateCheckpoints(...)
**위치**: [TimelineDataModel.swift:348-411](swift_app_demo/space/TimelineDataModel.swift#L348-L411)

GPS 및 건강 데이터로부터 체크포인트를 자동 생성합니다.

```swift
func generateCheckpoints(
    coordinates: [CLLocationCoordinate2D],
    timestamps: [Date],
    healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)]
) -> [Checkpoint]
```

**자동 생성 알고리즘**:

1. **정지 감지 조건**:
   - 속도 < 0.5 km/h
   - 지속 시간 ≥ 30초

2. **처리 과정**:
   ```swift
   for i in 1..<coordinates.count {
       // 1. 거리 및 속도 계산
       let distance = loc2.distance(from: loc1)
       let timeInterval = timestamps[i].timeIntervalSince(timestamps[i - 1])
       let speed = (distance / timeInterval) * 3.6  // km/h

       // 2. 정지 감지
       if speed < 0.5 {
           if currentStopStart == nil {
               currentStopStart = i
               currentStopDuration = 0
           }
           currentStopDuration += timeInterval
       } else {
           // 3. 정지 종료 및 체크포인트 생성
           if currentStopDuration >= 30 {
               checkpoints.append(createCheckpointAt(...))
           }
       }
   }
   ```

3. **체크포인트 데이터 수집**:
   - 위치: 정지 시작 지점의 좌표
   - 체류 시간: 정지 지속 시간
   - 건강 데이터: 해당 시점의 심박수, 칼로리 등
   - 기분: 심박수 기반 휴리스틱으로 자동 판단
   - 스트레스: 이전 체크포인트와 비교

##### 1.4 createCheckpointAt(...)
**위치**: [TimelineDataModel.swift:414-480](swift_app_demo/space/TimelineDataModel.swift#L414-L480)

특정 인덱스에서 체크포인트를 생성합니다 (내부 함수).

```swift
private func createCheckpointAt(
    index: Int,
    coordinates: [CLLocationCoordinate2D],
    timestamps: [Date],
    healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)],
    stayDuration: TimeInterval,
    previousCheckpoint: Checkpoint? = nil
) -> Checkpoint
```

**기분 판단 휴리스틱**:
```swift
if hr < 60 {
    mood = .happy      // 휴식, 안정
} else if hr < 80 {
    mood = .neutral    // 정상
} else if hr < 100 {
    mood = .happy      // 활동적, 에너지 넘침
} else {
    mood = .neutral    // 높은 활동
}
```

**스트레스 변화 계산**:
```swift
let stressDiff = currentStressLevel - previousStress
if stressDiff > 10 {
    stressChange = .increased
} else if stressDiff < -10 {
    stressChange = .decreased
} else {
    stressChange = .unchanged
}
```

##### 1.5 createManualCheckpoint(...)
**위치**: [TimelineDataModel.swift:483-523](swift_app_demo/space/TimelineDataModel.swift#L483-L523)

사용자가 수동으로 체크포인트를 생성합니다.

```swift
func createManualCheckpoint(
    coordinate: CLLocationCoordinate2D,
    timestamp: Date,
    mood: CheckpointMood,
    note: String? = nil
) -> Checkpoint
```

**특징**:
- 사용자가 기분을 직접 선택
- 현재 HealthKitManager의 실시간 데이터 사용
- 체류 시간 = 0 (수동 체크포인트이므로)

##### 1.6 addCheckpoint(to:checkpoint:)
**위치**: [TimelineDataModel.swift:328-334](swift_app_demo/space/TimelineDataModel.swift#L328-L334)

기존 타임라인에 체크포인트를 추가합니다.

```swift
func addCheckpoint(to timelineId: UUID, checkpoint: Checkpoint) {
    if let index = timelines.firstIndex(where: { $0.id == timelineId }) {
        timelines[index].checkpoints.append(checkpoint)
        saveToUserDefaults()
    }
}
```

##### 1.7 영구 저장 함수

**saveToUserDefaults()** - [TimelineDataModel.swift:267-270](swift_app_demo/space/TimelineDataModel.swift#L267-L270)
```swift
private func saveToUserDefaults() {
    if let encoded = try? JSONEncoder().encode(timelines) {
        UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
    }
}
```

**loadTimelines()** - [TimelineDataModel.swift:273-279](swift_app_demo/space/TimelineDataModel.swift#L273-L279)
```swift
private func loadTimelines() {
    if let data = UserDefaults.standard.data(forKey: userDefaultsKey),
       let decoded = try? JSONDecoder().decode([TimelineRecord].self, from: data) {
        timelines = decoded
    }
}
```

---

### 2. LocationManager (iPhone)
**파일**: [LocationManager.swift](swift_app_demo/space/LocationManager.swift)

iPhone에서 GPS 추적을 담당합니다.

#### 주요 프로퍼티
**위치**: [LocationManager.swift:18-44](swift_app_demo/space/LocationManager.swift#L18-L44)

```swift
class LocationManager: NSObject, ObservableObject {
    static let shared = LocationManager()

    // 현재 위치 데이터
    @Published var location: CLLocation?
    @Published var isTracking = false
    @Published var currentLatitude: Double = 0.0
    @Published var currentLongitude: Double = 0.0
    @Published var currentAltitude: Double = 0.0
    @Published var currentSpeed: Double = 0.0      // km/h
    @Published var currentHeading: Double = 0.0
    @Published var horizontalAccuracy: Double = 0.0
    @Published var verticalAccuracy: Double = 0.0

    // 추적 기록
    @Published var routeCoordinates: [CLLocationCoordinate2D] = []
    @Published var totalDistance: Double = 0.0     // meters
    @Published var speedHistory: [Double] = []
    @Published var timestampHistory: [Date] = []

    // 건강 데이터 기록 (GPS와 동기화)
    @Published var healthDataHistory: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)] = []
}
```

#### 핵심 함수

##### 2.1 setupLocationManager()
**위치**: [LocationManager.swift:59-67](swift_app_demo/space/LocationManager.swift#L59-L67)

LocationManager 초기 설정을 수행합니다.

```swift
private func setupLocationManager() {
    locationManager.delegate = self
    locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation  // 최고 정확도
    locationManager.distanceFilter = 5.0                                    // 5m마다 업데이트
    locationManager.allowsBackgroundLocationUpdates = false
    locationManager.pausesLocationUpdatesAutomatically = false
}
```

**설정 설명**:
- `desiredAccuracy`: GPS 정확도 설정 (내비게이션 수준)
- `distanceFilter`: 최소 이동 거리 (5m 이상 이동 시 업데이트)
- `allowsBackgroundLocationUpdates`: 백그라운드 추적 비활성화
- `pausesLocationUpdatesAutomatically`: 자동 일시정지 비활성화

##### 2.2 startTracking()
**위치**: [LocationManager.swift:77-95](swift_app_demo/space/LocationManager.swift#L77-L95)

GPS 추적을 시작합니다.

```swift
func startTracking() {
    guard authorizationStatus == .authorizedWhenInUse ||
          authorizationStatus == .authorizedAlways else {
        requestPermission()
        return
    }

    isTracking = true
    routeCoordinates.removeAll()
    totalDistance = 0.0
    speedHistory.removeAll()
    timestampHistory.removeAll()
    lastLocation = nil

    locationManager.startUpdatingLocation()
    locationManager.startUpdatingHeading()
}
```

##### 2.3 locationManager(_:didUpdateLocations:)
**위치**: [LocationManager.swift:140-192](swift_app_demo/space/LocationManager.swift#L140-L192)

위치 업데이트 시 호출되는 델리게이트 메서드입니다.

```swift
func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    guard let newLocation = locations.last else { return }

    // 1. 현재 값 업데이트
    location = newLocation
    currentLatitude = newLocation.coordinate.latitude
    currentLongitude = newLocation.coordinate.longitude
    currentAltitude = newLocation.altitude
    currentSpeed = max(0, newLocation.speed * 3.6)  // m/s -> km/h
    horizontalAccuracy = newLocation.horizontalAccuracy
    verticalAccuracy = newLocation.verticalAccuracy
    lastUpdateTime = newLocation.timestamp

    // 2. 추적 중인 경우 데이터 저장
    if isTracking {
        routeCoordinates.append(newLocation.coordinate)
        speedHistory.append(currentSpeed)
        timestampHistory.append(newLocation.timestamp)

        // 3. 현재 건강 데이터 수집
        let healthManager = HealthKitManager.shared
        let healthData = (
            heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
            calories: healthManager.currentCalories > 0 ? healthManager.currentCalories : nil,
            steps: healthManager.currentSteps > 0 ? healthManager.currentSteps : nil,
            distance: healthManager.currentDistance > 0 ? healthManager.currentDistance : nil
        )
        healthDataHistory.append(healthData)

        // 4. 거리 계산
        if let previous = lastLocation {
            let distance = newLocation.distance(from: previous)
            totalDistance += distance
        }

        lastLocation = newLocation
    }
}
```

**처리 순서**:
1. 현재 위치 정보 업데이트
2. 추적 중이면 좌표, 속도, 타임스탬프 저장
3. HealthKitManager에서 실시간 건강 데이터 수집
4. 이전 위치와의 거리 계산 및 누적

---

### 3. WatchLocationManager (Watch)
**파일**: [WatchLocationManager.swift](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift)

Apple Watch에서 GPS 추적을 담당합니다.

#### 주요 프로퍼티
**위치**: [WatchLocationManager.swift:17-29](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L17-L29)

```swift
class WatchLocationManager: NSObject, ObservableObject {
    static let shared = WatchLocationManager()

    @Published var location: CLLocation?
    @Published var isTracking: Bool = false
    @Published var coordinates: [CLLocationCoordinate2D] = []
    @Published var timestamps: [Date] = []
    @Published var speeds: [Double] = []
    @Published var totalDistance: Double = 0.0
    @Published var currentSpeed: Double = 0.0
    @Published var accuracy: Double = 0.0

    // 건강 데이터 기록
    @Published var healthDataHistory: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)] = []
}
```

#### 핵심 함수

##### 3.1 setupLocationManager()
**위치**: [WatchLocationManager.swift:46-55](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L46-L55)

Watch용 LocationManager 설정입니다.

```swift
private func setupLocationManager() {
    locationManager.delegate = self
    locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
    locationManager.distanceFilter = 5.0
    locationManager.activityType = .fitness                      // 운동 모드
    locationManager.allowsBackgroundLocationUpdates = true       // 백그라운드 허용
}
```

**iPhone과의 차이점**:
- `activityType`: `.fitness`로 설정하여 운동 추적 최적화
- `allowsBackgroundLocationUpdates`: `true`로 설정하여 백그라운드에서도 추적

##### 3.2 startTracking()
**위치**: [WatchLocationManager.swift:66-89](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L66-L89)

Watch에서 추적을 시작합니다.

```swift
func startTracking() {
    guard !isTracking else { return }

    // 데이터 초기화
    coordinates.removeAll()
    timestamps.removeAll()
    speeds.removeAll()
    healthDataHistory.removeAll()
    totalDistance = 0.0
    lastLocation = nil
    startTime = Date()

    // 위치 업데이트 시작
    locationManager.startUpdatingLocation()
    isTracking = true

    // iPhone에 추적 상태 전송
    WatchConnectivityManager.shared.sendTrackingStatus(isTracking: true)
}
```

##### 3.3 stopTracking()
**위치**: [WatchLocationManager.swift:91-108](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L91-L108)

추적을 중지하고 데이터를 iPhone으로 전송합니다.

```swift
func stopTracking() {
    guard isTracking else { return }

    locationManager.stopUpdatingLocation()
    isTracking = false

    // iPhone에 추적 상태 전송
    WatchConnectivityManager.shared.sendTrackingStatus(isTracking: false)

    // 최종 위치 데이터를 iPhone으로 전송
    sendLocationDataToiPhone()
}
```

##### 3.4 sendLocationDataToiPhone()
**위치**: [WatchLocationManager.swift:112-150](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L112-L150)

수집된 GPS 및 건강 데이터를 iPhone으로 전송합니다.

```swift
private func sendLocationDataToiPhone() {
    guard !coordinates.isEmpty else { return }

    // 좌표와 건강 데이터를 딕셔너리 형식으로 변환
    let coordinatesData: [[String: Any]] = zip(zip(coordinates, timestamps), healthDataHistory).map { coordTime, health in
        var data: [String: Any] = [
            "latitude": coordTime.0.latitude,
            "longitude": coordTime.0.longitude,
            "timestamp": coordTime.1.timeIntervalSince1970
        ]

        // 건강 데이터 추가 (있는 경우에만)
        if let heartRate = health.heartRate {
            data["heartRate"] = heartRate
        }
        if let calories = health.calories {
            data["calories"] = calories
        }
        if let steps = health.steps {
            data["steps"] = steps
        }
        if let distance = health.distance {
            data["healthDistance"] = distance
        }

        return data
    }

    // WatchConnectivity로 전송
    WatchConnectivityManager.shared.sendLocationUpdate(
        coordinates: coordinatesData,
        timestamp: Date()
    )
}
```

**전송 전략**:
- 추적 중: 10개 좌표마다 주기적 전송
- 추적 종료: 전체 데이터 일괄 전송

##### 3.5 locationManager(_:didUpdateLocations:)
**위치**: [WatchLocationManager.swift:187-231](swift_app_demo/space%20Watch%20App%20Watch%20App/WatchLocationManager.swift#L187-L231)

Watch에서 위치 업데이트를 처리합니다.

```swift
func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    guard let newLocation = locations.last else { return }

    location = newLocation
    accuracy = newLocation.horizontalAccuracy

    guard isTracking else { return }

    // 거리 및 속도 계산
    if let lastLoc = lastLocation {
        let distance = calculateDistance(from: lastLoc, to: newLocation)
        totalDistance += distance

        let timeInterval = newLocation.timestamp.timeIntervalSince(lastLoc.timestamp)
        let speed = calculateSpeed(distance: distance, time: timeInterval)
        currentSpeed = speed
        speeds.append(speed)
    }

    // 경로에 추가
    coordinates.append(newLocation.coordinate)
    timestamps.append(newLocation.timestamp)

    // WatchHealthKitManager에서 건강 데이터 수집
    let healthManager = WatchHealthKitManager.shared
    let healthData = (
        heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
        calories: healthManager.totalCalories > 0 ? healthManager.totalCalories : nil,
        steps: healthManager.totalSteps > 0 ? healthManager.totalSteps : nil,
        distance: healthManager.totalDistance > 0 ? healthManager.totalDistance : nil
    )
    healthDataHistory.append(healthData)

    lastLocation = newLocation

    // 10개 좌표마다 iPhone에 전송
    if coordinates.count % 10 == 0 {
        sendLocationDataToiPhone()
    }
}
```

---

### 4. HealthKitManager (iPhone)
**파일**: [HealthKitManager.swift](swift_app_demo/space/HealthKitManager.swift)

iPhone에서 건강 데이터를 수집하고 관리합니다.

#### 주요 프로퍼티
**위치**: [HealthKitManager.swift:18-38](swift_app_demo/space/HealthKitManager.swift#L18-L38)

```swift
class HealthKitManager: ObservableObject {
    static let shared = HealthKitManager()

    // 오늘의 건강 지표
    @Published var sleepHours: Double = 0.0            // hours
    @Published var stressLevel: Int = 0                // 0-100
    @Published var caloriesBurned: Double = 0.0        // kcal

    // 실시간 지표
    @Published var currentHeartRate: Double = 0.0      // bpm
    @Published var currentCalories: Double = 0.0       // kcal
    @Published var currentSteps: Int = 0               // steps
    @Published var currentDistance: Double = 0.0       // meters
    @Published var currentActiveMinutes: Int = 0       // minutes
    @Published var currentHRV: Double = 0.0            // ms (심박변이도)

    // 주간 데이터
    @Published var weeklySleepData: [DailyHealthData] = []
    @Published var weeklyStressData: [DailyHealthData] = []
    @Published var weeklyCaloriesData: [DailyHealthData] = []
}
```

#### 핵심 함수

##### 4.1 requestAuthorization()
**위치**: [HealthKitManager.swift:70-94](swift_app_demo/space/HealthKitManager.swift#L70-L94)

HealthKit 접근 권한을 요청합니다.

```swift
func requestAuthorization() {
    guard isAvailable else { return }

    let readTypes: Set<HKObjectType> = [
        HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
        HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
        HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!,  // 스트레스 프록시
        HKObjectType.quantityType(forIdentifier: .restingHeartRate)!
    ]

    healthStore.requestAuthorization(toShare: nil, read: readTypes) { success, error in
        if success {
            self.fetchTodayHealthData()
            self.fetchWeeklyHealthData()
        }
    }
}
```

##### 4.2 fetchStressData(from:to:)
**위치**: [HealthKitManager.swift:169-199](swift_app_demo/space/HealthKitManager.swift#L169-L199)

HRV(심박변이도)를 사용하여 스트레스 레벨을 계산합니다.

```swift
private func fetchStressData(from startDate: Date, to endDate: Date) {
    guard let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else { return }

    let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)

    let query = HKStatisticsQuery(quantityType: hrvType, quantitySamplePredicate: predicate, options: .discreteAverage) { _, result, error in
        guard let result = result, let average = result.averageQuantity() else { return }

        let hrvValue = average.doubleValue(for: HKUnit.secondUnit(with: .milli))

        // HRV를 스트레스 레벨로 변환 (역관계)
        // 정상 HRV 범위: 20-100ms
        // 높은 HRV = 낮은 스트레스
        let stressLevel = max(0, min(100, Int(100 - hrvValue)))

        DispatchQueue.main.async {
            self.currentHRV = hrvValue
            self.stressLevel = stressLevel
        }
    }

    healthStore.execute(query)
}
```

**스트레스 계산 공식**:
```
stressLevel = 100 - HRV
where HRV is in milliseconds (ms)
```

##### 4.3 startRealtimeObservers()
**위치**: [HealthKitManager.swift:344-357](swift_app_demo/space/HealthKitManager.swift#L344-L357)

실시간 건강 데이터 변경을 감지하는 옵저버를 시작합니다.

```swift
func startRealtimeObservers() {
    guard isAvailable else { return }

    startHeartRateObserver()
    startCaloriesObserver()
    startStepsObserver()
    startDistanceObserver()
}
```

**옵저버 작동 방식**:
1. `HKObserverQuery` 생성 및 실행
2. 데이터 변경 시 콜백 호출
3. 최신 데이터 fetch 및 UI 업데이트
4. `enableBackgroundDelivery`로 백그라운드 전달 활성화

##### 4.4 fetchLatestHeartRate()
**위치**: [HealthKitManager.swift:480-496](swift_app_demo/space/HealthKitManager.swift#L480-L496)

가장 최근의 심박수 데이터를 가져옵니다.

```swift
private func fetchLatestHeartRate() {
    guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }

    let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
    let query = HKSampleQuery(sampleType: heartRateType, predicate: nil, limit: 1, sortDescriptors: [sortDescriptor]) { _, samples, error in
        guard let sample = samples?.first as? HKQuantitySample else { return }

        let heartRate = sample.quantity.doubleValue(for: HKUnit(from: "count/min"))

        DispatchQueue.main.async {
            self.currentHeartRate = heartRate
        }
    }

    healthStore.execute(query)
}
```

---

### 5. WatchConnectivityManager (iPhone & Watch)
**파일**: [WatchConnectivityManager.swift](swift_app_demo/space/WatchConnectivityManager.swift)

iPhone과 Apple Watch 간의 양방향 통신을 담당합니다.

#### 주요 프로퍼티
**위치**: [WatchConnectivityManager.swift:17-22](swift_app_demo/space/WatchConnectivityManager.swift#L17-L22)

```swift
class WatchConnectivityManager: NSObject, ObservableObject {
    static let shared = WatchConnectivityManager()

    @Published var isWatchPaired: Bool = false
    @Published var isWatchReachable: Bool = false
    @Published var isSessionActivated: Bool = false

    private var session: WCSession?
    private var messageQueue: [[String: Any]] = []
}
```

#### 통신 방법

WatchConnectivity는 3가지 통신 방법을 제공합니다:

1. **sendMessage(_:)** - 즉시 전송, Watch가 reachable해야 함
2. **transferUserInfo(_:)** - 백그라운드 큐 전송, 순서 보장
3. **updateApplicationContext(_:)** - 최신 상태만 전송, 이전 데이터 덮어쓰기

#### 핵심 함수

##### 5.1 sendMessage(_:replyHandler:errorHandler:)
**위치**: [WatchConnectivityManager.swift:46-60](swift_app_demo/space/WatchConnectivityManager.swift#L46-L60)

Watch가 reachable한 경우 즉시 메시지를 전송합니다.

```swift
func sendMessage(_ message: [String: Any], replyHandler: (([String: Any]) -> Void)? = nil, errorHandler: ((Error) -> Void)? = nil) {
    guard let session = session, session.isReachable else {
        // Watch가 연결되지 않은 경우 큐에 저장
        messageQueue.append(message)
        errorHandler?(WatchConnectivityError.notReachable)
        return
    }

    session.sendMessage(message, replyHandler: replyHandler, errorHandler: { error in
        errorHandler?(error)
    })
}
```

**사용 사례**: 체크포인트 전송

##### 5.2 transferUserInfo(_:)
**위치**: [WatchConnectivityManager.swift:63-71](swift_app_demo/space/WatchConnectivityManager.swift#L63-L71)

백그라운드에서 안정적으로 데이터를 전송합니다.

```swift
func transferUserInfo(_ userInfo: [String: Any]) {
    guard let session = session else { return }

    session.transferUserInfo(userInfo)
}
```

**사용 사례**: 위치 데이터 전송 (대용량, 순서 보장 필요)

##### 5.3 updateApplicationContext(_:)
**위치**: [WatchConnectivityManager.swift:74-86](swift_app_demo/space/WatchConnectivityManager.swift#L74-L86)

최신 상태만 유지하는 방식으로 업데이트합니다.

```swift
func updateApplicationContext(_ context: [String: Any]) {
    guard let session = session else { return }

    do {
        try session.updateApplicationContext(context)
    } catch {
        print("❌ Failed to update application context: \(error.localizedDescription)")
    }
}
```

**사용 사례**: 추적 상태 (시작/중지), 인증 상태

##### 5.4 sendLocationUpdate(coordinates:timestamp:)
**위치**: [WatchConnectivityManager.swift:91-99](swift_app_demo/space/WatchConnectivityManager.swift#L91-L99)

위치 업데이트를 iPhone으로 전송합니다.

```swift
func sendLocationUpdate(coordinates: [[String: Any]], timestamp: Date) {
    let message: [String: Any] = [
        "type": "locationUpdate",
        "coordinates": coordinates,
        "timestamp": timestamp.timeIntervalSince1970
    ]

    transferUserInfo(message)
}
```

##### 5.5 sendAuthenticationStatus(isAuthenticated:userId:userEmail:)
**위치**: [WatchConnectivityManager.swift:122-139](swift_app_demo/space/WatchConnectivityManager.swift#L122-L139)

인증 상태를 Watch로 전송합니다.

```swift
func sendAuthenticationStatus(isAuthenticated: Bool, userId: String? = nil, userEmail: String? = nil) {
    var message: [String: Any] = [
        "type": "authentication",
        "isAuthenticated": isAuthenticated
    ]

    if let userId = userId {
        message["userId"] = userId
    }

    if let userEmail = userEmail {
        message["userEmail"] = userEmail
    }

    updateApplicationContext(message)
}
```

##### 5.6 handleLocationUpdate(_:)
**위치**: [WatchConnectivityManager.swift:270-325](swift_app_demo/space/WatchConnectivityManager.swift#L270-L325)

Watch로부터 받은 위치 데이터를 처리합니다.

```swift
private func handleLocationUpdate(_ message: [String: Any]) {
    guard let coordinates = message["coordinates"] as? [[String: Any]] else { return }

    // 딕셔너리를 CLLocationCoordinate2D로 변환
    let locationCoordinates: [CLLocationCoordinate2D] = coordinates.compactMap { coordDict in
        guard let lat = coordDict["latitude"] as? Double,
              let lon = coordDict["longitude"] as? Double else {
            return nil
        }
        return CLLocationCoordinate2D(latitude: lat, longitude: lon)
    }

    let timestamps: [Date] = coordinates.compactMap { coordDict in
        guard let timestamp = coordDict["timestamp"] as? TimeInterval else {
            return nil
        }
        return Date(timeIntervalSince1970: timestamp)
    }

    // 건강 데이터 파싱
    let healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)] = coordinates.map { coordDict in
        (
            heartRate: coordDict["heartRate"] as? Double,
            calories: coordDict["calories"] as? Double,
            steps: coordDict["steps"] as? Int,
            distance: coordDict["healthDistance"] as? Double
        )
    }

    // LocationManager 업데이트
    DispatchQueue.main.async {
        let locationManager = LocationManager.shared

        for coordinate in locationCoordinates {
            locationManager.coordinates.append(coordinate)
        }

        for timestamp in timestamps {
            locationManager.timestamps.append(timestamp)
        }

        for health in healthData {
            locationManager.healthDataHistory.append(health)
        }
    }
}
```

**처리 과정**:
1. 좌표 딕셔너리를 CLLocationCoordinate2D로 변환
2. 타임스탬프 파싱
3. 건강 데이터 추출
4. LocationManager의 배열에 추가

##### 5.7 handleHealthData(_:)
**위치**: [WatchConnectivityManager.swift:327-379](swift_app_demo/space/WatchConnectivityManager.swift#L327-L379)

Watch로부터 받은 건강 데이터를 처리합니다.

```swift
private func handleHealthData(_ message: [String: Any]) {
    guard let healthData = message["data"] as? [String: Any] else { return }

    let heartRate = healthData["heartRate"] as? Double
    let calories = healthData["calories"] as? Double
    let steps = healthData["steps"] as? Int
    let distance = healthData["distance"] as? Double

    // HealthKitManager 업데이트
    DispatchQueue.main.async {
        let healthManager = HealthKitManager.shared

        if let hr = heartRate {
            healthManager.currentHeartRate = hr
        }
        if let cal = calories {
            healthManager.currentCalories = cal
        }
        if let st = steps {
            healthManager.currentSteps = st
        }
        if let dist = distance {
            healthManager.currentDistance = dist
        }
    }
}
```

##### 5.8 processMessageQueue()
**위치**: [WatchConnectivityManager.swift:144-156](swift_app_demo/space/WatchConnectivityManager.swift#L144-L156)

Watch가 reachable해질 때 대기 중인 메시지를 전송합니다.

```swift
private func processMessageQueue() {
    guard !messageQueue.isEmpty, let session = session, session.isReachable else {
        return
    }

    for message in messageQueue {
        sendMessage(message)
    }

    messageQueue.removeAll()
}
```

---

## 뷰 컴포넌트

### 1. TimelineWidget
**파일**: [TimelineWidget.swift](swift_app_demo/space/TimelineWidget.swift)

홈 화면에 표시되는 160x160 타임라인 위젯입니다.

#### 구조
**위치**: [TimelineWidget.swift:12-47](swift_app_demo/space/TimelineWidget.swift#L12-L47)

```swift
struct TimelineWidget: View {
    @StateObject private var locationManager = LocationManager()
    @StateObject private var timelineManager = TimelineManager.shared

    @State private var showDetailView = false
    @State private var timelineStartTime: Date?

    var body: some View {
        Button(action: handleTap) {
            ZStack {
                Color(hex: "F3DEE5")

                if let latestTimeline = timelineManager.timelines.first {
                    timelineMiniMapView(timeline: latestTimeline)
                } else if locationManager.isTracking {
                    trackingView
                } else {
                    emptyStateView
                }
            }
        }
        .sheet(isPresented: $showDetailView) {
            TimelineDetailView(...)
        }
    }
}
```

#### 상태별 뷰

##### 1.1 Empty State (기록 없음)
**위치**: [TimelineWidget.swift:51-61](swift_app_demo/space/TimelineWidget.swift#L51-L61)

```swift
private var emptyStateView: some View {
    VStack(spacing: 8) {
        Image(systemName: "plus.circle.fill")
            .font(.system(size: 36))
            .foregroundColor(Color(hex: "A50034"))

        Text("타임라인 기록하기")
            .font(.system(size: 14, weight: .medium))
    }
}
```

##### 1.2 Tracking View (추적 중)
**위치**: [TimelineWidget.swift:65-106](swift_app_demo/space/TimelineWidget.swift#L65-L106)

```swift
private var trackingView: some View {
    VStack(spacing: 8) {
        // 미니 지도 또는 로딩 인디케이터
        if locationManager.routeCoordinates.count > 1 {
            Map(position: .constant(.region(currentRegion))) {
                MapPolyline(coordinates: locationManager.routeCoordinates)
                    .stroke(Color(hex: "A50034"), lineWidth: 3)

                if let lastCoord = locationManager.routeCoordinates.last {
                    Annotation("", coordinate: lastCoord) {
                        Circle()
                            .fill(Color(hex: "A50034"))
                            .frame(width: 12, height: 12)
                    }
                }
            }
            .frame(height: 100)
        } else {
            ProgressView()
                .scaleEffect(1.5)
        }

        // 현재 통계
        VStack(spacing: 4) {
            Text(String(format: "%.2f km/h", locationManager.currentSpeed))
                .font(.system(size: 16, weight: .bold))

            Text(String(format: "%.2f km", locationManager.totalDistance / 1000))
                .font(.system(size: 12))
        }
    }
}
```

##### 1.3 Timeline Mini Map (최근 기록)
**위치**: [TimelineWidget.swift:110-154](swift_app_demo/space/TimelineWidget.swift#L110-L154)

```swift
private func timelineMiniMapView(timeline: TimelineRecord) -> some View {
    VStack(spacing: 0) {
        // 미니 지도
        if let region = timeline.region {
            Map(position: .constant(.region(region))) {
                MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                    .stroke(Color(hex: "A50034"), lineWidth: 3)

                // 시작점 (녹색)
                if let firstCoord = timeline.coordinates.first?.coordinate {
                    Annotation("", coordinate: firstCoord) {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 10, height: 10)
                    }
                }

                // 종료점 (빨강)
                if let lastCoord = timeline.coordinates.last?.coordinate {
                    Annotation("", coordinate: lastCoord) {
                        Circle()
                            .fill(Color(hex: "A50034"))
                            .frame(width: 10, height: 10)
                    }
                }
            }
            .frame(height: 110)
        }

        // 통계 오버레이
        VStack(spacing: 2) {
            Text(timeline.distanceFormatted)
                .font(.system(size: 14, weight: .semibold))

            Text(timeline.durationFormatted)
                .font(.system(size: 11))
        }
        .padding(.vertical, 8)
        .background(Color(hex: "F3DEE5").opacity(0.95))
    }
}
```

#### 이벤트 핸들러

##### 1.4 handleTap()
**위치**: [TimelineWidget.swift:173-184](swift_app_demo/space/TimelineWidget.swift#L173-L184)

위젯 탭 시 동작을 처리합니다.

```swift
private func handleTap() {
    if locationManager.isTracking {
        // 추적 중이면 상세 뷰 표시
        showDetailView = true
    } else if timelineManager.timelines.isEmpty {
        // 기록이 없으면 추적 시작
        startTracking()
    } else {
        // 기록이 있으면 상세 뷰 표시
        showDetailView = true
    }
}
```

##### 1.5 stopTracking()
**위치**: [TimelineWidget.swift:191-218](swift_app_demo/space/TimelineWidget.swift#L191-L218)

추적을 중지하고 타임라인을 저장합니다.

```swift
private func stopTracking() {
    guard let startTime = timelineStartTime else { return }

    locationManager.stopTracking()

    // 체크포인트 자동 생성
    let checkpoints = timelineManager.generateCheckpoints(
        coordinates: locationManager.routeCoordinates,
        timestamps: locationManager.timestampHistory,
        healthData: locationManager.healthDataHistory
    )

    // 타임라인 생성 및 저장
    if let timeline = timelineManager.createTimeline(
        startTime: startTime,
        endTime: Date(),
        coordinates: locationManager.routeCoordinates,
        timestamps: locationManager.timestampHistory,
        speeds: locationManager.speedHistory,
        checkpoints: checkpoints
    ) {
        timelineManager.saveTimeline(timeline)
    }

    locationManager.resetTracking()
    timelineStartTime = nil
}
```

**처리 순서**:
1. LocationManager 중지
2. GPS 및 건강 데이터로부터 체크포인트 자동 생성
3. TimelineRecord 생성
4. TimelineManager에 저장
5. LocationManager 초기화

---

### 2. TimelineDetailView
**파일**: [TimelineDetailView.swift](swift_app_demo/space/TimelineDetailView.swift)

전체 화면 타임라인 뷰로, 지도, 통계, 컨트롤을 제공합니다.

#### 구조
**위치**: [TimelineDetailView.swift:12-69](swift_app_demo/space/TimelineDetailView.swift#L12-L69)

```swift
struct TimelineDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var locationManager: LocationManager
    @Binding var isTracking: Bool

    var onStartTracking: () -> Void
    var onStopTracking: () -> Void

    @StateObject private var timelineManager = TimelineManager.shared
    @State private var selectedTimeline: TimelineRecord?
    @State private var cameraPosition: MapCameraPosition = .automatic
    @State private var selectedCheckpoint: Checkpoint?

    var body: some View {
        NavigationStack {
            ZStack {
                VStack(spacing: 0) {
                    mapView
                    statsView
                    Spacer()
                    controlButtons
                    if !timelineManager.timelines.isEmpty {
                        timelineHistorySection
                    }
                }
            }
            .navigationTitle("나의 타임라인")
        }
    }
}
```

#### 주요 서브뷰

##### 2.1 Map View
**위치**: [TimelineDetailView.swift:73-189](swift_app_demo/space/TimelineDetailView.swift#L73-L189)

지도에 경로와 체크포인트를 표시합니다.

```swift
private var mapView: some View {
    Map(position: $cameraPosition) {
        if let timeline = selectedTimeline {
            // 선택된 타임라인 표시
            MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                .stroke(Color(hex: "A50034"), lineWidth: 4)

            // 시작점
            if let firstCoord = timeline.coordinates.first?.coordinate {
                Annotation("시작", coordinate: firstCoord) {
                    ZStack {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 20, height: 20)
                        Circle()
                            .stroke(Color.white, lineWidth: 3)
                    }
                }
            }

            // 종료점
            if let lastCoord = timeline.coordinates.last?.coordinate {
                Annotation("종료", coordinate: lastCoord) {
                    ZStack {
                        Circle()
                            .fill(Color(hex: "A50034"))
                            .frame(width: 20, height: 20)
                        Circle()
                            .stroke(Color.white, lineWidth: 3)
                    }
                }
            }

            // 체크포인트
            ForEach(timeline.checkpoints) { checkpoint in
                Annotation("", coordinate: checkpoint.coordinate.coordinate) {
                    CheckpointAnnotationView(
                        checkpoint: checkpoint,
                        isSelected: selectedCheckpoint?.id == checkpoint.id,
                        onTap: {
                            withAnimation(.spring(response: 0.3)) {
                                if selectedCheckpoint?.id == checkpoint.id {
                                    selectedCheckpoint = nil
                                } else {
                                    selectedCheckpoint = checkpoint
                                }
                            }
                        }
                    )
                }
            }
        } else if isTracking && locationManager.routeCoordinates.count > 1 {
            // 현재 추적 중인 경로 표시
            MapPolyline(coordinates: locationManager.routeCoordinates)
                .stroke(Color(hex: "A50034"), lineWidth: 4)

            if let lastCoord = locationManager.routeCoordinates.last {
                Annotation("", coordinate: lastCoord) {
                    ZStack {
                        Circle()
                            .fill(Color(hex: "A50034"))
                            .frame(width: 20, height: 20)

                        // 펄스 애니메이션
                        Circle()
                            .fill(Color(hex: "A50034").opacity(0.3))
                            .frame(width: 30, height: 30)
                            .scaleEffect(1.5)
                            .animation(
                                .easeInOut(duration: 1.5).repeatForever(autoreverses: true),
                                value: isTracking
                            )
                    }
                }
            }
        } else if let location = locationManager.location {
            // 현재 위치만 표시
            Annotation("", coordinate: location.coordinate) {
                ZStack {
                    Circle()
                        .fill(Color.blue)
                        .frame(width: 20, height: 20)
                    Circle()
                        .stroke(Color.white, lineWidth: 3)
                }
            }
        }

        UserAnnotation()
    }
    .mapStyle(.standard(elevation: .realistic))
    .mapControls {
        MapUserLocationButton()
        MapCompass()
        MapScaleView()
    }
}
```

**지도 표시 우선순위**:
1. 선택된 타임라인 (체크포인트 포함)
2. 추적 중인 경로 (펄스 애니메이션)
3. 현재 위치만

##### 2.2 Stats View
**위치**: [TimelineDetailView.swift:193-244](swift_app_demo/space/TimelineDetailView.swift#L193-L244)

통계 정보를 표시합니다.

```swift
private var statsView: some View {
    VStack(spacing: 16) {
        if let timeline = selectedTimeline {
            // 선택된 타임라인 통계
            HStack(spacing: 20) {
                statItem(title: "거리", value: timeline.distanceFormatted, icon: "figure.walk")
                statItem(title: "시간", value: timeline.durationFormatted, icon: "clock.fill")
                statItem(title: "평균 속도", value: String(format: "%.1f km/h", timeline.averageSpeed), icon: "speedometer")
            }
        } else if isTracking {
            // 현재 추적 통계
            HStack(spacing: 20) {
                statItem(
                    title: "거리",
                    value: String(format: "%.2f km", locationManager.totalDistance / 1000),
                    icon: "figure.walk"
                )
                statItem(
                    title: "속도",
                    value: String(format: "%.1f km/h", locationManager.currentSpeed),
                    icon: "speedometer"
                )
                statItem(
                    title: "고도",
                    value: String(format: "%.0f m", locationManager.currentAltitude),
                    icon: "arrow.up.arrow.down"
                )
            }

            // GPS 정확도 정보
            HStack(spacing: 8) {
                Image(systemName: "location.fill")
                Text("H: ±\(String(format: "%.0f", locationManager.horizontalAccuracy))m | V: ±\(String(format: "%.0f", locationManager.verticalAccuracy))m")
                    .font(.system(size: 11))
            }
        } else {
            Text("타임라인을 보려면 기록을 시작하세요")
                .font(.system(size: 14))
        }
    }
    .padding(16)
    .background(Color.white)
    .cornerRadius(16)
}
```

##### 2.3 Control Buttons
**위치**: [TimelineDetailView.swift:265-315](swift_app_demo/space/TimelineDetailView.swift#L265-L315)

추적 시작/중지 버튼을 제공합니다.

```swift
private var controlButtons: some View {
    HStack(spacing: 12) {
        if selectedTimeline != nil {
            // 뒤로가기 버튼
            Button(action: {
                selectedTimeline = nil
            }) {
                HStack {
                    Image(systemName: "arrow.left")
                    Text("뒤로")
                }
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Color.gray.opacity(0.2))
                .cornerRadius(12)
            }
        } else if isTracking {
            // 중지 버튼
            Button(action: {
                onStopTracking()
            }) {
                HStack {
                    Image(systemName: "stop.fill")
                    Text("중지")
                }
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Color(hex: "A50034"))
                .foregroundColor(.white)
                .cornerRadius(12)
            }
        } else {
            // 시작 버튼
            Button(action: {
                selectedTimeline = nil
                onStartTracking()
            }) {
                HStack {
                    Image(systemName: "play.fill")
                    Text("기록 시작")
                }
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .background(Color(hex: "A50034"))
                .foregroundColor(.white)
                .cornerRadius(12)
            }
        }
    }
}
```

##### 2.4 Timeline History Section
**위치**: [TimelineDetailView.swift:319-402](swift_app_demo/space/TimelineDetailView.swift#L319-L402)

저장된 타임라인 목록을 가로 스크롤로 표시합니다.

```swift
private var timelineHistorySection: some View {
    VStack(alignment: .leading, spacing: 12) {
        HStack {
            Text("기록")
                .font(.system(size: 18, weight: .semibold))

            Spacer()

            Button(action: {
                timelineManager.clearAllTimelines()
            }) {
                Text("전체 삭제")
                    .font(.system(size: 13))
                    .foregroundColor(Color(hex: "A50034"))
            }
        }

        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(timelineManager.timelines) { timeline in
                    timelineHistoryCard(timeline: timeline)
                }
            }
        }
    }
}

private func timelineHistoryCard(timeline: TimelineRecord) -> some View {
    Button(action: {
        selectedTimeline = timeline
    }) {
        VStack(alignment: .leading, spacing: 8) {
            // 미니 지도 미리보기
            if let region = timeline.region {
                Map(position: .constant(.region(region))) {
                    MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                        .stroke(Color(hex: "A50034"), lineWidth: 2)
                }
                .frame(width: 120, height: 80)
                .cornerRadius(8)
            }

            // 통계
            VStack(alignment: .leading, spacing: 4) {
                Text(timeline.distanceFormatted)
                    .font(.system(size: 13, weight: .semibold))

                Text(timeline.durationFormatted)
                    .font(.system(size: 11))

                Text(formatDate(timeline.startTime))
                    .font(.system(size: 10))
            }
        }
        .padding(10)
        .background(selectedTimeline?.id == timeline.id ? Color(hex: "F3DEE5") : Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(selectedTimeline?.id == timeline.id ? Color(hex: "A50034") : Color.clear, lineWidth: 2)
        )
    }
    .contextMenu {
        Button(role: .destructive) {
            timelineManager.deleteTimeline(timeline)
            if selectedTimeline?.id == timeline.id {
                selectedTimeline = nil
            }
        } label: {
            Label("삭제", systemImage: "trash")
        }
    }
}
```

**기능**:
- 가로 스크롤로 모든 타임라인 표시
- 각 카드는 미니 지도 + 통계 표시
- 탭하여 상세 보기
- 길게 눌러 삭제 (Context Menu)

#### 헬퍼 함수

##### 2.5 updateCameraPosition()
**위치**: [TimelineDetailView.swift:406-420](swift_app_demo/space/TimelineDetailView.swift#L406-L420)

지도 카메라 위치를 업데이트합니다.

```swift
private func updateCameraPosition() {
    if let timeline = selectedTimeline, let region = timeline.region {
        // 선택된 타임라인에 맞춰 카메라 이동
        cameraPosition = .region(region)
    } else if isTracking, let lastLocation = locationManager.location {
        // 추적 중이면 현재 위치 추적
        cameraPosition = .region(MKCoordinateRegion(
            center: lastLocation.coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        ))
    } else if let location = locationManager.location {
        // 기본 위치로 이동
        cameraPosition = .region(MKCoordinateRegion(
            center: location.coordinate,
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        ))
    }
}
```

---

### 3. CheckpointAnnotationView
**파일**: [TimelineDetailView.swift:431-466](swift_app_demo/space/TimelineDetailView.swift#L431-L466)

지도에 체크포인트를 표시하는 커스텀 Annotation입니다.

```swift
struct CheckpointAnnotationView: View {
    let checkpoint: Checkpoint
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // 선택 시 말풍선 표시
            if isSelected {
                CheckpointBubbleView(checkpoint: checkpoint)
                    .transition(.scale.combined(with: .opacity))
            }

            // 이모지 마커
            Button(action: onTap) {
                ZStack {
                    // 배경 원
                    Circle()
                        .fill(Color(hex: checkpoint.mood.color).opacity(0.2))
                        .frame(width: 44, height: 44)

                    Circle()
                        .fill(Color.white)
                        .frame(width: 36, height: 36)
                        .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)

                    Text(checkpoint.mood.emoji)
                        .font(.system(size: 20))
                }
            }
            .buttonStyle(.plain)
            .scaleEffect(isSelected ? 1.2 : 1.0)
            .animation(.spring(response: 0.3), value: isSelected)
        }
    }
}
```

**특징**:
- 기분에 따른 색상 배경
- 탭하여 상세 정보 표시/숨김
- 선택 시 1.2배 확대 애니메이션

---

### 4. CheckpointBubbleView
**파일**: [TimelineDetailView.swift:470-622](swift_app_demo/space/TimelineDetailView.swift#L470-L622)

체크포인트의 상세 정보를 말풍선 형태로 표시합니다.

```swift
struct CheckpointBubbleView: View {
    let checkpoint: Checkpoint

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // 기분 헤더
            HStack(spacing: 6) {
                Text(checkpoint.mood.emoji)
                Text(checkpoint.mood.label)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(hex: checkpoint.mood.color))
            }

            Divider()

            // 체류 시간
            HStack(spacing: 6) {
                Image(systemName: "clock.fill")
                Text("체류: \(checkpoint.stayDurationFormatted)")
                    .font(.system(size: 12))
            }

            // 스트레스 변화
            HStack(spacing: 6) {
                Image(systemName: checkpoint.stressChange.icon)
                    .foregroundColor(Color(hex: checkpoint.stressChange.color))
                Text("스트레스: \(checkpoint.stressChange.label)")
                    .font(.system(size: 12))
            }

            // 건강 데이터 (있는 경우만)
            if checkpoint.heartRate != nil || checkpoint.calories != nil ||
               checkpoint.steps != nil || checkpoint.distance != nil {
                Divider()

                // 심박수
                if let heartRate = checkpoint.heartRate {
                    HStack(spacing: 6) {
                        Image(systemName: "heart.fill")
                            .foregroundColor(.red)
                        Text("심박수: \(Int(heartRate)) bpm")
                            .font(.system(size: 12))
                    }
                }

                // 칼로리
                if let calories = checkpoint.calories {
                    HStack(spacing: 6) {
                        Image(systemName: "flame.fill")
                            .foregroundColor(.orange)
                        Text("칼로리: \(Int(calories)) kcal")
                            .font(.system(size: 12))
                    }
                }

                // 걸음수
                if let steps = checkpoint.steps {
                    HStack(spacing: 6) {
                        Image(systemName: "figure.walk")
                            .foregroundColor(.green)
                        Text("걸음수: \(steps)")
                            .font(.system(size: 12))
                    }
                }

                // 거리
                if let distance = checkpoint.distance {
                    HStack(spacing: 6) {
                        Image(systemName: "location.fill")
                            .foregroundColor(.blue)
                        Text("거리: \(distanceFormatted(distance))")
                            .font(.system(size: 12))
                    }
                }

                // HRV (심박변이도)
                if let hrv = checkpoint.hrv {
                    HStack(spacing: 6) {
                        Image(systemName: "waveform.path.ecg")
                            .foregroundColor(.purple)
                        Text("HRV: \(String(format: "%.1f", hrv)) ms")
                            .font(.system(size: 12))
                    }
                }

                // 스트레스 레벨
                if let stressLevel = checkpoint.stressLevel {
                    HStack(spacing: 6) {
                        Image(systemName: "brain.head.profile")
                            .foregroundColor(stressLevelColor(for: stressLevel))
                        Text("스트레스: \(stressLevel)%")
                            .font(.system(size: 12))
                    }
                }
            }

            // 노트 (있는 경우만)
            if let note = checkpoint.note, !note.isEmpty {
                Divider()
                Text(note)
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
                    .lineLimit(2)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.white)
                .shadow(color: .black.opacity(0.15), radius: 8, x: 0, y: 4)
        )
        .frame(minWidth: 160)
        .offset(y: -8)
    }

    // 스트레스 레벨에 따른 색상
    private func stressLevelColor(for level: Int) -> Color {
        switch level {
        case 0..<30:
            return .green   // 낮은 스트레스
        case 30..<60:
            return .yellow  // 보통 스트레스
        default:
            return .red     // 높은 스트레스
        }
    }
}
```

**표시 정보**:
1. **필수 정보**: 기분, 체류 시간, 스트레스 변화
2. **건강 데이터** (옵션): 심박수, 칼로리, 걸음수, 거리, HRV, 스트레스 레벨
3. **노트** (옵션): 사용자 메모

---

### 5. WatchMapView (Watch App)
**파일**: Watch App ContentView

Apple Watch에서 지도와 추적 컨트롤을 표시합니다.

#### ContentView 구조
**위치**: [ContentView.swift:14-23](swift_app_demo/space%20Watch%20App%20Watch%20App/ContentView.swift#L14-L23)

```swift
struct ContentView: View {
    @StateObject private var locationManager = WatchLocationManager.shared
    @StateObject private var connectivityManager = WatchConnectivityManager.shared

    var body: some View {
        NavigationStack {
            if connectivityManager.isAuthenticated {
                authenticatedView
            } else {
                notAuthenticatedView
            }
        }
    }
}
```

#### Authenticated View
**위치**: [ContentView.swift:28-112](swift_app_demo/space%20Watch%20App%20Watch%20App/ContentView.swift#L28-L112)

```swift
private var authenticatedView: some View {
    VStack(spacing: 20) {
        // 앱 타이틀
        Text("SPACE")
            .font(.system(size: 24, weight: .bold))
            .foregroundColor(Color(hex: "A50034"))

        // 추적 상태
        VStack(spacing: 8) {
            if locationManager.isTracking {
                HStack {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 8, height: 8)
                    Text("추적 중")
                        .font(.system(size: 14))
                        .foregroundColor(.green)
                }
            } else {
                HStack {
                    Circle()
                        .fill(Color.gray)
                        .frame(width: 8, height: 8)
                    Text("대기 중")
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                }
            }

            // iPhone 연결 상태
            HStack {
                Image(systemName: connectivityManager.isPhoneReachable ? "iphone.and.arrow.forward" : "iphone.slash")
                Text(connectivityManager.isPhoneReachable ? "iPhone 연결됨" : "iPhone 연결 끊김")
                    .font(.system(size: 12))
            }
            .foregroundColor(connectivityManager.isPhoneReachable ? .green : .gray)
        }

        // 지도 네비게이션 버튼
        NavigationLink(destination: WatchMapView()) {
            VStack(spacing: 4) {
                Image(systemName: "map.fill")
                    .font(.system(size: 28))
                Text("지도")
                    .font(.system(size: 14, weight: .semibold))
            }
            .frame(maxWidth: .infinity)
            .frame(height: 80)
            .background(Color(hex: "A50034"))
            .foregroundColor(.white)
            .cornerRadius(12)
        }

        // 추적 중일 때 빠른 통계
        if locationManager.isTracking {
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("거리:")
                        .font(.system(size: 12))
                    Spacer()
                    Text(distanceText)
                        .font(.system(size: 12, weight: .semibold))
                }

                HStack {
                    Text("포인트:")
                        .font(.system(size: 12))
                    Spacer()
                    Text("\(locationManager.coordinates.count)")
                        .font(.system(size: 12, weight: .semibold))
                }
            }
            .padding(8)
            .background(Color.secondary.opacity(0.1))
            .cornerRadius(8)
        }
    }
}
```

#### Not Authenticated View
**위치**: [ContentView.swift:116-161](swift_app_demo/space%20Watch%20App%20Watch%20App/ContentView.swift#L116-L161)

```swift
private var notAuthenticatedView: some View {
    VStack(spacing: 20) {
        Spacer()

        // 잠금 아이콘
        Image(systemName: "lock.fill")
            .font(.system(size: 40))
            .foregroundColor(Color(hex: "A50034"))

        Text("SPACE")
            .font(.system(size: 24, weight: .bold))

        // 메시지
        VStack(spacing: 8) {
            Text("iPhone 앱에서")
                .font(.system(size: 14))

            Text("로그인이 필요합니다")
                .font(.system(size: 14, weight: .semibold))
        }

        // 연결 상태
        HStack {
            Image(systemName: connectivityManager.isPhoneReachable ? "iphone.and.arrow.forward" : "iphone.slash")
            Text(connectivityManager.isPhoneReachable ? "iPhone 연결됨" : "iPhone 연결 끊김")
                .font(.system(size: 12))
        }
        .foregroundColor(connectivityManager.isPhoneReachable ? .green : .gray)

        Spacer()

        Text("iPhone 앱을 열어 로그인해주세요")
            .font(.system(size: 11))
            .multilineTextAlignment(.center)
    }
}
```

---

## iPhone-Watch 통신

### 통신 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         iPhone App                          │
├─────────────────────────────────────────────────────────────┤
│  LocationManager         HealthKitManager                   │
│       ↓                        ↓                            │
│  WatchConnectivityManager                                   │
│       ↕ (WatchConnectivity Framework)                       │
├─────────────────────────────────────────────────────────────┤
│                        Watch App                            │
├─────────────────────────────────────────────────────────────┤
│  WatchConnectivityManager                                   │
│       ↓                        ↓                            │
│  WatchLocationManager    WatchHealthKitManager              │
└─────────────────────────────────────────────────────────────┘
```

### 메시지 타입

#### 1. 인증 상태 (iPhone → Watch)
**전송 방법**: `updateApplicationContext`
**타이밍**: 로그인/로그아웃 시

```swift
{
    "type": "authentication",
    "isAuthenticated": true,
    "userId": "user_123",
    "userEmail": "user@example.com"
}
```

#### 2. 추적 명령 (iPhone ↔ Watch)
**전송 방법**: `updateApplicationContext`
**타이밍**: 추적 시작/중지 시

```swift
{
    "type": "trackingCommand",
    "isTracking": true
}
```

#### 3. 위치 업데이트 (Watch → iPhone)
**전송 방법**: `transferUserInfo`
**타이밍**: 10개 좌표마다 또는 추적 종료 시

```swift
{
    "type": "locationUpdate",
    "coordinates": [
        {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "timestamp": 1699999999.0,
            "heartRate": 75.0,
            "calories": 120.5,
            "steps": 5000,
            "healthDistance": 3500.0
        },
        // ... more coordinates
    ],
    "timestamp": 1699999999.0
}
```

#### 4. 건강 데이터 (Watch → iPhone)
**전송 방법**: `sendMessage`
**타이밍**: 실시간 업데이트

```swift
{
    "type": "healthData",
    "data": {
        "heartRate": 75.0,
        "calories": 120.5,
        "steps": 5000,
        "distance": 3500.0
    }
}
```

#### 5. 체크포인트 (iPhone ↔ Watch)
**전송 방법**: `sendMessage`
**타이밍**: 수동 체크포인트 생성 시

```swift
{
    "type": "checkpoint",
    "data": {
        "latitude": 37.5665,
        "longitude": 126.9780,
        "timestamp": 1699999999.0,
        "mood": "happy",
        "note": "카페에서 휴식"
    }
}
```

### 통신 흐름 예시

#### 시나리오 1: Watch에서 추적 시작

```
1. Watch: 사용자가 "추적 시작" 버튼 탭
2. WatchLocationManager.startTracking() 호출
3. WatchConnectivityManager.sendTrackingStatus(isTracking: true)
4. → iPhone: WatchConnectivityManager.handleTrackingStatus() 호출
5. iPhone: LocationManager 업데이트 또는 UI 반영
```

#### 시나리오 2: Watch에서 GPS 데이터 수집 및 전송

```
1. Watch: WatchLocationManager가 GPS 업데이트 수신
2. Watch: WatchHealthKitManager에서 현재 건강 데이터 수집
3. Watch: GPS 좌표 + 건강 데이터를 healthDataHistory에 추가
4. Watch: 10개 좌표마다 sendLocationDataToiPhone() 호출
5. → iPhone: WatchConnectivityManager.handleLocationUpdate() 호출
6. iPhone: LocationManager.coordinates, healthDataHistory에 추가
7. iPhone: UI 자동 업데이트 (@Published 프로퍼티)
```

#### 시나리오 3: iPhone에서 로그인

```
1. iPhone: 사용자 로그인 성공
2. iPhone: WatchConnectivityManager.sendAuthenticationStatus(isAuthenticated: true, userId: "...", userEmail: "...")
3. → Watch: WatchConnectivityManager.handleApplicationContext() 호출
4. Watch: isAuthenticated = true 업데이트
5. Watch: ContentView가 authenticatedView로 전환
```

---

## 위치 추적

### GPS 정확도 설정

#### iPhone
```swift
locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
locationManager.distanceFilter = 5.0  // 5m마다 업데이트
```

#### Watch
```swift
locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
locationManager.distanceFilter = 5.0
locationManager.activityType = .fitness  // 운동 모드 최적화
```

### 거리 계산 알고리즘

**메서드**: `CLLocation.distance(from:)`

```swift
func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    guard let newLocation = locations.last, let previous = lastLocation else { return }

    // 이전 위치와의 거리 계산 (Haversine 공식 사용)
    let distance = newLocation.distance(from: previous)  // meters
    totalDistance += distance

    lastLocation = newLocation
}
```

**Haversine 공식** (CoreLocation 내부 사용):
```
a = sin²(Δφ/2) + cos φ1 * cos φ2 * sin²(Δλ/2)
c = 2 * atan2( √a, √(1−a) )
d = R * c

where:
  φ = latitude (in radians)
  λ = longitude (in radians)
  R = Earth's radius (6,371 km)
```

### 속도 계산

```swift
// 방법 1: CLLocation.speed 사용 (권장)
let currentSpeed = max(0, newLocation.speed * 3.6)  // m/s -> km/h

// 방법 2: 거리/시간으로 계산
let distance = newLocation.distance(from: previousLocation)
let timeInterval = newLocation.timestamp.timeIntervalSince(previousLocation.timestamp)
let speed = (distance / timeInterval) * 3.6  // km/h
```

### 정확도 모니터링

```swift
// 수평 정확도 (위치 오차)
let horizontalAccuracy = location.horizontalAccuracy  // meters

// 수직 정확도 (고도 오차)
let verticalAccuracy = location.verticalAccuracy  // meters

// 정확도가 좋지 않은 데이터 필터링
if horizontalAccuracy > 50 {
    // 50m 이상 오차가 있으면 무시
    return
}
```

**정확도 수준**:
- `< 10m`: 매우 정확 (건물 레벨)
- `10-50m`: 정확 (거리 레벨)
- `50-100m`: 보통 (블록 레벨)
- `> 100m`: 부정확 (사용 비권장)

---

## 헬스 데이터 통합

### 수집 데이터

#### 1. 심박수 (Heart Rate)
**단위**: BPM (Beats Per Minute)
**소스**: Apple Watch 센서
**업데이트 주기**: 실시간 (Observer Query)

```swift
HKObjectType.quantityType(forIdentifier: .heartRate)
```

#### 2. 칼로리 (Active Energy Burned)
**단위**: kcal
**소스**: HealthKit 누적 데이터
**업데이트 주기**: 오늘 시작부터 누적

```swift
HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)
```

#### 3. 걸음수 (Step Count)
**단위**: steps
**소스**: 가속도계
**업데이트 주기**: 오늘 시작부터 누적

```swift
HKObjectType.quantityType(forIdentifier: .stepCount)
```

#### 4. 거리 (Distance Walking/Running)
**단위**: meters
**소스**: GPS + 가속도계
**업데이트 주기**: 오늘 시작부터 누적

```swift
HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)
```

#### 5. HRV (Heart Rate Variability)
**단위**: ms (milliseconds)
**소스**: Apple Watch ECG
**의미**: 심박 간격의 변동성 (스트레스 지표)

```swift
HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)
```

**HRV 범위**:
- `60-100ms`: 낮은 스트레스
- `40-60ms`: 보통 스트레스
- `20-40ms`: 높은 스트레스
- `< 20ms`: 매우 높은 스트레스

#### 6. 스트레스 레벨 (Calculated)
**단위**: 0-100 (%)
**계산 공식**: `stressLevel = 100 - HRV`

```swift
let stressLevel = max(0, min(100, Int(100 - hrvValue)))
```

### GPS와 건강 데이터 동기화

#### 동기화 전략

모든 GPS 업데이트 시 동일한 인덱스에 건강 데이터를 저장하여 1:1 매핑을 유지합니다.

```swift
func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
    guard let newLocation = locations.last else { return }

    // 1. GPS 데이터 저장
    routeCoordinates.append(newLocation.coordinate)
    timestampHistory.append(newLocation.timestamp)
    speedHistory.append(currentSpeed)

    // 2. 동일한 시점의 건강 데이터 수집
    let healthManager = HealthKitManager.shared
    let healthData = (
        heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
        calories: healthManager.currentCalories > 0 ? healthManager.currentCalories : nil,
        steps: healthManager.currentSteps > 0 ? healthManager.currentSteps : nil,
        distance: healthManager.currentDistance > 0 ? healthManager.currentDistance : nil
    )

    // 3. 동일한 인덱스에 저장
    healthDataHistory.append(healthData)

    // 이제 routeCoordinates[i], timestampHistory[i], healthDataHistory[i]는 동일한 시점의 데이터
}
```

#### 체크포인트 생성 시 활용

```swift
let checkpoints = timelineManager.generateCheckpoints(
    coordinates: routeCoordinates,
    timestamps: timestampHistory,
    healthData: healthDataHistory
)

// generateCheckpoints 내부에서:
for i in 0..<coordinates.count {
    let coordinate = coordinates[i]
    let timestamp = timestamps[i]
    let health = healthData[i]  // 동일한 인덱스 사용

    // coordinate, timestamp, health는 모두 같은 시점의 데이터
}
```

### 건강 데이터 기반 기분 판단

**위치**: [TimelineDataModel.swift:430-444](swift_app_demo/space/TimelineDataModel.swift#L430-L444)

```swift
let mood: CheckpointMood
if let hr = health.heartRate {
    if hr < 60 {
        mood = .happy      // 휴식 상태
    } else if hr < 80 {
        mood = .neutral    // 정상 범위
    } else if hr < 100 {
        mood = .happy      // 활동적
    } else {
        mood = .neutral    // 격렬한 운동
    }
} else {
    mood = .neutral  // 데이터 없음
}
```

**심박수 범위 참고**:
- `< 60 BPM`: 휴식 심박수 (Resting Heart Rate)
- `60-80 BPM`: 정상 범위
- `80-100 BPM`: 가벼운 활동
- `100-120 BPM`: 중간 활동
- `> 120 BPM`: 격렬한 활동

---

## 체크포인트 자동 생성 알고리즘

### 정지 감지 알고리즘

**위치**: [TimelineDataModel.swift:348-411](swift_app_demo/space/TimelineDataModel.swift#L348-L411)

```swift
func generateCheckpoints(
    coordinates: [CLLocationCoordinate2D],
    timestamps: [Date],
    healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)]
) -> [Checkpoint] {
    guard coordinates.count >= 2 else { return [] }

    var checkpoints: [Checkpoint] = []
    var currentStopStart: Int? = nil
    var currentStopDuration: TimeInterval = 0

    for i in 1..<coordinates.count {
        let loc1 = CLLocation(latitude: coordinates[i - 1].latitude, longitude: coordinates[i - 1].longitude)
        let loc2 = CLLocation(latitude: coordinates[i].latitude, longitude: coordinates[i].longitude)

        // 거리 및 속도 계산
        let distance = loc2.distance(from: loc1)  // meters
        let timeInterval = timestamps[i].timeIntervalSince(timestamps[i - 1])
        let speed = timeInterval > 0 ? (distance / timeInterval) * 3.6 : 0  // km/h

        // 정지 감지
        if speed < 0.5 {  // 0.5 km/h 미만
            if currentStopStart == nil {
                currentStopStart = i
                currentStopDuration = 0
            }
            currentStopDuration += timeInterval
        } else {
            // 이동 재개
            if let stopStart = currentStopStart, currentStopDuration >= 30 {
                // 30초 이상 정지했으면 체크포인트 생성
                let checkpoint = createCheckpointAt(
                    index: stopStart,
                    coordinates: coordinates,
                    timestamps: timestamps,
                    healthData: healthData,
                    stayDuration: currentStopDuration,
                    previousCheckpoint: checkpoints.last
                )
                checkpoints.append(checkpoint)
            }

            // 정지 상태 초기화
            currentStopStart = nil
            currentStopDuration = 0
        }
    }

    // 마지막 정지 처리
    if let stopStart = currentStopStart, currentStopDuration >= 30 {
        let checkpoint = createCheckpointAt(
            index: stopStart,
            coordinates: coordinates,
            timestamps: timestamps,
            healthData: healthData,
            stayDuration: currentStopDuration,
            previousCheckpoint: checkpoints.last
        )
        checkpoints.append(checkpoint)
    }

    return checkpoints
}
```

### 알고리즘 파라미터

| 파라미터 | 값 | 설명 |
|---------|-----|------|
| 정지 속도 임계값 | < 0.5 km/h | 이 속도 미만이면 정지로 간주 |
| 최소 정지 시간 | ≥ 30초 | 30초 이상 정지해야 체크포인트 생성 |
| 스트레스 변화 임계값 | ±10% | 10% 이상 변화 시 증가/감소로 표시 |

### 플로우차트

```
시작
  │
  ├─ 각 GPS 포인트 순회
  │   │
  │   ├─ 이전 포인트와의 거리 계산
  │   ├─ 시간 간격 계산
  │   ├─ 속도 계산 (거리 / 시간)
  │   │
  │   ├─ 속도 < 0.5 km/h?
  │   │   ├─ Yes: 정지 지속
  │   │   │   ├─ 정지 시작 지점 저장 (최초 1회)
  │   │   │   └─ 정지 시간 누적
  │   │   │
  │   │   └─ No: 이동 중
  │   │       ├─ 이전에 정지했었는가?
  │   │       │   ├─ Yes: 정지 시간 ≥ 30초?
  │   │       │   │   ├─ Yes: 체크포인트 생성
  │   │       │   │   └─ No: 무시
  │   │       │   └─ No: 계속 이동
  │   │       └─ 정지 상태 초기화
  │   │
  │   └─ 다음 포인트로
  │
  └─ 마지막 정지 처리 (있다면)
      └─ 정지 시간 ≥ 30초이면 체크포인트 생성
```

---

## 데이터 흐름 다이어그램

### 전체 시스템 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                          사용자 액션                                   │
│                     (타임라인 기록 시작)                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
         ┌──────▼──────┐                 ┌─────▼──────┐
         │   iPhone    │                 │   Watch    │
         └──────┬──────┘                 └─────┬──────┘
                │                               │
    ┌───────────┴──────────┐        ┌──────────┴──────────┐
    │ LocationManager      │        │ WatchLocationManager│
    │ - GPS 추적           │        │ - GPS 추적          │
    │ - 좌표 저장          │        │ - 좌표 저장         │
    └───────────┬──────────┘        └──────────┬──────────┘
                │                               │
    ┌───────────▼──────────┐        ┌──────────▼──────────┐
    │ HealthKitManager     │        │WatchHealthKitManager│
    │ - 심박수             │        │ - 심박수            │
    │ - 칼로리             │        │ - 칼로리            │
    │ - 걸음수             │        │ - 걸음수            │
    │ - HRV/스트레스       │        │ - 거리              │
    └───────────┬──────────┘        └──────────┬──────────┘
                │                               │
                │                    ┌──────────▼──────────┐
                │                    │ WatchConnectivity   │
                │                    │ - 좌표 전송         │
                │                    │ - 건강 데이터 전송  │
                │                    └──────────┬──────────┘
                │                               │
    ┌───────────▼──────────────────────────────▼──────────┐
    │         WatchConnectivityManager (iPhone)           │
    │         - 데이터 수신 및 통합                        │
    └───────────┬─────────────────────────────────────────┘
                │
                │ (사용자가 추적 중지)
                │
    ┌───────────▼──────────┐
    │  TimelineManager     │
    │  - generateCheckpoints│
    │  - createTimeline    │
    │  - saveTimeline      │
    └───────────┬──────────┘
                │
    ┌───────────▼──────────┐
    │  UserDefaults        │
    │  - 영구 저장         │
    └──────────────────────┘
                │
    ┌───────────▼──────────┐
    │  TimelineDetailView  │
    │  - 지도 시각화       │
    │  - 체크포인트 표시   │
    └──────────────────────┘
```

### 체크포인트 생성 흐름

```
추적 종료
   │
   ├─ LocationManager.stopTracking()
   │   └─ 수집된 데이터:
   │       ├─ routeCoordinates: [CLLocationCoordinate2D]
   │       ├─ timestampHistory: [Date]
   │       ├─ speedHistory: [Double]
   │       └─ healthDataHistory: [(heartRate, calories, steps, distance)]
   │
   ├─ TimelineManager.generateCheckpoints(coordinates, timestamps, healthData)
   │   │
   │   ├─ 정지 감지 알고리즘 실행
   │   │   ├─ 속도 < 0.5 km/h && 지속 시간 ≥ 30초
   │   │   └─ 조건 만족 시 체크포인트 후보 생성
   │   │
   │   ├─ 각 체크포인트에 대해 createCheckpointAt() 호출
   │   │   ├─ 좌표 정보
   │   │   ├─ 체류 시간
   │   │   ├─ 건강 데이터 (심박수, 칼로리, 걸음수, 거리)
   │   │   ├─ HRV → 스트레스 레벨 계산
   │   │   ├─ 심박수 → 기분 추정
   │   │   └─ 이전 체크포인트와 비교 → 스트레스 변화 계산
   │   │
   │   └─ [Checkpoint] 배열 반환
   │
   ├─ TimelineManager.createTimeline(startTime, endTime, coordinates, timestamps, speeds, checkpoints)
   │   ├─ 좌표 → CoordinateData 변환
   │   ├─ 총 거리 계산 (점 간 거리 누적)
   │   ├─ 평균/최고 속도 계산
   │   └─ TimelineRecord 생성
   │
   └─ TimelineManager.saveTimeline(timeline)
       ├─ timelines 배열 맨 앞에 추가
       └─ UserDefaults에 JSON 인코딩하여 저장
```

---

## 주요 설정 및 상수

### GPS 설정

```swift
// LocationManager 설정
desiredAccuracy = kCLLocationAccuracyBestForNavigation  // 최고 정확도
distanceFilter = 5.0                                    // 5m마다 업데이트
allowsBackgroundLocationUpdates = false                 // 백그라운드 비활성화 (iPhone)

// WatchLocationManager 설정
desiredAccuracy = kCLLocationAccuracyBestForNavigation
distanceFilter = 5.0
activityType = .fitness                                 // 운동 모드
allowsBackgroundLocationUpdates = true                  // 백그라운드 활성화 (Watch)
```

### 체크포인트 생성 파라미터

```swift
// 정지 감지
let STOP_SPEED_THRESHOLD: Double = 0.5      // km/h
let MIN_STOP_DURATION: TimeInterval = 30    // seconds

// 스트레스 변화 감지
let STRESS_CHANGE_THRESHOLD: Int = 10       // percentage points
```

### 색상 팔레트

```swift
// 브랜드 색상
let PRIMARY_COLOR = "A50034"      // 빨강 (버건디)
let BACKGROUND_COLOR = "F9F9F9"   // 밝은 회색
let WIDGET_BG_COLOR = "F3DEE5"    // 연분홍

// 기분 색상
let MOOD_VERY_HAPPY = "4CAF50"    // Green
let MOOD_HAPPY = "8BC34A"         // Light Green
let MOOD_NEUTRAL = "FFC107"       // Amber
let MOOD_SAD = "FF9800"           // Orange
let MOOD_VERY_SAD = "F44336"      // Red

// 스트레스 변화 색상
let STRESS_INCREASED = "F44336"   // Red
let STRESS_UNCHANGED = "9E9E9E"   // Gray
let STRESS_DECREASED = "4CAF50"   // Green
```

---

## 핵심 함수 요약표

| 함수명 | 파일 | 라인 | 설명 |
|-------|------|-----|------|
| `TimelineManager.saveTimeline(_:)` | TimelineDataModel.swift | 247-251 | 타임라인을 저장하고 영구 저장 |
| `TimelineManager.createTimeline(...)` | TimelineDataModel.swift | 282-324 | GPS 데이터로부터 타임라인 생성 |
| `TimelineManager.generateCheckpoints(...)` | TimelineDataModel.swift | 348-411 | 정지 감지로 체크포인트 자동 생성 |
| `TimelineManager.createCheckpointAt(...)` | TimelineDataModel.swift | 414-480 | 특정 인덱스에 체크포인트 생성 |
| `TimelineManager.createManualCheckpoint(...)` | TimelineDataModel.swift | 483-523 | 사용자 수동 체크포인트 생성 |
| `LocationManager.startTracking()` | LocationManager.swift | 77-95 | iPhone GPS 추적 시작 |
| `LocationManager.stopTracking()` | LocationManager.swift | 98-104 | iPhone GPS 추적 중지 |
| `LocationManager.locationManager(_:didUpdateLocations:)` | LocationManager.swift | 140-192 | GPS 업데이트 처리 및 데이터 저장 |
| `WatchLocationManager.startTracking()` | WatchLocationManager.swift | 66-89 | Watch GPS 추적 시작 |
| `WatchLocationManager.stopTracking()` | WatchLocationManager.swift | 91-108 | Watch GPS 추적 중지 |
| `WatchLocationManager.sendLocationDataToiPhone()` | WatchLocationManager.swift | 112-150 | Watch → iPhone 위치 데이터 전송 |
| `WatchLocationManager.locationManager(_:didUpdateLocations:)` | WatchLocationManager.swift | 187-231 | Watch GPS 업데이트 처리 |
| `HealthKitManager.requestAuthorization()` | HealthKitManager.swift | 70-94 | HealthKit 권한 요청 |
| `HealthKitManager.fetchStressData(from:to:)` | HealthKitManager.swift | 169-199 | HRV → 스트레스 레벨 계산 |
| `HealthKitManager.startRealtimeObservers()` | HealthKitManager.swift | 344-357 | 실시간 건강 데이터 옵저버 시작 |
| `HealthKitManager.fetchLatestHeartRate()` | HealthKitManager.swift | 480-496 | 최신 심박수 가져오기 |
| `WatchConnectivityManager.sendMessage(_:replyHandler:errorHandler:)` | WatchConnectivityManager.swift | 46-60 | 즉시 메시지 전송 |
| `WatchConnectivityManager.transferUserInfo(_:)` | WatchConnectivityManager.swift | 63-71 | 백그라운드 데이터 전송 |
| `WatchConnectivityManager.updateApplicationContext(_:)` | WatchConnectivityManager.swift | 74-86 | 최신 상태 전송 |
| `WatchConnectivityManager.sendLocationUpdate(coordinates:timestamp:)` | WatchConnectivityManager.swift | 91-99 | 위치 업데이트 전송 |
| `WatchConnectivityManager.sendAuthenticationStatus(...)` | WatchConnectivityManager.swift | 122-139 | 인증 상태 전송 |
| `WatchConnectivityManager.handleLocationUpdate(_:)` | WatchConnectivityManager.swift | 270-325 | Watch로부터 위치 데이터 수신 처리 |
| `WatchConnectivityManager.handleHealthData(_:)` | WatchConnectivityManager.swift | 327-379 | Watch로부터 건강 데이터 수신 처리 |
| `TimelineWidget.handleTap()` | TimelineWidget.swift | 173-184 | 위젯 탭 이벤트 처리 |
| `TimelineWidget.stopTracking()` | TimelineWidget.swift | 191-218 | 추적 중지 및 타임라인 저장 |
| `TimelineDetailView.updateCameraPosition()` | TimelineDetailView.swift | 406-420 | 지도 카메라 위치 업데이트 |

---

## 파일 구조

```
SWE-G04-SPACE/
├── swift_app_demo/
│   ├── space/                          # iPhone App
│   │   ├── TimelineDataModel.swift     # 데이터 모델 & TimelineManager
│   │   ├── TimelineDetailView.swift    # 전체 화면 타임라인 뷰
│   │   ├── TimelineWidget.swift        # 홈 화면 위젯
│   │   ├── LocationManager.swift       # iPhone GPS 추적
│   │   ├── HealthKitManager.swift      # iPhone 건강 데이터 관리
│   │   ├── WatchConnectivityManager.swift  # iPhone-Watch 통신
│   │   └── ...
│   │
│   └── space Watch App Watch App/      # Watch App
│       ├── ContentView.swift           # Watch 메인 화면
│       ├── WatchLocationManager.swift  # Watch GPS 추적
│       ├── WatchHealthKitManager.swift # Watch 건강 데이터 관리
│       ├── WatchConnectivityManager.swift  # Watch-iPhone 통신
│       └── ...
│
└── TIMELINE_DOCUMENTATION.md           # 이 문서
```

---

## 의존성

### 프레임워크

- **CoreLocation**: GPS 추적
- **MapKit**: 지도 시각화
- **HealthKit**: 건강 데이터 접근
- **WatchConnectivity**: iPhone-Watch 통신
- **Combine**: 리액티브 프로그래밍 (@Published)
- **SwiftUI**: UI 프레임워크

### Info.plist 권한

```xml
<!-- iPhone -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>타임라인 추적을 위해 위치 접근이 필요합니다</string>

<key>NSHealthShareUsageDescription</key>
<string>건강 데이터를 체크포인트에 통합하기 위해 필요합니다</string>

<!-- Watch -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>Watch에서 타임라인 추적을 위해 위치 접근이 필요합니다</string>

<key>NSHealthShareUsageDescription</key>
<string>건강 데이터를 체크포인트에 통합하기 위해 필요합니다</string>
```

---

## 성능 최적화

### 1. GPS 업데이트 빈도
```swift
distanceFilter = 5.0  // 5m 이하 이동 시 무시
```

### 2. Watch → iPhone 전송 최적화
```swift
// 10개 좌표마다 전송 (배치 처리)
if coordinates.count % 10 == 0 {
    sendLocationDataToiPhone()
}

// 추적 종료 시 전체 전송
func stopTracking() {
    sendLocationDataToiPhone()  // 최종 전송
}
```

### 3. UserDefaults 저장 최적화
```swift
// 메모리 내 배열 유지, 변경 시에만 저장
@Published var timelines: [TimelineRecord] = []

func saveTimeline(_ timeline: TimelineRecord) {
    timelines.insert(timeline, at: 0)
    saveToUserDefaults()  // 변경 시에만 호출
}
```

### 4. 지도 렌더링 최적화
```swift
// 체크포인트만 선택 가능하게 설정
.allowsHitTesting(false)  // 미니 지도는 터치 비활성화

// 좌표 개수 제한 (필요시)
let MAX_COORDINATES = 1000
if coordinates.count > MAX_COORDINATES {
    // 다운샘플링 또는 경고
}
```

---

## 에러 처리

### 1. GPS 권한 미허용
```swift
guard authorizationStatus == .authorizedWhenInUse ||
      authorizationStatus == .authorizedAlways else {
    print("❌ Location permission not granted")
    requestPermission()
    return
}
```

### 2. HealthKit 사용 불가
```swift
if !HKHealthStore.isHealthDataAvailable() {
    print("❌ HealthKit is not available on this device")
    return
}
```

### 3. Watch 연결 실패
```swift
guard let session = session, session.isReachable else {
    print("⚠️ Watch not reachable, queueing message")
    messageQueue.append(message)
    return
}
```

### 4. 좌표 데이터 없음
```swift
guard !coordinates.isEmpty else {
    print("⚠️ No coordinates to save")
    return nil
}
```

---

## 테스트 시나리오

### 1. 기본 추적 흐름
1. 앱 실행 → 위치 권한 허용
2. 타임라인 위젯 탭 → 추적 시작
3. 5분 이상 이동 (걷기/달리기)
4. 중간에 1분 이상 정지 (카페, 벤치 등)
5. 다시 이동
6. 중지 버튼 탭
7. 타임라인 저장 확인
8. 체크포인트 자동 생성 확인

### 2. Watch 통신 테스트
1. Watch에서 추적 시작
2. iPhone에서 실시간 업데이트 확인
3. Watch 추적 중지
4. iPhone에 최종 데이터 전송 확인
5. 체크포인트에 건강 데이터 포함 확인

### 3. 체크포인트 검증
1. 저장된 타임라인 열기
2. 지도에서 체크포인트 탭
3. 말풍선 정보 확인:
   - 기분 이모지
   - 체류 시간
   - 스트레스 변화
   - 건강 데이터 (심박수, 칼로리, 걸음수, 거리)
   - HRV, 스트레스 레벨

---

## 향후 개선 사항

### 1. 수동 체크포인트 생성 UI
- 추적 중 "체크포인트 추가" 버튼
- 기분 선택 모달
- 메모 입력 기능

### 2. 체크포인트 편집
- 기분 수정
- 메모 추가/수정
- 체크포인트 삭제

### 3. 체크포인트 필터링
- 기분별 필터
- 스트레스 레벨별 필터
- 날짜별 필터

### 4. 통계 대시보드
- 주간/월간 통계
- 기분 트렌드 그래프
- 스트레스 패턴 분석
- 건강 데이터 차트

### 5. 데이터 내보내기
- JSON 형식 내보내기
- GPX 파일 내보내기 (GPS 데이터)
- CSV 내보내기 (통계 데이터)

### 6. 백그라운드 추적
- iPhone 백그라운드 추적 활성화
- 배터리 효율 최적화
- 알림으로 추적 상태 표시

---

## 문서 업데이트 이력

| 날짜 | 버전 | 내용 |
|-----|------|------|
| 2025-11-26 | 1.0 | 초기 문서 작성 - 전체 타임라인 기능 문서화 |

---

## 작성자

**프로젝트**: SWE-G04-SPACE
**문서 작성일**: 2025-11-26
**버전**: 1.0

---

이 문서는 타임라인 기능의 모든 핵심 함수, 데이터 모델, 통신 프로토콜, 알고리즘을 상세히 설명합니다.
코드 참조 링크를 통해 실제 구현을 확인할 수 있습니다.
