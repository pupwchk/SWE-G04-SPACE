import SwiftUI

struct EmergencyCallView: View {
    @State private var emergencyCallEnabled = true

    var body: some View {
        VStack(spacing: 0) {
            // Emergency call toggle row
            HStack(spacing: 16) {
                Image(systemName: "bell")
                    .font(.system(size: 22))
                    .foregroundColor(.black)
                    .frame(width: 28)

                VStack(alignment: .leading, spacing: 4) {
                    Text("긴급 상황 감지 시 전화")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)

                    Text("전화 발신을 까눌 앱 발원을 재공 힘~")
                        .font(.system(size: 13))
                        .foregroundColor(.gray)
                }

                Spacer()

                Toggle("", isOn: $emergencyCallEnabled)
                    .labelsHidden()
                    .tint(Color(hex: "A50034"))
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.white)

            Spacer()
        }
        .navigationTitle("긴급 전화 알림")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

#Preview {
    NavigationStack {
        EmergencyCallView()
    }
}