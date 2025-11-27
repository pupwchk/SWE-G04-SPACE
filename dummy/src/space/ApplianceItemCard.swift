//
//  ApplianceItemCard.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Individual appliance card with toggle and temperature display
struct ApplianceItemCard: View {
    let title: String
    let status: String
    let temperatureLabel: String
    let temperature: String
    @Binding var isOn: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top) {
                // Title and status
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)

                    Text(status)
                        .font(.system(size: 14, weight: .regular))
                        .foregroundColor(.gray)
                }

                Spacer()

                // Toggle switch
                Toggle("", isOn: $isOn)
                    .labelsHidden()
                    .tint(Color(hex: "A50034"))
            }
            .padding(.horizontal, 20)
            .padding(.top, 20)
            .padding(.bottom, 16)

            // Temperature display
            VStack(spacing: 4) {
                Text(temperatureLabel)
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(.gray)

                Text(temperature)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.black)
            }
            .frame(maxWidth: .infinity)
            .padding(.bottom, 20)
        }
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 4)
    }
}

#Preview {
    VStack(spacing: 16) {
        ApplianceItemCard(
            title: "에어컨 1",
            status: "거실",
            temperatureLabel: "실내 온도",
            temperature: "30°C",
            isOn: .constant(false)
        )

        ApplianceItemCard(
            title: "에어컨 2",
            status: "거실",
            temperatureLabel: "설정 온도",
            temperature: "18°C",
            isOn: .constant(true)
        )
    }
    .padding()
    .background(Color(hex: "F9F9F9"))
}
