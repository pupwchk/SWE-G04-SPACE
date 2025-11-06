import SwiftUI

struct SpaceNotificationView: View {
    @State private var aiRecommendation = true
    @State private var dndFollowup = true
    @State private var locationAlarm = true

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                // AI 제안 피드백 알림
                SpaceNotificationRow(
                    icon: "sparkles",
                    title: "AI 제안 피드백 알림",
                    subtitle: "SPACE가 추천한 아이템 대한\n피드백 알림을 받니다",
                    isOn: $aiRecommendation
                )

                Divider()
                    .padding(.leading, 68)

                // SPACE 방해금지 시간 추천
                SpaceNotificationRow(
                    icon: "moon.stars",
                    title: "SPACE 방해금지 시간 추천",
                    subtitle: "사용자의 위치, 앱 사용 등 패턴을 분석하여\nSPACE가 자동으로 방해 금지 시간을 설정합니다.",
                    isOn: $dndFollowup
                )

                Divider()
                    .padding(.leading, 68)

                // 위치 알림
                SpaceNotificationRow(
                    icon: "location",
                    title: "위치 알림",
                    subtitle: "사용자의 위치를 알림받으려 알까요~",
                    isOn: $locationAlarm
                )
            }

            Spacer()
        }
        .navigationTitle("SPACE 알림")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

struct SpaceNotificationRow: View {
    let icon: String
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 22))
                .foregroundColor(.black)
                .frame(width: 28)
                .padding(.top, 2)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.black)

                Text(subtitle)
                    .font(.system(size: 13))
                    .foregroundColor(.gray)
                    .lineSpacing(2)
            }

            Spacer()

            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(Color(hex: "A50034"))
                .padding(.top, 2)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white)
    }
}

#Preview {
    NavigationStack {
        SpaceNotificationView()
    }
}
