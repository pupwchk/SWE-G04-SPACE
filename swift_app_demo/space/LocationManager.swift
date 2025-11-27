//
//  LocationManager.swift
//  space
//
//  GPS tracking manager using CoreLocation
//

import Foundation
import CoreLocation
import Combine
import UserNotifications

/// GPS tracking manager for routine recording
class LocationManager: NSObject, ObservableObject {
    // MARK: - Singleton

    static let shared = LocationManager()

    // MARK: - Published Properties

    @Published var location: CLLocation?
    @Published var isTracking = false
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined

    // Current tracking data
    @Published var currentLatitude: Double = 0.0
    @Published var currentLongitude: Double = 0.0
    @Published var currentAltitude: Double = 0.0
    @Published var currentSpeed: Double = 0.0 // km/h
    @Published var currentHeading: Double = 0.0
    @Published var horizontalAccuracy: Double = 0.0
    @Published var verticalAccuracy: Double = 0.0
    @Published var lastUpdateTime: Date?

    // Tracking history
    @Published var routeCoordinates: [CLLocationCoordinate2D] = []
    @Published var coordinates: [CLLocationCoordinate2D] = [] // Alias for WatchConnectivity compatibility
    @Published var totalDistance: Double = 0.0 // meters
    @Published var speedHistory: [Double] = []
    @Published var timestampHistory: [Date] = []
    @Published var timestamps: [Date] = [] // Alias for WatchConnectivity compatibility

    // Health data history (synchronized with GPS data)
    @Published var healthDataHistory: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)] = []
    @Published var liveCheckpoints: [Checkpoint] = []

    // Timeline tracking
    @Published var timelineStartTime: Date?

    // MARK: - Private Properties

    private let locationManager = CLLocationManager()
    private var lastRecordedLocation: CLLocation?
    private var smoothingBuffer: [CLLocationCoordinate2D] = []
    private let smoothingWindowSize = 4
    private let maxAllowedHorizontalAccuracy: CLLocationAccuracy = 100
    private let maxReasonableSpeed: CLLocationSpeed = 50 // m/s (~180 km/h) – relaxed to avoid over-filtering
    private let minMovementDistance: CLLocationDistance = 1

    // Live checkpoint detection state
    private var lastCheckpointDate: Date?
    private var lastHRVForCheckpoint: Double?
    private var lastHRVCheckpointTime: Date?
    private var stayAnchorLocation: CLLocation?
    private var stayAnchorDate: Date?
    private var stayCheckpointIssued = false

    private let hrvChangeThreshold: Double = 15 // ms
    private let hrvPercentThreshold: Double = 0.2 // 20% change
    private let minTimeBetweenHRVCheckpoints: TimeInterval = 180 // seconds
    private let stayRadius: CLLocationDistance = 15
    private let minStayDuration: TimeInterval = 5 * 60 // 5 minutes
    private let fallbackCheckpointInterval: TimeInterval = 10 * 60 // 10 minutes

    // MARK: - Initialization

    override init() {
        super.init()
        setupLocationManager()
    }

    // MARK: - Setup

    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        locationManager.distanceFilter = kCLDistanceFilterNone // 가장 세밀하게 수신
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.showsBackgroundLocationIndicator = true
        locationManager.pausesLocationUpdatesAutomatically = false // 끊김 없이 계속 받기

        authorizationStatus = locationManager.authorizationStatus
    }

    // MARK: - Public Methods

    /// Request location permission
    func requestPermission() {
        // 앱 내부에서 바로 Always 권한까지 요청해 끊김 없이 위치를 받도록 한다
        if authorizationStatus == .authorizedWhenInUse {
            locationManager.requestAlwaysAuthorization()
        } else {
            locationManager.requestAlwaysAuthorization()
        }
    }

    /// Request notification permission for location proximity alerts
    func requestNotificationPermission() {
        Task {
            do {
                let granted = try await UNUserNotificationCenter.current().requestAuthorization(
                    options: [.alert, .sound, .badge]
                )
                if granted {
                    print(" Notification permission granted")
                } else {
                    print("⚠️ Notification permission denied")
                }
            } catch {
                print("  Failed to request notification permission: \(error)")
            }
        }
    }

    /// Start tracking GPS
    func startTracking() {
        guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
            print("  Location permission not granted")
            requestPermission()
            return
        }

        // 백그라운드에서도 계속 위치를 받을 수 있도록 Always 승격 시도
        if authorizationStatus == .authorizedWhenInUse {
            locationManager.requestAlwaysAuthorization()
        }

        isTracking = true
        timelineStartTime = Date()
        lastCheckpointDate = timelineStartTime
        routeCoordinates.removeAll()
        totalDistance = 0.0
        speedHistory.removeAll()
        timestampHistory.removeAll()
        lastRecordedLocation = nil
        smoothingBuffer.removeAll()
        liveCheckpoints.removeAll()
        lastHRVForCheckpoint = nil
        lastHRVCheckpointTime = nil
        stayAnchorLocation = nil
        stayAnchorDate = nil
        stayCheckpointIssued = false

        locationManager.startUpdatingLocation()
        locationManager.startUpdatingHeading()

        print("🟢 GPS tracking started at \(timelineStartTime!)")
    }

    /// Stop tracking GPS
    func stopTracking() {
        isTracking = false
        locationManager.stopUpdatingLocation()
        locationManager.stopUpdatingHeading()

        print("🔴 GPS tracking stopped")
    }

    /// Reset tracking data
    func resetTracking() {
        routeCoordinates.removeAll()
        totalDistance = 0.0
        speedHistory.removeAll()
        timestampHistory.removeAll()
        healthDataHistory.removeAll()
        lastRecordedLocation = nil
        smoothingBuffer.removeAll()
        lastUpdateTime = nil
        timelineStartTime = nil
        liveCheckpoints.removeAll()
        lastCheckpointDate = nil
        lastHRVForCheckpoint = nil
        lastHRVCheckpointTime = nil
        stayAnchorLocation = nil
        stayAnchorDate = nil
        stayCheckpointIssued = false
    }
}

