# Watch 단독 기록 타임라인 저장 문제 수정 완료

## 문제 요약

Watch에서만 기록을 시작하고 종료해도 iPhone 측에서 타임라인이 자동으로 생성되지 않는 문제가 있었습니다.

### 근본 원인

1. **`timelineStartTime` 관리 문제**
   - `TimelineWidget`에서만 로컬 상태로 `timelineStartTime`을 관리
   - Watch가 보낸 `trackingStatus` 메시지를 받아도 이 값이 설정되지 않음
   - `stopTracking()`의 `guard let startTime = timelineStartTime` 검사에서 항상 실패

2. **Watch 이벤트 처리 불완전**
   - `handleTrackingStatus`가 `LocationManager`의 `startTracking()`/`stopTracking()`만 호출
   - 타임라인 생성/저장 로직이 전혀 실행되지 않음
   - 수집한 GPS 데이터가 다음 `startTracking()` 호출 시 유실

## 수정 내용

### 1. LocationManager 수정 ([LocationManager.swift](swift_app_demo/space/LocationManager.swift))

#### 추가된 프로퍼티
```swift
// Timeline tracking
@Published var timelineStartTime: Date?
```

#### `startTracking()` 메서드 수정
```swift
func startTracking() {
    guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
        print("❌ Location permission not granted")
        requestPermission()
        return
    }

    isTracking = true
    timelineStartTime = Date()  // ✅ 시작 시각 기록
    routeCoordinates.removeAll()
    totalDistance = 0.0
    speedHistory.removeAll()
    timestampHistory.removeAll()
    lastLocation = nil

    locationManager.startUpdatingLocation()
    locationManager.startUpdatingHeading()

    print("🟢 GPS tracking started at \(timelineStartTime!)")
}
```

#### `resetTracking()` 메서드 수정
```swift
func resetTracking() {
    routeCoordinates.removeAll()
    totalDistance = 0.0
    speedHistory.removeAll()
    timestampHistory.removeAll()
    healthDataHistory.removeAll()
    lastLocation = nil
    lastUpdateTime = nil
    timelineStartTime = nil  // ✅ 시작 시각 초기화
}
```

### 2. WatchConnectivityManager 수정 ([WatchConnectivityManager.swift](swift_app_demo/space/WatchConnectivityManager.swift))

#### `handleTrackingStatus()` 메서드 완전 재구현
```swift
private func handleTrackingStatus(_ message: [String: Any]) {
    guard let isTracking = message["isTracking"] as? Bool else {
        print("⚠️ Invalid tracking status")
        return
    }

    print("🏃 Tracking status from Watch: \(isTracking ? "Started" : "Stopped")")

    DispatchQueue.main.async {
        let locationManager = LocationManager.shared
        let timelineManager = TimelineManager.shared

        if isTracking {
            // Watch started tracking - start iPhone GPS to mirror Watch state
            if !locationManager.isTracking {
                locationManager.startTracking()
                print("✅ iPhone GPS started to mirror Watch tracking")
            }
        } else {
            // Watch stopped tracking - create and save timeline
            guard let startTime = locationManager.timelineStartTime else {
                print("⚠️ No timeline start time recorded, skipping timeline save")
                if locationManager.isTracking {
                    locationManager.stopTracking()
                }
                return
            }

            // Stop iPhone GPS
            if locationManager.isTracking {
                locationManager.stopTracking()
                print("✅ iPhone GPS stopped to mirror Watch tracking")
            }

            // Generate checkpoints automatically
            let checkpoints = timelineManager.generateCheckpoints(
                coordinates: locationManager.routeCoordinates,
                timestamps: locationManager.timestampHistory,
                healthData: locationManager.healthDataHistory
            )

            // Create timeline record using LocationManager's history
            if let timeline = timelineManager.createTimeline(
                startTime: startTime,
                endTime: Date(),
                coordinates: locationManager.routeCoordinates,
                timestamps: locationManager.timestampHistory,
                speeds: locationManager.speedHistory,
                checkpoints: checkpoints
            ) {
                timelineManager.saveTimeline(timeline)
                print("✅ Timeline saved from Watch session with \(checkpoints.count) checkpoint(s)")
            } else {
                print("⚠️ Failed to create timeline from Watch session")
            }

            // Reset tracking data
            locationManager.resetTracking()
        }
    }
}
```

