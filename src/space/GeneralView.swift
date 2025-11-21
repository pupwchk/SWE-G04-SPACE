import SwiftUI

struct GeneralView: View {
    @Environment(\.dismiss) var dismiss
    @State private var showNotificationMethod = false
    @State private var showDoNotDisturb = false
    @State private var showSpaceNotification = false
    @State private var showEmergencyCall = false
    @State private var showCallErrorHistory = false
    @State private var showFontSize = false

    var body: some View {
        VStack(spacing: 0) {
            // Top profile section
            HStack(spacing: 16) {
                // Profile avatar
                Circle()
                    .fill(Color(red: 0.89, green: 0.82, blue: 0.85))
                    .frame(width: 60, height: 60)
                    .overlay(
                        Image(systemName: "person.fill")
                            .font(.system(size: 28))
                            .foregroundColor(Color(red: 0.71, green: 0.47, blue: 0.56))
                    )

                // Profile text
                Text("소고기 웨이퍼 공격")
                    .font(.system(size: 17))
                    .foregroundColor(.black)

                Spacer()

                // Chevron
                Image(systemName: "chevron.right")
                    .font(.system(size: 14))
                    .foregroundColor(.gray.opacity(0.5))
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 20)
            .background(Color.white)

            Divider()

            ScrollView {
                VStack(spacing: 0) {
                    // 알림 section
                    SectionHeader(title: "알림")

                    Button(action: {
                        showNotificationMethod = true
                    }) {
                        GeneralRow(title: "알림 방식 설정")
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showDoNotDisturb = true
                    }) {
                        GeneralRow(title: "방해금지 시간 설정")
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showSpaceNotification = true
                    }) {
                        GeneralRow(title: "SPACE 알림")
                    }
                    .buttonStyle(.plain)

                    Divider()
                        .padding(.vertical, 16)

                    // 채팅 화면 section
                    SectionHeader(title: "채팅 화면")

                    Button(action: {
                        showFontSize = true
                    }) {
                        GeneralRow(title: "글자 크기")
                    }
                    .buttonStyle(.plain)

                    Divider()
                        .padding(.vertical, 16)

                    // 전화 section
                    SectionHeader(title: "전화")

                    Button(action: {
                        showEmergencyCall = true
                    }) {
                        GeneralRow(title: "긴급전화 알림")
                    }
                    .buttonStyle(.plain)

                    Button(action: {
                        showCallErrorHistory = true
                    }) {
                        GeneralRow(title: "전화 오약 기록")
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
                        .font(.system(size: 14))
                        .foregroundColor(Color(white: 0.7))
                }

                Button(action: {
                    // Account deletion action
                }) {
                    Text("탈퇴하기")
                        .font(.system(size: 14))
                        .foregroundColor(Color(white: 0.7))
                }
            }
            .padding(.bottom, 40)
        }
        .navigationTitle("General")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color.white)
        .navigationDestination(isPresented: $showNotificationMethod) {
            NotificationMethodView()
        }
        .navigationDestination(isPresented: $showDoNotDisturb) {
            DoNotDisturbView()
        }
        .navigationDestination(isPresented: $showSpaceNotification) {
            SpaceNotificationView()
        }
        .navigationDestination(isPresented: $showEmergencyCall) {
            EmergencyCallView()
        }
        .navigationDestination(isPresented: $showCallErrorHistory) {
            CallErrorHistoryView()
        }
        .navigationDestination(isPresented: $showFontSize) {
            FontSizeView()
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

    var body: some View {
        HStack {
            Text(title)
                .font(.system(size: 17))
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
