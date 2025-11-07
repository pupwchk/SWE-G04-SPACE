import SwiftUI

struct DoNotDisturbView: View {
    var body: some View {
        VStack(spacing: 0) {
            VStack(spacing: 0) {
                // Time row
                HStack(spacing: 16) {
                    Image(systemName: "clock")
                        .font(.system(size: 22))
                        .foregroundColor(.black)
                        .frame(width: 28)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("시간")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.black)

                        Text("예: 12:30 ~ 02:30")
                            .font(.system(size: 13))
                            .foregroundColor(.gray)
                    }

                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color.white)

                Divider()
                    .padding(.leading, 68)

                // Location row
                HStack(spacing: 16) {
                    Image(systemName: "location")
                        .font(.system(size: 22))
                        .foregroundColor(.black)
                        .frame(width: 28)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("위치")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.black)

                        Text("예: '집에서 도서관 때'")
                            .font(.system(size: 13))
                            .foregroundColor(.gray)
                    }

                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color.white)

                Divider()
                    .padding(.leading, 68)

                // Method row
                HStack(spacing: 16) {
                    Image(systemName: "bell.slash")
                        .font(.system(size: 22))
                        .foregroundColor(.black)
                        .frame(width: 28)

                    VStack(alignment: .leading, spacing: 4) {
                        Text("앱")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.black)

                        Text("예: '도서 앱을 쓸 때'")
                            .font(.system(size: 13))
                            .foregroundColor(.gray)
                    }

                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color.white)
            }

            Spacer()
        }
        .navigationTitle("방해금지시간 설정")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

#Preview {
    NavigationStack {
        DoNotDisturbView()
    }
}
