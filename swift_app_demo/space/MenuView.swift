//
//  MenuView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Menu screen - settings and user options
struct MenuView: View {
    @StateObject private var supabaseManager = SupabaseManager.shared
    @StateObject private var fontSizeManager = FontSizeManager.shared
    @State private var userProfile: UserProfile?
    @State private var showMyPage = false
    @State private var showGeneral = false
    @State private var showLogoutAlert = false
    @State private var isLoading = true
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 0) {
                        // User profile section
                        HStack(spacing: 16) {
                            // Profile image
                            Circle()
                                .fill(
                                    LinearGradient(
                                        gradient: Gradient(colors: [
                                            Color(hex: "D4A5B5"),
                                            Color(hex: "B87A92")
                                        ]),
                                        startPoint: .top,
                                        endPoint: .bottom
                                    )
                                )
                                .frame(width: 80, height: 80)
                                .overlay(
                                    Image(systemName: "person.fill")
                                        .font(.system(size: 40))
                                        .foregroundColor(Color.white.opacity(0.8))
                                )

                            // User info
                            VStack(alignment: .leading, spacing: 4) {
                                if isLoading {
                                    Text("로딩 중...")
                                        .font(.system(size: fontSizeManager.fontSize + 2, weight: .semibold))
                                        .foregroundColor(.gray)
                                } else {
                                    Text(userProfile?.name ?? supabaseManager.currentUser?.name ?? "사용자")
                                        .font(.system(size: fontSizeManager.fontSize + 2, weight: .semibold))
                                        .foregroundColor(.black)

                                    Text(userProfile?.email ?? supabaseManager.currentUser?.email ?? "")
                                        .font(.system(size: fontSizeManager.fontSize - 2, weight: .regular))
                                        .foregroundColor(.gray)
                                }
                            }

                            Spacer()
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 24)

                        // Menu items
                        VStack(spacing: 0) {
                            MenuRow(icon: "person", title: "My page", action: {
                                handleMyPage()
                            }, fontSize: fontSizeManager.fontSize)

                            Divider()
                                .padding(.leading, 64)

                            MenuRow(icon: "gearshape", title: "General", action: {
                                handleGeneral()
                            }, fontSize: fontSizeManager.fontSize)

                            Divider()
                                .padding(.leading, 64)

                            MenuRow(icon: "questionmark.circle", title: "FAQ", action: {
                                handleFAQ()
                            }, fontSize: fontSizeManager.fontSize)
                        }
                        .background(Color.white)

                        Spacer(minLength: 40)

                        // Logout button
                        Button(action: {
                            handleLogout()
                        }) {
                            Text("로그아웃")
                                .font(.system(size: fontSizeManager.fontSize, weight: .regular))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                        .padding(.vertical, 40)

                        Spacer(minLength: 100)
                    }
                    .padding(.top, 20)
                }
            }
            .navigationTitle("Menu")
            .navigationBarTitleDisplayMode(.large)
            .toolbarColorScheme(.light, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarBackground(Color(hex: "F9F9F9"), for: .navigationBar)
            .navigationDestination(isPresented: $showMyPage) {
                MyPageView()
            }
            .navigationDestination(isPresented: $showGeneral) {
                GeneralView()
            }
            .alert("로그아웃", isPresented: $showLogoutAlert) {
                Button("취소", role: .cancel) { }
                Button("로그아웃", role: .destructive) {
                    Task {
                        await performLogout()
                    }
                }
            } message: {
                Text("로그아웃 하시겠습니까?")
            }
            .onAppear {
                Task {
                    await loadUserProfile()
                }
            }
        }
    }

    // MARK: - Actions

    private func handleMyPage() {
        print("My page tapped")
        showMyPage = true
    }

    private func handleGeneral() {
        print("General tapped")
        showGeneral = true
    }

    private func handleFAQ() {
        print("FAQ tapped")
    }

    private func handleLogout() {
        showLogoutAlert = true
    }

    // MARK: - Data Loading

    private func loadUserProfile() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let profile = try await supabaseManager.fetchUserProfile()
            userProfile = profile
        } catch {
            print("❌ Failed to load user profile: \(error.localizedDescription)")
            // If profile fetch fails, we still show user info from currentUser
        }
    }

    private func performLogout() async {
        do {
            try await supabaseManager.signOut()
            print("✅ Logged out successfully")
            // The app will automatically navigate to login screen via ContentView
        } catch {
            print("❌ Logout failed: \(error.localizedDescription)")
        }
    }
}

#Preview {
    MenuView()
}
