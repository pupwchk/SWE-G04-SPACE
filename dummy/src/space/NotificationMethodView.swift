import SwiftUI

struct NotificationMethodView: View {
    @State private var voiceNotification = true
    @State private var vibrationNotification = true

    var body: some View {
        VStack(spacing: 0) {
            // Notification rows
            VStack(spacing: 0) {
                NotificationToggleRow(
                    title: "소리알림",
                    isOn: $voiceNotification
                )

                Divider()
                    .padding(.leading, 20)

                NotificationToggleRow(
                    title: "진동알림",
                    isOn: $vibrationNotification
                )
            }
            .background(Color.white)

            Spacer()
        }
        .navigationTitle("알림 방식 설정")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

struct NotificationToggleRow: View {
    let title: String
    @Binding var isOn: Bool

    var body: some View {
        HStack {
            Text(title)
                .font(.system(size: 17))
                .foregroundColor(.black)

            Spacer()

            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(Color(hex: "A50034"))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 16)
        .background(Color.white)
    }
}

#Preview {
    NavigationStack {
        NotificationMethodView()
    }
}
