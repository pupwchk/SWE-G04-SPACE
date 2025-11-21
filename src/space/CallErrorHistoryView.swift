import SwiftUI

struct CallErrorHistoryView: View {
    @State private var callErrorEnabled = true

    var body: some View {
        VStack(spacing: 0) {
            // Toggle row
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("전화 오약")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)

                    Text("전화 사용 보력 캐기/끄기")
                        .font(.system(size: 13))
                        .foregroundColor(.gray)
                }

                Spacer()

                Toggle("", isOn: $callErrorEnabled)
                    .labelsHidden()
                    .tint(Color(hex: "A50034"))
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.white)

            // Section header
            HStack {
                Text("최근 기록")
                    .font(.system(size: 13))
                    .foregroundColor(.gray.opacity(0.7))
                    .padding(.leading, 20)
                    .padding(.vertical, 12)

                Spacer()
            }
            .background(Color(hex: "F9F9F9"))

            // Call error history list
            ScrollView {
                VStack(spacing: 12) {
                    ForEach(0..<4) { _ in
                        CallErrorCard()
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
            }
            .background(Color(hex: "F9F9F9"))
        }
        .navigationTitle("전화 오약 기록")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

struct CallErrorCard: View {
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "phone.fill")
                .font(.system(size: 20))
                .foregroundColor(.black)
                .frame(width: 28)

            VStack(alignment: .leading, spacing: 8) {
                Text("My home")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.black)

                Text("무슨 내용으로 전화를 했을까? 집에 할일이 생겼다거나 아떠구저떠구아떠구 저떠구\n무슨 내용으로 전화를 했을까? 집에 할일이 생겼다거나 아떠구저떠구아떠구 저떠구")
                    .font(.system(size: 14))
                    .foregroundColor(.black)
                    .lineSpacing(4)

                Text("2025년 11월 3일 : 12:32")
                    .font(.system(size: 12))
                    .foregroundColor(.gray.opacity(0.5))
            }

            Spacer()
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(red: 0.95, green: 0.89, blue: 0.91))
        )
    }
}

#Preview {
    NavigationStack {
        CallErrorHistoryView()
    }
}
