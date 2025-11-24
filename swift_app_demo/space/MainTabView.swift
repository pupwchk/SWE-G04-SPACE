//
//  MainTabView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Main tab bar view with Home, Appliance, Chat, and Menu tabs
struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            // Home Tab
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("Home")
                }
                .tag(0)

            // Appliance Tab
            ApplianceView()
                .tabItem {
                    Image(systemName: "refrigerator")
                    Text("Appliance")
                }
                .tag(1)

            // Chat Tab
            ChatView()
                .tabItem {
                    Image(systemName: "message.fill")
                    Text("Chat")
                }
                .tag(2)

            // Menu Tab
            MenuView()
                .tabItem {
                    Image(systemName: "line.3.horizontal")
                    Text("Menu")
                }
                .tag(3)
        }
        .accentColor(Color(hex: "A50034"))
    }
}

#Preview {
    MainTabView()
}
