//
//  ContentView.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var supabaseManager = SupabaseManager.shared
    @State private var showSplash = true
    @State private var isLoggedIn = false

    var body: some View {
        if showSplash {
            SplashView()
                .onAppear {
                    // 3초 후 메인 화면으로 전환
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                        withAnimation {
                            showSplash = false
                            // Check authentication status
                            isLoggedIn = supabaseManager.isAuthenticated
                        }
                    }
                }
        } else if isLoggedIn || supabaseManager.isAuthenticated {
            MainTabView()
                .onChange(of: supabaseManager.isAuthenticated) { oldValue, newValue in
                    // Update login state when authentication changes
                    isLoggedIn = newValue
                }
        } else {
            LoginView(isLoggedIn: $isLoggedIn)
        }
    }
}

#Preview {
    ContentView()
}
