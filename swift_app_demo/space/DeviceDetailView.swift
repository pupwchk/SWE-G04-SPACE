//
//  DeviceDetailView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Detailed view for a specific appliance with contextual controls
struct ApplianceDetailView: View {
    @Binding var appliance: ApplianceItem

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                headerCard

                controlSection

                if !appliance.status.isEmpty && appliance.status != appliance.statusSummary {
                    statusCard
                }

                Spacer(minLength: 20)
            }
            .padding(20)
        }
        .background(Color(hex: "F9F9F9"))
        .navigationTitle(appliance.type.displayName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: {
                    appliance.syncStatusFromControls()
                }) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .foregroundColor(Color(hex: "A50034"))
                }
            }
        }
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                ZStack {
                    Circle()
                        .fill(appliance.accentColor.opacity(0.12))
                        .frame(width: 48, height: 48)

                    Image(systemName: appliance.iconName)
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(appliance.accentColor)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text(appliance.type.displayName)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.black)

                    Text(appliance.location)
                        .font(.system(size: 14))
                        .foregroundColor(.gray)

                    Text(appliance.statusSummary)
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.black.opacity(0.85))
                }

                Spacer()

                Toggle("", isOn: $appliance.isOn)
                    .labelsHidden()
                    .tint(Color(hex: "A50034"))
            }

            if let secondaryText = appliance.secondaryValueText {
                HStack(spacing: 12) {
                    valueBadge(title: appliance.primaryLabel, value: appliance.primaryValueText)
                    valueBadge(title: appliance.secondaryLabel ?? "설정", value: secondaryText)
                }
            } else {
                valueBadge(title: appliance.primaryLabel, value: appliance.primaryValueText)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.06), radius: 8, x: 0, y: 4)
    }

    @ViewBuilder
    private var controlSection: some View {
        switch appliance.type {
        case .airConditioner:
            airConditionerControls
        case .lighting:
            lightingControls
        case .airPurifier:
            airPurifierControls
        case .dehumidifier:
            dehumidifierControls
        case .humidifier:
            humidifierControls
        case .tv:
            tvControls
        }
    }

    private var airConditionerControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "운전 모드", subtitle: appliance.mode) {
                Picker("운전 모드", selection: $appliance.mode) {
                    ForEach(["냉방", "제습", "송풍", "자동"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "설정 온도", subtitle: "\(Int(appliance.primaryValue))°C") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 18...28,
                    step: 1
                )
            }

            controlCard(title: "풍량", subtitle: "\(Int(secondaryBinding(defaultValue: 3).wrappedValue))단") {
                Slider(value: secondaryBinding(defaultValue: 3), in: 1...5, step: 1)
            }
        }
    }

    private var lightingControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "조명 모드", subtitle: appliance.mode) {
                Picker("조명 모드", selection: $appliance.mode) {
                    ForEach(["집중", "휴식", "수면"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "밝기", subtitle: "\(Int(appliance.primaryValue))%") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 0...100,
                    step: 1
                )
            }

            controlCard(title: "색온도", subtitle: "\(Int(secondaryBinding(defaultValue: 4200).wrappedValue))K") {
                Slider(value: secondaryBinding(defaultValue: 4200), in: 2700...6500, step: 100)
            }
        }
    }

    private var airPurifierControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "운전 모드", subtitle: appliance.mode) {
                Picker("운전 모드", selection: $appliance.mode) {
                    ForEach(["자동", "수동", "저소음"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "풍량", subtitle: "\(Int(appliance.primaryValue))단") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 1...5,
                    step: 1
                )
            }

            controlCard(title: "공기질 표시", subtitle: appliance.status.isEmpty ? "공기질 상태" : appliance.status) {
                Picker("공기질", selection: $appliance.status) {
                    Text("공기질 좋음").tag("공기질 좋음")
                    Text("공기질 보통").tag("공기질 보통")
                    Text("공기질 나쁨").tag("공기질 나쁨")
                }
                .pickerStyle(.segmented)
            }
        }
    }

    private var dehumidifierControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "제습 모드", subtitle: appliance.mode) {
                Picker("제습 모드", selection: $appliance.mode) {
                    ForEach(["일반", "연속", "세탁물"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "목표 습도", subtitle: "\(Int(appliance.primaryValue))%") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 35...60,
                    step: 1
                )
            }

            controlCard(title: "송풍 세기", subtitle: "\(Int(secondaryBinding(defaultValue: 2).wrappedValue))단") {
                Slider(value: secondaryBinding(defaultValue: 2), in: 1...4, step: 1)
            }
        }
    }

    private var humidifierControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "가습 모드", subtitle: appliance.mode) {
                Picker("가습 모드", selection: $appliance.mode) {
                    ForEach(["자동", "수면", "쾌적"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "목표 습도", subtitle: "\(Int(appliance.primaryValue))%") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 40...65,
                    step: 1
                )
            }

            controlCard(title: "분무 세기", subtitle: "\(Int(secondaryBinding(defaultValue: 2).wrappedValue))단") {
                Slider(value: secondaryBinding(defaultValue: 2), in: 1...4, step: 1)
            }
        }
    }

    private var tvControls: some View {
        VStack(spacing: 12) {
            controlCard(title: "입력/장면", subtitle: appliance.mode) {
                Picker("입력/장면", selection: $appliance.mode) {
                    ForEach(["HDMI 1", "OTT", "게임", "음악"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _ in
                    appliance.syncStatusFromControls()
                }
            }

            controlCard(title: "볼륨", subtitle: "\(Int(appliance.primaryValue))") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 0...100,
                    step: 1
                )
            }

            controlCard(title: "화면 밝기", subtitle: "\(Int(secondaryBinding(defaultValue: 65).wrappedValue))%") {
                Slider(value: secondaryBinding(defaultValue: 65), in: 30...100, step: 1)
            }
        }
    }

    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("상태 메모")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.black)

            Text(appliance.status)
                .font(.system(size: 14))
                .foregroundColor(.gray)
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(14)
        .shadow(color: Color.black.opacity(0.05), radius: 6, x: 0, y: 2)
    }

    private func controlCard<Content: View>(title: String, subtitle: String? = nil, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.black)

                Spacer()

                if let subtitle {
                    Text(subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.gray)
                }
            }

            content()
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(14)
        .shadow(color: Color.black.opacity(0.05), radius: 8, x: 0, y: 4)
    }

    private func valueBadge(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.system(size: 12))
                .foregroundColor(.gray)

            Text(value)
                .font(.system(size: 18, weight: .bold))
                .foregroundColor(.black)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(Color(hex: "F5F5F7"))
        .cornerRadius(12)
    }

    private func secondaryBinding(defaultValue: Double) -> Binding<Double> {
        Binding(
            get: { appliance.secondaryValue ?? defaultValue },
            set: { newValue in
                appliance.secondaryValue = newValue
                appliance.syncStatusFromControls()
            }
        )
    }
}

#Preview {
    NavigationStack {
        ApplianceDetailView(
            appliance: .constant(
                ApplianceItem(
                    type: .airConditioner,
                    location: "거실",
                    status: "실내 27°C",
                    mode: "냉방",
                    isOn: true,
                    primaryValue: 23,
                    secondaryValue: 3
                )
            )
        )
    }
}
