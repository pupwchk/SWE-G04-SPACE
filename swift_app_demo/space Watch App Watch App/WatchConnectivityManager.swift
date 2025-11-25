//
//  WatchConnectivityManager.swift
//  space Watch App
//
//  WatchConnectivity manager for Watch ↔ iPhone communication
//

import Foundation
import WatchConnectivity
import Combine

/// Manager for WatchConnectivity session (Watch ↔ iPhone communication)
class WatchConnectivityManager: NSObject, ObservableObject {
    static let shared = WatchConnectivityManager()

    // MARK: - Published Properties

    @Published var isPhoneReachable: Bool = false
    @Published var isSessionActivated: Bool = false
    @Published var isTracking: Bool = false
    @Published var isAuthenticated: Bool = false
    @Published var userId: String?
    @Published var userEmail: String?

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
            print("⌚ WatchConnectivity session initialized")
        } else {
            print("❌ WatchConnectivity not supported on this device")
        }
    }

    // MARK: - Send Messages

    /// Send message to iPhone (requires iPhone to be reachable)
    func sendMessage(_ message: [String: Any], replyHandler: (([String: Any]) -> Void)? = nil, errorHandler: ((Error) -> Void)? = nil) {
        guard let session = session, session.isReachable else {
            print("⚠️ iPhone not reachable, queueing message")
            messageQueue.append(message)
            errorHandler?(WatchConnectivityError.notReachable)
            return
        }

        session.sendMessage(message, replyHandler: replyHandler, errorHandler: { error in
            print("❌ Failed to send message: \(error.localizedDescription)")
            errorHandler?(error)
        })

        print("📤 Message sent to iPhone: \(message.keys.joined(separator: ", "))")
    }

    /// Transfer user info to iPhone (background transfer, queued)
    func transferUserInfo(_ userInfo: [String: Any]) {
        guard let session = session else {
            print("❌ WCSession not available")
            return
        }

        session.transferUserInfo(userInfo)
        print("📤 User info transferred to iPhone: \(userInfo.keys.joined(separator: ", "))")
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

    /// Send location update to iPhone
    func sendLocationUpdate(coordinates: [[String: Any]], timestamp: Date) {
        let message: [String: Any] = [
            "type": "locationUpdate",
            "coordinates": coordinates,
            "timestamp": timestamp.timeIntervalSince1970
        ]

        transferUserInfo(message)
    }

    /// Send health data to iPhone
    func sendHealthData(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?) {
        var healthData: [String: Any] = [:]

        if let heartRate = heartRate {
            healthData["heartRate"] = heartRate
        }
        if let calories = calories {
            healthData["calories"] = calories
        }
        if let steps = steps {
            healthData["steps"] = steps
        }
        if let distance = distance {
            healthData["distance"] = distance
        }

        let message: [String: Any] = [
            "type": "healthData",
            "data": healthData,
            "timestamp": Date().timeIntervalSince1970
        ]

        transferUserInfo(message)
    }

    /// Send checkpoint to iPhone
    func sendCheckpoint(checkpoint: [String: Any]) {
        let message: [String: Any] = [
            "type": "checkpoint",
            "data": checkpoint
        ]

        sendMessage(message)
    }

    /// Send tracking status to iPhone
    func sendTrackingStatus(isTracking: Bool) {
        let message: [String: Any] = [
            "type": "trackingStatus",
            "isTracking": isTracking
        ]

        updateApplicationContext(message)

        DispatchQueue.main.async {
            self.isTracking = isTracking
        }
    }

    // MARK: - Process Queue

    /// Process queued messages when iPhone becomes reachable
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
                self.updatePhoneStatus()
            }
        }
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        DispatchQueue.main.async {
            self.isPhoneReachable = session.isReachable
            print("📡 iPhone reachability changed: \(session.isReachable)")

            if session.isReachable {
                self.processMessageQueue()
            }
        }
    }

    // MARK: - Receive Messages

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        print("📥 Message received from iPhone: \(message)")

        DispatchQueue.main.async {
            self.handleMessage(message)
        }
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any], replyHandler: @escaping ([String: Any]) -> Void) {
        print("📥 Message received from iPhone (with reply): \(message)")

        DispatchQueue.main.async {
            self.handleMessage(message)
            replyHandler(["status": "received"])
        }
    }

    func session(_ session: WCSession, didReceiveUserInfo userInfo: [String: Any] = [:]) {
        print("📥 User info received from iPhone: \(userInfo)")

        DispatchQueue.main.async {
            self.handleUserInfo(userInfo)
        }
    }

    func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        print("📥 Application context received from iPhone: \(applicationContext)")

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
        case "trackingCommand":
            handleTrackingCommand(message)
        case "timelineRequest":
            handleTimelineRequest(message)
        case "checkpoint":
            handleCheckpoint(message)
        case "authentication":
            handleAuthentication(message)
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

    private func handleTrackingCommand(_ message: [String: Any]) {
        guard let isTracking = message["isTracking"] as? Bool else {
            print("⚠️ Invalid tracking command")
            return
        }

        print("🏃 Tracking command from iPhone: \(isTracking ? "Start" : "Stop")")

        DispatchQueue.main.async {
            self.isTracking = isTracking
        }

        // TODO: Update WatchLocationManager tracking status
        // This will be implemented in Phase 4
    }

    private func handleTimelineRequest(_ message: [String: Any]) {
        guard let timelineId = message["timelineId"] as? String else {
            print("⚠️ Invalid timeline request")
            return
        }

        print("📍 Timeline request from iPhone: \(timelineId)")

        // TODO: Load and send timeline data
        // This will be implemented in Phase 4
    }

    private func handleCheckpoint(_ message: [String: Any]) {
        guard let checkpointData = message["data"] as? [String: Any] else {
            print("⚠️ Invalid checkpoint data")
            return
        }

        print("📍 Checkpoint received from iPhone")

        // TODO: Display checkpoint on Watch map
        // This will be implemented in Phase 7
    }

    private func handleAuthentication(_ message: [String: Any]) {
        guard let isAuthenticated = message["isAuthenticated"] as? Bool else {
            print("⚠️ Invalid authentication message")
            return
        }

        let userId = message["userId"] as? String
        let userEmail = message["userEmail"] as? String

        DispatchQueue.main.async {
            self.isAuthenticated = isAuthenticated
            self.userId = userId
            self.userEmail = userEmail

            print("🔐 Authentication status updated: \(isAuthenticated)")
            if isAuthenticated, let email = userEmail {
                print("👤 Logged in as: \(email)")
            } else {
                print("👤 Logged out")
            }
        }
    }

    // MARK: - Phone Status

    private func updatePhoneStatus() {
        guard let session = session else { return }

        isPhoneReachable = session.isReachable

        print("""
        ⌚ iPhone Status:
        - Reachable: \(session.isReachable)
        - Activation State: \(session.activationState.rawValue)
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
            return "iPhone is not reachable"
        case .sessionNotActivated:
            return "WatchConnectivity session is not activated"
        case .invalidData:
            return "Invalid data format"
        }
    }
}