### 3. TimelineWidget 수정 ([TimelineWidget.swift](swift_app_demo/space/TimelineWidget.swift))

#### LocationManager를 싱글톤으로 변경
```swift
@StateObject private var locationManager = LocationManager.shared  // ✅ singleton 사용
@StateObject private var timelineManager = TimelineManager.shared

@State private var showDetailView = false
// ❌ 제거: @State private var timelineStartTime: Date?
```

#### `startTracking()` 메서드 간소화
```swift
private func startTracking() {
    locationManager.startTracking()  // ✅ LocationManager가 timelineStartTime 관리
}
```

#### `stopTracking()` 메서드 수정
```swift
private func stopTracking() {
    guard let startTime = locationManager.timelineStartTime else {  // ✅ LocationManager에서 가져옴
        print("⚠️ No timeline start time recorded")
        return
    }

    locationManager.stopTracking()

    // Generate checkpoints automatically
    let checkpoints = timelineManager.generateCheckpoints(
        coordinates: locationManager.routeCoordinates,
        timestamps: locationManager.timestampHistory,
        healthData: locationManager.healthDataHistory
    )

    // Create timeline record using LocationManager's history
    if let timeline = timelineManager.createTimeline(
        startTime: startTime,
        endTime: Date(),
        coordinates: locationManager.routeCoordinates,
        timestamps: locationManager.timestampHistory,
        speeds: locationManager.speedHistory,
        checkpoints: checkpoints
    ) {
        timelineManager.saveTimeline(timeline)
        print("✅ Timeline saved with \(checkpoints.count) checkpoint(s)")
    }

    locationManager.resetTracking()  // ✅ timelineStartTime도 여기서 nil로 초기화
}
```

### 4. TimelineDetailView 수정 ([TimelineDetailView.swift](swift_app_demo/space/TimelineDetailView.swift))

#### Preview 수정
```swift
#Preview {
    TimelineDetailView(
        locationManager: LocationManager.shared,  // ✅ singleton 사용
        isTracking: .constant(false),
        onStartTracking: {},
        onStopTracking: {}
    )
}
```

## 동작 흐름

### Watch에서 기록 시작 시

1. **Watch**: `WatchLocationManager.startTracking()` 호출
2. **Watch**: `WatchConnectivityManager.sendTrackingStatus(isTracking: true)` 호출
3. **iPhone**: `WatchConnectivityManager.handleTrackingStatus()` 수신
4. **iPhone**: `LocationManager.shared.startTracking()` 호출
5. **iPhone**: `timelineStartTime = Date()` 설정 ✅

### Watch에서 기록 종료 시

1. **Watch**: `WatchLocationManager.stopTracking()` 호출
2. **Watch**: GPS 좌표 + 헬스 데이터를 iPhone으로 전송
3. **Watch**: `WatchConnectivityManager.sendTrackingStatus(isTracking: false)` 호출
4. **iPhone**: `WatchConnectivityManager.handleTrackingStatus()` 수신
5. **iPhone**: `timelineStartTime` 확인 ✅
6. **iPhone**: `LocationManager.stopTracking()` 호출
7. **iPhone**: `TimelineManager.generateCheckpoints()` 호출 ✅
8. **iPhone**: `TimelineManager.createTimeline()` 호출 ✅
9. **iPhone**: `TimelineManager.saveTimeline()` 호출 ✅
10. **iPhone**: `LocationManager.resetTracking()` 호출 (데이터 정리) ✅

### iPhone에서 직접 기록 시작/종료

