//
//  DeviceDetailView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Detailed view for a specific appliance (냉장고/에어컨 etc.)
struct DeviceDetailView: View {
    let appliance: ApplianceItem
    @State private var rapidCooling: Bool = false

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                // Device 3D Image Section
                ZStack {
                    Color(hex: "F5F5F7")
                        .ignoresSafeArea()

                    // Placeholder for 3D refrigerator image
                    Image(systemName: "refrigerator")
                        .font(.system(size: 120))
                        .foregroundColor(Color.gray.opacity(0.3))
                        .padding(.vertical, 60)
                }
                .frame(height: 300)

                // Temperature Cards Section
                HStack(spacing: 12) {
                    // 냉장실 (Refrigerator)
                    TemperatureCard(
                        icon: "snowflake",
                        iconColor: Color(hex: "A50034"),
                        title: "냉장실",
                        temperature: "2°C",
                        subtitle: "온도가 잘 유지되고\n있어요"
                    )

                    // 냉동실 (Freezer)
                    TemperatureCard(
                        icon: "asterisk",
                        iconColor: Color(hex: "A50034"),
                        title: "냉동실",
                        temperature: "-18°C",
                        subtitle: "설정 온도보다 온도가\n높아졌어요"
                    )
                }
                .padding(.horizontal, 20)
                .padding(.top, 20)

                // 특급 냉동 Toggle
                HStack {
                    Image(systemName: "snowflake.circle")
                        .font(.system(size: 32))
                        .foregroundColor(Color(hex: "A50034"))

                    Text("특급 냉동")
                        .font(.system(size: 17, weight: .medium))
                        .foregroundColor(.black)

                    Spacer()

                    Toggle("", isOn: $rapidCooling)
                        .labelsHidden()
                        .tint(Color(hex: "A50034"))
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color(hex: "F3DEE5"))
                .cornerRadius(16)
                .padding(.horizontal, 20)
                .padding(.top, 16)

                // 온도 정보 확인하기 Button
                Button(action: {
                    // Navigate to temperature details
                }) {
                    HStack {
                        Text("온도 정보 확인하기")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(Color(hex: "A50034"))

                        Image(systemName: "chevron.right")
                            .font(.system(size: 14))
                            .foregroundColor(Color(hex: "A50034"))
                    }
                }
                .padding(.top, 20)

                // 아이스 메이커 Section
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "cube")
                            .font(.system(size: 20))
                            .foregroundColor(Color(hex: "A50034"))

                        Text("아이스 메이커")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.black)

                        Spacer()

                        Image(systemName: "chevron.right")
                            .font(.system(size: 14))
                            .foregroundColor(.gray.opacity(0.5))
                    }

                    // Ice maker options
                    HStack(spacing: 12) {
                        IceMakerOption(
                            icon: "square.grid.3x3",
                            title: "얼음 가득 참",
                            isSelected: true
                        )

                        IceMakerOption(
                            icon: "snowflake.circle",
                            title: "얼음 생성 중",
                            isSelected: false
                        )
                    }
                }
                .padding(20)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: Color.black.opacity(0.06), radius: 12, x: 0, y: 4)
                .padding(.horizontal, 20)
                .padding(.top, 24)

                Spacer(minLength: 40)
            }
        }
        .background(Color(hex: "F9F9F9"))
        .navigationTitle(appliance.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HStack(spacing: 16) {
                    Button(action: {
                        // Handle upgrade
                    }) {
                        Image(systemName: "arrow.up.circle")
                            .foregroundColor(Color(hex: "A50034"))
                    }

                    Button(action: {
                        // Handle settings
                    }) {
                        Image(systemName: "gearshape")
                            .foregroundColor(.black)
                    }
                }
            }
        }
    }
}

// MARK: - Temperature Card Component

struct TemperatureCard: View {
    let icon: String
    let iconColor: Color
    let title: String
    let temperature: String
    let subtitle: String

    var body: some View {
        VStack(spacing: 12) {
            // Icon with gradient background
            ZStack {
                Circle()
                    .fill(Color.white.opacity(0.5))
                    .frame(width: 60, height: 60)

                Image(systemName: icon)
                    .font(.system(size: 28))
                    .foregroundColor(iconColor)
            }

            Text(title)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.gray)

            Text(temperature)
                .font(.system(size: 32, weight: .bold))
                .foregroundColor(iconColor)

            Text(subtitle)
                .font(.system(size: 13, weight: .regular))
                .foregroundColor(.gray)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 20)
        .padding(.horizontal, 12)
        .background(Color(hex: "F3DEE5"))
        .cornerRadius(16)
    }
}

// MARK: - Ice Maker Option Component

struct IceMakerOption: View {
    let icon: String
    let title: String
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.white.opacity(0.5))
                    .frame(width: 80, height: 80)

                Image(systemName: icon)
                    .font(.system(size: 32))
                    .foregroundColor(Color(hex: "A50034"))
            }

            Text(title)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.black)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(isSelected ? Color(hex: "F3DEE5") : Color.white)
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isSelected ? Color(hex: "A50034") : Color.clear, lineWidth: 2)
        )
    }
}

#Preview {
    NavigationStack {
        DeviceDetailView(
            appliance: ApplianceItem(
                id: 1,
                title: "냉장고",
                status: "거실",
                temperatureLabel: "실내 온도",
                temperature: "2°C",
                isOn: true
            )
        )
    }
}
