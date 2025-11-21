import SwiftUI

struct FontSizeView: View {
    @State private var fontSize: Double = 16.0

    var body: some View {
        VStack(spacing: 0) {
            // Preview section
            VStack(spacing: 20) {
                Text("미리보기")
                    .font(.system(size: 13))
                    .foregroundColor(.gray.opacity(0.7))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    .padding(.bottom, 8)
                    .background(Color(hex: "F9F9F9"))

                // Sample chat messages preview
                VStack(spacing: 12) {
                    // Received message
                    HStack {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("LG 냉장고")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(.gray)

                            Text("안녕하세요! 무엇을 도와드릴까요?")
                                .font(.system(size: fontSize))
                                .foregroundColor(.black)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 12)
                                .background(Color(hex: "F0F0F0"))
                                .cornerRadius(18)
                        }
                        Spacer()
                    }
                    .padding(.horizontal, 20)

                    // Sent message
                    HStack {
                        Spacer()
                        Text("냉장고 온도를 조절하고 싶어요")
                            .font(.system(size: fontSize))
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 12)
                            .background(Color(hex: "A50034"))
                            .cornerRadius(18)
                    }
                    .padding(.horizontal, 20)
                }
                .padding(.bottom, 24)
            }
            .background(Color.white)

            Divider()

            // Font size control section
            VStack(spacing: 16) {
                Text("글자 크기 조절")
                    .font(.system(size: 13))
                    .foregroundColor(.gray.opacity(0.7))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                    .padding(.bottom, 8)
                    .background(Color(hex: "F9F9F9"))

                VStack(spacing: 12) {
                    // Slider
                    HStack(spacing: 16) {
                        Text("A")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.gray)

                        Slider(value: $fontSize, in: 12...24, step: 1)
                            .tint(Color(hex: "A50034"))

                        Text("A")
                            .font(.system(size: 20, weight: .medium))
                            .foregroundColor(.gray)
                    }
                    .padding(.horizontal, 20)

                    // Current size display
                    Text("\(Int(fontSize))pt")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(Color(hex: "A50034"))
                        .padding(.bottom, 8)
                }
                .padding(.vertical, 16)
                .background(Color.white)
            }

            Spacer()
        }
        .navigationTitle("글자 크기")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
    }
}

#Preview {
    NavigationStack {
        FontSizeView()
    }
}
