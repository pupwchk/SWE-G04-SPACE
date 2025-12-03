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

        // Initialize Sendbird Calls SDK
        SendbirdCallsManager.shared.initializeSDK(appId: Config.sendbirdAppId) { success in
            if success {
                print("📱 Sendbird Calls SDK initialized")

                // Authenticate user with SendBird Calls after SDK initialization
                Task {
                    // Wait a bit for Supabase to be ready
                    try? await Task.sleep(nanoseconds: 1_000_000_000) // 1 second

                    // Use FastAPI user_id from UserDefaults (NOT Supabase UUID or email)
                    if let fastapiUserId = UserDefaults.standard.string(forKey: "fastapi_user_id") {
                        // Use dual authentication method to register both user and AI assistant
                        SendbirdManager.shared.authenticateForCalls(userId: fastapiUserId) { success, error in
                            if success {
                                print("✅ [App] Dual authentication complete - ready for calls")
                            } else {
                                print("❌ [App] Dual authentication failed: \(error?.localizedDescription ?? "unknown error")")
                            }
                        }
                    } else {
                        print("⚠️ [App] FastAPI user_id not found in UserDefaults - skipping SendBird Calls authentication")
                    }
                }
            } else {
                print("❌ Sendbird Calls SDK initialization failed")
            }
        }

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
