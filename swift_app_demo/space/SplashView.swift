//
//  SplashView.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

struct SplashView: View {
    @State private var innerCircleScale: CGFloat = 0.0
    @State private var middleCircleScale: CGFloat = 0.0
    @State private var outerCircleScale: CGFloat = 0.0
    @State private var logoOpacity: Double = 0.0
    @State private var fillProgress: CGFloat = 0.0

    var body: some View {
        ZStack {
            // Background color
            Color(hex: "A50034")
                .ignoresSafeArea()

            // Outer circle (stroke only)
            Circle()
                .stroke(Color.white.opacity(0.15), lineWidth: 2)
                .frame(width: UIScreen.main.bounds.width * 1.35,
                       height: UIScreen.main.bounds.width * 1.35)
                .scaleEffect(outerCircleScale)
                .opacity(outerCircleScale * 0.15)

            // Middle circle (stroke only)
            Circle()
                .stroke(Color.white.opacity(0.3), lineWidth: 2)
                .frame(width: UIScreen.main.bounds.width * 0.89,
                       height: UIScreen.main.bounds.width * 0.89)
                .scaleEffect(middleCircleScale)
                .opacity(middleCircleScale * 0.3)

            // Inner circle (stroke only)
            Circle()
                .stroke(Color.white, lineWidth: 2)
                .frame(width: UIScreen.main.bounds.width * 0.52,
                       height: UIScreen.main.bounds.width * 0.52)
                .scaleEffect(innerCircleScale)

            // Logo text with fill animation (transparent outline → white fill, left to right)
            Text("HARU")
                .font(.system(size: 96, weight: .bold, design: .default))
                .foregroundStyle(
                    LinearGradient(
                        stops: [
                            .init(color: .white, location: 0),
                            .init(color: .white, location: fillProgress),
                            .init(color: .white.opacity(0.3), location: fillProgress),
                            .init(color: .white.opacity(0.3), location: 1)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .opacity(logoOpacity)
                .scaleEffect(innerCircleScale)
        }
        .onAppear {
            // Inner circle animation (0.0 ~ 0.4s)
            withAnimation(.easeOut(duration: 0.8)) {
                innerCircleScale = 1.0
            }

            // Middle circle animation (0.15 ~ 0.6s)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                withAnimation(.easeOut(duration: 0.9)) {
                    middleCircleScale = 1.0
                }
            }

            // Outer circle animation (0.3 ~ 0.8s)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) {
                withAnimation(.easeOut(duration: 1.0)) {
                    outerCircleScale = 1.0
                }
            }

            // Logo fade in and fill animation (0.6 ~ 2.0s)
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
                withAnimation(.easeIn(duration: 0.8)) {
                    logoOpacity = 1.0
                }
                withAnimation(.easeInOut(duration: 2.5)) {
                    fillProgress = 1.0
                }
            }
        }
    }
}

// Color extension for hex color support
extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

#Preview {
    SplashView()
}
