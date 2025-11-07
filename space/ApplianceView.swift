//
//  ApplianceView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Appliance screen - manages home appliances
struct ApplianceView: View {
    @State private var appliances: [ApplianceItem] = [
        ApplianceItem(id: 1, title: "에어컨 1", status: "거실", temperatureLabel: "실내 온도", temperature: "30°C", isOn: false),
        ApplianceItem(id: 2, title: "에어컨 2", status: "거실", temperatureLabel: "설정 온도", temperature: "18°C", isOn: true)
    ]
    @State private var selectedAppliance: ApplianceItem?

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 16) {
                        // Appliance cards
                        ForEach(appliances) { appliance in
                            Button(action: {
                                selectedAppliance = appliance
                            }) {
                                ApplianceItemCard(
                                    title: appliance.title,
                                    status: appliance.status,
                                    temperatureLabel: appliance.temperatureLabel,
                                    temperature: appliance.temperature,
                                    isOn: Binding(
                                        get: { appliance.isOn },
                                        set: { newValue in
                                            if let index = appliances.firstIndex(where: { $0.id == appliance.id }) {
                                                appliances[index].isOn = newValue
                                            }
                                        }
                                    )
                                )
                            }
                            .buttonStyle(.plain)
                        }

                        // Add button
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
            .navigationTitle("Devices")
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
                DeviceDetailView(appliance: appliance)
            }
        }
    }

    // MARK: - Actions

    private func handleAddAppliance() {
        // TODO: Navigate to add appliance screen
        print("Add appliance tapped")
    }
}

// MARK: - Appliance Data Model

struct ApplianceItem: Identifiable, Hashable {
    let id: Int
    let title: String
    let status: String
    let temperatureLabel: String
    let temperature: String
    var isOn: Bool
}

#Preview {
    ApplianceView()
}
