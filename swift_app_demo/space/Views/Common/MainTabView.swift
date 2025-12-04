//
//  MainTabView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Main tab bar view with Home, Appliance, Chat, and Menu tabs
struct MainTabView: View {
    @StateObject private var navigationCoordinator = NavigationCoordinator.shared

    var body: some View {
        TabView(selection: $navigationCoordinator.selectedTab) {
            // Home Tab
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("홈")
                }
                .tag(0)

            // Appliance Tab
            ApplianceView()
                .tabItem {
                    Image(systemName: "refrigerator")
                    Text("가전제품")
                }
                .tag(1)

            // Chat Tab
            ChatView()
                .environmentObject(navigationCoordinator)
                .tabItem {
                    Image(systemName: "message.fill")
                    Text("채팅")
                }
                .tag(2)

            // Menu Tab
            MenuView()
                .tabItem {
                    Image(systemName: "line.3.horizontal")
                    Text("메뉴")
                }
                .tag(3)
        }
        .accentColor(Color(hex: "A50034"))
    }
}

#Preview {
    MainTabView()
}
