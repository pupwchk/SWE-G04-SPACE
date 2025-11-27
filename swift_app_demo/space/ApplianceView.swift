//
//  ApplianceView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Appliance screen - manages home appliances
struct ApplianceView: View {
    @State private var appliances: [ApplianceItem] = ApplianceItem.sampleAppliances
    @State private var selectedAppliance: ApplianceItem?

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 16) {
                        ForEach(appliances) { appliance in
                            Button(action: {
                                selectedAppliance = appliance
                            }) {
                                ApplianceItemCard(
                                    appliance: appliance,
                                    isOn: Binding(
                                        get: { appliance.isOn },
                                        set: { newValue in
                                            if let index = appliances.firstIndex(where: { $0.id == appliance.id }) {
                                                appliances[index].isOn = newValue
                                                appliances[index].syncStatusFromControls()
                                            }
                                        }
                                    )
                                )
                            }
                            .buttonStyle(.plain)
                        }

                        Button(action: {
                            handleAddAppliance()
                        }) {
                            VStack(spacing: 8) {
                                Text("제품 추가")
                                    .font(.system(size: 16, weight: .regular))
                                    .foregroundColor(.black)

                                Image(systemName: "plus")
                                    .font(.system(size: 24, weight: .regular))
                                    .foregroundColor(.black)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 32)
                        }
                        .buttonStyle(.plain)

                        Spacer(minLength: 40)
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                }
            }
            .navigationTitle("가전제품")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        // Handle QR code scan
                    }) {
                        Image(systemName: "qrcode.viewfinder")
                            .foregroundColor(.black)
                    }
                }
            }
            .navigationDestination(item: $selectedAppliance) { appliance in
                if let binding = binding(for: appliance) {
                    ApplianceDetailView(appliance: binding)
                } else {
                    Text("선택한 기기를 불러올 수 없습니다.")
                }
            }
        }
    }

    // MARK: - Helpers

    private func binding(for appliance: ApplianceItem) -> Binding<ApplianceItem>? {
        guard let index = appliances.firstIndex(where: { $0.id == appliance.id }) else { return nil }
        return $appliances[index]
    }

    private func handleAddAppliance() {
        // TODO: Navigate to add appliance screen
        print("Add appliance tapped")
    }
}

// MARK: - Appliance Types

enum ApplianceType: String, CaseIterable, Identifiable {
    case airConditioner, lighting, airPurifier, dehumidifier, humidifier, tv

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .airConditioner: return "에어컨"
        case .lighting: return "조명"
        case .airPurifier: return "공기청정기"
        case .dehumidifier: return "제습기"
        case .humidifier: return "가습기"
        case .tv: return "TV"
        }
    }

    var iconName: String {
        switch self {
        case .airConditioner: return "wind"
        case .lighting: return "lightbulb.fill"
        case .airPurifier: return "aqi.medium"
        case .dehumidifier: return "drop.circle.fill"
        case .humidifier: return "drop.fill"
        case .tv: return "tv.fill"
        }
    }

    var accentColor: Color {
        switch self {
        case .airConditioner: return Color(hex: "3A86FF")
        case .lighting: return Color(hex: "FFB703")
        case .airPurifier: return Color(hex: "6ECB63")
        case .dehumidifier: return Color(hex: "5DB7DE")
        case .humidifier: return Color(hex: "B983FF")
        case .tv: return Color(hex: "A50034")
        }
    }

    var primaryLabel: String {
        switch self {
        case .airConditioner: return "설정 온도"
        case .lighting: return "밝기"
        case .airPurifier: return "풍량"
        case .dehumidifier: return "목표 습도"
        case .humidifier: return "목표 습도"
        case .tv: return "볼륨"
        }
    }

    var secondaryLabel: String? {
        switch self {
        case .airConditioner: return "풍량"
        case .lighting: return "색온도"
        case .airPurifier: return "공기질"
        case .dehumidifier: return "송풍 세기"
        case .humidifier: return "분무 세기"
        case .tv: return "화면 밝기"
        }
    }

    func primaryDisplay(for item: ApplianceItem) -> String {
        switch self {
        case .airConditioner:
            return "\(Int(item.primaryValue))°C"
        case .lighting:
            return "\(Int(item.primaryValue))%"
        case .airPurifier:
            return "\(Int(item.primaryValue))단"
        case .dehumidifier, .humidifier:
            return "\(Int(item.primaryValue))%"
        case .tv:
            return "\(Int(item.primaryValue))"
        }
    }

    func secondaryDisplay(for item: ApplianceItem) -> String? {
        switch self {
        case .airConditioner:
            guard let level = item.secondaryValue else { return nil }
            return "풍량 \(Int(level))단"
        case .lighting:
            guard let colorTemp = item.secondaryValue else { return nil }
            return "\(Int(colorTemp))K"
        case .airPurifier:
            return item.status.isEmpty ? nil : item.status
        case .dehumidifier:
            guard let level = item.secondaryValue else { return nil }
            return "\(Int(level))단"
        case .humidifier:
            guard let level = item.secondaryValue else { return nil }
            return "\(Int(level))단"
        case .tv:
            guard let brightness = item.secondaryValue else { return nil }
            return "\(Int(brightness))%"
        }
    }

    func summary(for item: ApplianceItem) -> String {
        if !item.isOn {
            return "전원 꺼짐"
        }

        switch self {
        case .airConditioner:
            return "\(item.mode) · \(primaryDisplay(for: item))"
        case .lighting:
            return "\(item.mode) · 밝기 \(Int(item.primaryValue))%"
        case .airPurifier:
            return "\(item.mode) · \(Int(item.primaryValue))단"
        case .dehumidifier:
            return "\(item.mode) · 목표 \(Int(item.primaryValue))%"
        case .humidifier:
            return "\(item.mode) · 목표 \(Int(item.primaryValue))%"
        case .tv:
            return "\(item.mode) · 볼륨 \(Int(item.primaryValue))"
        }
    }
}

