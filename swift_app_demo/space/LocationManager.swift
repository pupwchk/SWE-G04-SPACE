//
//  LocationManager.swift
//  space
//
//  GPS tracking manager using CoreLocation
//

import Foundation
import CoreLocation
import Combine

/// GPS tracking manager for routine recording
class LocationManager: NSObject, ObservableObject {
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
    @Published var totalDistance: Double = 0.0 // meters
    @Published var speedHistory: [Double] = []
    @Published var timestampHistory: [Date] = []

    // MARK: - Private Properties

    private let locationManager = CLLocationManager()
    private var lastLocation: CLLocation?

    // MARK: - Initialization

    override init() {
        super.init()
        setupLocationManager()
    }

    // MARK: - Setup

    private func setupLocationManager() {
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
        locationManager.distanceFilter = 5.0 // Update every 5 meters
        locationManager.allowsBackgroundLocationUpdates = false // Change to true if needed
        locationManager.pausesLocationUpdatesAutomatically = false

        authorizationStatus = locationManager.authorizationStatus
    }

    // MARK: - Public Methods

    /// Request location permission
    func requestPermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    /// Start tracking GPS
    func startTracking() {
        guard authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways else {
            print("❌ Location permission not granted")
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

        print("🟢 GPS tracking started")
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
        lastLocation = nil
        lastUpdateTime = nil
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
            routeCoordinates.append(newLocation.coordinate)
            speedHistory.append(currentSpeed)
            timestampHistory.append(newLocation.timestamp)

            if let previous = lastLocation {
                let distance = newLocation.distance(from: previous)
                totalDistance += distance
            }

            lastLocation = newLocation
        }

        // Console logging
        print("""
        📍 위치 업데이트:
        - 위도: \(String(format: "%.8f", currentLatitude))
        - 경도: \(String(format: "%.8f", currentLongitude))
        - 고도: \(String(format: "%.1f", currentAltitude)) m
        - 속도: \(String(format: "%.2f", currentSpeed)) km/h
        - 정확도(H): ±\(String(format: "%.1f", horizontalAccuracy))m / V: ±\(String(format: "%.1f", verticalAccuracy))m
        - 타임스탬프: \(newLocation.timestamp)
        """)

        if isTracking {
            print("- 총 거리: \(String(format: "%.2f", totalDistance / 1000)) km")
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateHeading newHeading: CLHeading) {
        if newHeading.headingAccuracy >= 0 {
            currentHeading = newHeading.trueHeading

            print("""
            🧭 방위 업데이트:
            - 진북 기준: \(String(format: "%.1f", newHeading.trueHeading))°
            - 자북 기준: \(String(format: "%.1f", newHeading.magneticHeading))°
            - 정확도: ±\(String(format: "%.1f", newHeading.headingAccuracy))°
            """)
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        print("❌ Location error: \(error.localizedDescription)")
    }
}
