//
//  ApplianceItemCard.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Individual appliance card with toggle and temperature display
struct ApplianceItemCard: View {
    let appliance: ApplianceItem
    var onToggle: (() -> Void)?
    var onTap: (() -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                icon

                VStack(alignment: .leading, spacing: 4) {
                    Text(appliance.type.displayName)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)

                    Text(appliance.location)
                        .font(.system(size: 14, weight: .regular))
                        .foregroundColor(.gray)

                    Text(appliance.statusSummary)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.black.opacity(0.85))

                    if !appliance.status.isEmpty && appliance.status != appliance.statusSummary {
                        Text(appliance.status)
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                    }
                }
                .contentShape(Rectangle())
                .onTapGesture {
                    onTap?()
                }

                Spacer(minLength: 12)

                Toggle("", isOn: .constant(appliance.isOn))
                    .labelsHidden()
                    .tint(Color(hex: "A50034"))
                    .disabled(true)  // Disable drag interaction
                    .allowsHitTesting(false)  // Disable toggle's own tap handling
                    .overlay(
                        // Custom tap area
                        Color.clear
                            .contentShape(Rectangle())
                            .onTapGesture {
                                onToggle?()
                            }
                    )
            }

            Divider()

            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text(appliance.primaryLabel)
                        .font(.system(size: 12))
                        .foregroundColor(.gray)

                    Text(appliance.primaryValueText)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.black)
                }

                Spacer()

                if let secondaryLabel = appliance.secondaryLabel,
                   let secondaryValue = appliance.secondaryValueText {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(secondaryLabel)
                            .font(.system(size: 12))
                            .foregroundColor(.gray)

                        Text(secondaryValue)
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.black)
                    }
                }
            }
            .contentShape(Rectangle())
            .onTapGesture {
                onTap?()
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.08), radius: 12, x: 0, y: 4)
    }

    private var icon: some View {
        ZStack {
            Circle()
                .fill(appliance.accentColor.opacity(0.12))
                .frame(width: 44, height: 44)

            Image(systemName: appliance.iconName)
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(appliance.accentColor)
        }
    }
}

#Preview {
    ApplianceItemCard(
        appliance: ApplianceItem(
            type: .airConditioner,
            location: "거실",
            status: "실내 27°C",
            mode: "냉방",
            isOn: true,
            primaryValue: 23,
            secondaryValue: 3
        )
    )
    .padding()
    .background(Color(hex: "F9F9F9"))
}
