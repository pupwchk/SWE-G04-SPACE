import SwiftUI

struct SpaceNotificationView: View {
    @StateObject private var locationManager = LocationManager.shared
    @StateObject private var tagManager = TaggedLocationManager.shared
    @AppStorage("locationNotificationsEnabled") private var locationAlarm = true

    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                // 위치 알림
                SpaceNotificationRow(
                    icon: "location.fill",
                    title: "집 근접 알림",
                    subtitle: homeLocationStatus,
                    isOn: $locationAlarm
                )
            }

            Spacer()
        }
        .navigationTitle("HARU 알림")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
        .onAppear {
            // Request notification permission if not already granted
            locationManager.requestNotificationPermission()

            // Only start tracking if we have a home location
            if locationAlarm && !locationManager.isTracking && tagManager.primaryHomeLocation != nil {
                locationManager.startTracking()
            }
        }
        .onChange(of: locationAlarm) { oldValue, newValue in
            // Start or stop location tracking based on setting
            if newValue {
                if !locationManager.isTracking && tagManager.primaryHomeLocation != nil {
                    locationManager.startTracking()
                }
            } else {
                if locationManager.isTracking {
                    locationManager.stopTracking()
                }
            }
        }
    }

    private var homeLocationStatus: String {
        if let home = tagManager.primaryHomeLocation {
            if home.notificationEnabled {
                return "설정한 집 위치(\(home.displayName))에\n가까워지면 알림을 받습니다"
            } else {
                return "집 위치는 설정되어 있지만\n알림이 비활성화되어 있습니다"
            }
        } else {
            return "집 위치를 먼저 설정해주세요"
        }
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
