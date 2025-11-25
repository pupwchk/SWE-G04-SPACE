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

        // Initialize HealthKitManager and start real-time observers
        let healthManager = HealthKitManager.shared
        if healthManager.isAvailable {
            healthManager.startRealtimeObservers()
            print("📱 HealthKit real-time observers started")
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
