import SwiftUI

struct MyPageView: View {
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 0) {
            // Navigation bar
            HStack {
                Button(action: {
                    dismiss()
                }) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 20))
                        .foregroundColor(.black)
                }
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)

            // Title
            Text("My page")
                .font(.system(size: 18, weight: .semibold))
                .frame(maxWidth: .infinity)
                .padding(.bottom, 30)

            // Profile avatar
            ZStack(alignment: .bottomTrailing) {
                Circle()
                    .fill(Color(red: 0.89, green: 0.82, blue: 0.85))
                    .frame(width: 100, height: 100)
                    .overlay(
                        Image(systemName: "person.fill")
                            .font(.system(size: 45))
                            .foregroundColor(Color(red: 0.71, green: 0.47, blue: 0.56))
                    )

                Circle()
                    .fill(Color(hex: "A50034"))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Image(systemName: "pencil")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                    )
                    .offset(x: 4, y: 4)
            }
            .padding(.bottom, 40)

            // Settings rows
            VStack(spacing: 0) {
                // Nickname row
                SettingsRow(
                    label: "닉네임",
                    value: "소고기 웨이퍼 공격"
                )

                Divider()
                    .padding(.horizontal, 20)

                // Account row
                SettingsRow(
                    label: "계정",
                    value: "softwareengineergin@gmail.com"
                )

                Divider()
                    .padding(.horizontal, 20)

                // Birthday row
                SettingsRow(
                    label: "생일",
                    value: "11 / 03"
                )
            }
            .background(Color.white)

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
        .navigationBarHidden(true)
        .background(Color.white)
    }
}

struct SettingsRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(label)
                    .font(.system(size: 12))
                    .foregroundColor(Color(white: 0.8))

                Text(value)
                    .font(.system(size: 16))
                    .foregroundColor(.black)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 14))
                .foregroundColor(Color(white: 0.8))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 20)
        .contentShape(Rectangle())
    }
}

#Preview {
    MyPageView()
}
