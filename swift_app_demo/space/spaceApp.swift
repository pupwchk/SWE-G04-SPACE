//
//  spaceApp.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

@main
struct HaruApp: App {
    // Initialize managers on app launch
    init() {
        // Initialize WatchConnectivityManager singleton
        _ = WatchConnectivityManager.shared
        print("📱 iOS App initialized with WatchConnectivity")

        // Initialize HealthKitManager and request authorization before starting observers
        let healthManager = HealthKitManager.shared
        if healthManager.isAvailable {
            // Request authorization first, then start observers only if granted
            healthManager.requestAuthorization { success in
                if success {
                    healthManager.startRealtimeObservers()
                    print("📱 HealthKit authorization granted, real-time observers started")
                } else {
                    print("⚠️ HealthKit authorization not granted, observers not started")
                }
            }
        } else {
            print("⚠️ HealthKit not available on this device")
        }

        // Request notification permission for location proximity alerts
        let locationManager = LocationManager.shared
        locationManager.requestNotificationPermission()
        print("📱 Requested notification permission for location alerts")
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
