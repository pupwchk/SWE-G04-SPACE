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

                    if let userId = await SupabaseManager.shared.currentUser?.id {
                        SendbirdCallsManager.shared.authenticate(userId: userId) { result in
                            switch result {
                            case .success(let user):
                                print("✅ [App] User authenticated with SendBird Calls: \(user.userId)")
                            case .failure(let error):
                                print("❌ [App] SendBird Calls authentication failed: \(error)")
                            }
                        }
                    } else {
                        print("⚠️ [App] No user session found, skipping SendBird Calls authentication")
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