// MARK: - CLLocationManagerDelegate

extension LocationManager: CLLocationManagerDelegate {
    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus

        switch authorizationStatus {
        case .notDetermined:
            print("📍 Location permission: Not Determined")
        case .restricted:
            print("📍 Location permission: Restricted")
        case .denied:
            print("📍 Location permission: Denied")
        case .authorizedAlways:
            print("📍 Location permission: Authorized Always")
        case .authorizedWhenInUse:
            print("📍 Location permission: Authorized When In Use")
        @unknown default:
            print("📍 Location permission: Unknown")
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let newLocation = locations.last else { return }

        location = newLocation

        // Update current values
        currentLatitude = newLocation.coordinate.latitude
        currentLongitude = newLocation.coordinate.longitude
        currentAltitude = newLocation.altitude
        currentSpeed = max(0, newLocation.speed * 3.6) // m/s to km/h
        horizontalAccuracy = newLocation.horizontalAccuracy
        verticalAccuracy = newLocation.verticalAccuracy
        lastUpdateTime = newLocation.timestamp

        // Calculate distance if tracking
        if isTracking {
            guard shouldRecord(newLocation) else { return }

            let smoothedCoordinate = smoothedCoordinate(from: newLocation.coordinate)
            let smoothedLocation = CLLocation(
                coordinate: smoothedCoordinate,
                altitude: newLocation.altitude,
                horizontalAccuracy: newLocation.horizontalAccuracy,
                verticalAccuracy: newLocation.verticalAccuracy,
                course: newLocation.course,
                speed: newLocation.speed,
                timestamp: newLocation.timestamp
            )

            routeCoordinates.append(smoothedCoordinate)
            speedHistory.append(currentSpeed)
            timestampHistory.append(newLocation.timestamp)

            // Collect current health data from HealthKitManager
            let healthManager = HealthKitManager.shared
            let healthData = (
                heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
                calories: healthManager.currentCalories > 0 ? healthManager.currentCalories : nil,
                steps: healthManager.currentSteps > 0 ? healthManager.currentSteps : nil,
                distance: healthManager.currentDistance > 0 ? healthManager.currentDistance : nil
            )
            healthDataHistory.append(healthData)

            if let previous = lastRecordedLocation {
                let distance = smoothedLocation.distance(from: previous)
                totalDistance += distance
            }

            lastRecordedLocation = smoothedLocation
            evaluateCheckpoints(with: smoothedLocation)
        }

        // Always check proximity to tagged locations for home notifications
        checkTaggedLocationProximity(at: newLocation)

        // Reduced console logging - only log significant updates
        #if DEBUG
        if Int(Date().timeIntervalSince1970) % 10 == 0 { // Log every ~10 seconds
            print("""
            📍 위치 업데이트:
            - 위도: \(String(format: "%.6f", currentLatitude))
            - 경도: \(String(format: "%.6f", currentLongitude))
            - 속도: \(String(format: "%.1f", currentSpeed)) km/h
            - 정확도: ±\(String(format: "%.1f", horizontalAccuracy))m
            """)
            if isTracking {
                print("- 총 거리: \(String(format: "%.2f", totalDistance / 1000)) km")
            }
        }
        #endif
    }

    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        if newHeading.headingAccuracy >= 0 {
            currentHeading = newHeading.trueHeading

            #if DEBUG
            // Only log occasionally to reduce console spam
            if Int(Date().timeIntervalSince1970) % 30 == 0 {
                print("🧭 방위: \(String(format: "%.1f", newHeading.trueHeading))°")
            }
            #endif
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("  Location error: \(error.localizedDescription)")
    }

