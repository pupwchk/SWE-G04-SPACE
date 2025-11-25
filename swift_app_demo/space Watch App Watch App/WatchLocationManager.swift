//
//  WatchLocationManager.swift
//  space Watch App
//
//  Location manager for Apple Watch GPS tracking
//

import Foundation
import CoreLocation
import Combine

/// Location manager for Apple Watch GPS tracking
class WatchLocationManager: NSObject, ObservableObject {
    static let shared = WatchLocationManager()

    // MARK: - Published Properties

    @Published var location: CLLocation?
    @Published var isTracking: Bool = false
    @Published var coordinates: [CLLocationCoordinate2D] = []
    @Published var timestamps: [Date] = []
    @Published var speeds: [Double] = []
    @Published var totalDistance: Double = 0.0 // meters
    @Published var currentSpeed: Double = 0.0 // km/h
    @Published var accuracy: Double = 0.0 // meters
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined

    // MARK: - Private Properties

    private let locationManager = CLLocationManager()
    private var startTime: Date?
    private var lastLocation: CLLocation?

    // MARK: - Initialization

    private override init() {
        super.init()
        setupLocationManager()
    }

    // MARK: - Setup

    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        locationManager.distanceFilter = 5.0 // Update every 5 meters
        locationManager.activityType = .fitness
        locationManager.allowsBackgroundLocationUpdates = true

        authorizationStatus = locationManager.authorizationStatus
        print("⌚ WatchLocationManager initialized")
    }

    // MARK: - Authorization

    func requestAuthorization() {
        locationManager.requestWhenInUseAuthorization()
        print("⌚ Requesting location authorization")
    }

    // MARK: - Tracking Control

    func startTracking() {
        guard !isTracking else {
            print("⚠️ Already tracking")
            return
        }

        // Reset data
        coordinates.removeAll()
        timestamps.removeAll()
        speeds.removeAll()
        totalDistance = 0.0
        lastLocation = nil
        startTime = Date()

        // Start location updates
        locationManager.startUpdatingLocation()
        isTracking = true

        // Notify WatchConnectivityManager
        WatchConnectivityManager.shared.sendTrackingStatus(isTracking: true)

        print("🏃 Location tracking started on Watch")
    }

    func stopTracking() {
        guard isTracking else {
            print("⚠️ Not tracking")
            return
        }

        locationManager.stopUpdatingLocation()
        isTracking = false

        // Notify WatchConnectivityManager
        WatchConnectivityManager.shared.sendTrackingStatus(isTracking: false)

        // Send final location data to iPhone
        sendLocationDataToiPhone()

        print("🛑 Location tracking stopped on Watch")
        print("📊 Tracked \(coordinates.count) points, \(String(format: "%.2f", totalDistance / 1000)) km")
    }

    // MARK: - Send Data to iPhone

    private func sendLocationDataToiPhone() {
        guard !coordinates.isEmpty else {
            print("⚠️ No coordinates to send")
            return
        }

        // Convert coordinates to dictionary format
        let coordinatesData: [[String: Any]] = zip(coordinates, timestamps).map { coord, time in
            [
                "latitude": coord.latitude,
                "longitude": coord.longitude,
                "timestamp": time.timeIntervalSince1970
            ]
        }

        // Send to iPhone via WatchConnectivity
        WatchConnectivityManager.shared.sendLocationUpdate(
            coordinates: coordinatesData,
            timestamp: Date()
        )

        print("📤 Sent \(coordinates.count) coordinates to iPhone")
    }

    // MARK: - Distance Calculation

    private func calculateDistance(from: CLLocation, to: CLLocation) -> Double {
        return to.distance(from: from)
    }

    // MARK: - Speed Calculation

    private func calculateSpeed(distance: Double, time: TimeInterval) -> Double {
        guard time > 0 else { return 0.0 }
        let metersPerSecond = distance / time
        let kmPerHour = metersPerSecond * 3.6
        return kmPerHour
    }
}

// MARK: - CLLocationManagerDelegate

extension WatchLocationManager: CLLocationManagerDelegate {

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus

        switch manager.authorizationStatus {
        case .authorizedWhenInUse, .authorizedAlways:
            print("✅ Location authorization granted")
        case .denied, .restricted:
            print("❌ Location authorization denied")
        case .notDetermined:
            print("⚠️ Location authorization not determined")
        @unknown default:
            print("⚠️ Unknown authorization status")
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let newLocation = locations.last else { return }

        // Update current location
        location = newLocation
        accuracy = newLocation.horizontalAccuracy

        // Only process if tracking
        guard isTracking else { return }

        // Calculate distance if we have a previous location
        if let lastLoc = lastLocation {
            let distance = calculateDistance(from: lastLoc, to: newLocation)
            totalDistance += distance

            // Calculate speed
            let timeInterval = newLocation.timestamp.timeIntervalSince(lastLoc.timestamp)
            let speed = calculateSpeed(distance: distance, time: timeInterval)
            currentSpeed = speed
            speeds.append(speed)
        }

        // Add to route
        coordinates.append(newLocation.coordinate)
        timestamps.append(newLocation.timestamp)
        lastLocation = newLocation

        // Send periodic updates to iPhone (every 10 points)
        if coordinates.count % 10 == 0 {
            sendLocationDataToiPhone()
        }

        print("📍 Location updated: \(String(format: "%.6f", newLocation.coordinate.latitude)), \(String(format: "%.6f", newLocation.coordinate.longitude)) - Accuracy: \(String(format: "%.1f", accuracy))m")
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("❌ Location manager error: \(error.localizedDescription)")

        if let clError = error as? CLError {
            switch clError.code {
            case .denied:
                print("⚠️ User denied location access")
            case .locationUnknown:
                print("⚠️ Location unknown, will retry")
            default:
                print("⚠️ Other CLError: \(clError.code.rawValue)")
            }
        }
    }
}