// MARK: - Appliance Data Model

struct ApplianceItem: Identifiable, Hashable {
    let id: UUID
    let type: ApplianceType
    var location: String
    var status: String
    var mode: String
    var isOn: Bool
    var primaryValue: Double
    var secondaryValue: Double?

    init(
        id: UUID = UUID(),
        type: ApplianceType,
        location: String,
        status: String,
        mode: String,
        isOn: Bool,
        primaryValue: Double,
        secondaryValue: Double? = nil
    ) {
        self.id = id
        self.type = type
        self.location = location
        self.status = status
        self.mode = mode
        self.isOn = isOn
        self.primaryValue = primaryValue
        self.secondaryValue = secondaryValue
    }

    static func == (lhs: ApplianceItem, rhs: ApplianceItem) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

extension ApplianceItem {
    var primaryLabel: String { type.primaryLabel }
    var primaryValueText: String { type.primaryDisplay(for: self) }
    var secondaryLabel: String? { type.secondaryLabel }
    var secondaryValueText: String? { type.secondaryDisplay(for: self) }
    var statusSummary: String { type.summary(for: self) }
    var iconName: String { type.iconName }
    var accentColor: Color { type.accentColor }

    mutating func syncStatusFromControls() {
        switch type {
        case .airConditioner:
            status = "\(mode) · \(Int(primaryValue))°C"
        case .lighting:
            let colorTemp = Int(secondaryValue ?? 4000)
            status = "색온도 \(colorTemp)K"
        case .airPurifier:
            if status.isEmpty {
                status = "공기질 보통"
            }
        case .dehumidifier:
            status = "\(mode) · 목표 \(Int(primaryValue))%"
        case .humidifier:
            status = "\(mode) · 목표 \(Int(primaryValue))%"
        case .tv:
            status = "\(mode) · 볼륨 \(Int(primaryValue))"
        }
    }

    static let sampleAppliances: [ApplianceItem] = [
        ApplianceItem(
            type: .airConditioner,
            location: "거실",
            status: "실내 27°C",
            mode: "냉방",
            isOn: true,
            primaryValue: 23,
            secondaryValue: 3
        ),
        ApplianceItem(
            type: .lighting,
            location: "거실",
            status: "따뜻한 색온도",
            mode: "집중",
            isOn: true,
            primaryValue: 70,
            secondaryValue: 4200
        ),
        ApplianceItem(
            type: .airPurifier,
            location: "거실",
            status: "공기질 좋음",
            mode: "자동",
            isOn: true,
            primaryValue: 3,
            secondaryValue: 12
        ),
        ApplianceItem(
            type: .dehumidifier,
            location: "안방",
            status: "세탁물 건조",
            mode: "세탁물",
            isOn: true,
            primaryValue: 45,
            secondaryValue: 2
        ),
        ApplianceItem(
            type: .humidifier,
            location: "아이방",
            status: "수면 모드",
            mode: "수면",
            isOn: true,
            primaryValue: 50,
            secondaryValue: 2
        ),
        ApplianceItem(
            type: .tv,
            location: "거실",
            status: "OTT 시청 중",
            mode: "OTT",
            isOn: true,
            primaryValue: 18,
            secondaryValue: 65
        )
    ]
}

#Preview {
    ApplianceView()
}
