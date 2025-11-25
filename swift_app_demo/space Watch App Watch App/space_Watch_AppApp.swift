//
//  space_Watch_AppApp.swift
//  space Watch App Watch App
//
//  Created by 임동현 on 11/25/25.
//

import SwiftUI

@main
struct space_Watch_App_Watch_AppApp: App {
    // Initialize WatchConnectivity on app launch
    init() {
        // Initialize WatchConnectivityManager singleton
        _ = WatchConnectivityManager.shared
        print("⌚ Watch App initialized with WatchConnectivity")
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