1. 사용자가 TimelineWidget 또는 TimelineDetailView에서 "기록 시작" 버튼 클릭
2. `onStartTracking` 클로저 실행 → `LocationManager.startTracking()` 호출
3. `timelineStartTime = Date()` 설정 ✅
4. 사용자가 "중지" 버튼 클릭
5. `onStopTracking` 클로저 실행 → 타임라인 생성/저장 로직 실행 ✅

## 테스트 방법

### 1. Watch 단독 기록 테스트

1. **iPhone과 Watch 모두에서 앱 실행**
2. **Watch에서만 "지도" 뷰로 이동**
3. **Watch에서 "Start Tracking" 버튼 탭**
   - iPhone 로그: `🟢 GPS tracking started at [시각]` 확인
   - Watch 로그: `🏃 Location tracking started on Watch` 확인
4. **잠시 이동 (5-10분)**
   - GPS 좌표가 수집되는지 확인
   - Watch에서 거리/포인트 수 증가 확인
5. **Watch에서 "Stop Tracking" 버튼 탭**
   - Watch 로그: `🛑 Location tracking stopped on Watch` 확인
   - Watch 로그: `📤 Sent X coordinates with health data to iPhone` 확인
   - iPhone 로그: `✅ Timeline saved from Watch session with X checkpoint(s)` 확인
6. **iPhone 앱 열어서 타임라인 위젯 확인**
   - 새로운 타임라인이 표시되는지 확인
   - 거리, 시간, 경로가 올바른지 확인

### 2. iPhone 직접 기록 테스트

1. **iPhone 앱에서 TimelineWidget 또는 TimelineDetailView 열기**
2. **"기록 시작" 버튼 탭**
   - 로그: `🟢 GPS tracking started at [시각]` 확인
3. **잠시 이동**
4. **"중지" 버튼 탭**
   - 로그: `✅ Timeline saved with X checkpoint(s)` 확인
5. **타임라인이 정상적으로 저장되었는지 확인**

### 3. 동시 추적 테스트

1. **Watch에서 추적 시작**
2. **iPhone 앱도 열어서 실시간 업데이트 확인**
3. **Watch에서 추적 종료**
4. **iPhone에서 타임라인이 자동 저장되는지 확인**

## 주요 변경 사항 체크리스트

- ✅ `LocationManager`에 `timelineStartTime` 프로퍼티 추가
- ✅ `LocationManager.startTracking()`에서 `timelineStartTime` 설정
- ✅ `LocationManager.resetTracking()`에서 `timelineStartTime` 초기화
- ✅ `WatchConnectivityManager.handleTrackingStatus()`에서 타임라인 저장 로직 추가
- ✅ `TimelineWidget`에서 로컬 `timelineStartTime` 상태 제거
- ✅ `TimelineWidget`에서 `LocationManager.shared` 싱글톤 사용
- ✅ `TimelineDetailView` Preview에서 `LocationManager.shared` 사용
- ✅ Watch 추적 종료 시 체크포인트 자동 생성
- ✅ Watch 추적 종료 시 타임라인 자동 저장
- ✅ Watch 추적 종료 후 데이터 초기화 (메모리 누수 방지)

## 기대 효과

1. **Watch 단독 기록 완전 지원**: Watch에서만 기록해도 iPhone에 타임라인이 자동 생성됩니다.
2. **데이터 유실 방지**: 추적 종료 시 즉시 타임라인으로 저장되므로 데이터가 유실되지 않습니다.
3. **일관된 상태 관리**: `LocationManager`에서 `timelineStartTime`을 중앙 관리하여 어디서든 접근 가능합니다.
4. **iPhone UI 정상 동작**: Watch 시작 세션도 iPhone에서 "중지" 버튼으로 제어 가능합니다.

## 빌드 상태

```
** BUILD SUCCEEDED **
```

모든 파일이 정상적으로 컴파일되며, 경고는 기존 코드의 사용하지 않는 변수에 대한 것으로 이번 수정과 무관합니다.
