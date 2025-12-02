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
    @State private var isSaving = false
    @State private var saveError: String?
    @State private var saveTask: Task<Void, Never>?
    @Environment(\.dismiss) private var dismiss

    // Callback to notify parent view to reload data after successful save
    var onSaveSuccess: (() async -> Void)?

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                headerCard

                controlSection

                statusCard

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
                    appliance.hasCustomStatus = false
                    appliance.syncStatusFromControls(force: true)
                }) {
                    Image(systemName: "arrow.triangle.2.circlepath")
                        .foregroundColor(appliance.accentColor)
                }
            }
        }
    }

    private var headerCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .center, spacing: 12) {
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [
                                    appliance.accentColor.opacity(0.24),
                                    appliance.accentColor.opacity(0.12)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 52, height: 52)

                    Image(systemName: appliance.iconName)
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(appliance.accentColor)
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text(appliance.type.displayName)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.black)

                    HStack(spacing: 8) {
                        Label(appliance.location, systemImage: "mappin.and.ellipse")
                            .labelStyle(.titleAndIcon)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.gray)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 6)
                            .background(Color.white.opacity(0.8))
                            .cornerRadius(20)

                        Text(appliance.statusSummary)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.black.opacity(0.85))
                    }

                    if !appliance.status.isEmpty {
                        Text(appliance.status)
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                    }
                }

                Spacer()

                Toggle("", isOn: Binding(
                    get: { appliance.isOn },
                    set: { newValue in
                        appliance.isOn = newValue
                        // For toggle, save immediately without debounce
                        saveChangesImmediately(actionOverride: newValue ? "on" : "off")
                    }
                ))
                    .labelsHidden()
                    .tint(appliance.accentColor)
            }

            if !appliance.mode.isEmpty {
                Text(appliance.mode)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(appliance.accentColor)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(appliance.accentColor.opacity(0.12))
                    .cornerRadius(10)
            }

            if let secondaryText = appliance.secondaryValueText {
                HStack(spacing: 12) {
                    infoChip(title: appliance.primaryLabel, icon: "gauge.medium", value: appliance.primaryValueText)
                    infoChip(title: appliance.secondaryLabel ?? "설정", icon: "slider.horizontal.3", value: secondaryText)
                }
            } else {
                infoChip(title: appliance.primaryLabel, icon: "gauge.medium", value: appliance.primaryValueText)
            }
        }
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            LinearGradient(
                gradient: Gradient(colors: [
                    appliance.accentColor.opacity(0.16),
                    Color.white
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18)
                .stroke(appliance.accentColor.opacity(0.12), lineWidth: 1)
                .allowsHitTesting(false)
        )
        .cornerRadius(18)
        .shadow(color: Color.black.opacity(0.05), radius: 10, x: 0, y: 6)
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
                    ForEach(["냉방", "난방", "제습", "송풍", "자동"], id: \.self) { mode in
                        Text(mode).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
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
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing {
                            saveChanges()
                        }
                    }
                )
                sliderLabels(min: "18°C", value: "\(Int(appliance.primaryValue))°C", max: "28°C")
            }

            if let fanSpeed = secondaryBinding() {
                controlCard(title: "바람 세기", subtitle: "\(Int(fanSpeed.wrappedValue))단") {
                    Slider(value: fanSpeed, in: 1...5, step: 1, onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    })
                    sliderLabels(
                        min: "1단",
                        value: "\(Int(fanSpeed.wrappedValue))단",
                        max: "5단"
                    )
                }
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
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
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
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    }
                )
                sliderLabels(min: "0%", value: "\(Int(appliance.primaryValue))%", max: "100%")
            }

            if let colorTemp = secondaryBinding() {
                controlCard(title: "색온도", subtitle: "\(Int(colorTemp.wrappedValue))K") {
                    Slider(value: colorTemp, in: 2700...6500, step: 100, onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    })
                    sliderLabels(
                        min: "2700K",
                        value: "\(Int(colorTemp.wrappedValue))K",
                        max: "6500K"
                    )
                }
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
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
                }
            }

            controlCard(title: "바람 세기", subtitle: "\(Int(appliance.primaryValue))단") {
                Slider(
                    value: Binding(
                        get: { appliance.primaryValue },
                        set: { newValue in
                            appliance.primaryValue = newValue
                            appliance.syncStatusFromControls()
                        }
                    ),
                    in: 1...5,
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    }
                )
                sliderLabels(min: "1단", value: "\(Int(appliance.primaryValue))단", max: "5단")
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
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
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
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    }
                )
                sliderLabels(min: "35%", value: "\(Int(appliance.primaryValue))%", max: "60%")
            }

            if let fanSpeed = secondaryBinding() {
                controlCard(title: "송풍 세기", subtitle: "\(Int(fanSpeed.wrappedValue))단") {
                    Slider(value: fanSpeed, in: 1...4, step: 1, onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    })
                    sliderLabels(
                        min: "1단",
                        value: "\(Int(fanSpeed.wrappedValue))단",
                        max: "4단"
                    )
                }
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
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
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
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    }
                )
                sliderLabels(min: "40%", value: "\(Int(appliance.primaryValue))%", max: "65%")
            }

            if let mistLevel = secondaryBinding() {
                controlCard(title: "분무 세기", subtitle: "\(Int(mistLevel.wrappedValue))단") {
                    Slider(value: mistLevel, in: 1...4, step: 1, onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    })
                    sliderLabels(
                        min: "1단",
                        value: "\(Int(mistLevel.wrappedValue))단",
                        max: "4단"
                    )
                }
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
                .onChange(of: appliance.mode) { _, _ in
                    appliance.syncStatusFromControls()
                    saveChanges()
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
                    step: 1,
                    onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    }
                )
                sliderLabels(min: "0", value: "\(Int(appliance.primaryValue))", max: "100")
            }

            if let brightness = secondaryBinding() {
                controlCard(title: "화면 밝기", subtitle: "\(Int(brightness.wrappedValue))%") {
                    Slider(value: brightness, in: 30...100, step: 1, onEditingChanged: { editing in
                        if !editing { saveChanges() }
                    })
                    sliderLabels(
                        min: "30%",
                        value: "\(Int(brightness.wrappedValue))%",
                        max: "100%"
                    )
                }
            }
        }
    }

    private var statusCard: some View {
        controlCard(title: "상태 메모") {
            VStack(alignment: .leading, spacing: 10) {
                TextField(
                    "메모를 입력해 주세요",
                    text: Binding(
                        get: { appliance.status },
                        set: { newValue in
                            appliance.status = newValue
                            appliance.hasCustomStatus = true
                        }
                    )
                )
                .textFieldStyle(.roundedBorder)

                HStack(spacing: 8) {
                    Label(
                        appliance.hasCustomStatus ? "사용자 입력을 유지 중" : "제어값에 따라 자동 업데이트",
                        systemImage: appliance.hasCustomStatus ? "pencil.circle" : "arrow.triangle.2.circlepath"
                    )
                    .font(.system(size: 12))
                    .foregroundColor(.gray)

                    Spacer()

                    if appliance.hasCustomStatus {
                        Button("자동 값으로 복원") {
                            appliance.hasCustomStatus = false
                            appliance.syncStatusFromControls(force: true)
                        }
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(appliance.accentColor)
                    }
                }
            }
        }
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
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(appliance.accentColor)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(appliance.accentColor.opacity(0.12))
                        .cornerRadius(10)
                }
            }

            content()
                .tint(appliance.accentColor)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(appliance.accentColor.opacity(0.08), lineWidth: 1)
                        .allowsHitTesting(false)
                )
        )
        .shadow(color: Color.black.opacity(0.04), radius: 12, x: 0, y: 6)
    }

    private func infoChip(title: String, icon: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(appliance.accentColor)

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 12))
                        .foregroundColor(.gray)

                    Text(value)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white.opacity(0.92))
        .cornerRadius(14)
    }

    private func secondaryBinding(autoSave: Bool = false) -> Binding<Double>? {
        guard appliance.secondaryValue != nil else { return nil }

        return Binding(
            get: { appliance.secondaryValue ?? 0 },
            set: { newValue in
                appliance.secondaryValue = newValue
                appliance.syncStatusFromControls()
                if autoSave {
                    saveChanges()
                }
            }
        )
    }

    private func sliderLabels(min: String, value: String, max: String) -> some View {
        HStack {
            Text(min)
                .font(.system(size: 12))
                .foregroundColor(.gray)

            Spacer()

            Text(value)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(appliance.accentColor)

            Spacer()

            Text(max)
                .font(.system(size: 12))
                .foregroundColor(.gray)
        }
    }

    // MARK: - Backend Save

    /// Save changes with debouncing (for sliders and pickers)
    private func saveChanges(actionOverride: String? = nil) {
        // Cancel previous save task if exists (debouncing)
        saveTask?.cancel()

        // Create new save task with debounce delay
        saveTask = Task {
            // Wait for 500ms to allow user to finish adjusting
            try? await Task.sleep(nanoseconds: 500_000_000)

            // Check if task was cancelled
            guard !Task.isCancelled else { return }

            await performSave(actionOverride: actionOverride)
        }
    }

    /// Save changes immediately without debouncing (for toggles)
    private func saveChangesImmediately(actionOverride: String? = nil) {
        // Cancel any pending debounced saves
        saveTask?.cancel()

        Task {
            await performSave(actionOverride: actionOverride)
        }
    }

    /// Perform the actual save operation
    private func performSave(actionOverride: String?) async {
        await MainActor.run { isSaving = true }

        let success = await appliance.saveToBackend(action: actionOverride)

        await MainActor.run {
            isSaving = false
            if success {
                // Trigger parent view reload to sync with backend state
                Task {
                    await onSaveSuccess?()
                }
            } else {
                saveError = "설정 저장에 실패했습니다"
                // Show error for 3 seconds
                Task {
                    try? await Task.sleep(nanoseconds: 3_000_000_000)
                    saveError = nil
                }
            }
        }
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
