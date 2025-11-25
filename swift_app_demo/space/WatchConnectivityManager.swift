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

        // Update LocationManager with Watch coordinates
        DispatchQueue.main.async {
            let locationManager = LocationManager.shared

            // Add coordinates to existing route
            for coordinate in locationCoordinates {
                locationManager.coordinates.append(coordinate)
            }

            // Add timestamps
            for timestamp in timestamps {
                locationManager.timestamps.append(timestamp)
            }

            print("✅ Added \(locationCoordinates.count) coordinates from Watch to LocationManager")
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

        // TODO: Add checkpoint to current timeline
        // This will be implemented in Phase 7
    }

    private func handleTrackingStatus(_ message: [String: Any]) {
        guard let isTracking = message["isTracking"] as? Bool else {
            print("⚠️ Invalid tracking status")
            return
        }

        print("🏃 Tracking status from Watch: \(isTracking ? "Started" : "Stopped")")

        // TODO: Update LocationManager tracking status
        // This will be implemented in Phase 4
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
