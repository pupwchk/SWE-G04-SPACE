//
//  spaceApp.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI
import UserNotifications

@main
struct HaruApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    // Initialize managers on app launch
    init() {
        // Request notification permission for chat messages
        NotificationManager.shared.requestAuthorization { granted in
            if granted {
                print("📱 Notification permission granted for chat messages")
            } else {
                print("⚠️ Notification permission denied for chat messages")
            }
        }

        // Initialize Sendbird Chat SDK
        SendbirdManager.shared.initializeChat()
        print("📱 Sendbird Chat SDK initialized")

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
        locationManager.requestPermission()
        print("📱 Requested notification permission for location alerts")

        // Load tagged locations cache first
        Task {
            await TaggedLocationManager.shared.loadTaggedLocations()

            // Only start tracking if notifications are enabled and we have a home location
            await MainActor.run {
                let notificationsEnabled = UserDefaults.standard.object(forKey: "locationNotificationsEnabled") as? Bool ?? true
                let hasHomeLocation = TaggedLocationManager.shared.primaryHomeLocation != nil

                if notificationsEnabled && hasHomeLocation {
                    // Delay to allow proper initialization
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                        if !locationManager.isTracking {
                            locationManager.startTracking()
                            print("📱 Started location tracking for proximity alerts")
                        }
                    }
                } else {
                    print("📱 Location tracking not started: notifications=\(notificationsEnabled), hasHome=\(hasHomeLocation)")
                }
            }
        }

        // Initialize auto-tracking manager for background health data uploads
        // This will start hourly health uploads and daily sleep uploads
        let autoTracking = AutoTrackingManager.shared
        autoTracking.startAutoTracking()
        print("📱 Auto-tracking initialized - hourly health & daily sleep uploads enabled")
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