    // MARK: - Live Checkpoints

    /// Evaluate conditions to create live checkpoints (HRV jumps, long stays, periodic fallback)
    private func evaluateCheckpoints(with location: CLLocation) {
        let timestamp = location.timestamp
        evaluateHRVChange(at: location.coordinate, timestamp: timestamp)
        evaluateStay(at: location)
        evaluateFallback(at: location)
    }

    /// Create checkpoint if HRV changed significantly
    private func evaluateHRVChange(at coordinate: CLLocationCoordinate2D, timestamp: Date) {
        let currentHRV = HealthKitManager.shared.currentHRV
        guard currentHRV > 0 else { return }

        if let lastHRV = lastHRVForCheckpoint {
            let diff = currentHRV - lastHRV
            let absDiff = abs(diff)
            let percentDiff = absDiff / max(lastHRV, 1)

            let timeSinceLastHRVCheckpoint = timestamp.timeIntervalSince(lastHRVCheckpointTime ?? .distantPast)
            guard timeSinceLastHRVCheckpoint >= minTimeBetweenHRVCheckpoints else { return }

            if absDiff >= hrvChangeThreshold || percentDiff >= hrvPercentThreshold {
                let direction = diff >= 0 ? "▲" : "▼"
                let stressChange: StressChange = diff >= 0 ? .decreased : .increased
                let note = "HRV \(direction)\(String(format: "%.0f", absDiff))ms (\(String(format: "%.0f", lastHRV)) → \(String(format: "%.0f", currentHRV)))"

                recordCheckpoint(
                    coordinate: coordinate,
                    timestamp: timestamp,
                    stayDuration: 0,
                    mood: .neutral,
                    stressChange: stressChange,
                    note: note
                )

                lastHRVForCheckpoint = currentHRV
                lastHRVCheckpointTime = timestamp
            }
        } else {
            lastHRVForCheckpoint = currentHRV
        }
    }

    /// Create checkpoint when user stays within a small radius for 5+ minutes
    private func evaluateStay(at location: CLLocation) {
        if let anchor = stayAnchorLocation {
            let distance = location.distance(from: anchor)
            if distance <= stayRadius {
                if !stayCheckpointIssued, let startDate = stayAnchorDate {
                    let duration = location.timestamp.timeIntervalSince(startDate)
                    if duration >= minStayDuration {
                        recordCheckpoint(
                            coordinate: location.coordinate,
                            timestamp: location.timestamp,
                            stayDuration: duration,
                            mood: .neutral,
                            stressChange: .unchanged,
                            note: "정지 \(Int(duration / 60))분"
                        )
                        stayCheckpointIssued = true
                    }
                }
            } else {
                // User moved away; reset stay tracking
                stayAnchorLocation = location
                stayAnchorDate = location.timestamp
                stayCheckpointIssued = false
            }
        } else {
            stayAnchorLocation = location
            stayAnchorDate = location.timestamp
            stayCheckpointIssued = false
        }
    }

    /// Fallback: create a checkpoint every 10 minutes if nothing else fired
    private func evaluateFallback(at location: CLLocation) {
        guard let start = timelineStartTime else { return }
        let lastTime = lastCheckpointDate ?? start
        if location.timestamp.timeIntervalSince(lastTime) >= fallbackCheckpointInterval {
            recordCheckpoint(
                coordinate: location.coordinate,
                timestamp: location.timestamp,
                stayDuration: 0,
                mood: .neutral,
                stressChange: .unchanged,
                note: "주기 체크포인트"
            )
        }
    }

