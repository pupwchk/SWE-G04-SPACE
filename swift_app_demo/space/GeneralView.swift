import SwiftUI

struct GeneralView: View {
    @StateObject private var fontSizeManager = FontSizeManager.shared
    @Environment(\.dismiss) var dismiss
    @State private var showNotificationMethod = false
    @State private var showDoNotDisturb = false
    @State private var showSpaceNotification = false
    @State private var showEmergencyCall = false
    @State private var showCallErrorHistory = false
    @State private var showFontSize = false
    @State private var showHomeLocationSetting = false

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(spacing: 0) {
                    // 알림 section
                    SectionHeader(title: "알림")

                    Button(action: {
                        showNotificationMethod = true
                    }) {
                        GeneralRow(title: "알림 방식 설정", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showDoNotDisturb = true
                    }) {
                        GeneralRow(title: "방해금지 시간 설정", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showSpaceNotification = true
                    }) {
                        GeneralRow(title: "HARU 알림", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Divider()
                        .padding(.vertical, 16)

                    // 위치 section
                    SectionHeader(title: "위치")

                    Button(action: {
                        print("🏠 Home location button tapped")
                        showHomeLocationSetting = true
                        print("🏠 showHomeLocationSetting set to: \(showHomeLocationSetting)")
                    }) {
                        GeneralRow(title: "홈 위치 설정", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Divider()
                        .padding(.vertical, 16)

                    // 채팅 화면 section
                    SectionHeader(title: "채팅 화면")

                    Button(action: {
                        showFontSize = true
                    }) {
                        GeneralRow(title: "글자 크기", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Divider()
                        .padding(.vertical, 16)

                    // 전화 section
                    SectionHeader(title: "전화")

                    Button(action: {
                        showEmergencyCall = true
                    }) {
                        GeneralRow(title: "긴급전화 알림", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showCallErrorHistory = true
                    }) {
                        GeneralRow(title: "전화 오약 기록", fontSize: fontSizeManager.fontSize)
                    }
                    .buttonStyle(.plain)
                }
            }

            Spacer()

            // Bottom buttons
            HStack(spacing: 40) {
                Button(action: {
                    // Password change action
                }) {
                    Text("비밀번호 변경")
                        .font(.system(size: fontSizeManager.fontSize - 2))
                        .foregroundColor(Color(white: 0.7))
                }

                Button(action: {
                    // Account deletion action
                }) {
                    Text("탈퇴하기")
                        .font(.system(size: fontSizeManager.fontSize - 2))
                        .foregroundColor(Color(white: 0.7))
                }
            }
            .padding(.bottom, 40)
        }
        .navigationTitle("General")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color.white)
        .sheet(isPresented: $showNotificationMethod) {
            NavigationStack {
                NotificationMethodView()
            }
        }
        .sheet(isPresented: $showDoNotDisturb) {
            NavigationStack {
                DoNotDisturbView()
            }
        }
        .sheet(isPresented: $showSpaceNotification) {
            NavigationStack {
                SpaceNotificationView()
            }
        }
        .sheet(isPresented: $showHomeLocationSetting) {
            NavigationStack {
                HomeLocationSetupView()
                    .onAppear {
                        print("🏠 HomeLocationSetupView appeared in sheet")
                    }
            }
        }
        .sheet(isPresented: $showEmergencyCall) {
            NavigationStack {
                EmergencyCallView()
            }
        }
        .sheet(isPresented: $showCallErrorHistory) {
            NavigationStack {
                CallErrorHistoryView()
            }
        }
        .sheet(isPresented: $showFontSize) {
            NavigationStack {
                FontSizeView()
            }
        }
    }
}

struct SectionHeader: View {
    let title: String

    var body: some View {
        HStack {
            Text(title)
                .font(.system(size: 13))
                .foregroundColor(.gray.opacity(0.7))
                .padding(.leading, 20)
                .padding(.vertical, 8)

            Spacer()
        }
        .background(Color(hex: "F9F9F9"))
    }
}

struct GeneralRow: View {
    let title: String
    let fontSize: Double

    var body: some View {
        HStack {
            Text(title)
                .font(.system(size: fontSize + 1))
                .foregroundColor(.black)

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 14))
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white)
        .contentShape(Rectangle())
    }
}

#Preview {
    NavigationStack {
        GeneralView()
    }
}
