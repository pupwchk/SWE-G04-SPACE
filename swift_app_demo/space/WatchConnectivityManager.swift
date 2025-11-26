//
//  WatchConnectivityManager.swift
//  space
//
//  WatchConnectivity manager for iOS ↔ Watch communication
//

import Foundation
import WatchConnectivity
import Combine
import CoreLocation

/// Manager for WatchConnectivity session (iOS ↔ Watch communication)
class WatchConnectivityManager: NSObject, ObservableObject {
    static let shared = WatchConnectivityManager()

    // MARK: - Published Properties

    @Published var isWatchPaired: Bool = false
    @Published var isWatchReachable: Bool = false
    @Published var isSessionActivated: Bool = false

    // MARK: - Private Properties

    private var session: WCSession?
    private var messageQueue: [[String: Any]] = []

    // MARK: - Initialization

    private override init() {
        super.init()

        if WCSession.isSupported() {
            session = WCSession.default
            session?.delegate = self
            session?.activate()
            print("📱 WatchConnectivity session initialized")
        } else {
            print("❌ WatchConnectivity not supported on this device")
        }
    }

    // MARK: - Send Messages

    /// Send message to Watch (requires Watch to be reachable)
    func sendMessage(_ message: [String: Any], replyHandler: (([String: Any]) -> Void)? = nil, errorHandler: ((Error) -> Void)? = nil) {
        guard let session = session, session.isReachable else {
            print("⚠️ Watch not reachable, queueing message")
            messageQueue.append(message)
            errorHandler?(WatchConnectivityError.notReachable)
            return
        }

        session.sendMessage(message, replyHandler: replyHandler, errorHandler: { error in
            print("❌ Failed to send message: \(error.localizedDescription)")
            errorHandler?(error)
        })

        print("📤 Message sent to Watch: \(message.keys.joined(separator: ", "))")
    }

    /// Transfer user info to Watch (background transfer, queued)
    func transferUserInfo(_ userInfo: [String: Any]) {
        guard let session = session else {
            print("❌ WCSession not available")
            return
        }

        session.transferUserInfo(userInfo)
        print("📤 User info transferred to Watch: \(userInfo.keys.joined(separator: ", "))")
    }

    /// Update application context (latest state only, overwrites previous)
    func updateApplicationContext(_ context: [String: Any]) {
        guard let session = session else {
            print("❌ WCSession not available")
            return
        }

        do {
            try session.updateApplicationContext(context)
            print("📤 Application context updated: \(context.keys.joined(separator: ", "))")
        } catch {
            print("❌ Failed to update application context: \(error.localizedDescription)")
        }
    }

    // MARK: - Send Specific Data

    /// Send location update to Watch
    func sendLocationUpdate(coordinates: [[String: Any]], timestamp: Date) {
        let message: [String: Any] = [
            "type": "locationUpdate",
            "coordinates": coordinates,
            "timestamp": timestamp.timeIntervalSince1970
        ]

        transferUserInfo(message)
    }

    /// Send checkpoint to Watch
    func sendCheckpoint(checkpoint: [String: Any]) {
        let message: [String: Any] = [
            "type": "checkpoint",
            "data": checkpoint
        ]

        sendMessage(message)
    }

    /// Send tracking command (start/stop)
    func sendTrackingCommand(isTracking: Bool) {
        let message: [String: Any] = [
            "type": "trackingCommand",
            "isTracking": isTracking
        ]

        updateApplicationContext(message)
    }

    /// Send authentication status to Watch
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

        // Use updateApplicationContext for persistent state
        updateApplicationContext(message)
        print("📱 Authentication status sent to Watch: \(isAuthenticated)")
    }

    // MARK: - Process Queue

    /// Process queued messages when Watch becomes reachable
    private func processMessageQueue() {
        guard !messageQueue.isEmpty, let session = session, session.isReachable else {
            return
        }

        print("📤 Processing \(messageQueue.count) queued messages")

        for message in messageQueue {
            sendMessage(message)
        }

        messageQueue.removeAll()
    }
}

// MARK: - WCSessionDelegate

extension WatchConnectivityManager: WCSessionDelegate {

    // MARK: - Session State

    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            self.isSessionActivated = (activationState == .activated)