    /// Create and store a checkpoint with current health data
    private func recordCheckpoint(
        coordinate: CLLocationCoordinate2D,
        timestamp: Date,
        stayDuration: TimeInterval,
        mood: CheckpointMood,
        stressChange: StressChange,
        note: String?
    ) {
        let healthManager = HealthKitManager.shared

        let checkpoint = Checkpoint(
            coordinate: CoordinateData(coordinate: coordinate, timestamp: timestamp),
            mood: mood,
            stayDuration: stayDuration,
            stressChange: stressChange,
            note: note,
            timestamp: timestamp,
            heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
            calories: healthManager.currentCalories > 0 ? healthManager.currentCalories : nil,
            steps: healthManager.currentSteps > 0 ? healthManager.currentSteps : nil,
            distance: healthManager.currentDistance > 0 ? healthManager.currentDistance : nil,
            hrv: healthManager.currentHRV > 0 ? healthManager.currentHRV : nil,
            stressLevel: healthManager.stressLevel > 0 ? healthManager.stressLevel : nil
        )

        liveCheckpoints.append(checkpoint)
        lastCheckpointDate = timestamp
    }

    // MARK: - Smoothing Helpers

    /// Filter out noisy updates and unrealistic jumps to keep the route smooth
    private func shouldRecord(_ newLocation: CLLocation) -> Bool {
        guard newLocation.horizontalAccuracy >= 0,
              newLocation.horizontalAccuracy <= maxAllowedHorizontalAccuracy else {
            return false
        }

        if let previous = lastRecordedLocation {
            let timeDelta = newLocation.timestamp.timeIntervalSince(previous.timestamp)
            if timeDelta <= 0 { return false }

            let distance = newLocation.distance(from: previous)
            let speed = distance / timeDelta

            if speed > maxReasonableSpeed { return false }
        }

        return true
    }

    /// Apply a simple moving average to reduce zig-zags in the drawn polyline
    private func smoothedCoordinate(from coordinate: CLLocationCoordinate2D) -> CLLocationCoordinate2D {
        smoothingBuffer.append(coordinate)
        if smoothingBuffer.count > smoothingWindowSize {
            smoothingBuffer.removeFirst()
        }

        let averageLatitude = smoothingBuffer.map { $0.latitude }.reduce(0, +) / Double(smoothingBuffer.count)
        let averageLongitude = smoothingBuffer.map { $0.longitude }.reduce(0, +) / Double(smoothingBuffer.count)

        return CLLocationCoordinate2D(latitude: averageLatitude, longitude: averageLongitude)
    }

    // MARK: - Tagged Location Proximity Detection

    /// Check proximity to tagged locations and send notifications if needed
    private func checkTaggedLocationProximity(at location: CLLocation) {
        // Check if location notifications are enabled
        let notificationsEnabled = UserDefaults.standard.bool(forKey: "locationNotificationsEnabled")
        guard notificationsEnabled else {
            return
        }

        Task { @MainActor in
            let tagManager = TaggedLocationManager.shared
            let nearbyLocations = tagManager.checkProximity(to: location)

            for (taggedLocation, distance) in nearbyLocations {
                // Check if we should send notification
                guard tagManager.shouldSendNotification(for: taggedLocation) else {
                    continue
                }

                // Send notification
                await sendLocationProximityNotification(
                    for: taggedLocation,
                    distance: distance
                )

                // Record notification
                await tagManager.recordNotification(
                    for: taggedLocation,
                    distance: distance
                )
            }
        }
    }

    /// Send local notification for location proximity
    private func sendLocationProximityNotification(
        for location: TaggedLocation,
        distance: CLLocationDistance
    ) async {
        let content = UNMutableNotificationContent()

        // Customize message based on whether it's a home location
        if location.isHome {
            content.title = "\(location.tag.icon) 집에 다가오고 있습니다"

            // Different messages based on distance
            if distance < 100 {
                content.body = "거의 도착했습니다!"
            } else if distance < 500 {
                content.body = String(format: "약 %.0fm 남았습니다", distance)
            } else {
                content.body = String(format: "%.1fkm 거리에 있습니다", distance / 1000)
            }
        } else {
            content.title = "\(location.tag.icon) \(location.displayName) 근처"
            content.body = String(format: "%.0fm 거리에 도착했습니다", distance)
        }

        content.sound = .default
        content.badge = 1

        // Add user info for deep linking
        content.userInfo = [
            "type": "location_proximity",
            "location_id": location.id.uuidString,
            "location_name": location.displayName,
            "is_home": location.isHome
        ]

        let request = UNNotificationRequest(
            identifier: "location_\(location.id.uuidString)",
            content: content,
            trigger: nil // Immediate delivery
        )

        do {
            try await UNUserNotificationCenter.current().add(request)
            print("📍 Sent proximity notification for \(location.fullDisplayName) at \(String(format: "%.0fm", distance))")
        } catch {
            print("  Failed to send notification: \(error)")
        }
    }
}
