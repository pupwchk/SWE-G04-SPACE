//
//  ApplianceCard.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Card component for displaying added home appliances
struct ApplianceCard: View {
    let icon: String
    let title: String
    let subtitle: String
    let status: String
    let isOn: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Appliance icon
            Image(systemName: icon)
                .font(.system(size: 50))
                .foregroundColor(Color.gray.opacity(0.7))
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.top, 20)

            // Appliance info
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(.white)

                Text(subtitle)
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(.white.opacity(0.9))

                Text(status)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.white.opacity(0.7))
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 16)
        }
        .frame(width: 170, height: 200)
        .background(
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hex: "6B2737"),
                    Color(hex: "4A1C27")
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .cornerRadius(20)
        .shadow(color: Color.black.opacity(0.15), radius: 8, x: 0, y: 4)
    }
}

#Preview {
    HStack(spacing: 16) {
        ApplianceCard(
            icon: "speaker.wave.2.fill",
            title: "거실",
            subtitle: "스탠드형 에어컨",
            status: "꺼짐",
            isOn: false
        )

        ApplianceCard(
            icon: "tv.fill",
            title: "TV",
            subtitle: "문 닫힘",
            status: "문 닫힘",
            isOn: false
        )
    }
    .padding()
    .background(Color(hex: "F9F9F9"))
}
