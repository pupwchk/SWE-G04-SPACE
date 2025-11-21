//
//  DeviceCard.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Card component for displaying added devices (Apple Watch, AirPods, etc.)
struct DeviceCard: View {
    let icon: String
    let modelName: String

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Device icon
            Image(systemName: icon)
                .font(.system(size: 50))
                .foregroundColor(Color.gray.opacity(0.7))

            Spacer()

            // Device model name
            Text(modelName)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
                .padding(.bottom, 20)
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
        DeviceCard(
            icon: "applewatch",
            modelName: "Apple Watch"
        )

        DeviceCard(
            icon: "airpodspro",
            modelName: "AirPods Pro"
        )
    }
    .padding()
    .background(Color(hex: "F9F9F9"))
}
