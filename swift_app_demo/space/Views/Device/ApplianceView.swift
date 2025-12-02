//
//  ApplianceView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Appliance screen - manages home appliances
struct ApplianceView: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var appliances: [ApplianceItem] = []
    @State private var selectedAppliance: ApplianceItem?
    @State private var isLoadingAppliances = false
    @State private var autoRefreshTask: Task<Void, Never>?

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
                                                Task {
                                                    let action = newValue ? "on" : "off"
                                                    _ = await appliances[index].saveToBackend(action: action)
                                                    await loadAppliances()  // Reload after save
                                                }
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
                        .onDisappear {
                            // Reload appliances when returning from detail view
                            Task {
                                await loadAppliances()
                            }
                        }
                } else {
                    Text("선택한 기기를 불러올 수 없습니다.")
                }
            }
        }
        .task {
            await loadAppliances()
        }
        .onAppear {
            startAutoRefresh()
        }
        .onDisappear {
            stopAutoRefresh()
        }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active:
                startAutoRefresh()
                Task { await loadAppliances() }  // Refresh when returning to foreground
            case .inactive, .background:
                stopAutoRefresh()
            @unknown default:
                break
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

    private func loadAppliances() async {
        guard !isLoadingAppliances else {
            print("⏳ [ApplianceView] Already loading appliances, skipping...")
            return
        }

        guard let fastAPIUserId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("⚠️ [ApplianceView] FastAPI user ID not found")
            return
        }

        await MainActor.run {
            isLoadingAppliances = true
        }

        print("🔄 [ApplianceView] Reloading appliances from backend...")
        let items = await FastAPIService.shared.fetchApplianceItems(userId: fastAPIUserId)

        await MainActor.run {
            appliances = items
            isLoadingAppliances = false
            print("✅ [ApplianceView] Loaded \(items.count) appliances")
        }
    }

    private func startAutoRefresh() {
        guard autoRefreshTask == nil else { return }
        autoRefreshTask = Task {
            while !Task.isCancelled {
                await loadAppliances()
                try? await Task.sleep(nanoseconds: 10 * 1_000_000_000)
            }
        }
    }

    private func stopAutoRefresh() {
        autoRefreshTask?.cancel()
        autoRefreshTask = nil
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
        case .airPurifier: return "바람 세기"
        case .dehumidifier: return "목표 습도"
        case .humidifier: return "목표 습도"
        case .tv: return "볼륨"
        }
    }

    var secondaryLabel: String? {
        switch self {
        case .airConditioner: return "바람 세기"
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
            return "바람 세기 \(Int(level))단"
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
    let backendId: String?  // Original backend ID for API calls
    let type: ApplianceType
    var location: String
    var status: String
    var mode: String
    var isOn: Bool
    var primaryValue: Double
    var secondaryValue: Double?
    var hasCustomStatus: Bool

    init(
        id: UUID = UUID(),
        backendId: String? = nil,
        type: ApplianceType,
        location: String,
        status: String,
        mode: String,
        isOn: Bool,
        primaryValue: Double,
        secondaryValue: Double? = nil,
        hasCustomStatus: Bool = false
    ) {
        self.id = id
        self.backendId = backendId
        self.type = type
        self.location = location
        self.status = status
        self.mode = mode
        self.isOn = isOn
        self.primaryValue = primaryValue
        self.secondaryValue = secondaryValue
        self.hasCustomStatus = hasCustomStatus
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

    mutating func syncStatusFromControls(force: Bool = false) {
        guard force || !hasCustomStatus else { return }

        switch type {
        case .airConditioner:
            status = "\(mode) · \(Int(primaryValue))°C"
        case .lighting:
            if let colorTemp = secondaryValue {
                status = "색온도 \(Int(colorTemp))K"
            } else {
                status = ""
            }
        case .airPurifier:
            break
        case .dehumidifier:
            status = "\(mode) · 목표 \(Int(primaryValue))%"
        case .humidifier:
            status = "\(mode) · 목표 \(Int(primaryValue))%"
        case .tv:
            status = "\(mode) · 볼륨 \(Int(primaryValue))"
        }
    }

    /// Save current appliance state to backend using smart-control
    /// - Parameter action: Optional explicit action ("on" / "off" / "set"). Defaults to "set" when isOn, otherwise "off".
    func saveToBackend(action actionOverride: String? = nil) async -> Bool {
        guard let userId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("⚠️ [ApplianceItem] FastAPI user ID not found")
            return false
        }

        let action = actionOverride ?? (isOn ? "set" : "off")
        let settings = buildSmartControlSettings()

        print("📤 [ApplianceItem] Smart-control \(type.displayName) (action: \(action))")
        return await FastAPIService.shared.controlAppliance(
            userId: userId,
            applianceType: type.displayName,
            action: action,
            settings: settings
        )
    }

    /// Build smart-control settings payload with numeric fan speeds
    private func buildSmartControlSettings() -> [String: Any] {
        var settings: [String: Any] = [:]

        switch type {
        case .airConditioner:
            settings["mode"] = mode
            settings["target_temp_c"] = Int(primaryValue)
            if let fanSpeed = fanSpeedLevel(secondaryValue) {
                settings["fan_speed"] = fanSpeed
            }

        case .lighting:
            settings["scene"] = mode
            settings["brightness_pct"] = Int(primaryValue)
            if let colorTemp = secondaryValue {
                settings["color_temperature_k"] = Int(colorTemp)
            }

        case .airPurifier:
            settings["mode"] = mode
            settings["fan_speed"] = Int(primaryValue)

        case .dehumidifier:
            settings["mode"] = mode
            settings["target_humidity_pct"] = Int(primaryValue)
            if let fanSpeed = fanSpeedLevel(secondaryValue) {
                settings["fan_speed"] = fanSpeed
            }

        case .humidifier:
            settings["mode"] = mode
            settings["target_humidity_pct"] = Int(primaryValue)
            if let mistLevel = secondaryValue {
                settings["mist_level"] = Int(mistLevel)
            }

        case .tv:
            settings["input_source"] = mode
            settings["volume"] = Int(primaryValue)
            if let brightness = secondaryValue {
                settings["brightness"] = Int(brightness)
            }
        }

        return settings
    }

    /// Convert fan-speed slider value to backend numeric level
    private func fanSpeedLevel(_ value: Double?) -> Int? {
        guard let value else { return nil }
        return Int(value)
    }
}

#Preview {
    ApplianceView()
}
