//
//  MenuView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Menu screen - settings and user options
struct MenuView: View {
    @State private var showMyPage = false
    @State private var showGeneral = false
    @State private var showResetAlert = false

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
                                Text("소고기 웨이퍼 공격")
                                    .font(.system(size: 18, weight: .semibold))
                                    .foregroundColor(.black)

                                Text("softwareengineering@gmail.com")
                                    .font(.system(size: 14, weight: .regular))
                                    .foregroundColor(.gray)
                            }

                            Spacer()
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 24)

                        // Menu items
                        VStack(spacing: 0) {
                            MenuRow(icon: "person", title: "My page", action: {
                                handleMyPage()
                            })

                            Divider()
                                .padding(.leading, 64)

                            MenuRow(icon: "gearshape", title: "General", action: {
                                handleGeneral()
                            })

                            Divider()
                                .padding(.leading, 64)

                            MenuRow(icon: "questionmark.circle", title: "FAQ", action: {
                                handleFAQ()
                            })

                            Divider()
                                .padding(.leading, 64)

                            MenuRow(icon: "arrow.counterclockwise", title: "페르소나 초기화", action: {
                                showResetAlert = true
                            })
                        }
                        .background(Color.white)

                        Spacer(minLength: 40)

                        // Logout button
                        Button(action: {
                            handleLogout()
                        }) {
                            Text("로그아웃")
                                .font(.system(size: 16, weight: .regular))
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
            .navigationDestination(isPresented: $showMyPage) {
                MyPageView()
            }
            .navigationDestination(isPresented: $showGeneral) {
                GeneralView()
            }
            .alert("페르소나 초기화", isPresented: $showResetAlert) {
                Button("취소", role: .cancel) { }
                Button("초기화", role: .destructive) {
                    handleResetPersona()
                }
            } message: {
                Text("저장된 모든 페르소나가 삭제됩니다.\n처음부터 다시 시작하시겠습니까?")
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
        print("Logout tapped")
        // TODO: Implement logout logic
    }

    private func handleResetPersona() {
        PersonaManager.shared.clearPersonas()
        print("Personas cleared successfully")
    }
}

#Preview {
    MenuView()
}