            if let error = error {
                print("❌ Session activation failed: \(error.localizedDescription)")
            } else {
                print("✅ WatchConnectivity session activated: \(activationState.rawValue)")
                self.updateWatchStatus()
            }
        }
    }

    func sessionDidBecomeInactive(_ session: WCSession) {
        print("⚠️ Session became inactive")
        DispatchQueue.main.async {
            self.isSessionActivated = false
        }
    }

    func sessionDidDeactivate(_ session: WCSession) {
        print("⚠️ Session deactivated, reactivating...")
        session.activate()
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        DispatchQueue.main.async {
            self.isWatchReachable = session.isReachable
            print("📡 Watch reachability changed: \(session.isReachable)")

            if session.isReachable {
                self.processMessageQueue()
            }
        }
    }

    // MARK: - Receive Messages

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        print("📥 Message received from Watch: \(message)")

        DispatchQueue.main.async {
            self.handleMessage(message)
        }
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any], replyHandler: @escaping ([String: Any]) -> Void) {
        print("📥 Message received from Watch (with reply): \(message)")

        DispatchQueue.main.async {
            self.handleMessage(message)
            replyHandler(["status": "received"])
        }
    }

    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any] = [:]) {
        print("📥 User info received from Watch: \(userInfo)")

        DispatchQueue.main.async {
            self.handleUserInfo(userInfo)
        }
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        print("📥 Application context received from Watch: \(applicationContext)")

        DispatchQueue.main.async {
            self.handleApplicationContext(applicationContext)
        }
    }

    // MARK: - Message Handlers

    private func handleMessage(_ message: [String: Any]) {
        guard let type = message["type"] as? String else {
            print("⚠️ Message type not specified")
            return
        }

        switch type {
        case "locationUpdate":
            handleLocationUpdate(message)
        case "healthData":
            handleHealthData(message)
        case "checkpoint":
            handleCheckpoint(message)
        case "trackingStatus":
            handleTrackingStatus(message)
        default:
            print("⚠️ Unknown message type: \(type)")
        }
    }

    private func handleUserInfo(_ userInfo: [String: Any]) {
        // Handle background transfers
        handleMessage(userInfo)
    }

    private func handleApplicationContext(_ context: [String: Any]) {
        // Handle application context updates
        handleMessage(context)
    }

    // MARK: - Specific Message Handlers

    private func handleLocationUpdate(_ message: [String: Any]) {
        guard let coordinates = message["coordinates"] as? [[String: Any]] else {
            print("⚠️ Invalid location update data")
            return
        }

        print("📍 Location update received: \(coordinates.count) coordinates from Watch")

        // Convert dictionary coordinates to CLLocationCoordinate2D
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

        // Parse health data from coordinates
        let healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)] = coordinates.map { coordDict in
            (
                heartRate: coordDict["heartRate"] as? Double,
                calories: coordDict["calories"] as? Double,
                steps: coordDict["steps"] as? Int,
                distance: coordDict["healthDistance"] as? Double
            )
        }

        // Calculate speeds from consecutive coordinates
        var speeds: [Double] = []
        for i in 1..<locationCoordinates.count {
            if i < timestamps.count {
                let loc1 = CLLocation(latitude: locationCoordinates[i - 1].latitude, longitude: locationCoordinates[i - 1].longitude)
                let loc2 = CLLocation(latitude: locationCoordinates[i].latitude, longitude: locationCoordinates[i].longitude)

                let distance = loc2.distance(from: loc1) // meters
                let timeInterval = timestamps[i].timeIntervalSince(timestamps[i - 1])
                let speed = timeInterval > 0 ? (distance / timeInterval) * 3.6 : 0 // km/h

                speeds.append(speed)
            }
        }
        // First point has no previous point, so use 0 or the first calculated speed
        if !speeds.isEmpty {
            speeds.insert(speeds.first ?? 0, at: 0)
        }

        // Update LocationManager with Watch coordinates and health data
        DispatchQueue.main.async {
            let locationManager = LocationManager.shared

            // Add coordinates to BOTH arrays (coordinates and routeCoordinates)
            for coordinate in locationCoordinates {
                locationManager.coordinates.append(coordinate)
                locationManager.routeCoordinates.append(coordinate)
            }

            // Add timestamps to BOTH arrays (timestamps and timestampHistory)
            for timestamp in timestamps {
                locationManager.timestamps.append(timestamp)
                locationManager.timestampHistory.append(timestamp)
            }

            // Add speeds to speedHistory
            for speed in speeds {
                locationManager.speedHistory.append(speed)
            }

            // Add health data
            for health in healthData {
                locationManager.healthDataHistory.append(health)
            }

            print("✅ Added \(locationCoordinates.count) coordinates with health data from Watch to LocationManager (both arrays)")
        }
    }

    private func handleHealthData(_ message: [String: Any]) {
        guard let healthData = message["data"] as? [String: Any] else {
            print("⚠️ Invalid health data")
            return
        }

        print("❤️ Health data received from Watch")

        // Extract health metrics
        let heartRate = healthData["heartRate"] as? Double
        let calories = healthData["calories"] as? Double
        let steps = healthData["steps"] as? Int
        let distance = healthData["distance"] as? Double

        // Log received data
        if let hr = heartRate {
            print("  - Heart Rate: \(Int(hr)) bpm")
        }
        if let cal = calories {
            print("  - Calories: \(Int(cal)) kcal")
        }
        if let st = steps {
            print("  - Steps: \(st)")
        }
        if let dist = distance {
            print("  - Distance: \(String(format: "%.2f", dist / 1000)) km")
        }

        // Update HealthKitManager with Watch data
        DispatchQueue.main.async {
            let healthManager = HealthKitManager.shared

            // Store the latest Watch health data
            if let hr = heartRate {
                healthManager.currentHeartRate = hr
                print("✅ Heart rate updated: \(Int(hr)) bpm")
            }
            if let cal = calories {
                healthManager.currentCalories = cal
                print("✅ Calories updated: \(Int(cal)) kcal")
            }
            if let st = steps {
                healthManager.currentSteps = st
                print("✅ Steps updated: \(st)")
            }
            if let dist = distance {
                healthManager.currentDistance = dist
                print("✅ Distance updated: \(String(format: "%.2f", dist / 1000)) km")
            }

            print("✅ Health data integrated into HealthKitManager")
        }
    }

    private func handleCheckpoint(_ message: [String: Any]) {
        guard let checkpointData = message["data"] as? [String: Any] else {
            print("⚠️ Invalid checkpoint data")
            return
        }

        print("📍 Checkpoint received from Watch")

        // Parse checkpoint data according to documentation format
        guard let coordDict = checkpointData["coordinate"] as? [String: Any],
              let latitude = coordDict["latitude"] as? Double,
              let longitude = coordDict["longitude"] as? Double,
              let timestamp = coordDict["timestamp"] as? TimeInterval,
              let moodString = checkpointData["mood"] as? String,
              let mood = CheckpointMood(rawValue: moodString),
              let stayDuration = checkpointData["stayDuration"] as? TimeInterval,
              let stressChangeString = checkpointData["stressChange"] as? String,
              let stressChange = StressChange(rawValue: stressChangeString) else {
            print("⚠️ Failed to parse checkpoint data")
            return
        }

        // Optional fields
        let note = checkpointData["note"] as? String
        let heartRate = checkpointData["heartRate"] as? Double
        let calories = checkpointData["calories"] as? Double
        let steps = checkpointData["steps"] as? Int
        let distance = checkpointData["distance"] as? Double
        let hrv = checkpointData["hrv"] as? Double
        let stressLevel = checkpointData["stressLevel"] as? Int

        // Create CoordinateData
        let coordinate = CoordinateData(
            coordinate: CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
            timestamp: Date(timeIntervalSince1970: timestamp)
        )

        // Create Checkpoint
        let checkpoint = Checkpoint(
            coordinate: coordinate,
            mood: mood,
            stayDuration: stayDuration,
            stressChange: stressChange,
            note: note,
            timestamp: Date(timeIntervalSince1970: timestamp),
            heartRate: heartRate,
            calories: calories,
            steps: steps,
            distance: distance,
            hrv: hrv,
            stressLevel: stressLevel
        )

        // Add checkpoint to the current timeline or queue it for next timeline
        DispatchQueue.main.async {
            let timelineManager = TimelineManager.shared

            if let currentTimeline = timelineManager.currentTimeline {
                // Add to existing current timeline
                timelineManager.addCheckpoint(to: currentTimeline.id, checkpoint: checkpoint)
                print("✅ Checkpoint added to current timeline from Watch")
            } else if let latestTimeline = timelineManager.timelines.first {
                // Add to the most recent timeline if no current timeline
                timelineManager.addCheckpoint(to: latestTimeline.id, checkpoint: checkpoint)
                print("✅ Checkpoint added to latest timeline from Watch")
            } else {
                print("⚠️ No timeline available to add checkpoint")
            }
        }
    }

    private func handleTrackingStatus(_ message: [String: Any]) {
        guard let isTracking = message["isTracking"] as? Bool else {
            print("⚠️ Invalid tracking status")
            return
        }

        print("🏃 Tracking status from Watch: \(isTracking ? "Started" : "Stopped")")

        // Update iPhone's LocationManager to reflect Watch tracking state
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

    // MARK: - Watch Status

    private func updateWatchStatus() {
        guard let session = session else { return }

        isWatchPaired = session.isPaired
        isWatchReachable = session.isReachable

        print("""
        📱 Watch Status:
        - Paired: \(session.isPaired)
        - Reachable: \(session.isReachable)
        - Watch App Installed: \(session.isWatchAppInstalled)
        """)
    }
}

// MARK: - Errors

enum WatchConnectivityError: Error {
    case notReachable
    case sessionNotActivated
    case invalidData

    var localizedDescription: String {
        switch self {
        case .notReachable:
            return "Watch is not reachable"
        case .sessionNotActivated:
            return "WatchConnectivity session is not activated"
        case .invalidData:
            return "Invalid data format"
        }
    }
}
